"""
运营管理后台 API
模块12: 运营管理后台
"""
import random
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException

from ..services.redis_service import redis_service
from ..core.security import get_current_user
from ..schemas import TEMP_THRESHOLD

router = APIRouter(prefix="/api/v1/dashboard", tags=["管理后台"])


@router.get("/kpi")
async def get_kpi(user: dict = Depends(get_current_user)):
    """
    获取 KPI 仪表盘数据
    温控达标率、设备在线率、能耗统计
    """
    try:
        online_devices = await redis_service.get_online_devices()
    except (RuntimeError, Exception):
        online_devices = set()

    # Redis 不可用或无数据时，返回模拟数据
    if not online_devices:
        total_devices = 110
        total_online = random.randint(78, 95)
        temp_compliant = random.randint(65, 88)
        active_alerts = random.randint(3, 15)
        critical_alerts = random.randint(0, 3)
        return {
            "total_devices": total_devices,
            "online_devices": total_online,
            "online_rate": round(total_online / total_devices * 100, 1),
            "temperature_compliance_rate": round(temp_compliant / total_online * 100, 1),
            "active_alerts": active_alerts,
            "critical_alerts": critical_alerts,
            "avg_temperature": round(random.uniform(-18.5, 3.5), 1),
            "avg_humidity": round(random.uniform(55, 75), 1),
            "timestamp": datetime.utcnow().isoformat(),
            "data_source": "simulated",
        }

    total_online = len(online_devices)
    total_temp = 0.0
    total_humidity = 0.0
    temp_compliant = 0
    active_alerts = 0
    critical_alerts = 0

    for device_id in online_devices:
        status = await redis_service.get_device_status(device_id)
        if status:
            temp = float(status.get("temperature", 0))
            total_temp += temp
            if TEMP_THRESHOLD["COMPLIANCE_MIN"] <= temp <= TEMP_THRESHOLD["COMPLIANCE_MAX"]:
                temp_compliant += 1
            total_humidity += float(status.get("humidity", 0))
        count = await redis_service.get_active_alerts(device_id)
        if count > 0:
            active_alerts += count

    total_devices = 110

    return {
        "total_devices": total_devices,
        "online_devices": total_online,
        "online_rate": round(total_online / total_devices * 100, 1) if total_devices > 0 else 0,
        "temperature_compliance_rate": round(
            temp_compliant / total_online * 100, 1
        ) if total_online > 0 else 0,
        "active_alerts": active_alerts,
        "critical_alerts": critical_alerts,
        "avg_temperature": round(total_temp / total_online, 1) if total_online > 0 else 0,
        "avg_humidity": round(total_humidity / total_online, 1) if total_online > 0 else 0,
        "timestamp": datetime.utcnow().isoformat(),
        "data_source": "redis",
    }


@router.get("/devices")
async def get_devices_status(user: dict = Depends(get_current_user)):
    """获取所有设备状态列表"""
    try:
        online_devices = await redis_service.get_online_devices()
    except (RuntimeError, Exception):
        online_devices = set()

    # Redis 不可用时返回模拟设备列表
    if not online_devices:
        device_types = ["vehicle"] * 15 + ["cold_room"] * 5
        devices = []
        for i in range(20):
            prefix = "VEH" if device_types[i] == "vehicle" else "CR"
            dev_id = f"{prefix}-{i+1:03d}"
            temp = round(random.uniform(-22, 6), 1)
            has_alert = random.random() < 0.2
            devices.append({
                "device_id": dev_id,
                "online": True,
                "temperature": temp,
                "humidity": round(random.uniform(50, 80), 1),
                "door_status": random.randint(0, 1),
                "vibration": round(random.uniform(0, 3), 2),
                "active_alerts": random.randint(1, 3) if has_alert else 0,
                "last_update": datetime.utcnow().isoformat(),
                "device_type": device_types[i],
            })
        devices.sort(key=lambda x: x["active_alerts"], reverse=True)
        return {"total": len(devices), "devices": devices, "data_source": "simulated"}

    devices = []
    for device_id in online_devices:
        status = await redis_service.get_device_status(device_id)
        if status:
            alert_count = await redis_service.get_active_alerts(device_id)
            devices.append({
                "device_id": device_id,
                "online": True,
                "temperature": float(status.get("temperature", 0)),
                "humidity": float(status.get("humidity", 0)),
                "door_status": int(status.get("door_status", 0)),
                "vibration": float(status.get("vibration", 0)),
                "active_alerts": int(alert_count) if alert_count else 0,
                "last_update": status.get("last_update"),
                "device_type": "vehicle" if device_id.startswith("VEH") else "cold_room",
            })
    devices.sort(key=lambda x: x["active_alerts"], reverse=True)
    return {"total": len(devices), "devices": devices, "data_source": "redis"}


@router.get("/overview")
async def get_overview(user: dict = Depends(get_current_user)):
    """获取全局态势图数据"""
    try:
        online_devices = await redis_service.get_online_devices()
    except (RuntimeError, Exception):
        online_devices = set()

    # 按设备类型分组统计
    vehicles = []
    cold_rooms = []

    for device_id in online_devices:
        status = await redis_service.get_device_status(device_id)
        if not status:
            continue

        info = {
            "device_id": device_id,
            "temperature": float(status.get("temperature", 0)),
            "humidity": float(status.get("humidity", 0)),
            "latitude": float(status.get("latitude", 0)),
            "longitude": float(status.get("longitude", 0)),
            "door_status": int(status.get("door_status", 0)),
        }

        if device_id.startswith("VEH"):
            vehicles.append(info)
        else:
            cold_rooms.append(info)

    return {
        "vehicles": {"count": len(vehicles), "data": vehicles},
        "cold_rooms": {"count": len(cold_rooms), "data": cold_rooms},
        "total_online": len(online_devices),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/alerts/summary")
async def get_alerts_summary(user: dict = Depends(get_current_user)):
    """获取告警摘要统计"""
    try:
        online_devices = await redis_service.get_online_devices()
    except (RuntimeError, Exception):
        online_devices = set()

    total_alerts = 0
    total_devices_with_alerts = 0

    for device_id in online_devices:
        count = await redis_service.get_active_alerts(device_id)
        if count > 0:
            total_alerts += count
            total_devices_with_alerts += 1

    return {
        "total_alerts": total_alerts,
        "devices_with_alerts": total_devices_with_alerts,
        "total_devices_online": len(online_devices),
        "alert_rate": round(total_devices_with_alerts / len(online_devices) * 100, 1) if online_devices else 0,
        "timestamp": datetime.utcnow().isoformat(),
    }
