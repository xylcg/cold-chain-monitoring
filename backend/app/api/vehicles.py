"""
车辆实时追踪 API
使用统一世界状态，确保数据跨页面联通
"""
import random
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query

from ..services.world_state import get_world_state, CITY_COORDS, VEHICLE_ROUTES
from ..core.security import get_current_user

router = APIRouter(prefix="/api/v1/vehicles", tags=["车辆追踪"])


@router.get("/list")
async def get_vehicle_list(
    user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    keyword: str = Query(None),
):
    """获取车辆列表（分页）- 来自统一世界状态"""
    ws = get_world_state()
    vehicles = ws["vehicles"]

    # 过滤
    if status == "alert":
        vehicles = [v for v in vehicles if v["active_alerts"] > 0]
    if keyword:
        keyword_lower = keyword.lower()
        vehicles = [v for v in vehicles
                    if keyword_lower in v["device_id"].lower()
                    or keyword_lower in v["plate_number"].lower()]

    total = len(vehicles)
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "total": total, "page": page, "page_size": page_size,
        "vehicles": vehicles[start:end],
        "timestamp": ws["timestamp"],
    }


@router.get("/{device_id}/detail")
async def get_vehicle_detail(device_id: str, user: dict = Depends(get_current_user)):
    """获取单辆车详情 - 来自统一世界状态"""
    ws = get_world_state()
    for v in ws["vehicles"]:
        if v["device_id"] == device_id:
            detail = dict(v)
            # 附加维护数据
            from ..services.world_state import _generate_maintenance_data
            detail["maintenance"] = _generate_maintenance_data(v)
            return detail

    # 如果找不到，从世界状态重新生成
    from ..services.world_state import _generate_vehicle
    idx = int(device_id.split("-")[1]) - 1 if "-" in device_id else 0
    return _generate_vehicle(idx)


@router.get("/{device_id}/trajectory")
async def get_vehicle_trajectory(
    device_id: str,
    user: dict = Depends(get_current_user),
    hours: int = Query(2, ge=1, le=24),
):
    """获取车辆历史轨迹 - 基于统一世界状态的路线"""
    ws = get_world_state()
    vehicle = None
    for v in ws["vehicles"]:
        if v["device_id"] == device_id:
            vehicle = v
            break

    route_idx = int(device_id.split("-")[1]) % len(VEHICLE_ROUTES) if "-" in device_id else 0
    route = vehicle["route"] if vehicle else VEHICLE_ROUTES[route_idx]

    now = datetime.utcnow()
    points = []
    step_count = min(hours * 30, 720)

    for i in range(step_count, 0, -1):
        t = now - timedelta(minutes=i * 2)
        city_idx = (step_count - i) * len(route) // step_count
        city_idx = min(city_idx, len(route) - 1)
        next_city_idx = min(city_idx + 1, len(route) - 1)
        progress = ((step_count - i) * len(route) / step_count) - city_idx
        progress = max(0, min(1, progress))

        from_coord = CITY_COORDS.get(route[city_idx], (39.9, 116.4))
        to_coord = CITY_COORDS.get(route[next_city_idx], (30.5, 104.0))
        lat = from_coord[0] + (to_coord[0] - from_coord[0]) * progress + random.uniform(-0.1, 0.1)
        lng = from_coord[1] + (to_coord[1] - from_coord[1]) * progress + random.uniform(-0.1, 0.1)

        base_temp = vehicle["temperature"] if vehicle else -18
        temp = base_temp + random.gauss(0, 0.8)

        points.append({
            "time": t.isoformat(),
            "latitude": round(lat, 4),
            "longitude": round(lng, 4),
            "temperature": round(temp, 1),
            "humidity": round(vehicle["humidity"] + random.gauss(0, 3), 1) if vehicle else round(random.uniform(55, 75), 1),
            "vehicle_speed": round(random.uniform(0, 100), 1),
            "door_status": 0 if random.random() > 0.05 else 1,
            "cold_car_status": 1 if random.random() > 0.02 else 0,
        })

    return {
        "device_id": device_id,
        "route": route,
        "points": points,
        "point_count": len(points),
        "start_time": points[0]["time"] if points else None,
        "end_time": points[-1]["time"] if points else None,
    }


@router.get("/all/positions")
async def get_all_vehicle_positions(user: dict = Depends(get_current_user)):
    """获取所有车辆实时位置 - 来自统一世界状态"""
    ws = get_world_state()
    positions = []
    for v in ws["vehicles"]:
        positions.append({
            "device_id": v["device_id"],
            "plate_number": v["plate_number"],
            "latitude": v["latitude"],
            "longitude": v["longitude"],
            "temperature": v["temperature"],
            "vehicle_speed": v["vehicle_speed"],
            "cold_car_status": v["cold_car_status"],
            "online": True,
            "has_alert": v["active_alerts"] > 0,
            "cargo_type": v["cargo_type"],
            "current_city": v["current_city"],
            "last_update": v["last_update"],
        })

    return {
        "count": len(positions),
        "vehicles": positions,
        "timestamp": ws["timestamp"],
    }
