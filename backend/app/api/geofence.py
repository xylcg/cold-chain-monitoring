"""
冷链电子围栏管理 API
支持4种围栏类型：圆形点围栏、带状线路围栏、多边形围栏、行政城市围栏
联动：路线规划、设备心跳、温控数据、中转分拨、追溯链
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from ..core.security import get_current_user, require_role
from ..schemas.geofence import (
    FenceCreate, FenceUpdate, FenceInDB, FenceEvent, FenceEventCreate,
    FenceType, FenceCategory, AlertLevel, GeoJSONFeature
)
from ..services.fence_store import (
    create_fence, get_fence, get_fences, update_fence, delete_fence,
    create_fence_event, get_fence_events, resolve_event,
    get_all_fences_geojson, get_fence_stats
)
from ..services.fence_judge import is_point_in_fence, find_containing_fences
from ..services.fence_event_processor import (
    process_vehicle_position, process_heartbeat_offline, get_active_fence_alerts,
    get_alerts_by_level, get_vehicle_state, update_vehicle_state
)
from ..services.world_state import get_world_state, CITY_COORDS
from ..api.traceability import auto_add_geofence_record, WAYBILL_TRACE_MAP
from ..api.resources import MULTI_ZONE_VEHICLES, _unlock_resource, RESOURCE_LOCKS

router = APIRouter(prefix="/api/v1/geofence", tags=["电子围栏"])


# ==================== 常量定义 ====================

@router.get("/constants")
async def get_fence_constants(
    user: dict = Depends(get_current_user),
):
    """获取电子围栏相关常量"""
    return {
        "fence_types": [
            {"value": t.value, "label": _fence_type_label(t.value)}
            for t in FenceType
        ],
        "fence_categories": [
            {"value": c.value, "label": _fence_category_label(c.value)}
            for c in FenceCategory
        ],
        "alert_levels": [
            {"value": a.value, "label": _alert_level_label(a.value)}
            for a in AlertLevel
        ],
        "city_coords": CITY_COORDS,
    }


# ==================== GeoJSON 导出 ====================

@router.get("/geojson")
async def export_geojson(
    fence_type: Optional[str] = Query(None, description="围栏类型"),
    user: dict = Depends(get_current_user),
):
    """导出围栏为 GeoJSON 格式（用于地图渲染）"""
    geojson = get_all_fences_geojson()
    
    if fence_type:
        try:
            type_enum = FenceType(fence_type)
            geojson["features"] = [
                f for f in geojson["features"]
                if f["properties"]["type"] == type_enum.value
            ]
        except ValueError:
            pass
    
    return JSONResponse(content=geojson)


# ==================== 统计信息 ====================

@router.get("/stats")
async def get_fence_statistics(
    user: dict = Depends(get_current_user),
):
    """获取电子围栏统计信息"""
    stats = get_fence_stats()
    return stats


# ==================== 围栏列表 ====================

@router.get("")
async def list_fences(
    fence_type: Optional[str] = Query(None, description="围栏类型"),
    category: Optional[str] = Query(None, description="围栏类别"),
    active: Optional[bool] = Query(None, description="是否启用"),
    route_id: Optional[str] = Query(None, description="关联路线ID"),
    user: dict = Depends(get_current_user),
):
    """获取电子围栏列表"""
    type_enum = FenceType(fence_type) if fence_type else None
    category_enum = FenceCategory(category) if category else None
    
    fences = get_fences(
        fence_type=type_enum,
        category=category_enum,
        active=active,
        route_id=route_id,
    )
    
    return {
        "count": len(fences),
        "fences": [f.dict() for f in fences]
    }


# ==================== 围栏告警 ====================

@router.get("/alerts")
async def get_all_fence_alerts(
    hours: int = Query(24, description="最近N小时"),
    level: Optional[str] = Query(None, description="告警等级"),
    user: dict = Depends(get_current_user),
):
    """获取围栏告警列表"""
    if level:
        try:
            level_enum = AlertLevel(level)
            events = get_alerts_by_level(level_enum, hours=hours)
        except ValueError:
            events = get_active_fence_alerts(hours=hours)
    else:
        events = get_active_fence_alerts(hours=hours)
    
    return {
        "count": len(events),
        "alerts": [e.dict() for e in events]
    }


@router.get("/alerts/active")
async def get_active_alerts(
    hours: int = Query(24, description="最近N小时"),
    user: dict = Depends(get_current_user),
):
    """获取活跃的围栏告警"""
    events = get_active_fence_alerts(hours=hours)
    return {
        "count": len(events),
        "alerts": [e.dict() for e in events]
    }


# ==================== 围栏事件 ====================

@router.get("/events")
async def get_fence_events_api(
    fence_id: Optional[str] = Query(None, description="围栏ID"),
    vehicle_id: Optional[str] = Query(None, description="车辆ID"),
    event_type: Optional[str] = Query(None, description="事件类型"),
    alert_level: Optional[str] = Query(None, description="告警等级"),
    resolved: Optional[bool] = Query(None, description="是否已处理"),
    hours: Optional[int] = Query(24, description="最近N小时"),
    user: dict = Depends(get_current_user),
):
    """查询围栏事件"""
    level_enum = AlertLevel(alert_level) if alert_level else None
    
    events = get_fence_events(
        fence_id=fence_id,
        vehicle_id=vehicle_id,
        event_type=event_type,
        alert_level=level_enum,
        resolved=resolved,
        hours=hours,
    )
    
    return {
        "count": len(events),
        "events": [e.dict() for e in events]
    }


# ==================== 创建围栏 ====================

@router.post("")
async def create_fence_api(
    data: FenceCreate,
    user: dict = Depends(require_role("admin", "warehouse")),
):
    """创建电子围栏"""
    fence = create_fence(data)
    return {"status": "ok", "fence": fence.dict()}


# ==================== 围栏事件处理 ====================

@router.post("/events/check")
async def check_fence_event(
    vehicle_id: str,
    plate_number: str = "",
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    temperature_c: Optional[float] = None,
    heartbeat_time: Optional[datetime] = None,
    user: dict = Depends(require_role("admin", "warehouse", "driver")),
):
    """检查车辆位置是否触发围栏事件"""
    events = process_vehicle_position(
        vehicle_id=vehicle_id,
        plate_number=plate_number,
        lat=lat,
        lng=lng,
        temperature_c=temperature_c,
        heartbeat_time=heartbeat_time,
        city_coords=CITY_COORDS,
    )
    
    # 🚀 自动写入追溯链（联动冷链追溯模块）
    # 当触发围栏事件时，自动记录到追溯链
    try:
        for event in events:
            event_type = event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type)
            
            waybill_id = ""
            for wb in WAYBILL_TRACE_MAP:
                if vehicle_id in wb or plate_number in wb:
                    waybill_id = wb
                    break
            
            if waybill_id:
                await auto_add_geofence_record(
                    waybill_id=waybill_id,
                    fence_name=event.fence_name,
                    event_type=event_type,
                    location=f"{event.city_section}" if hasattr(event, 'city_section') else "",
                    temperature=temperature_c or 0.0,
                    lat=lat,
                    lng=lng,
                    user={"sub": "system", "role": "admin"},
                )
    except Exception as e:
        from loguru import logger
        logger.warning(f"围栏事件写入追溯链失败: {e}")
    
    # 🚀 资源状态联动更新（联动资源调度模块）
    # 当车辆进入仓库围栏时，自动更新车辆状态
    try:
        for event in events:
            event_type = event.event_type.value if hasattr(event.event_type, 'value') else str(event.event_type)
            if event_type == "enter" and hasattr(event, 'fence_name') and "仓库" in event.fence_name:
                for vehicle in MULTI_ZONE_VEHICLES:
                    if vehicle["id"] == vehicle_id or vehicle["plate"] == plate_number:
                        vehicle["status"] = "idle"
                        vehicle["current_task"] = ""
                        vehicle["location"] = event.fence_name
                        
                        for lock_id, lock_info in list(RESOURCE_LOCKS.items()):
                            if lock_info["resource_id"] == vehicle["id"] and lock_info["resource_type"] == "vehicle":
                                _unlock_resource(lock_id)
                                break
                        break
    except Exception as e:
        from loguru import logger
        logger.warning(f"围栏事件更新资源状态失败: {e}")
    
    return {
        "vehicle_id": vehicle_id,
        "location": {"lat": lat, "lng": lng},
        "event_count": len(events),
        "events": [e.dict() for e in events]
    }


@router.post("/events/offline")
async def report_offline_event(
    vehicle_id: str,
    plate_number: str = "",
    last_lat: float = Query(..., ge=-90, le=90),
    last_lng: float = Query(..., ge=-180, le=180),
    offline_duration_seconds: float = Query(..., ge=0),
    user: dict = Depends(require_role("admin", "warehouse")),
):
    """上报设备离线事件"""
    events = process_heartbeat_offline(
        vehicle_id=vehicle_id,
        plate_number=plate_number,
        last_lat=last_lat,
        last_lng=last_lng,
        offline_duration_seconds=offline_duration_seconds,
        city_coords=CITY_COORDS,
    )
    
    return {
        "vehicle_id": vehicle_id,
        "offline_duration_minutes": int(offline_duration_seconds / 60),
        "event_count": len(events),
        "events": [e.dict() for e in events]
    }


# ==================== 路线围栏生成 ====================

@router.post("/route/{route_id}/generate")
async def generate_route_fences(
    route_id: str,
    cities: List[str] = Query(..., description="路线途经城市列表"),
    buffer_meters: int = Query(100, ge=50, le=500),
    user: dict = Depends(require_role("admin", "warehouse")),
):
    """根据路线自动生成带状围栏"""
    generated_fences = []
    
    for i in range(len(cities) - 1):
        from_city = cities[i]
        to_city = cities[i + 1]
        
        from_coord = CITY_COORDS.get(from_city)
        to_coord = CITY_COORDS.get(to_city)
        
        if not from_coord or not to_coord:
            continue
        
        mid_lat = (from_coord[0] + to_coord[0]) / 2
        mid_lng = (from_coord[1] + to_coord[1]) / 2
        
        fence_data = FenceCreate(
            name=f"{from_city}-{to_city}干线",
            fence_type=FenceType.LINE_BUFFER,
            category=FenceCategory.ROUTE_SEGMENT,
            data={
                "points": [
                    {"lat": from_coord[0], "lng": from_coord[1]},
                    {"lat": mid_lat, "lng": mid_lng},
                    {"lat": to_coord[0], "lng": to_coord[1]},
                ],
                "buffer_meters": buffer_meters,
                "start_city": from_city,
                "end_city": to_city,
            },
            description=f"{from_city}到{to_city}规划行驶路线",
            active=True,
            alert_level=AlertLevel.SEVERE,
            tags=["route", from_city, to_city],
            route_id=route_id,
        )
        
        fence = create_fence(fence_data)
        generated_fences.append(fence.dict())
    
    return {
        "status": "ok",
        "route_id": route_id,
        "generated_count": len(generated_fences),
        "fences": generated_fences,
    }


# ==================== 动态路径路由（必须放在最后） ====================

@router.get("/{fence_id}")
async def get_fence_detail(
    fence_id: str,
    user: dict = Depends(get_current_user),
):
    """获取单个电子围栏详情"""
    fence = get_fence(fence_id)
    if not fence:
        raise HTTPException(status_code=404, detail="电子围栏不存在")
    return fence.dict()


@router.put("/{fence_id}")
async def update_fence_api(
    fence_id: str,
    data: FenceUpdate,
    user: dict = Depends(require_role("admin", "warehouse")),
):
    """更新电子围栏"""
    fence = update_fence(fence_id, data)
    if not fence:
        raise HTTPException(status_code=404, detail="电子围栏不存在")
    return {"status": "ok", "fence": fence.dict()}


@router.delete("/{fence_id}")
async def delete_fence_api(
    fence_id: str,
    user: dict = Depends(require_role("admin", "warehouse")),
):
    """删除电子围栏"""
    success = delete_fence(fence_id)
    if not success:
        raise HTTPException(status_code=404, detail="电子围栏不存在")
    return {"status": "ok", "deleted": fence_id}


@router.post("/events/{event_id}/resolve")
async def resolve_fence_event(
    event_id: str,
    user: dict = Depends(require_role("admin", "warehouse")),
):
    """处理围栏事件"""
    event = resolve_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="事件不存在")
    return {"status": "ok", "event": event.dict()}


@router.get("/alerts/by-level/{level}")
async def get_alerts_by_level_api(
    level: str,
    hours: int = Query(24, description="最近N小时"),
    user: dict = Depends(get_current_user),
):
    """按告警等级获取围栏告警"""
    try:
        level_enum = AlertLevel(level)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的告警等级")
    
    events = get_alerts_by_level(level_enum, hours=hours)
    return {
        "count": len(events),
        "alerts": [e.dict() for e in events]
    }


@router.get("/device/{device_id}/status")
async def get_device_fence_status(
    device_id: str,
    user: dict = Depends(get_current_user),
):
    """获取设备当前围栏状态"""
    ws = get_world_state()
    vehicle = next((v for v in ws.get("vehicles", []) if v["device_id"] == device_id), None)
    
    if not vehicle:
        raise HTTPException(status_code=404, detail="设备不存在或离线")
    
    lat = vehicle["latitude"]
    lng = vehicle["longitude"]
    temperature = vehicle["temperature"]
    
    state = get_vehicle_state(device_id)
    
    containing_fences = []
    all_fences = [FenceInDB(**f) for f in ws.get("fences", [])]
    for fence in all_fences:
        if is_point_in_fence(lat, lng, fence, CITY_COORDS):
            containing_fences.append({
                "fence_id": fence.fence_id,
                "fence_name": fence.name,
                "fence_type": fence.fence_type.value,
                "category": fence.category.value,
                "city_section": state.get("current_city_section"),
            })
    
    return {
        "device_id": device_id,
        "location": {"lat": lat, "lng": lng},
        "temperature": temperature,
        "current_fences": containing_fences,
        "heartbeat_status": state.get("heartbeat_status", "online"),
        "current_city_section": state.get("current_city_section"),
        "consecutive_off_route": state.get("consecutive_off_route", 0),
    }


# ==================== 辅助函数 ====================

def _fence_type_label(value: str) -> str:
    labels = {
        "circle": "圆形点围栏",
        "line_buffer": "带状线路围栏",
        "polygon": "多边形围栏",
        "city": "行政城市围栏",
    }
    return labels.get(value, value)


def _fence_category_label(value: str) -> str:
    labels = {
        "warehouse": "仓库",
        "hub": "枢纽冷仓",
        "service_area": "高速服务区",
        "repair_station": "维修站点",
        "route_segment": "路线干线",
        "forbidden": "禁行区",
        "high_temp": "高温管控区",
        "restricted": "风险路段",
        "city_zone": "城市区域",
        "checkpoint": "检查点",
    }
    return labels.get(value, value)


def _alert_level_label(value: str) -> str:
    labels = {
        "severe": "严重",
        "warning": "警告",
        "normal": "一般",
        "info": "正常",
    }
    return labels.get(value, value)
