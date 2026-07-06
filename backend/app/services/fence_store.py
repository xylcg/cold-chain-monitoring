from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid
from ..schemas.geofence import (
    FenceInDB, FenceCreate, FenceUpdate, FenceEvent, FenceEventCreate,
    FenceType, FenceCategory, AlertLevel, GeoJSONFeature
)
from ..services.world_state import get_world_state


_fences: Dict[str, FenceInDB] = {}
_fence_events: Dict[str, FenceEvent] = {}
_sync_time: float = 0
_SYNC_INTERVAL = 60
_demo_events_seeded: bool = False


def _seed_demo_events():
    """为演示环境生成围栏事件种子数据（仅在首次调用时执行）"""
    global _demo_events_seeded
    if _demo_events_seeded:
        return
    _demo_events_seeded = True

    # 确保围栏数据已同步
    _sync_with_world_state()

    # 取前8个活跃围栏作为事件目标
    active_fences = [f for f in _fences.values() if f.active][:8]
    if not active_fences:
        return

    import random
    random.seed(42)

    demo_vehicles = ["V-001", "V-002", "V-003", "V-004", "V-005"]
    event_types = ["enter", "exit", "deviation", "stay", "stay_severe"]
    event_type_labels = {
        "enter": "进入围栏区域",
        "exit": "离开围栏区域",
        "deviation": "路线偏离告警",
        "stay": "异常停留提醒",
        "stay_severe": "严重超时停留",
    }
    level_map = {
        "enter": AlertLevel.INFO, "exit": AlertLevel.INFO,
        "deviation": AlertLevel.SEVERE, "stay": AlertLevel.WARNING,
        "stay_severe": AlertLevel.SEVERE,
    }

    now = datetime.utcnow()
    event_idx = 0
    for fence in active_fences:
        # 每个围栏生成 2~4 条事件
        num_events = random.randint(2, 4)
        for i in range(num_events):
            et = event_types[random.randint(0, len(event_types) - 1)]
            vid = demo_vehicles[random.randint(0, len(demo_vehicles) - 1)]
            hours_ago = random.uniform(0.5, 23)
            event_time = now - timedelta(hours=hours_ago)

            # 根据围栏类型构造位置
            if fence.fence_type.value == "circle" and fence.data:
                c = fence.data.get("center", {})
                lat = c.get("lat", 39.9042) + random.uniform(-0.01, 0.01)
                lng = c.get("lng", 116.4074) + random.uniform(-0.01, 0.01)
            else:
                lat = 30.0 + random.uniform(-10, 10)
                lng = 110.0 + random.uniform(-15, 15)

            event_id = f"DEMO-E{event_idx:03d}"
            desc_prefix = event_type_labels.get(et, "围栏事件")
            plate = f"冷A-{int(vid.split('-')[-1]):04d}"
            desc = f"{desc_prefix} | 车辆 {plate} | 围栏 {fence.name}"

            event = FenceEvent(
                event_id=event_id,
                fence_id=fence.fence_id,
                fence_name=fence.name,
                fence_type=fence.fence_type,
                fence_category=fence.category,
                vehicle_id=vid,
                plate_number=plate,
                event_type=et,
                event_time=event_time,
                location={"lat": lat, "lng": lng},
                previous_location={"lat": lat + 0.005, "lng": lng - 0.005},
                alert_level=level_map.get(et, AlertLevel.WARNING),
                description=desc,
                temperature_c=round(random.uniform(-2.0, 8.0), 1),
                heartbeat_status="online",
                stay_duration_minutes=random.choice([None, None, 12, 25, 45]),
                resolved=random.random() < 0.35,  # 约35%已处理
            )
            _fence_events[event_id] = event
            event_idx += 1


def _sync_with_world_state():
    """同步世界状态中的围栏数据到内存存储"""
    global _sync_time
    now = datetime.utcnow().timestamp()
    
    if now - _sync_time < _SYNC_INTERVAL:
        return
    
    ws = get_world_state()
    world_fences = ws.get("fences", [])
    
    for wf in world_fences:
        fence_id = wf.get("fence_id", "")
        if not fence_id:
            continue
        
        if fence_id not in _fences:
            try:
                fence = FenceInDB(
                    fence_id=fence_id,
                    name=wf.get("name", ""),
                    fence_type=FenceType(wf.get("fence_type", "circle")),
                    category=FenceCategory(wf.get("category", "warehouse")),
                    data=wf.get("data", {}),
                    description=wf.get("description", ""),
                    active=wf.get("active", True),
                    alert_level=AlertLevel(wf.get("alert_level", "warning")),
                    speed_limit=wf.get("speed_limit"),
                    allowed_stay_minutes=wf.get("allowed_stay_minutes"),
                    effective_from=None,
                    effective_to=None,
                    tags=wf.get("tags", []),
                    route_id=wf.get("route_id"),
                    created_at=datetime.fromisoformat(wf.get("created_at", datetime.utcnow().isoformat()).replace("Z", "+00:00")) if wf.get("created_at") else datetime.utcnow(),
                    updated_at=datetime.fromisoformat(wf.get("updated_at", datetime.utcnow().isoformat()).replace("Z", "+00:00")) if wf.get("updated_at") else datetime.utcnow(),
                )
                _fences[fence_id] = fence
            except Exception:
                continue
    
    _sync_time = now


def create_fence(data: FenceCreate) -> FenceInDB:
    fence_id = f"FENCE-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.utcnow()
    fence = FenceInDB(
        fence_id=fence_id,
        name=data.name,
        fence_type=data.fence_type,
        category=data.category,
        data=data.data,
        description=data.description or "",
        active=data.active,
        alert_level=data.alert_level,
        speed_limit=data.speed_limit,
        allowed_stay_minutes=data.allowed_stay_minutes,
        effective_from=data.effective_from,
        effective_to=data.effective_to,
        tags=data.tags or [],
        route_id=data.route_id,
        created_at=now,
        updated_at=now,
    )
    _fences[fence_id] = fence
    return fence


def get_fence(fence_id: str) -> Optional[FenceInDB]:
    _sync_with_world_state()
    return _fences.get(fence_id)


def get_fences(
    fence_type: Optional[FenceType] = None,
    category: Optional[FenceCategory] = None,
    active: Optional[bool] = None,
    route_id: Optional[str] = None,
) -> List[FenceInDB]:
    _sync_with_world_state()
    result = []
    for fence in _fences.values():
        if fence_type and fence.fence_type != fence_type:
            continue
        if category and fence.category != category:
            continue
        if active is not None and fence.active != active:
            continue
        if route_id and fence.route_id != route_id:
            continue
        result.append(fence)
    return result


def update_fence(fence_id: str, data: FenceUpdate) -> Optional[FenceInDB]:
    fence = _fences.get(fence_id)
    if not fence:
        return None
    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(fence, key, value)
    fence.updated_at = datetime.utcnow()
    _fences[fence_id] = fence
    return fence


def delete_fence(fence_id: str) -> bool:
    if fence_id in _fences:
        del _fences[fence_id]
        return True
    return False


def create_fence_event(data: FenceEventCreate, fence: FenceInDB, plate_number: str = "") -> FenceEvent:
    event_id = f"EVENT-{uuid.uuid4().hex[:8].upper()}"
    
    event_type_map = {
        "enter": {"level": AlertLevel.INFO, "desc": "进入围栏"},
        "exit": {"level": AlertLevel.INFO, "desc": "离开围栏"},
        "depart": {"level": AlertLevel.WARNING, "desc": "离开节点"},
        "stay": {"level": AlertLevel.WARNING, "desc": "异常停留"},
        "stay_severe": {"level": AlertLevel.SEVERE, "desc": "严重停留"},
        "violation": {"level": AlertLevel.SEVERE, "desc": "违规事件"},
        "offline": {"level": AlertLevel.SEVERE, "desc": "设备离线"},
        "timeout": {"level": AlertLevel.NORMAL, "desc": "节点超时"},
        "deviation": {"level": AlertLevel.SEVERE, "desc": "路线偏离"},
        "forbidden_entry": {"level": AlertLevel.SEVERE, "desc": "禁区闯入"},
    }
    
    event_info = event_type_map.get(data.event_type, {"level": AlertLevel.WARNING, "desc": "围栏事件"})
    alert_level = event_info["level"]
    
    description_parts = [f"{event_info['desc']}: {fence.name}"]
    if data.city_section:
        description_parts.append(f"城市区间: {data.city_section}")
    if data.stay_duration_minutes:
        description_parts.append(f"停留时长: {data.stay_duration_minutes}分钟")
    if data.temperature_c is not None:
        description_parts.append(f"温度: {data.temperature_c}°C")
    if data.heartbeat_status == "offline":
        description_parts.append("设备离线")
    
    event = FenceEvent(
        event_id=event_id,
        fence_id=fence.fence_id,
        fence_name=fence.name,
        fence_type=fence.fence_type,
        fence_category=fence.category,
        vehicle_id=data.vehicle_id,
        plate_number=plate_number,
        event_type=data.event_type,
        event_time=datetime.utcnow(),
        location=data.location,
        previous_location=data.previous_location,
        alert_level=alert_level,
        description=" | ".join(description_parts),
        temperature_c=data.temperature_c,
        heartbeat_status=data.heartbeat_status,
        stay_duration_minutes=data.stay_duration_minutes,
        city_section=data.city_section,
    )
    _fence_events[event_id] = event
    return event


def get_fence_events(
    fence_id: Optional[str] = None,
    vehicle_id: Optional[str] = None,
    event_type: Optional[str] = None,
    alert_level: Optional[AlertLevel] = None,
    resolved: Optional[bool] = None,
    hours: Optional[int] = None,
) -> List[FenceEvent]:
    _seed_demo_events()
    result = []
    now = datetime.utcnow()
    for event in _fence_events.values():
        if fence_id and event.fence_id != fence_id:
            continue
        if vehicle_id and event.vehicle_id != vehicle_id:
            continue
        if event_type and event.event_type != event_type:
            continue
        if alert_level and event.alert_level != alert_level:
            continue
        if resolved is not None and event.resolved != resolved:
            continue
        if hours:
            if (now - event.event_time).total_seconds() > hours * 3600:
                continue
        result.append(event)
    result.sort(key=lambda x: x.event_time, reverse=True)
    return result


def resolve_event(event_id: str) -> Optional[FenceEvent]:
    event = _fence_events.get(event_id)
    if event:
        event.resolved = True
    return event


def fence_to_geojson(fence: FenceInDB) -> GeoJSONFeature:
    geometry = {}
    properties = {
        "fence_id": fence.fence_id,
        "name": fence.name,
        "type": fence.fence_type.value,
        "category": fence.category.value,
        "alert_level": fence.alert_level.value,
        "active": fence.active,
        "description": fence.description,
        "tags": fence.tags,
    }

    if fence.fence_type == FenceType.CIRCLE:
        center = fence.data.get("center", {})
        radius = fence.data.get("radius_meters", 100)
        geometry = {
            "type": "Point",
            "coordinates": [center.get("lng", 0), center.get("lat", 0)],
        }
        properties["radius"] = radius
        properties["style"] = {
            "color": "#3b82f6",
            "fillColor": "#3b82f6",
            "fillOpacity": 0.1,
            "radius": radius / 100,
        }

    elif fence.fence_type == FenceType.LINE_BUFFER:
        points = fence.data.get("points", [])
        coordinates = [[p.get("lng", 0), p.get("lat", 0)] for p in points]
        geometry = {
            "type": "LineString",
            "coordinates": coordinates,
        }
        properties["buffer_meters"] = fence.data.get("buffer_meters", 50)
        properties["start_city"] = fence.data.get("start_city", "")
        properties["end_city"] = fence.data.get("end_city", "")
        properties["style"] = {
            "color": "#22c55e",
            "weight": 4,
            "opacity": 0.7,
        }

    elif fence.fence_type == FenceType.POLYGON:
        coords = fence.data.get("coordinates", [])
        coordinates = [[[p.get("lng", 0), p.get("lat", 0)] for p in ring] for ring in coords]
        geometry = {
            "type": "Polygon",
            "coordinates": coordinates,
        }
        properties["style"] = {
            "color": "#ef4444",
            "fillColor": "#ef4444",
            "fillOpacity": 0.2,
            "weight": 2,
        }

    elif fence.fence_type == FenceType.CITY:
        center = fence.data.get("center", {"lat": 0, "lng": 0})
        geometry = {
            "type": "Point",
            "coordinates": [center.get("lng", 0), center.get("lat", 0)],
        }
        properties["city_name"] = fence.data.get("city_name", "")
        properties["province"] = fence.data.get("province", "")
        properties["radius"] = fence.data.get("radius_meters", 50000)
        properties["style"] = {
            "color": "#8b5cf6",
            "fillColor": "#8b5cf6",
            "fillOpacity": 0.05,
            "radius": 50,
        }

    return GeoJSONFeature(
        type="Feature",
        id=fence.fence_id,
        geometry=geometry,
        properties=properties,
    )


def get_all_fences_geojson() -> Dict[str, any]:
    _sync_with_world_state()
    features = [fence_to_geojson(f).dict() for f in _fences.values()]
    return {
        "type": "FeatureCollection",
        "features": features,
    }


def get_fence_stats() -> Dict[str, any]:
    _sync_with_world_state()
    _seed_demo_events()
    total = len(_fences)
    by_type = {}
    by_category = {}
    active_count = 0
    for fence in _fences.values():
        by_type[fence.fence_type.value] = by_type.get(fence.fence_type.value, 0) + 1
        by_category[fence.category.value] = by_category.get(fence.category.value, 0) + 1
        if fence.active:
            active_count += 1

    events_by_level = {"severe": 0, "warning": 0, "normal": 0, "info": 0}
    for event in _fence_events.values():
        if not event.resolved:
            events_by_level[event.alert_level.value] = events_by_level.get(event.alert_level.value, 0) + 1

    return {
        "total_fences": total,
        "active_fences": active_count,
        "fences_by_type": by_type,
        "fences_by_category": by_category,
        "total_events": len(_fence_events),
        "active_events": sum(events_by_level.values()),
        "events_by_level": events_by_level,
    }


def clear_all_events():
    """清空所有围栏事件"""
    global _fence_events
    _fence_events = {}


def force_sync():
    """强制同步世界状态"""
    global _sync_time
    _sync_time = 0
    _sync_with_world_state()