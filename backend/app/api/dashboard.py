"""
运营管理后台 API
模块12: 运营管理后台
设备状态优先从 Redis 读取实时传感器数据，fallback 到统一世界状态模拟数据
Redis 实时数据会根据温区规则自动计算告警
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends

from ..services.world_state import get_world_state
from ..services.redis_service import redis_service
from ..core.security import get_current_user
from loguru import logger

router = APIRouter(prefix="/api/v1/dashboard", tags=["["])

# 温区阈值配置（单位：摄氏度，相对于目标温度的允许偏差）
ZONE_THRESHOLDS = {
    "frozen": {"target_range": (-25, -18), "warn_offset": 3, "critical_offset": 5},
    "refrigerated": {"target_range": (2, 8), "warn_offset": 2.5, "critical_offset": 5},
    "ambient": {"target_range": (15, 25), "warn_offset": 3, "critical_offset": 6},
}

# 默认阈值（无法识别温区时使用）
DEFAULT_THRESHOLD = {"warn_offset": 3, "critical_offset": 6}


def _calc_temperature_alerts(temp: float, target_temp: float, cargo_zone: str) -> int:
    """
    根据当前温度、目标温度和温区计算告警数
    
    规则：
    - 温度在目标±warn_offset内 → 0条告警（正常）
    - 温度超出warn_offset但未超critical_offset → 1条告警（警告）
    - 温度超出critical_offset → 2条告警（严重）
    
    特殊处理：
    - 冷冻车(frozen)：目标-18°C以下，温度 > -13°C 就要报警
    - 冷藏车(refrigerated)：目标2~8°C，温度 > 10.5°C 或 < -0.5°C 要报警
    """
    if target_temp == 0 and cargo_zone:
        # 没有目标温度但有温区信息，用温区默认范围中值作为参考
        zone_cfg = ZONE_THRESHOLDS.get(cargo_zone, DEFAULT_THRESHOLD)
        target_range = zone_cfg.get("target_range", (0, 20))
        target_temp = (target_range[0] + target_range[1]) / 2
    
    if target_temp == 0:
        # 完全没有参考基准，用绝对值判断
        if temp > 30 or temp < -15:
            return 2  # 严重异常
        elif temp > 20 or temp < -5:
            return 1  # 轻微异常
        return 0
    
    offset = abs(temp - target_temp)
    
    # 根据温区选择阈值
    if cargo_zone in ZONE_THRESHOLDS:
        warn_off = ZONE_THRESHOLDS[cargo_zone]["warn_offset"]
        crit_off = ZONE_THRESHOLDS[cargo_zone]["critical_offset"]
    else:
        warn_off = DEFAULT_THRESHOLD["warn_offset"]
        crit_off = DEFAULT_THRESHOLD["critical_offset"]
    
    if offset >= crit_off:
        return 2  # 严重：温度严重超标
    elif offset >= warn_off:
        return 1  # 警告：温度轻微偏离
    return 0


def _is_temperature_compliant(temp: float, target_temp: float, cargo_zone: str) -> bool:
    """判断温度是否合规"""
    return _calc_temperature_alerts(temp, target_temp, cargo_zone) == 0


@router.get("/kpi")
async def get_kpi(user: dict = Depends(get_current_user)):
    """
    获取 KPI 仪表盘数据
    基础指标来自统一世界状态，设备在线数/总数优先从 Redis 实时数据获取
    """
    ws = get_world_state()
    kpi = ws["kpi"].copy()
    
    # 尝试用 Redis 实时数据覆盖设备统计（更准确）
    try:
        online_devices = await redis_service.get_online_devices()
        if online_devices:
            total_real = len(online_devices)
            # 计算实时合规率
            compliant_count = 0
            alert_count = 0
            for device_id in online_devices:
                data = await redis_service.get_latest_sensor_data(device_id)
                if data:
                    temp = data.get("temperature", 0)
                    target_temp = data.get("target_temperature", 0)
                    cargo_zone = data.get("cargo_zone", data.get("device_type", ""))
                    alerts = _calc_temperature_alerts(float(temp), float(target_temp), str(cargo_zone))
                    if alerts == 0:
                        compliant_count += 1
                    if alerts > 0:
                        alert_count += 1
            
            online_rate = round(total_real / max(total_real, 1) * 100, 1)
            compliance_rate = round(compliant_count / max(total_real, 1) * 100, 1)
            
            kpi["total_devices"] = total_real
            kpi["online_devices"] = total_real
            kpi["online_rate"] = online_rate
            kpi["temperature_compliance_rate"] = compliance_rate
            kpi["total_online_devices"] = total_real
            kpi["device_compliant_count"] = compliant_count
            kpi["device_anomaly_count"] = total_real - compliant_count
            kpi["active_alerts"] = alert_count
            kpi["fleet_online_rate"] = online_rate
            kpi["data_source"] = "redis_enhanced"
            logger.info(f"KPI 设备统计已用 Redis 实时数据覆盖: {total_real} 台在线, 合规率 {compliance_rate}%")
    except Exception as e:
        logger.warning(f"KPI 使用 Redis 数据增强失败，使用模拟数据: {e}")
    
    return kpi


@router.get("/devices")
async def get_devices_status(user: dict = Depends(get_current_user)):
    """
    获取所有设备状态列表
    优先从 Redis 读取实时传感器数据（由 simulator 或真实设备上报）
    Redis 中无数据时 fallback 到统一世界状态模拟数据
    自动根据温度与温区阈值计算告警数
    """
    # 尝试从 Redis 获取所有在线设备的实时数据
    try:
        online_devices = await redis_service.get_online_devices()
        if online_devices:
            devices = []
            for device_id in online_devices:
                data = await redis_service.get_latest_sensor_data(device_id)
                if data:
                    temp = data.get("temperature", 0)
                    target_temp = data.get("target_temperature", 0)
                    cargo_zone = data.get("cargo_zone", data.get("device_type", ""))
                    
                    # 自动计算告警
                    active_alerts = _calc_temperature_alerts(
                        float(temp), float(target_temp), str(cargo_zone)
                    )
                    temp_compliant = active_alerts == 0
                    
                    # 将 Redis 中的最新传感器数据转换为设备状态格式
                    devices.append({
                        "device_id": device_id,
                        "plate_number": data.get("plate_number", device_id),
                        "device_type": data.get("device_type", "vehicle"),
                        "online": True,
                        "temperature": temp,
                        "humidity": data.get("humidity", 0),
                        "target_temperature": target_temp,
                        "external_temp": data.get("external_temp", 0),
                        "vehicle_speed": data.get("vehicle_speed", 0),
                        "door_status": data.get("door_status", 0),
                        "vibration": data.get("vibration", 0),
                        "cold_car_status": data.get("cold_car_status", 1),
                        "cold_car_health": data.get("cold_car_health", 0.8),
                        "battery_level": data.get("battery_level", 100),
                        "signal_strength": data.get("signal_strength", 5),
                        "latitude": data.get("latitude", 0),
                        "longitude": data.get("longitude", 0),
                        "route": data.get("route", []),
                        "current_city": data.get("current_city", ""),
                        "cargo_type": data.get("cargo_type", ""),
                        "cargo_zone": str(cargo_zone),
                        "waybill_no": data.get("waybill_no", ""),
                        "active_alerts": active_alerts,
                        "last_update": data.get("timestamp", datetime.utcnow().isoformat()),
                        "temperature_compliant": temp_compliant,
                    })
                else:
                    # Redis 有设备在线记录，但没有最新传感器数据，尝试读设备状态
                    status = await redis_service.get_device_status(device_id)
                    if status:
                        devices.append({
                            "device_id": device_id,
                            "online": True,
                            "temperature": float(status.get("temperature", 0)),
                            "humidity": float(status.get("humidity", 0)),
                            "last_update": status.get("last_update", ""),
                            "active_alerts": 0,
                            "temperature_compliant": True,
                        })
            
            if devices:
                devices.sort(key=lambda x: x.get("active_alerts", 0), reverse=True)
                alert_count = sum(1 for d in devices if d.get("active_alerts", 0) > 0)
                logger.info(f"设备列表来自 Redis 实时数据，共 {len(devices)} 台，其中 {alert_count} 台有告警")
                return {"total": len(devices), "devices": devices, "data_source": "redis_realtime"}
    except Exception as e:
        logger.warning(f"从 Redis 读取设备数据失败，fallback 到模拟数据: {e}")

    # Fallback：从统一世界状态获取模拟数据
    ws = get_world_state()
    devices = list(ws["vehicles"])
    # 合并冷库传感器设备
    if "cold_room_sensors" in ws:
        devices.extend(ws["cold_room_sensors"])
    devices.sort(key=lambda x: x.get("active_alerts", 0), reverse=True)
    return {"total": len(devices), "devices": devices, "data_source": "simulated"}


@router.get("/overview")
async def get_overview(user: dict = Depends(get_current_user)):
    """获取全局态势图数据 - 来自统一世界状态"""
    ws = get_world_state()
    vehicles = ws["vehicles"]
    return {
        "vehicles": {"count": len(vehicles), "data": vehicles},
        "cold_rooms": {"count": len(ws["warehouses"]), "data": ws["warehouses"]},
        "total_online": len(vehicles),
        "timestamp": ws["timestamp"],
    }


@router.get("/alerts/summary")
async def get_alerts_summary(user: dict = Depends(get_current_user)):
    """获取告警摘要统计 - 来自统一世界状态"""
    ws = get_world_state()
    alerts = ws["alerts"]
    devices_with_alerts = len(set(a["device_id"] for a in alerts))
    return {
        "total_alerts": len(alerts),
        "devices_with_alerts": devices_with_alerts,
        "total_devices_online": len(ws["vehicles"]),
        "alert_rate": round(devices_with_alerts / max(len(ws["vehicles"]), 1) * 100, 1),
        "timestamp": ws["timestamp"],
    }
