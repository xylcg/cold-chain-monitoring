from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from ..schemas.geofence import FenceInDB, FenceEvent, FenceEventCreate, FenceCategory, AlertLevel
from .fence_store import create_fence_event, get_fence_events, force_sync
from .fence_judge import is_point_in_fence, check_route_deviation, find_containing_fences, haversine_distance
from ..services.world_state import get_world_state, CITY_COORDS
from ..services.alert_engine import alert_engine
from ..schemas import TEMP_THRESHOLD


VEHICLE_FENCE_STATE: Dict[str, Dict[str, any]] = {}


def get_vehicle_state(vehicle_id: str) -> Dict[str, any]:
    if vehicle_id not in VEHICLE_FENCE_STATE:
        VEHICLE_FENCE_STATE[vehicle_id] = {
            "current_fences": [],
            "previous_fences": [],
            "consecutive_off_route": 0,
            "stay_start_time": None,
            "stay_fence_id": None,
            "last_location": None,
            "last_update_time": None,
            "heartbeat_status": "online",
            "last_heartbeat_time": datetime.utcnow(),
            "current_city_section": None,
            "route_fence_ids": [],
            "door_open_time": None,
            "last_event_time": None,
        }
    return VEHICLE_FENCE_STATE[vehicle_id]


def update_vehicle_state(vehicle_id: str, updates: Dict[str, any]):
    state = get_vehicle_state(vehicle_id)
    state.update(updates)
    VEHICLE_FENCE_STATE[vehicle_id] = state


def is_whitelist_fence(fence: FenceInDB) -> bool:
    whitelist_categories = [
        FenceCategory.SERVICE_AREA,
        FenceCategory.WAREHOUSE,
        FenceCategory.HUB,
        FenceCategory.CHECKPOINT,
    ]
    return fence.category in whitelist_categories


def is_high_temp_zone(fence: FenceInDB) -> bool:
    return fence.category == FenceCategory.HIGH_TEMP


def is_forbidden_zone(fence: FenceInDB) -> bool:
    forbidden_categories = [
        FenceCategory.FORBIDDEN,
        FenceCategory.RESTRICTED,
    ]
    return fence.category in forbidden_categories


def _send_system_alert(event: FenceEvent):
    """将围栏事件转换为系统告警并发送"""
    severity_map = {
        AlertLevel.SEVERE: "critical",
        AlertLevel.WARNING: "severe",
        AlertLevel.NORMAL: "normal",
        AlertLevel.INFO: "normal",
    }
    
    system_severity = severity_map.get(event.alert_level, "normal")
    
    alert_data = {
        "device_id": event.vehicle_id,
        "alert_type": f"fence_{event.event_type}",
        "severity": system_severity,
        "message": event.description,
        "sensor_value": event.stay_duration_minutes or event.temperature_c,
        "threshold_value": None,
        "timestamp": event.event_time.isoformat(),
        "targets": alert_engine.SEVERITY_ROUTES.get(system_severity, ["driver"]),
        "metadata": {
            "fence_id": event.fence_id,
            "fence_name": event.fence_name,
            "fence_type": event.fence_type.value,
            "fence_category": event.fence_category.value,
            "plate_number": event.plate_number,
            "location": event.location.dict(),
            "city_section": event.city_section,
            "heartbeat_status": event.heartbeat_status,
        },
    }
    
    import asyncio
    asyncio.create_task(alert_engine.process_alert(alert_data))


def process_vehicle_position(
    vehicle_id: str,
    plate_number: str,
    lat: float,
    lng: float,
    temperature_c: Optional[float] = None,
    heartbeat_time: Optional[datetime] = None,
    city_coords: Dict[str, Tuple[float, float]] = None,
) -> List[FenceEvent]:
    events: List[FenceEvent] = []
    state = get_vehicle_state(vehicle_id)
    ws = get_world_state()
    
    force_sync()
    all_fences = get_fence_events.__globals__['_fences'].values()
    all_fences = list(all_fences)
    
    route_fences = [f for f in all_fences if f.category == FenceCategory.ROUTE_SEGMENT]
    
    current_fences = find_containing_fences(lat, lng, all_fences, city_coords or CITY_COORDS)
    previous_fences = state["current_fences"]

    update_vehicle_state(vehicle_id, {
        "last_location": {"lat": lat, "lng": lng},
        "last_update_time": datetime.utcnow(),
    })

    if heartbeat_time:
        time_since_heartbeat = (datetime.utcnow() - heartbeat_time).total_seconds()
        if time_since_heartbeat > TEMP_THRESHOLD["DEVICE_OFFLINE_SECONDS"]:
            state["heartbeat_status"] = "offline"
        else:
            state["heartbeat_status"] = "online"
        state["last_heartbeat_time"] = heartbeat_time

    # 1. 路线偏离检测
    is_deviation, new_off_count = check_route_deviation(
        lat, lng, route_fences, state["consecutive_off_route"], city_coords or CITY_COORDS
    )
    update_vehicle_state(vehicle_id, {"consecutive_off_route": new_off_count})

    if is_deviation and route_fences:
        closest_fence = route_fences[0] if route_fences else None
        if closest_fence:
            city_section = f"{closest_fence.data.get('start_city', '')}-{closest_fence.data.get('end_city', '')}"
            event_data = FenceEventCreate(
                fence_id=closest_fence.fence_id,
                vehicle_id=vehicle_id,
                event_type="deviation",
                location={"lat": lat, "lng": lng},
                temperature_c=temperature_c,
                heartbeat_status=state["heartbeat_status"],
                city_section=city_section,
            )
            event = create_fence_event(event_data, closest_fence, plate_number)
            events.append(event)
            _send_system_alert(event)

    # 2. 围栏进出检测
    entered_fences = [f for f in current_fences if f not in previous_fences]
    exited_fences = [f for f in previous_fences if f not in current_fences]

    for fence in entered_fences:
        if is_forbidden_zone(fence):
            event_data = FenceEventCreate(
                fence_id=fence.fence_id,
                vehicle_id=vehicle_id,
                event_type="forbidden_entry",
                location={"lat": lat, "lng": lng},
                temperature_c=temperature_c,
                heartbeat_status=state["heartbeat_status"],
            )
            event = create_fence_event(event_data, fence, plate_number)
            events.append(event)
            _send_system_alert(event)
        else:
            event_data = FenceEventCreate(
                fence_id=fence.fence_id,
                vehicle_id=vehicle_id,
                event_type="enter",
                location={"lat": lat, "lng": lng},
                temperature_c=temperature_c,
                heartbeat_status=state["heartbeat_status"],
            )
            event = create_fence_event(event_data, fence, plate_number)
            events.append(event)

        if fence.fence_type == FenceType.CITY:
            update_vehicle_state(vehicle_id, {
                "current_city_section": fence.data.get("city_name", "")
            })

        if fence.category in [FenceCategory.WAREHOUSE, FenceCategory.HUB, FenceCategory.CHECKPOINT]:
            update_vehicle_state(vehicle_id, {
                "stay_start_time": datetime.utcnow(),
                "stay_fence_id": fence.fence_id,
            })

    for fence in exited_fences:
        event_data = FenceEventCreate(
            fence_id=fence.fence_id,
            vehicle_id=vehicle_id,
            event_type="exit",
            location={"lat": lat, "lng": lng},
            temperature_c=temperature_c,
            heartbeat_status=state["heartbeat_status"],
        )
        event = create_fence_event(event_data, fence, plate_number)
        events.append(event)

        if state["stay_fence_id"] == fence.fence_id and state["stay_start_time"]:
            stay_duration = (datetime.utcnow() - state["stay_start_time"]).total_seconds() / 60
            event_data = FenceEventCreate(
                fence_id=fence.fence_id,
                vehicle_id=vehicle_id,
                event_type="depart",
                location={"lat": lat, "lng": lng},
                temperature_c=temperature_c,
                heartbeat_status=state["heartbeat_status"],
                stay_duration_minutes=int(stay_duration),
            )
            event = create_fence_event(event_data, fence, plate_number)
            events.append(event)
            update_vehicle_state(vehicle_id, {
                "stay_start_time": None,
                "stay_fence_id": None,
            })

    # 3. 违规停留检测
    speed = 0
    if state["last_location"]:
        last_lat, last_lng = state["last_location"]["lat"], state["last_location"]["lng"]
        dist = 0
        if last_lat and last_lng:
            dist = haversine_distance(lat, lng, last_lat, last_lng)
        time_diff = (datetime.utcnow() - (state["last_update_time"] or datetime.utcnow())).total_seconds()
        if time_diff > 0:
            speed = dist / time_diff * 3.6

    is_stopped = speed < 2

    if is_stopped and not state["stay_start_time"]:
        non_whitelist_fences = [f for f in current_fences if not is_whitelist_fence(f)]
        if non_whitelist_fences:
            update_vehicle_state(vehicle_id, {
                "stay_start_time": datetime.utcnow(),
                "stay_fence_id": non_whitelist_fences[0].fence_id,
            })

    if state["stay_start_time"]:
        stay_duration = (datetime.utcnow() - state["stay_start_time"]).total_seconds() / 60
        current_fence = next((f for f in all_fences if f.fence_id == state["stay_fence_id"]), None)

        if current_fence:
            if is_high_temp_zone(current_fence) and stay_duration > 30:
                event_data = FenceEventCreate(
                    fence_id=current_fence.fence_id,
                    vehicle_id=vehicle_id,
                    event_type="stay_severe",
                    location={"lat": lat, "lng": lng},
                    temperature_c=temperature_c,
                    heartbeat_status=state["heartbeat_status"],
                    stay_duration_minutes=int(stay_duration),
                )
                event = create_fence_event(event_data, current_fence, plate_number)
                events.append(event)
                _send_system_alert(event)
            elif stay_duration > 15 and not is_whitelist_fence(current_fence):
                event_data = FenceEventCreate(
                    fence_id=current_fence.fence_id,
                    vehicle_id=vehicle_id,
                    event_type="stay",
                    location={"lat": lat, "lng": lng},
                    temperature_c=temperature_c,
                    heartbeat_status=state["heartbeat_status"],
                    stay_duration_minutes=int(stay_duration),
                )
                event = create_fence_event(event_data, current_fence, plate_number)
                events.append(event)
                _send_system_alert(event)

    update_vehicle_state(vehicle_id, {"current_fences": current_fences})

    return events


def process_heartbeat_offline(
    vehicle_id: str,
    plate_number: str,
    last_lat: float,
    last_lng: float,
    offline_duration_seconds: float,
    city_coords: Dict[str, Tuple[float, float]] = None,
) -> List[FenceEvent]:
    events: List[FenceEvent] = []
    ws = get_world_state()
    
    force_sync()
    all_fences = get_fence_events.__globals__['_fences'].values()
    all_fences = list(all_fences)
    
    city_fences = [f for f in all_fences if f.fence_type == FenceType.CITY]

    containing_cities = find_containing_fences(last_lat, last_lng, city_fences, city_coords or CITY_COORDS)
    city_section = containing_cities[0].data.get("city_name", "") if containing_cities else "未知区域"

    route_fences = [f for f in all_fences if f.category == FenceCategory.ROUTE_SEGMENT]
    in_route_segment = any(is_point_in_fence(last_lat, last_lng, f, city_coords or CITY_COORDS) for f in route_fences)

    event_type = "offline"
    for fence in containing_cities:
        event_data = FenceEventCreate(
            fence_id=fence.fence_id,
            vehicle_id=vehicle_id,
            event_type=event_type,
            location={"lat": last_lat, "lng": last_lng},
            heartbeat_status="offline",
            stay_duration_minutes=int(offline_duration_seconds / 60),
            city_section=city_section,
        )
        event = create_fence_event(event_data, fence, plate_number)
        events.append(event)
        _send_system_alert(event)

    if not containing_cities and route_fences:
        for fence in route_fences[:1]:
            event_data = FenceEventCreate(
                fence_id=fence.fence_id,
                vehicle_id=vehicle_id,
                event_type=event_type,
                location={"lat": last_lat, "lng": last_lng},
                heartbeat_status="offline",
                stay_duration_minutes=int(offline_duration_seconds / 60),
                city_section=f"{fence.data.get('start_city', '')}-{fence.data.get('end_city', '')}",
            )
            event = create_fence_event(event_data, fence, plate_number)
            events.append(event)
            _send_system_alert(event)

    return events


def get_active_fence_alerts(hours: int = 24) -> List[FenceEvent]:
    return get_fence_events(
        resolved=False,
        hours=hours,
    )


def get_alerts_by_level(level: AlertLevel, hours: int = 24) -> List[FenceEvent]:
    return get_fence_events(
        alert_level=level,
        resolved=False,
        hours=hours,
    )


from ..schemas.geofence import FenceType