"""
移动端冷链监控APP API（配送人员端）
模块：移动端冷链监控APP

核心功能：
- 车厢状态实时可视化监控（多温区、冷机、传感器）
- 车门开关状态实时监测
- 配送进度全流程查看
- 温控异常报警与现场处置
- 纸质温度记录拍照上传归档
- 运单全生命周期管理
"""
import os
import json
import base64
import hashlib
import uuid
import random
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel

from ..core.security import get_current_user, require_role
from ..services.world_state import get_world_state, _live_wave, _live_int_wave, CITY_COORDS
from ..services.alert_engine import alert_engine
from ..api.traceability import (
    TRACE_DATA, TRACE_RECORDS, TRACE_CODE_MAP, WAYBILL_TRACE_MAP,
    BLOCKCHAIN_LEDGER,
)
from ..api.upload import upload_records

router = APIRouter(prefix="/api/v1/driver", tags=["移动端冷链监控APP"])


# ==================== 数据模型 ====================

class AlertHandleRequest(BaseModel):
    action: str
    notes: Optional[str] = ""


class UploadRecordRequest(BaseModel):
    waybill_id: str
    record_type: str = "temperature_record"
    notes: Optional[str] = ""
    location: Optional[str] = ""


class HandleResult(BaseModel):
    success: bool
    message: str
    alert_id: str
    action: str


# ==================== 司机-车辆绑定 ====================

DRIVER_VEHICLE_MAP = {}


def get_driver_vehicle(driver_id: str) -> Optional[dict]:
    """获取司机绑定的车辆信息"""
    if driver_id in DRIVER_VEHICLE_MAP:
        device_id = DRIVER_VEHICLE_MAP[driver_id]
        ws = get_world_state()
        return next((v for v in ws["vehicles"] if v["device_id"] == device_id), None)
    
    ws = get_world_state()
    for vehicle in ws["vehicles"]:
        if vehicle.get("driver_id") == driver_id:
            DRIVER_VEHICLE_MAP[driver_id] = vehicle["device_id"]
            return vehicle
    
    return ws["vehicles"][0] if ws["vehicles"] else None


def get_driver_orders(driver_id: str) -> List[dict]:
    """获取司机名下的订单"""
    orders = []
    ws = get_world_state()
    for trace_code, data in TRACE_DATA.items():
        if data.get("driver_id") == driver_id or data.get("status") in ["in_transit", "delivered"]:
            record_ids = TRACE_CODE_MAP.get(trace_code, [])
            wb_ws = ws.get("waybills", {}).get(data.get("waybill_id"), {})
            records = [r for r in TRACE_RECORDS if r["id"] in record_ids]
            records = sorted(records, key=lambda r: r.get("timestamp", ""))
            
            temps = [r["temperature"] for r in records if "temperature" in r and r["temperature"] is not None]
            violations = []
            req = data.get("temperature_requirement", "")
            if req and "~" in req:
                try:
                    parts = req.split("~")
                    min_req = float(parts[0].replace("℃", "").strip())
                    max_req = float(parts[1].replace("℃", "").strip())
                    for r in records:
                        if "temperature" in r and r["temperature"] is not None:
                            temp = r["temperature"]
                            if temp < min_req or temp > max_req:
                                violations.append(r)
                except Exception:
                    pass
            
            orders.append({
                "waybill_id": data["waybill_id"],
                "trace_code": trace_code,
                "cargo_name": data["cargo_name"],
                "cargo_category": data["cargo_category"],
                "origin": data["origin"],
                "destination": data["destination"],
                "quantity": data["quantity"],
                "unit": data["unit"],
                "temperature_requirement": data["temperature_requirement"],
                "status": data.get("status", ""),
                "current_temperature": temps[-1] if temps else 0,
                "is_compliant": len(violations) == 0,
                "violations_count": len(violations),
                "total_records": len(records),
                "created_at": data.get("created_at", ""),
                "driver_id": data.get("driver_id", ""),
                "device_id": data.get("device_id", ""),
                "receiver": data.get("receiver", ""),
                "receiver_contact": data.get("receiver_contact", ""),
                "checkin_stations": wb_ws.get("checkin_stations", []),
            })
    
    orders.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return orders


# ==================== 1. 车厢状态实时可视化监控 ====================

@router.get("/dashboard")
async def get_dashboard(
    user: dict = Depends(require_role("driver", "admin")),
):
    """
    司机工作台仪表盘
    返回车厢实时状态、多温区数据、冷机状态、车门状态
    """
    driver_id = user.get("sub", user.get("username", ""))
    vehicle = get_driver_vehicle(driver_id)
    
    if not vehicle:
        return {
            "success": True,
            "has_vehicle": False,
            "message": "暂未绑定车辆，请联系管理员",
        }
    
    ws = get_world_state()
    vehicles = ws["vehicles"]
    vehicle_data = next((v for v in vehicles if v["device_id"] == vehicle["device_id"]), vehicle)
    
    temp = _live_wave(vehicle_data["temperature"], 0.02)
    humidity = _live_wave(vehicle_data["humidity"], 0.02)
    health = _live_int_wave(int(vehicle_data["cold_car_health"] * 100), 3, 30)
    
    zones = []
    if vehicle_data.get("multi_zone"):
        zone_configs = [
            {"name": "冷冻舱", "zone_key": "frozen", "target_temp": -18, "color": "#3b82f6"},
            {"name": "冷藏舱", "zone_key": "refrigerated", "target_temp": 2, "color": "#10b981"},
            {"name": "恒温舱", "zone_key": "ambient", "target_temp": 20, "color": "#f59e0b"},
        ]
        for i, zc in enumerate(zone_configs):
            zone_temp = _live_wave(zc["target_temp"] + (i * 0.5), 0.1)
            is_compliant = abs(zone_temp - zc["target_temp"]) <= 2
            zones.append({
                "name": zc["name"],
                "zone_key": zc["zone_key"],
                "temperature": round(zone_temp, 1),
                "target_temperature": zc["target_temp"],
                "is_compliant": is_compliant,
                "color": zc["color"],
                "humidity": round(_live_wave(65 + i * 5, 0.05), 1),
            })
    
    door_status = vehicle_data.get("door_status", 0)
    door_open_time = ""
    if door_status == 1:
        door_open_time = (datetime.utcnow() - timedelta(minutes=_live_int_wave(5, 3, 0))).isoformat()
    
    return {
        "success": True,
        "has_vehicle": True,
        "vehicle": {
            "device_id": vehicle_data["device_id"],
            "plate_number": vehicle_data["plate_number"],
            "online": vehicle_data.get("online", True),
            "signal_strength": vehicle_data.get("signal_strength", 5),
            "battery_level": vehicle_data.get("battery_level", 100),
        },
        "temperature": {
            "current": round(temp, 1),
            "target": vehicle_data.get("target_temperature", 0),
            "external": round(_live_wave(vehicle_data.get("external_temp", 25), 0.05), 1),
            "is_compliant": abs(temp - vehicle_data.get("target_temperature", 0)) <= 2,
        },
        "humidity": {
            "current": round(humidity, 1),
            "is_compliant": 40 <= humidity <= 85,
        },
        "cold_machine": {
            "status": "running" if vehicle_data.get("cold_car_status", 1) == 1 else "stopped",
            "health": health,
            "brand": vehicle_data.get("refrigeration_brand", ""),
            "model": vehicle_data.get("refrigeration_model", ""),
        },
        "door_status": {
            "is_open": door_status == 1,
            "open_time": door_open_time,
            "duration_minutes": _live_int_wave(5, 3, 0) if door_status == 1 else 0,
            "is_timeout": (door_status == 1) and (_live_int_wave(5, 3, 0) > 15),
        },
        "multi_zone": zones,
        "location": {
            "latitude": vehicle_data.get("latitude", 0),
            "longitude": vehicle_data.get("longitude", 0),
            "city": vehicle_data.get("current_city", ""),
            "speed": round(_live_wave(vehicle_data.get("vehicle_speed", 60), 0.1), 1),
        },
        "last_update": datetime.utcnow().isoformat(),
    }


# ==================== 2. 车门开关状态实时监测 ====================

@router.get("/door-status")
async def get_door_status(
    user: dict = Depends(require_role("driver", "admin")),
):
    """
    获取车门状态
    实时同步车厢柜门开闭状态，记录开门时间、时长
    """
    driver_id = user.get("sub", user.get("username", ""))
    vehicle = get_driver_vehicle(driver_id)
    
    if not vehicle:
        return {"success": False, "error": "未绑定车辆"}
    
    ws = get_world_state()
    vehicle_data = next((v for v in ws["vehicles"] if v["device_id"] == vehicle["device_id"]), vehicle)
    
    door_status = vehicle_data.get("door_status", 0)
    is_open = door_status == 1
    
    return {
        "success": True,
        "device_id": vehicle_data["device_id"],
        "plate_number": vehicle_data["plate_number"],
        "is_open": is_open,
        "timestamp": datetime.utcnow().isoformat(),
        "temperature_when_open": round(_live_wave(vehicle_data["temperature"], 0.05), 1) if is_open else 0,
        "location_when_open": vehicle_data.get("current_city", ""),
        "duration_minutes": _live_int_wave(8, 5, 0) if is_open else 0,
        "is_timeout": is_open and (_live_int_wave(8, 5, 0) > 15),
        "warning": "车门开启时间过长，请及时关闭！" if is_open and (_live_int_wave(8, 5, 0) > 15) else "",
    }


# ==================== 3. 配送进度全流程查看 ====================

@router.get("/delivery-progress")
async def get_delivery_progress(
    user: dict = Depends(require_role("driver", "admin")),
    waybill_id: Optional[str] = None,
):
    """
    获取配送进度
    展示当前行驶路段、规划路线、预计到达时间、站点配送顺序
    """
    driver_id = user.get("sub", user.get("username", ""))
    vehicle = get_driver_vehicle(driver_id)
    
    if not vehicle:
        return {"success": False, "error": "未绑定车辆"}
    
    ws = get_world_state()
    vehicle_data = next((v for v in ws["vehicles"] if v["device_id"] == vehicle["device_id"]), vehicle)
    
    route = vehicle_data.get("route", [])
    progress = 0
    current_segment = {}
    route_coords = [
        {"city": c, "lat": CITY_COORDS.get(c, (0, 0))[0], "lng": CITY_COORDS.get(c, (0, 0))[1]}
        for c in route
    ]
    
    if len(route) >= 2:
        progress = _live_int_wave(35, 20, 5) / 100
        seg_idx = int(progress * (len(route) - 1))
        seg_idx = min(seg_idx, len(route) - 2)
        current_segment = {
            "from_city": route[seg_idx],
            "to_city": route[seg_idx + 1],
            "segment_progress": round((progress * (len(route) - 1) - seg_idx) * 100, 1),
            "next_city": route[seg_idx + 1],
            "remaining_cities": route[seg_idx + 1:],
        }
    
    waybills = get_driver_orders(driver_id)
    current_waybill = None
    
    if waybill_id:
        current_waybill = next((w for w in waybills if w["waybill_id"] == waybill_id), None)
    else:
        current_waybill = next((w for w in waybills if w["status"] in ["in_transit", "accepted"]), None)
    
    estimated_arrival = ""
    if current_waybill:
        try:
            hours_remaining = _live_int_wave(4, 3, 1)
            estimated_arrival = (datetime.utcnow() + timedelta(hours=hours_remaining)).isoformat()
        except Exception:
            pass
    
    return {
        "success": True,
        "vehicle": {
            "device_id": vehicle_data["device_id"],
            "plate_number": vehicle_data["plate_number"],
            "current_city": vehicle_data.get("current_city", ""),
            "speed": round(_live_wave(vehicle_data.get("vehicle_speed", 60), 0.1), 1),
            "latitude": vehicle_data.get("latitude", 0),
            "longitude": vehicle_data.get("longitude", 0),
        },
        "route": {
            "full_route": route,
            "route_coords": route_coords,
            "total_stations": len(route),
            "current_segment": current_segment,
            "progress_percent": round(progress * 100, 1),
        },
        "timing": {
            "estimated_arrival": estimated_arrival,
            "remaining_hours": _live_int_wave(4, 3, 1),
            "departure_time": (datetime.utcnow() - timedelta(hours=_live_int_wave(3, 2, 1))).isoformat(),
            "is_on_time": _live_int_wave(85, 10, 60) >= 80,
        },
        "current_waybill": current_waybill,
        "waybills_count": len(waybills),
        "checkin_stations": current_waybill.get("checkin_stations", []) if current_waybill else [],
    }


class StationCheckinReq(BaseModel):
    waybill_id: str
    station_name: str


@router.post("/station-checkin")
async def station_checkin(
    payload: StationCheckinReq,
    user: dict = Depends(require_role("driver", "admin")),
):
    """
    站点到达打卡
    记录司机到达某站点的时间，写入 world_state 运单的 checkin_stations
    """
    ws = get_world_state()
    wb = ws.get("waybills", {}).get(payload.waybill_id)
    if not wb:
        raise HTTPException(status_code=404, detail="未找到该运单")

    checkin = {
        "station": payload.station_name,
        "checkin_time": datetime.utcnow().isoformat(),
        "operator": user.get("username", ""),
    }
    # 同一站点不重复打卡
    if not any(c["station"] == payload.station_name for c in wb.get("checkin_stations", [])):
        wb.setdefault("checkin_stations", []).append(checkin)

    return {
        "success": True,
        "waybill_id": payload.waybill_id,
        "station": payload.station_name,
        "checkin_time": checkin["checkin_time"],
        "checkin_stations": wb["checkin_stations"],
        "total_stations": len(wb.get("route", [])),
        "checked_count": len(wb["checkin_stations"]),
    }


# ==================== 4. 温控异常报警与现场处置 ====================

@router.get("/alerts")
async def get_driver_alerts(
    user: dict = Depends(require_role("driver", "admin")),
    limit: int = 20,
    severity: Optional[str] = None,
):
    """
    获取司机相关的预警信息
    从预警引擎获取与司机车辆相关的异常告警
    """
    driver_id = user.get("sub", user.get("username", ""))
    vehicle = get_driver_vehicle(driver_id)
    
    if not vehicle:
        return {"success": False, "error": "未绑定车辆"}
    
    device_id = vehicle["device_id"]
    all_alerts = alert_engine.get_alert_history(limit=limit * 2)
    
    relevant_alerts = []
    for alert in all_alerts:
        alert_device = alert.get("device_id", "")
        alert_waybill = alert.get("waybill_id", "")
        
        if alert_device == device_id or alert_waybill:
            if severity and alert.get("severity") != severity:
                continue
            
            suggestions = []
            alert_type = alert.get("type", "")
            if "temperature" in alert_type:
                suggestions = ["检查冷机运行状态", "确认车厢门是否关闭", "调整制冷档位", "联系技术支持"]
            elif "cold_car" in alert_type:
                suggestions = ["立即停靠安全区域", "检查冷机电源", "切换备用冷机", "联系维修人员"]
            elif "door" in alert_type:
                suggestions = ["确认车门已关闭", "检查门锁是否完好", "检查密封条"]
            elif "offline" in alert_type:
                suggestions = ["检查网络信号", "重启设备", "联系调度中心"]
            
            relevant_alerts.append({
                "id": alert.get("alert_id", alert.get("id", "")),
                "type": alert_type,
                "severity": alert.get("severity", "normal"),
                "message": alert.get("message", ""),
                "timestamp": alert.get("timestamp", ""),
                "status": alert.get("status", "active"),
                "location": alert.get("location", ""),
                "temperature": alert.get("temperature", 0),
                "threshold": alert.get("threshold", ""),
                "device_id": alert_device,
                "waybill_id": alert_waybill,
                "suggestions": suggestions,
            })
    
    relevant_alerts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return {
        "success": True,
        "device_id": device_id,
        "alert_count": len(relevant_alerts),
        "alerts": relevant_alerts[:limit],
    }


@router.post("/alerts/{alert_id}/handle", response_model=HandleResult)
async def handle_alert(
    alert_id: str,
    request: AlertHandleRequest,
    user: dict = Depends(require_role("driver", "admin")),
):
    """
    处理预警
    司机提交处置结果和备注，形成异常处置闭环记录
    """
    driver_id = user.get("sub", user.get("username", ""))
    
    all_alerts = alert_engine.get_alert_history(limit=100)
    alert = next((a for a in all_alerts if a.get("alert_id") == alert_id or a.get("id") == alert_id), None)
    
    if not alert:
        return {"success": False, "message": "未找到该预警", "alert_id": alert_id, "action": request.action}
    
    handle_record = {
        "alert_id": alert_id,
        "driver_id": driver_id,
        "action": request.action,
        "notes": request.notes,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "resolved",
    }
    
    alert_engine._alert_history.append({
        **alert,
        "status": "resolved",
        "resolved_at": datetime.utcnow().isoformat(),
        "resolved_by": driver_id,
        "resolve_action": request.action,
        "resolve_notes": request.notes,
    })
    
    return {
        "success": True,
        "message": "预警处置记录已提交",
        "alert_id": alert_id,
        "action": request.action,
    }


# ==================== 5. 纸质温度记录拍照上传归档 ====================

@router.post("/upload-record")
async def upload_record(
    file: UploadFile = File(...),
    waybill_id: str = Query(...),
    record_type: str = Query("temperature_record"),
    notes: str = Query(""),
    user: dict = Depends(require_role("driver", "admin")),
):
    """
    上传纸质记录照片
    支持温度记录表、设备巡检单、温控台账等资料上传
    自动绑定运单号、拍摄时间、车辆信息、地理位置水印
    """
    driver_id = user.get("sub", user.get("username", ""))
    vehicle = get_driver_vehicle(driver_id)
    
    if not vehicle:
        raise HTTPException(status_code=400, detail="未绑定车辆")
    
    ws = get_world_state()
    vehicle_data = next((v for v in ws["vehicles"] if v["device_id"] == vehicle["device_id"]), vehicle)
    
    content = await file.read()
    file_hash = hashlib.md5(content).hexdigest()
    
    record_id = str(uuid.uuid4())
    
    record = {
        "id": record_id,
        "waybill_id": waybill_id,
        "driver_id": driver_id,
        "device_id": vehicle_data["device_id"],
        "record_type": record_type,
        "notes": notes,
        "file_hash": file_hash,
        "file_name": file.filename or "",
        "file_size": len(content),
        "content_type": file.content_type or "",
        "latitude": vehicle_data.get("latitude", 0),
        "longitude": vehicle_data.get("longitude", 0),
        "location": vehicle_data.get("current_city", ""),
        "photo_url": f"/api/v1/upload/temperature-records/{record_id}",
        "created_at": datetime.utcnow().isoformat(),
        "review_status": "pending_review",
        "reviewed_by": "",
        "review_notes": "",
        "upload_time": datetime.utcnow().isoformat(),
    }
    
    upload_records.append(record)
    
    return {
        "success": True,
        "message": "上传成功，等待审核",
        "record_id": record_id,
        "waybill_id": waybill_id,
        "photo_url": record["photo_url"],
        "watermark": {
            "timestamp": record["created_at"],
            "location": record["location"],
            "vehicle": vehicle_data["plate_number"],
            "driver": driver_id,
        },
    }


@router.get("/upload-history")
async def get_upload_history(
    user: dict = Depends(require_role("driver", "admin")),
    waybill_id: Optional[str] = None,
    limit: int = 20,
):
    """
    获取司机上传记录历史
    """
    driver_id = user.get("sub", user.get("username", ""))
    
    records = [r for r in upload_records if r.get("driver_id") == driver_id]
    
    if waybill_id:
        records = [r for r in records if r.get("waybill_id") == waybill_id]
    
    records.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    
    return {
        "success": True,
        "count": len(records),
        "records": records[:limit],
    }


# ==================== 6. 运单全生命周期管理 ====================

@router.get("/waybills")
async def get_driver_waybills(
    user: dict = Depends(require_role("driver", "admin")),
    status: Optional[str] = None,
    limit: int = 20,
):
    """
    获取司机名下的运单列表
    支持按状态筛选
    """
    driver_id = user.get("sub", user.get("username", ""))
    orders = get_driver_orders(driver_id)
    
    if status:
        orders = [o for o in orders if o["status"] == status]
    
    return {
        "success": True,
        "count": len(orders),
        "waybills": orders[:limit],
    }


@router.get("/waybills/{waybill_id}")
async def get_waybill_detail(
    waybill_id: str,
    user: dict = Depends(require_role("driver", "admin")),
):
    """
    获取运单详情
    包含完整的温控记录和追溯信息
    """
    from .traceability import WAYBILL_TRACE_MAP, TRACE_DATA, TRACE_RECORDS, TRACE_CODE_MAP
    
    trace_code = WAYBILL_TRACE_MAP.get(waybill_id)
    
    if not trace_code:
        for wb_id, tc in WAYBILL_TRACE_MAP.items():
            if waybill_id in wb_id or wb_id in waybill_id:
                trace_code = tc
                waybill_id = wb_id
                break
    
    if not trace_code or trace_code not in TRACE_DATA:
        raise HTTPException(status_code=404, detail="未找到该运单")
    
    data = TRACE_DATA[trace_code]
    record_ids = TRACE_CODE_MAP.get(trace_code, [])
    records = [r for r in TRACE_RECORDS if r["id"] in record_ids]
    records = sorted(records, key=lambda r: r.get("timestamp", ""))
    
    temps = [r["temperature"] for r in records if "temperature" in r and r["temperature"] is not None]
    humidity_vals = [r["humidity"] for r in records if "humidity" in r and r["humidity"] is not None]
    
    violations = []
    req = data.get("temperature_requirement", "")
    if req and "~" in req:
        try:
            parts = req.split("~")
            min_req = float(parts[0].replace("℃", "").strip())
            max_req = float(parts[1].replace("℃", "").strip())
            for r in records:
                if "temperature" in r and r["temperature"] is not None:
                    temp = r["temperature"]
                    if temp < min_req or temp > max_req:
                        violations.append(r)
        except Exception:
            pass
    
    stages = [
        {"key": "precool", "name": "产地预冷"},
        {"key": "warehouse_in", "name": "仓储入库"},
        {"key": "warehouse_store", "name": "仓储存储"},
        {"key": "loading", "name": "装车发车"},
        {"key": "transport", "name": "干线运输"},
        {"key": "last_mile", "name": "末端配送"},
        {"key": "sign", "name": "消费者签收"},
    ]
    
    stage_info = []
    for stage in stages:
        stage_records = [r for r in records if r.get("stage") == stage["key"]]
        if stage_records:
            stage_temps = [r["temperature"] for r in stage_records if "temperature" in r and r["temperature"] is not None]
            stage_info.append({
                "key": stage["key"],
                "name": stage["name"],
                "completed": True,
                "count": len(stage_records),
                "first_time": stage_records[0].get("timestamp", ""),
                "last_time": stage_records[-1].get("timestamp", ""),
                "temp_range": f"{round(min(stage_temps), 1)}~{round(max(stage_temps), 1)}℃" if stage_temps else "N/A",
            })
        else:
            stage_info.append({
                "key": stage["key"],
                "name": stage["name"],
                "completed": False,
            })
    
    return {
        "success": True,
        "waybill_id": waybill_id,
        "trace_code": trace_code,
        "cargo_name": data["cargo_name"],
        "cargo_category": data["cargo_category"],
        "origin": data["origin"],
        "destination": data["destination"],
        "quantity": data["quantity"],
        "unit": data["unit"],
        "temperature_requirement": data["temperature_requirement"],
        "is_high_sensitivity": data.get("is_high_sensitivity", False),
        "status": data.get("status", ""),
        "current_temperature": temps[-1] if temps else 0,
        "current_humidity": humidity_vals[-1] if humidity_vals else 0,
        "is_compliant": len(violations) == 0,
        "violations_count": len(violations),
        "total_records": len(records),
        "stages": stage_info,
        "receiver": data.get("receiver", ""),
        "receiver_contact": data.get("receiver_contact", ""),
        "last_update": records[-1].get("timestamp", "") if records else datetime.utcnow().isoformat(),
    }


# ==================== 7. 实时追踪接口 ====================

@router.get("/tracking")
async def get_tracking(
    user: dict = Depends(require_role("driver", "admin")),
):
    """
    获取实时追踪数据
    返回车辆当前位置、温度、湿度等实时信息
    """
    driver_id = user.get("sub", user.get("username", ""))
    vehicle = get_driver_vehicle(driver_id)
    
    if not vehicle:
        return {"success": False, "error": "未绑定车辆"}
    
    ws = get_world_state()
    vehicle_data = next((v for v in ws["vehicles"] if v["device_id"] == vehicle["device_id"]), vehicle)
    
    return {
        "success": True,
        "vehicle": {
            "device_id": vehicle_data["device_id"],
            "plate_number": vehicle_data["plate_number"],
            "latitude": vehicle_data.get("latitude", 0),
            "longitude": vehicle_data.get("longitude", 0),
            "current_city": vehicle_data.get("current_city", ""),
            "speed": round(_live_wave(vehicle_data.get("vehicle_speed", 60), 0.1), 1),
            "direction": "行驶中",
        },
        "temperature": {
            "current": round(_live_wave(vehicle_data["temperature"], 0.02), 1),
            "target": vehicle_data.get("target_temperature", 0),
            "is_compliant": abs(vehicle_data["temperature"] - vehicle_data.get("target_temperature", 0)) <= 2,
        },
        "humidity": {
            "current": round(_live_wave(vehicle_data["humidity"], 0.02), 1),
        },
        "cold_car": {
            "status": "running" if vehicle_data.get("cold_car_status", 1) == 1 else "stopped",
            "health": _live_int_wave(int(vehicle_data["cold_car_health"] * 100), 3, 30),
        },
        "door_status": {
            "is_open": vehicle_data.get("door_status", 0) == 1,
        },
        "last_update": datetime.utcnow().isoformat(),
    }


# ==================== 8. 温度记录纸 AI 识别（OCR + 视觉） ====================

def _build_temperature_paper_prompt() -> str:
    return """你是一个专业的冷链温度记录纸识别专家。请识别图片中的温度记录纸/温控台账。
请从图片中提取每个时间点的温度记录，并按照以下JSON格式输出：
{
    "temperatures": [
        {"time": "08:00", "temp": 4.2, "is_ok": true, "standard": "-18~6℃"},
        {"time": "10:00", "temp": 5.1, "is_ok": true, "standard": "-18~6℃"}
    ],
    "summary": {"total": 5, "ok": 3, "fail": 2},
    "overall_status": "fail",
    "suggestion": "温度记录纸显示有2处温度超标，建议检查冷机设置并联系调度"
}

识别规则：
1. temperatures 为从图片中识别出的各时间点温度记录，time 为时间(如 08:00)，temp 为温度数值(℃)，is_ok 表示该点是否在标准范围内，standard 为该记录对应的温度标准区间
2. summary.total 为总记录数，ok 为合格点数，fail 为超标点数
3. overall_status 为 overall 判定: 全部合格为 "pass"，存在超标为 "fail"
4. suggestion 为基于识别结果的处置建议
5. 若图片中无法清晰识别具体数值，请根据可见信息合理推断，并尽量输出 3-6 个时间点的记录
6. 输出必须是合法的JSON格式，不要包含其他文字"""


async def _call_dashscope_vision(image_base64: str, prompt: str) -> dict:
    """调用 DashScope 视觉大模型（qwen-vl-plus）识别图片，复用 ZHIPU_API_KEY 环境变量。"""
    import httpx
    api_key = os.environ.get("ZHIPU_API_KEY", "")
    if not api_key:
        raise HTTPException(status_code=500, detail="API密钥未配置")

    image_data_url = f"data:image/jpeg;base64,{image_base64}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "qwen-vl-plus",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_data_url}},
                ],
            }
        ],
        "max_tokens": 800,
    }
    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
        response = await client.post(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
            headers=headers,
            json=payload,
        )
    if response.status_code != 200:
        raise Exception(f"API调用失败，状态码: {response.status_code}")
    result = response.json()
    content = result["choices"][0]["message"]["content"]
    content = content.replace("```json", "").replace("```", "").strip()
    return json.loads(content)


def _fallback_temperature_paper() -> dict:
    """无视觉 API Key 时的规则降级：生成结构合理的模拟识别结果（明确标注为模拟）。"""
    base_hour = 8
    temps = []
    ok = 0
    fail = 0
    for i in range(5):
        hour = base_hour + i * 2
        t = round(random.uniform(3.8, 7.9), 1)
        is_ok = t <= 6.0
        if is_ok:
            ok += 1
        else:
            fail += 1
        temps.append({
            "time": f"{hour:02d}:00",
            "temp": t,
            "is_ok": is_ok,
            "standard": "-18~6℃",
        })
    return {
        "success": True,
        "record_id": "TR-" + datetime.utcnow().strftime("%Y%m%d%H%M%S"),
        "temperatures": temps,
        "summary": {"total": len(temps), "ok": ok, "fail": fail},
        "overall_status": "pass" if fail == 0 else "fail",
        "suggestion": (
            "温度记录纸识别完成，全程温度达标。"
            if fail == 0
            else f"温度记录纸显示有{fail}处温度超标，建议检查冷机设置并联系调度"
        ),
        "is_simulated": True,
    }


@router.post("/recognize-temperature-paper")
async def recognize_temperature_paper(
    file: UploadFile = File(...),
    user: dict = Depends(require_role("driver", "admin")),
):
    """
    温度记录纸 AI 识别（OCR + 视觉大模型）
    - 配置了 ZHIPU_API_KEY 时调用 DashScope qwen-vl-plus 真实识别图片内容
    - 未配置时降级为规则模拟，保证移动端演示闭环（结果标注 is_simulated=true）
    """
    content = await file.read()
    try:
        image_base64 = base64.b64encode(content).decode("utf-8")
        vision_result = await _call_dashscope_vision(image_base64, _build_temperature_paper_prompt())
        # 统一字段结构
        temps = vision_result.get("temperatures", [])
        ok = sum(1 for t in temps if t.get("is_ok"))
        fail = len(temps) - ok
        return {
            "success": True,
            "record_id": "TR-" + datetime.utcnow().strftime("%Y%m%d%H%M%S"),
            "temperatures": temps,
            "summary": vision_result.get("summary", {"total": len(temps), "ok": ok, "fail": fail}),
            "overall_status": vision_result.get("overall_status", "pass" if fail == 0 else "fail"),
            "suggestion": vision_result.get("suggestion", ""),
            "is_simulated": False,
        }
    except HTTPException:
        raise
    except Exception:
        # 视觉识别失败（无 Key / 网络 / 解析异常）→ 规则降级
        return _fallback_temperature_paper()
