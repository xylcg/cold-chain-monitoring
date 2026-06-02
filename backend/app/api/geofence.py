"""
冷链电子围栏管理 API
模块8: 冷链电子围栏管理
- 创建/编辑/删除电子围栏
- 围栏进出事件记录
- 围栏区域温控衔接监控
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query

from ..core.security import get_current_user
from ..services.redis_service import redis_service

router = APIRouter(prefix="/api/v1/geofence", tags=["电子围栏"])

# 内存存储电子围栏数据（后续可迁移到 PostgreSQL）
_geofences: list[dict] = []
_geofence_events: list[dict] = []


# ==================== 初始化默认围栏 ====================
def _init_default_geofences():
    if not _geofences:
        _geofences.extend([
            {
                "id": "gf-001",
                "name": "华北中心冷库",
                "type": "cold_storage",
                "center": {"lat": 39.9042, "lng": 116.4074},
                "radius": 500,
                "address": "北京市朝阳区",
                "contact": "张经理",
                "phone": "13800138001",
                "temp_range": {"min": -25, "max": -15},
                "created_at": datetime.utcnow().isoformat(),
            },
            {
                "id": "gf-002",
                "name": "华东配送中心",
                "type": "distribution_center",
                "center": {"lat": 31.2304, "lng": 121.4737},
                "radius": 800,
                "address": "上海市浦东新区",
                "contact": "李经理",
                "phone": "13800138002",
                "temp_range": {"min": 0, "max": 8},
                "created_at": datetime.utcnow().isoformat(),
            },
            {
                "id": "gf-003",
                "name": "华南前置仓",
                "type": "front_warehouse",
                "center": {"lat": 23.1291, "lng": 113.2644},
                "radius": 300,
                "address": "广州市天河区",
                "contact": "王经理",
                "phone": "13800138003",
                "temp_range": {"min": -18, "max": -12},
                "created_at": datetime.utcnow().isoformat(),
            },
            {
                "id": "gf-004",
                "name": "西南冷链基地",
                "type": "cold_storage",
                "center": {"lat": 30.5728, "lng": 104.0668},
                "radius": 600,
                "address": "成都市高新区",
                "contact": "赵经理",
                "phone": "13800138004",
                "temp_range": {"min": -25, "max": -15},
                "created_at": datetime.utcnow().isoformat(),
            },
            {
                "id": "gf-005",
                "name": "华中分拨中心",
                "type": "distribution_center",
                "center": {"lat": 30.5928, "lng": 114.3055},
                "radius": 500,
                "address": "武汉市江汉区",
                "contact": "陈经理",
                "phone": "13800138005",
                "temp_range": {"min": 0, "max": 4},
                "created_at": datetime.utcnow().isoformat(),
            },
        ])


_init_default_geofences()


# ==================== 围栏管理 ====================

@router.get("")
async def list_geofences(
    type: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    """获取电子围栏列表"""
    result = _geofences
    if type:
        result = [g for g in result if g["type"] == type]
    return {"count": len(result), "geofences": result}


@router.get("/{geofence_id}")
async def get_geofence(
    geofence_id: str,
    user: dict = Depends(get_current_user),
):
    """获取单个电子围栏详情"""
    for g in _geofences:
        if g["id"] == geofence_id:
            return g
    raise HTTPException(status_code=404, detail="电子围栏不存在")


@router.post("")
async def create_geofence(
    name: str,
    type: str,
    lat: float,
    lng: float,
    radius: float,
    address: str = "",
    contact: str = "",
    phone: str = "",
    temp_min: float = -25,
    temp_max: float = -15,
    user: dict = Depends(get_current_user),
):
    """创建电子围栏"""
    import uuid
    geofence = {
        "id": f"gf-{uuid.uuid4().hex[:6]}",
        "name": name,
        "type": type,
        "center": {"lat": lat, "lng": lng},
        "radius": radius,
        "address": address,
        "contact": contact,
        "phone": phone,
        "temp_range": {"min": temp_min, "max": temp_max},
        "created_at": datetime.utcnow().isoformat(),
    }
    _geofences.append(geofence)
    return {"status": "ok", "geofence": geofence}


@router.put("/{geofence_id}")
async def update_geofence(
    geofence_id: str,
    name: Optional[str] = None,
    radius: Optional[float] = None,
    contact: Optional[str] = None,
    phone: Optional[str] = None,
    temp_min: Optional[float] = None,
    temp_max: Optional[float] = None,
    user: dict = Depends(get_current_user),
):
    """更新电子围栏"""
    for g in _geofences:
        if g["id"] == geofence_id:
            if name: g["name"] = name
            if radius: g["radius"] = radius
            if contact: g["contact"] = contact
            if phone: g["phone"] = phone
            if temp_min is not None: g["temp_range"]["min"] = temp_min
            if temp_max is not None: g["temp_range"]["max"] = temp_max
            return {"status": "ok", "geofence": g}
    raise HTTPException(status_code=404, detail="电子围栏不存在")


@router.delete("/{geofence_id}")
async def delete_geofence(
    geofence_id: str,
    user: dict = Depends(get_current_user),
):
    """删除电子围栏"""
    global _geofences
    original_len = len(_geofences)
    _geofences = [g for g in _geofences if g["id"] != geofence_id]
    if len(_geofences) == original_len:
        raise HTTPException(status_code=404, detail="电子围栏不存在")
    return {"status": "ok", "deleted": geofence_id}


# ==================== 围栏事件 ====================

@router.get("/events")
async def get_geofence_events(
    geofence_id: Optional[str] = None,
    device_id: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 50,
    user: dict = Depends(get_current_user),
):
    """查询围栏进出事件"""
    events = _geofence_events
    if geofence_id:
        events = [e for e in events if e["geofence_id"] == geofence_id]
    if device_id:
        events = [e for e in events if e["device_id"] == device_id]
    if event_type:
        events = [e for e in events if e["event_type"] == event_type]

    events = sorted(events, key=lambda e: e["timestamp"], reverse=True)
    return {"count": len(events[:limit]), "events": events[:limit]}


@router.post("/events/check")
async def check_geofence_event(
    device_id: str,
    lat: float,
    lng: float,
    temperature: float = 0.0,
):
    """
    检查设备是否进入/离开电子围栏
    由传感器数据上报时自动调用
    """
    events = []
    for gf in _geofences:
        center = gf["center"]
        distance = _haversine_distance(lat, lng, center["lat"], center["lng"])
        is_inside = distance <= gf["radius"]

        event = {
            "geofence_id": gf["id"],
            "geofence_name": gf["name"],
            "device_id": device_id,
            "is_inside": is_inside,
            "distance_meters": round(distance, 1),
            "temperature": temperature,
            "temp_in_range": (
                gf["temp_range"]["min"] <= temperature <= gf["temp_range"]["max"]
            ) if is_inside else True,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if is_inside:
            event["event_type"] = "inside"
            if not event["temp_in_range"]:
                event["warning"] = f"温度{temperature}°C超出围栏要求[{gf['temp_range']['min']}~{gf['temp_range']['max']}°C]"
        else:
            event["event_type"] = "outside"

        _geofence_events.insert(0, event)
        events.append(event)

    return {"device_id": device_id, "events": events}


@router.get("/device/{device_id}/status")
async def get_device_geofence_status(
    device_id: str,
    user: dict = Depends(get_current_user),
):
    """获取设备当前围栏状态"""
    status = await redis_service.get_device_status(device_id)
    if not status:
        raise HTTPException(status_code=404, detail="设备离线或不存在")

    lat = float(status.get("latitude", 0))
    lng = float(status.get("longitude", 0))
    temperature = float(status.get("temperature", 0))

    fence_status = []
    for gf in _geofences:
        center = gf["center"]
        distance = _haversine_distance(lat, lng, center["lat"], center["lng"])
        is_inside = distance <= gf["radius"]
        fence_status.append({
            "geofence_id": gf["id"],
            "geofence_name": gf["name"],
            "is_inside": is_inside,
            "distance_meters": round(distance, 1),
        })

    return {
        "device_id": device_id,
        "location": {"lat": lat, "lng": lng},
        "temperature": temperature,
        "fences": fence_status,
    }


def _haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """计算两点间的 Haversine 距离（米）"""
    import math
    R = 6371000  # 地球半径（米）
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c
