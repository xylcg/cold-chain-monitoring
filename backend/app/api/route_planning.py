"""
冷链路径智能规划 API
模块5: 冷链路径智能规划
- 多目标优化路径规划（时效 + 能耗 + 成本）
- 温敏等级货物路径优先级
- 路径规划方案对比
"""
import random
import math
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..core.security import get_current_user

router = APIRouter(prefix="/api/v1/routes", tags=["路径规划"])

# ==================== 数据模型 ====================

class RoutePlanRequest(BaseModel):
    origin: str
    destination: str
    cargo_type: str = "冷藏生鲜"  # 冷冻食品/冷藏生鲜/疫苗医药/生物试剂
    cargo_weight_kg: float = 5000
    priority: str = "normal"  # high/normal/economic
    avoid_congestion: bool = True

class RoutePoint(BaseModel):
    name: str
    lat: float
    lng: float
    stop_duration_min: int = 0

# ==================== 城市坐标 ====================

CITY_COORDS = {
    "北京": (39.9042, 116.4074), "天津": (39.0842, 117.2009),
    "石家庄": (38.0428, 114.5149), "太原": (37.8706, 112.5489),
    "呼和浩特": (40.8424, 111.7490), "沈阳": (41.8057, 123.4315),
    "大连": (38.9140, 121.6147), "长春": (43.8171, 125.3235),
    "哈尔滨": (45.8038, 126.5350), "上海": (31.2304, 121.4737),
    "南京": (32.0603, 118.7969), "杭州": (30.2741, 120.1551),
    "合肥": (31.8206, 117.2272), "福州": (26.0745, 119.2965),
    "厦门": (24.4798, 118.0894), "南昌": (28.6820, 115.8579),
    "济南": (36.6512, 117.1201), "青岛": (36.0671, 120.3826),
    "郑州": (34.7466, 113.6253), "武汉": (30.5928, 114.3055),
    "长沙": (28.2282, 112.9388), "广州": (23.1291, 113.2644),
    "深圳": (22.5431, 114.0579), "南宁": (22.8167, 108.3669),
    "海口": (20.0442, 110.1999), "三亚": (18.2528, 109.5120),
    "成都": (30.5728, 104.0668), "重庆": (29.4316, 106.9123),
    "贵阳": (26.6470, 106.6302), "昆明": (25.0389, 102.7183),
    "拉萨": (29.6500, 91.1000), "西安": (34.3416, 108.9398),
    "兰州": (36.0611, 103.8343), "西宁": (36.6171, 101.7782),
    "银川": (38.4872, 106.2309), "乌鲁木齐": (43.8256, 87.6168),
}

CARGO_TEMP_REQUIREMENTS = {
    "冷冻食品": {"min_temp": -22, "max_temp": -15, "priority_weight": 1.0},
    "冷藏生鲜": {"min_temp": 0, "max_temp": 4, "priority_weight": 1.2},
    "疫苗医药": {"min_temp": 2, "max_temp": 8, "priority_weight": 2.0},
    "生物试剂": {"min_temp": -80, "max_temp": -60, "priority_weight": 2.5},
    "恒温药品": {"min_temp": 15, "max_temp": 25, "priority_weight": 1.3},
    "鲜花": {"min_temp": 2, "max_temp": 8, "priority_weight": 1.1},
    "巧克力": {"min_temp": 15, "max_temp": 22, "priority_weight": 1.0},
}


def haversine(lat1, lng1, lat2, lng2):
    """计算两点间距离(km)"""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _plan_routes(origin: str, destination: str, cargo_type: str, priority: str) -> dict:
    """多目标路径规划（模拟A* + 遗传算法混合）"""
    random.seed(hash(f"{origin}{destination}{cargo_type}{priority}") % 10000)

    o_coord = CITY_COORDS.get(origin, (39.9, 116.4))
    d_coord = CITY_COORDS.get(destination, (31.2, 121.5))
    direct_distance = haversine(o_coord[0], o_coord[1], d_coord[0], d_coord[1])

    cargo_req = CARGO_TEMP_REQUIREMENTS.get(cargo_type, CARGO_TEMP_REQUIREMENTS["冷藏生鲜"])

    # 生成3条备选路线
    routes = []
    route_names = ["高速优先", "最短路径", "经济路线"]

    for idx, name in enumerate(route_names):
        random.seed(hash(f"{origin}{destination}{name}") % 10000)

        if idx == 0:  # 高速优先 — 最快但成本高
            distance = direct_distance * random.uniform(1.05, 1.15)
            duration = distance / 80 + random.uniform(0.3, 1)
            toll_cost = distance * random.uniform(0.5, 0.8)
            energy_per_km = random.uniform(0.28, 0.35)
            congestion_level = "低"
        elif idx == 1:  # 最短路径
            distance = direct_distance * random.uniform(1.0, 1.08)
            duration = distance / 60 + random.uniform(0.5, 1.5)
            toll_cost = distance * random.uniform(0.3, 0.6)
            energy_per_km = random.uniform(0.30, 0.38)
            congestion_level = random.choice(["中", "低"])
        else:  # 经济路线
            distance = direct_distance * random.uniform(1.10, 1.25)
            duration = distance / 55 + random.uniform(1, 2)
            toll_cost = distance * random.uniform(0.1, 0.3)
            energy_per_km = random.uniform(0.25, 0.32)
            congestion_level = random.choice(["高", "中"])

        # 制冷能耗成本（温度越低、途中越久 → 能耗越高）
        avg_temp = (cargo_req["min_temp"] + cargo_req["max_temp"]) / 2
        cooling_load = abs(avg_temp - 25) * 0.02  # 外部25°C
        energy_cost = distance * energy_per_km * (1 + cooling_load)
        fuel_cost = energy_cost * random.uniform(6.5, 8.0)  # 柴油/电费 ¥/kWh

        # 碳排放计算（柴油: 0.00268吨CO2/kWh, 电动: 0.0005吨CO2/kWh由电网排放）
        diesel_co2_factor = 0.00268  # 吨CO2/kWh
        carbon_emission = distance * 0.78 * diesel_co2_factor + energy_cost * 0.3 * diesel_co2_factor

        # 温度偏离影响（冷链品质损失）
        temp_deviation = abs(avg_temp - 4.0)  # 理想冷链4°C
        quality_loss_rate = temp_deviation * 0.015 * (duration / 24)

        # 多目标评分
        time_score = 100 - (duration / max(direct_distance / 50, 1)) * 40  # 时效
        cost_score = 100 - fuel_cost * 0.05  # 成本
        quality_score = 100 - cooling_load * 50 - quality_loss_rate * 30  # 品质保障
        eco_score = 100 - carbon_emission * 50  # 环保评分

        # 温敏货物加权
        priority_weight = cargo_req["priority_weight"]
        composite_score = (
            time_score * (0.35 * priority_weight) +
            cost_score * (0.25 / priority_weight) +
            quality_score * (0.25 * priority_weight) +
            eco_score * (0.15 / priority_weight)
        )

        # 途经城市
        city_list = list(CITY_COORDS.keys())
        city_list.remove(origin)
        city_list.remove(destination)
        waypoints = random.sample(city_list, min(2, len(city_list)))
        waypoint_coords = [{"name": w, "lat": CITY_COORDS[w][0], "lng": CITY_COORDS[w][1]} for w in waypoints]

        routes.append({
            "route_id": f"R-{idx+1}",
            "route_name": name,
            "strategy": name,
            "origin": {"name": origin, "lat": o_coord[0], "lng": o_coord[1]},
            "destination": {"name": destination, "lat": d_coord[0], "lng": d_coord[1]},
            "waypoints": waypoint_coords,
            "distance_km": round(distance, 1),
            "estimated_duration_h": round(duration, 1),
            "toll_cost_yuan": round(toll_cost, 0),
            "fuel_cost_yuan": round(fuel_cost, 0),
            "total_cost_yuan": round(toll_cost + fuel_cost, 0),
            "energy_consumption_kwh": round(energy_cost, 1),
            "congestion_level": congestion_level,
            "composite_score": round(composite_score, 1),
            "carbon_emission_kg": round(carbon_emission * 1000, 1),
            "quality_loss_percent": round(quality_loss_rate * 100, 2),
            "scores": {
                "时效评分": round(time_score, 1),
                "成本评分": round(cost_score, 1),
                "品质保障评分": round(quality_score, 1),
                "环保评分": round(eco_score, 1),
            },
        })

    # 推荐最优路线
    routes.sort(key=lambda x: -x["composite_score"])
    routes[0]["recommended"] = True

    return {
        "cargo_type": cargo_type,
        "cargo_requirements": cargo_req,
        "priority": priority,
        "direct_distance_km": round(direct_distance, 1),
        "routes": routes,
        "recommended_route_id": routes[0]["route_id"],
    }


# ==================== API 接口 ====================

@router.post("/plan")
async def plan_route(
    request: RoutePlanRequest,
    user: dict = Depends(get_current_user),
):
    """规划冷链配送路线"""
    if request.origin not in CITY_COORDS:
        raise HTTPException(status_code=400, detail=f"未找到出发城市: {request.origin}")
    if request.destination not in CITY_COORDS:
        raise HTTPException(status_code=400, detail=f"未找到目的城市: {request.destination}")

    result = _plan_routes(request.origin, request.destination, request.cargo_type, request.priority)
    result["plan_request"] = request.model_dump()
    result["plan_time"] = datetime.utcnow().isoformat()
    return result


@router.get("/plan")
async def quick_plan(
    origin: str,
    destination: str,
    cargo_type: str = "冷藏生鲜",
    priority: str = "normal",
    user: dict = Depends(get_current_user),
):
    """快速路径规划（GET方式）"""
    if origin not in CITY_COORDS:
        raise HTTPException(status_code=400, detail=f"未找到出发城市: {origin}")
    if destination not in CITY_COORDS:
        raise HTTPException(status_code=400, detail=f"未找到目的城市: {destination}")

    result = _plan_routes(origin, destination, cargo_type, priority)
    result["plan_time"] = datetime.utcnow().isoformat()
    return result


@router.get("/active")
async def get_active_routes(
    user: dict = Depends(get_current_user),
):
    """获取当前活跃的配送路线"""
    random.seed(int(datetime.utcnow().timestamp()) // 100)

    city_list = list(CITY_COORDS.keys())
    active_routes = []

    for i in range(1, 9):
        o = random.choice(city_list)
        d = random.choice([c for c in city_list if c != o])
        cargo = random.choice(list(CARGO_TEMP_REQUIREMENTS.keys()))
        plan = _plan_routes(o, d, cargo, "normal")

        active_routes.append({
            "route_id": f"AR-{i:04d}",
            "vehicle_id": f"VEH-{random.randint(1, 100):04d}",
            "plate_number": f"冷A-{random.randint(1000, 9999)}",
            "origin": o,
            "destination": d,
            "cargo_type": cargo,
            "distance_km": plan["routes"][0]["distance_km"],
            "departed_at": (datetime.utcnow() - timedelta(hours=random.randint(1, 24))).isoformat(),
            "eta": (datetime.utcnow() + timedelta(hours=random.randint(1, 18))).isoformat(),
            "progress_percent": random.randint(10, 85),
            "status": random.choice(["运输中", "运输中", "运输中", "即将到达", "卸货中"]),
            "temperature_c": round(random.uniform(
                CARGO_TEMP_REQUIREMENTS[cargo]["min_temp"],
                CARGO_TEMP_REQUIREMENTS[cargo]["max_temp"]
            ), 1),
            "door_events": random.randint(0, 3),
        })

    return {"count": len(active_routes), "routes": active_routes}


@router.get("/cities")
async def get_city_list(
    user: dict = Depends(get_current_user),
):
    """获取支持的城市列表"""
    return {
        "count": len(CITY_COORDS),
        "cities": [{"name": k, "lat": v[0], "lng": v[1]} for k, v in CITY_COORDS.items()],
    }


@router.get("/cargo-types")
async def get_cargo_types(
    user: dict = Depends(get_current_user),
):
    """获取货物类型及温控要求"""
    return {
        "count": len(CARGO_TEMP_REQUIREMENTS),
        "types": [
            {"name": k, "range": f"{v['min_temp']}°C ~ {v['max_temp']}°C", "priority_weight": v["priority_weight"]}
            for k, v in CARGO_TEMP_REQUIREMENTS.items()
        ],
    }
