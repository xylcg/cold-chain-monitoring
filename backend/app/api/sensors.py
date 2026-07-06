"""
传感器数据接入 API
模块1: 多传感器数据采集
联动追溯链：传感器数据自动写入全程冷链追溯链
"""
import json
from datetime import datetime
from fastapi import APIRouter, Header, HTTPException, Depends
from typing import List
from loguru import logger

from ..schemas import SensorData, SensorDataBatch
from ..core.security import get_current_user, require_role
from ..services.kafka_service import kafka_service
from ..services.tdengine_service import tdengine_service
from ..services.redis_service import redis_service
from ..services.alert_engine import alert_engine
from ..services.websocket_manager import ws_manager
from ..core.security import verify_device_token
from ..api.traceability import auto_add_sensor_record, WAYBILL_TRACE_MAP
from ..api.resources import MULTI_ZONE_VEHICLES, COLD_PLATES, _unlock_resource, RESOURCE_LOCKS

router = APIRouter(prefix="/api/v1/sensors", tags=["传感器数据"])


async def validate_device(authorization: str = Header(...)):
    """验证设备 token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="缺少设备认证信息")
    token = authorization.replace("Bearer ", "")
    if not await verify_device_token(token):
        raise HTTPException(status_code=403, detail="无效的设备凭证")
    return token


@router.post("/data")
async def receive_sensor_data(
    data: SensorData,
    auth: str = Depends(validate_device),
):
    """
    接收传感器上报数据
    处理流程: 数据验证 → Kafka 写入 → Redis 缓存 → TDengine 存储 → 异常检测 → 告警 → WebSocket 推送 → 追溯链写入
    """
    data_dict = data.model_dump()
    data_dict["timestamp"] = data_dict["timestamp"].isoformat()

    # 1. 写入 Kafka（解耦数据流）
    kafka_service.send_sensor_data(data_dict)

    # 2. 更新 Redis 实时状态
    await redis_service.set_latest_sensor_data(data.device_id, data_dict)
    await redis_service.set_device_online(data.device_id)

    status = {
        "temperature": data.temperature,
        "humidity": data.humidity,
        "door_status": data.door_status,
        "vibration": data.vibration,
        "latitude": data.latitude,
        "longitude": data.longitude,
        "last_update": data_dict["timestamp"],
    }
    await redis_service.set_device_status(data.device_id, status)

    # 3. 存储到 TDengine
    tdengine_service.insert_sensor_data(data_dict)

    # 4. 维护温度滑动窗口（供模型推理使用）
    await redis_service.push_temperature_window(data.device_id, data.temperature)

    # 5. 异常检测 + 告警
    alerts = alert_engine.evaluate(data_dict)
    for alert in alerts:
        await alert_engine.process_alert(alert)

    # 6. WebSocket 实时推送到订阅该设备的客户端
    await ws_manager.broadcast_device_data(data.device_id, data_dict)

    # 7. 🚀 自动写入追溯链（联动冷链追溯模块）
    # 尝试通过设备ID查找关联的运单号
    waybill_id = ""
    try:
        for wb, tc in WAYBILL_TRACE_MAP.items():
            if data.device_id in wb or data.device_id in tc:
                waybill_id = wb
                break
        if waybill_id:
            await auto_add_sensor_record(
                device_id=data.device_id,
                waybill_id=waybill_id,
                temperature=data.temperature,
                humidity=data.humidity,
                latitude=data.latitude,
                longitude=data.longitude,
                door_status=data.door_status,
                vehicle_speed=data.vehicle_speed,
                cold_car_status=data.cold_car_status,
                user={"sub": "system", "role": "admin"},
            )
    except Exception as e:
        logger.warning(f"追溯链写入失败: {e}")

    # 8. 🚀 资源状态联动更新（联动资源调度模块）
    # 当车辆速度为0且冷机关闭，自动释放车辆资源
    try:
        if data.device_type == "vehicle" and data.vehicle_speed == 0 and data.cold_car_status == 0:
            for vehicle in MULTI_ZONE_VEHICLES:
                if vehicle.get("device_id") == data.device_id and vehicle["status"] == "in_transit":
                    vehicle["status"] = "idle"
                    vehicle["current_task"] = ""
                    
                    for lock_id, lock_info in list(RESOURCE_LOCKS.items()):
                        if lock_info["resource_id"] == vehicle["id"] and lock_info["resource_type"] == "vehicle":
                            _unlock_resource(lock_id)
                            logger.info(f"车辆 {vehicle['plate']} 自动释放资源")
                            break
                    break
    except Exception as e:
        logger.warning(f"资源状态更新失败: {e}")

    return {
        "status": "ok",
        "device_id": data.device_id,
        "alerts_triggered": len(alerts),
        "timestamp": data_dict["timestamp"],
    }


@router.post("/data/batch")
async def receive_sensor_data_batch(
    batch: SensorDataBatch,
    auth: str = Depends(validate_device),
):
    """批量接收传感器数据"""
    success_count = 0
    alert_count = 0

    for data in batch.records:
        result = await receive_sensor_data(data, auth)
        success_count += 1
        alert_count += result["alerts_triggered"]

    return {
        "status": "ok",
        "received": len(batch.records),
        "success": success_count,
        "alerts_triggered": alert_count,
    }


@router.get("/latest/{device_id}")
async def get_latest_data(device_id: str, user: dict = Depends(require_role("admin", "warehouse"))):
    """获取设备最新传感器数据"""
    data = await redis_service.get_latest_sensor_data(device_id)
    if not data:
        raise HTTPException(status_code=404, detail="设备数据不存在")
    return data


@router.get("/history/{device_id}")
async def get_history(
    device_id: str,
    start: str,
    end: str,
    limit: int = 100,
    user: dict = Depends(require_role("admin", "warehouse")),
):
    """查询设备历史数据"""
    data = tdengine_service.query_history(device_id, start, end, limit)
    return {"device_id": device_id, "count": len(data), "data": data}
