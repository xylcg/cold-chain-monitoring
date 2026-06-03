"""
车辆实时追踪 API
模块: 车辆GPS追踪、轨迹回放、车辆详情
"""
import random
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query

from ..services.redis_service import redis_service
from ..core.security import get_current_user

router = APIRouter(prefix="/api/v1/vehicles", tags=["车辆追踪"])

# 中国主要城市坐标范围 (用于模拟数据)
CITY_COORDS = {
    "北京": (39.9042, 116.4074),
    "上海": (31.2304, 121.4737),
    "广州": (23.1291, 113.2644),
    "成都": (30.5728, 104.0668),
    "武汉": (30.5928, 114.3055),
    "西安": (34.3416, 108.9398),
    "郑州": (34.7466, 113.6253),
    "长沙": (28.2282, 112.9388),
    "深圳": (22.5431, 114.0579),
    "杭州": (30.2741, 120.1551),
    "南京": (32.0603, 118.7969),
    "重庆": (29.4316, 106.9123),
    "济南": (36.6512, 117.1201),
    "沈阳": (41.8057, 123.4315),
    "天津": (39.0842, 117.2009),
}


def _find_nearest_city(lat: float, lng: float) -> str:
    """根据经纬度找到最近的中国城市"""
    import math
    best_city = "北京"
    best_dist = float("inf")
    for city, (clat, clng) in CITY_COORDS.items():
        # 用简单的欧几里得距离近似（纬度约111km/度，经度约111*cos(lat)km/度）
        dlat = (lat - clat) ** 2
        dlng = ((lng - clng) * math.cos(math.radians((lat + clat) / 2))) ** 2
        dist = dlat + dlng
        if dist < best_dist:
            best_dist = dist
            best_city = city
    return best_city

# 预设车辆路线
VEHICLE_ROUTES = [
    ["北京", "郑州", "武汉", "长沙", "广州"],
    ["北京", "西安", "成都", "广州"],
    ["上海", "杭州", "武汉", "成都"],
    ["上海", "郑州", "西安", "成都"],
    ["广州", "长沙", "武汉", "郑州", "北京"],
    ["成都", "武汉", "郑州", "北京"],
    ["上海", "武汉", "长沙", "深圳"],
    ["北京", "郑州", "武汉", "深圳"],
]


@router.get("/list")
async def get_vehicle_list(
    user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str = Query(None, description="过滤: online/offline/alert"),
    keyword: str = Query(None, description="搜索车牌/设备号"),
):
    """获取车辆列表（分页）"""
    try:
        online_devices = await redis_service.get_online_devices()
    except Exception:
        online_devices = set()

    vehicles = []
    online_set = set(online_devices)

    for i in range(1, 101):
        dev_id = f"VEH-{i:04d}"
        plate = f"冷A-{i:04d}"

        # 尝试从Redis获取实时数据
        status_data = {}
        if dev_id in online_set:
            try:
                status_data = await redis_service.get_device_status(dev_id) or {}
            except Exception:
                status_data = {}

        route_idx = (i - 1) % len(VEHICLE_ROUTES)
        route = VEHICLE_ROUTES[route_idx]

        online = dev_id in online_set

        # 在线车辆根据实际坐标推算城市，离线车辆随机选择路线城市
        if online and status_data.get("latitude") and status_data.get("longitude"):
            lat = float(status_data.get("latitude", 0))
            lng = float(status_data.get("longitude", 0))
            current_city = _find_nearest_city(lat, lng)
        else:
            current_city = route[random.randint(0, len(route) - 1)]
            city_coord = CITY_COORDS.get(current_city, (39.9, 116.4))
            lat = city_coord[0] + random.uniform(-0.5, 0.5)
            lng = city_coord[1] + random.uniform(-0.5, 0.5)

        temp = float(status_data.get("temperature", 0)) if online else round(random.uniform(-22, 6), 1)
        has_alert = random.random() < 0.15 if online else False

        vehicle = {
            "device_id": dev_id,
            "plate_number": plate,
            "device_type": "vehicle",
            "online": online,
            "temperature": temp,
            "humidity": float(status_data.get("humidity", 0)) if online else round(random.uniform(50, 80), 1),
            "latitude": lat,
            "longitude": lng,
            "vehicle_speed": float(status_data.get("vehicle_speed", 0)) if online else round(random.uniform(0, 100), 1),
            "door_status": int(status_data.get("door_status", 0)) if online else 0,
            "cold_car_status": int(status_data.get("cold_car_status", 1)) if online else 1,
            "battery_level": float(status_data.get("battery_level", 0)) if online else round(random.uniform(60, 100), 1),
            "signal_strength": int(status_data.get("signal_strength", 0)) if online else random.randint(3, 5),
            "waybill_no": f"WB-{datetime.now().strftime('%Y%m%d')}-{i:04d}",
            "cargo_type": random.choice(["冷冻肉类", "冷冻海鲜", "冷藏乳制品", "冷藏水果", "疫苗", "生物试剂"]),
            "route": route,
            "current_city": current_city,
            "active_alerts": random.randint(1, 3) if has_alert else 0,
            "last_update": status_data.get("last_update", datetime.utcnow().isoformat()),
        }

        # 按条件过滤
        if status == "online" and not online:
            continue
        if status == "offline" and online:
            continue
        if status == "alert" and not has_alert:
            continue
        if keyword and keyword.lower() not in dev_id.lower() and keyword not in plate:
            continue

        vehicles.append(vehicle)

    total = len(vehicles)
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "vehicles": vehicles[start:end],
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/{device_id}/detail")
async def get_vehicle_detail(
    device_id: str,
    user: dict = Depends(get_current_user),
):
    """获取单辆车详情"""
    try:
        status_data = await redis_service.get_device_status(device_id)
    except Exception:
        status_data = {}

    route_idx = int(device_id.split("-")[1]) % len(VEHICLE_ROUTES) if device_id.startswith("VEH-") else 0
    route = VEHICLE_ROUTES[route_idx]

    return {
        "device_id": device_id,
        "plate_number": f"冷A-{device_id.split('-')[1] if '-' in device_id else '0000'}",
        "device_type": "vehicle",
        "online": bool(status_data),
        "temperature": float(status_data.get("temperature", 0)) if status_data else round(random.uniform(-22, 6), 1),
        "humidity": float(status_data.get("humidity", 0)) if status_data else round(random.uniform(50, 80), 1),
        "latitude": float(status_data.get("latitude", 0)) if status_data else round(random.uniform(22, 40), 4),
        "longitude": float(status_data.get("longitude", 0)) if status_data else round(random.uniform(104, 122), 4),
        "vehicle_speed": float(status_data.get("vehicle_speed", 0)) if status_data else round(random.uniform(0, 100), 1),
        "door_status": int(status_data.get("door_status", 0)) if status_data else 0,
        "vibration": float(status_data.get("vibration", 0)) if status_data else round(random.uniform(0, 2), 2),
        "cold_car_status": int(status_data.get("cold_car_status", 1)) if status_data else 1,
        "battery_level": float(status_data.get("battery_level", 0)) if status_data else round(random.uniform(60, 100), 1),
        "signal_strength": int(status_data.get("signal_strength", 0)) if status_data else random.randint(3, 5),
        "waybill_no": f"WB-{datetime.now().strftime('%Y%m%d')}-{device_id.split('-')[1] if '-' in device_id else '0000'}",
        "cargo_type": random.choice(["冷冻肉类", "冷冻海鲜", "冷藏乳制品", "冷藏水果", "疫苗", "生物试剂"]),
        "route": route,
        "current_city": route[random.randint(0, len(route) - 1)],
        "target_temperature": float(status_data.get("target_temperature", 0)) if status_data else -18.0,
        "external_temp": float(status_data.get("external_temp", 0)) if status_data else round(random.uniform(20, 35), 1),
        "last_update": status_data.get("last_update", datetime.utcnow().isoformat()) if status_data else datetime.utcnow().isoformat(),
    }


@router.get("/{device_id}/trajectory")
async def get_vehicle_trajectory(
    device_id: str,
    user: dict = Depends(get_current_user),
    hours: int = Query(2, ge=1, le=24, description="回溯时长(小时)"),
):
    """获取车辆历史轨迹（最近N小时）"""
    # 模拟轨迹点
    now = datetime.utcnow()
    points = []

    route_idx = int(device_id.split("-")[1]) % len(VEHICLE_ROUTES) if device_id.startswith("VEH-") else 0
    route = VEHICLE_ROUTES[route_idx]
    step_count = min(hours * 30, 720)  # 每2分钟一个点

    for i in range(step_count, 0, -1):
        t = now - timedelta(minutes=i * 2)
        # 沿路线模拟坐标
        city_idx = (step_count - i) * len(route) // step_count
        city_idx = min(city_idx, len(route) - 1)
        next_city_idx = min(city_idx + 1, len(route) - 1)
        progress = ((step_count - i) * len(route) / step_count) - city_idx
        progress = max(0, min(1, progress))

        from_coord = CITY_COORDS.get(route[city_idx], (39.9, 116.4))
        to_coord = CITY_COORDS.get(route[next_city_idx], (30.5, 104.0))

        lat = from_coord[0] + (to_coord[0] - from_coord[0]) * progress + random.uniform(-0.1, 0.1)
        lng = from_coord[1] + (to_coord[1] - from_coord[1]) * progress + random.uniform(-0.1, 0.1)

        temp = round(random.uniform(-22, -16), 1) if random.random() > 0.05 else round(random.uniform(-10, 0), 1)

        points.append({
            "time": t.isoformat(),
            "latitude": round(lat, 4),
            "longitude": round(lng, 4),
            "temperature": temp,
            "humidity": round(random.uniform(55, 75), 1),
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
async def get_all_vehicle_positions(
    user: dict = Depends(get_current_user),
):
    """获取所有在线车辆的实时位置（地图标记用）"""
    try:
        online_devices = await redis_service.get_online_devices()
    except Exception:
        online_devices = set()

    if not online_devices:
        # 生成模拟数据
        online_devices = {f"VEH-{i:04d}" for i in range(1, 51)}

    positions = []
    for device_id in online_devices:
        if not device_id.startswith("VEH"):
            continue
        try:
            status_data = await redis_service.get_device_status(device_id) or {}
        except Exception:
            status_data = {}

        route_idx = int(device_id.split("-")[1]) % len(VEHICLE_ROUTES) if "-" in device_id else 0
        route = VEHICLE_ROUTES[route_idx]

        # 优先使用 Redis 中的坐标，否则回退到模拟城市坐标
        has_redis_coords = status_data.get("latitude") and status_data.get("longitude")
        if has_redis_coords:
            lat = float(status_data.get("latitude", 0))
            lng = float(status_data.get("longitude", 0))
            city = _find_nearest_city(lat, lng)
        else:
            city = route[random.randint(0, len(route) - 1)]
            coord = CITY_COORDS.get(city, (39.9, 116.4))
            lat = coord[0] + random.uniform(-0.3, 0.3)
            lng = coord[1] + random.uniform(-0.3, 0.3)

        temp = float(status_data.get("temperature", 0)) if status_data.get("temperature") else round(random.uniform(-22, 6), 1)
        has_alert = random.random() < 0.1

        positions.append({
            "device_id": device_id,
            "plate_number": f"冷A-{device_id.split('-')[1] if '-' in device_id else '0000'}",
            "latitude": round(lat, 4),
            "longitude": round(lng, 4),
            "temperature": temp,
            "vehicle_speed": float(status_data.get("vehicle_speed", 0)) if status_data.get("vehicle_speed") else round(random.uniform(0, 100), 1),
            "cold_car_status": int(status_data.get("cold_car_status", 1)) if status_data.get("cold_car_status") else 1,
            "online": True,
            "has_alert": has_alert,
            "cargo_type": random.choice(["冷冻肉类", "冷冻海鲜", "冷藏乳制品", "冷藏水果", "疫苗"]),
            "current_city": city,
            "last_update": datetime.utcnow().isoformat(),
        })

    return {
        "count": len(positions),
        "vehicles": positions,
        "timestamp": datetime.utcnow().isoformat(),
    }
