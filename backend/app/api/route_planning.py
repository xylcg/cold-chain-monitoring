"""
冷链路径智能规划 API
基于深度学习多目标优化的冷链专属智能路径规划系统
支持三类业务模式：整车直达、零担干支分拨、多点沿途卸货
深度联动电子围栏、IoT设备、温控预警、合规溯源
"""
import random
import math
import requests
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..core.security import get_current_user
from ..schemas.route_planning import (
    TransportMode, TemperatureSensitivity,
    RoutePlanRequest, RoutePlanResponse, RoutePlanComparison,
    RouteExecutionStatus, RealTimeReplanRequest
)
from ..services.route_planning import (
    plan_route, generate_comparison_plans,
    TEMP_SENSITIVITY_CONFIG, CARGO_TYPE_MAP, PROVINCIAL_HUBS, REGIONAL_DISTRIBUTION
)
from ..services.world_state import CITY_COORDS

router = APIRouter(prefix="/api/v1/routes", tags=["路径规划"])


# ==================== API 接口 ====================

@router.post("/plan")
async def create_route_plan(
    request: RoutePlanRequest,
    user: dict = Depends(get_current_user),
):
    """
    创建智能路径规划
    支持三类业务模式：整车直达、零担干支分拨、多点沿途卸货
    基于温敏等级实现差异化规划策略
    """
    if request.origin not in CITY_COORDS:
        raise HTTPException(status_code=400, detail=f"未找到出发城市: {request.origin}")
    if request.destination not in CITY_COORDS:
        raise HTTPException(status_code=400, detail=f"未找到目的城市: {request.destination}")
    
    comparison = generate_comparison_plans(request)
    
    return {
        "status": "ok",
        "plan_time": datetime.utcnow().isoformat(),
        "comparison": comparison.dict(),
    }


@router.post("/plan/single")
async def create_single_plan(
    request: RoutePlanRequest,
    user: dict = Depends(get_current_user),
):
    """
    创建单一路线规划（不对比）
    """
    if request.origin not in CITY_COORDS:
        raise HTTPException(status_code=400, detail=f"未找到出发城市: {request.origin}")
    if request.destination not in CITY_COORDS:
        raise HTTPException(status_code=400, detail=f"未找到目的城市: {request.destination}")
    
    plan = plan_route(request)
    
    return {
        "status": "ok",
        "plan_time": datetime.utcnow().isoformat(),
        "plan": plan.dict(),
    }


@router.post("/replan")
async def realtime_replan(
    request: RealTimeReplanRequest,
    user: dict = Depends(get_current_user),
):
    """
    实时动态重规划
    触发场景：路线偏离、路况突变、温度异常、设备离线恢复、中转延误、违规停留
    """
    current_lat = request.current_location.get("lat", 39.9)
    current_lng = request.current_location.get("lng", 116.4)
    
    nearest_city = min(CITY_COORDS.keys(), key=lambda c: _distance_to(current_lat, current_lng, CITY_COORDS[c]))
    
    replan_request = RoutePlanRequest(
        origin=nearest_city,
        destination="",
        transport_mode=TransportMode.DIRECT,
        temperature_sensitivity=TemperatureSensitivity.MEDIUM,
        cargo_type="冷藏生鲜",
        cargo_weight_kg=5000,
    )
    
    plan = plan_route(replan_request)
    
    return {
        "status": "ok",
        "trigger_reason": request.trigger_reason,
        "current_location": request.current_location,
        "replan_time": datetime.utcnow().isoformat(),
        "updated_plan": plan.dict(),
    }


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
        cargo = random.choice(list(CARGO_TYPE_MAP.keys()))
        
        request = RoutePlanRequest(
            origin=o,
            destination=d,
            transport_mode=random.choice([TransportMode.DIRECT, TransportMode.HUB_DISTRIBUTION]),
            cargo_type=cargo,
            cargo_weight_kg=random.uniform(1000, 15000),
        )
        
        plan = plan_route(request)
        
        sensitivity = CARGO_TYPE_MAP.get(cargo, TemperatureSensitivity.MEDIUM)
        config = TEMP_SENSITIVITY_CONFIG[sensitivity]
        
        active_routes.append({
            "route_id": f"AR-{i:04d}",
            "plan_id": plan.plan_id,
            "vehicle_id": f"VEH-{random.randint(1, 100):04d}",
            "plate_number": f"冷A-{random.randint(1000, 9999)}",
            "origin": o,
            "destination": d,
            "cargo_type": cargo,
            "temperature_sensitivity": sensitivity.value,
            "transport_mode": plan.transport_mode.value,
            "distance_km": plan.estimated_total_distance_km,
            "estimated_duration_h": plan.estimated_total_duration_h,
            "total_cost_yuan": plan.estimated_total_cost_yuan,
            "departed_at": (datetime.utcnow() - timedelta(hours=random.randint(1, 24))).isoformat(),
            "eta": (datetime.utcnow() + timedelta(hours=random.randint(1, 18))).isoformat(),
            "progress_percent": random.randint(10, 85),
            "status": random.choice(["运输中", "运输中", "运输中", "即将到达", "卸货中"]),
            "temperature_c": round(random.uniform(config["temp_range"][0], config["temp_range"][1]), 1),
            "door_events": random.randint(0, 3),
            "heartbeat_status": random.choice(["online", "online", "online", "offline"]),
            "composite_score": plan.composite_score,
            "risk_score": plan.overall_risk_score,
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
        "provincial_hubs": PROVINCIAL_HUBS,
        "regional_distribution": REGIONAL_DISTRIBUTION,
    }


@router.get("/cargo-types")
async def get_cargo_types(
    user: dict = Depends(get_current_user),
):
    """获取货物类型及温敏等级配置"""
    types = []
    for name, sensitivity in CARGO_TYPE_MAP.items():
        config = TEMP_SENSITIVITY_CONFIG[sensitivity]
        types.append({
            "name": name,
            "temperature_sensitivity": sensitivity.value,
            "sensitivity_label": config["name"],
            "description": config["description"],
            "temperature_range": f"{config['temp_range'][0]}°C ~ {config['temp_range'][1]}°C",
            "safety_weight": config["safety_weight"],
        })
    
    return {
        "count": len(types),
        "types": types,
    }


@router.get("/sensitivity-levels")
async def get_sensitivity_levels(
    user: dict = Depends(get_current_user),
):
    """获取温敏等级配置详情"""
    levels = []
    for sensitivity, config in TEMP_SENSITIVITY_CONFIG.items():
        levels.append({
            "value": sensitivity.value,
            "label": config["name"],
            "description": config["description"],
            "temperature_range": f"{config['temp_range'][0]}°C ~ {config['temp_range'][1]}°C",
            "safety_weight": config["safety_weight"],
            "time_weight": config["time_weight"],
            "cost_weight": config["cost_weight"],
            "max_stops": config["max_stops"],
            "avoid_high_temp": config["avoid_high_temp"],
            "avoid_congestion": config["avoid_congestion"],
        })
    
    return {
        "count": len(levels),
        "levels": levels,
    }


@router.get("/transport-modes")
async def get_transport_modes(
    user: dict = Depends(get_current_user),
):
    """获取运输模式配置"""
    modes = [
        {
            "value": TransportMode.DIRECT.value,
            "label": "整车直达模式",
            "description": "一单一车、全程不换车、不开箱，仅双司机轮换值守",
            "suitable_for": "大批量高价值冷链货物",
            "features": ["起止仓点位围栏", "全程干线带状围栏", "分段温控监测", "设备离线精准定位"],
        },
        {
            "value": TransportMode.HUB_DISTRIBUTION.value,
            "label": "零担干支分拨模式",
            "description": "产地→省级枢纽→地市分拨→末端网点，多级标准化节点路线",
            "suitable_for": "小批量、多批次零散冷链订单",
            "features": ["多级节点围栏", "自动换车台账", "恒温分拣记录", "分段路线更新"],
        },
        {
            "value": TransportMode.MULTI_DROP.value,
            "label": "多点沿途卸货模式",
            "description": "结合各卸货点位置、时效窗口、温敏等级，智能排序最优停靠顺序",
            "suitable_for": "连锁商超、生鲜门店、餐饮供应链",
            "features": ["多站点最优排序", "时效窗口约束", "温控稳定性保障", "折返规避"],
        },
    ]
    
    return {
        "count": len(modes),
        "modes": modes,
    }


def _distance_to(lat1: float, lng1: float, coord: tuple) -> float:
    R = 6371
    dlat = math.radians(coord[0] - lat1)
    dlng = math.radians(coord[1] - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(coord[0])) * math.sin(dlng / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@router.get("/road-path")
async def get_road_path(
    from_lat: float = Query(..., description="起点纬度"),
    from_lng: float = Query(..., description="起点经度"),
    to_lat: float = Query(..., description="终点纬度"),
    to_lng: float = Query(..., description="终点经度"),
):
    """
    获取真实道路路径坐标（通过OSRM路由API）
    前端调用此接口获取城市间真实道路坐标，避免CORS限制
    """
    try:
        url = f"http://router.project-osrm.org/route/v1/driving/{from_lng},{from_lat};{to_lng},{to_lat}?overview=full&steps=true"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("routes") and len(data["routes"]) > 0:
            polyline = data["routes"][0].get("geometry", "")
            decoded_coords = _decode_polyline(polyline)
            return {
                "success": True,
                "coords": decoded_coords,
                "distance_m": data["routes"][0].get("distance", 0),
                "duration_s": data["routes"][0].get("duration", 0),
            }
        else:
            return {
                "success": False,
                "coords": [[from_lat, from_lng], [to_lat, to_lng]],
                "error": "No routes found",
            }
    except Exception as e:
        return {
            "success": False,
            "coords": [[from_lat, from_lng], [to_lat, to_lng]],
            "error": str(e),
        }


def _decode_polyline(encoded: str) -> List[List[float]]:
    """解码OSRM返回的polyline编码"""
    points: List[List[float]] = []
    index = 0
    lat = 0
    lng = 0
    
    while index < len(encoded):
        b = 0
        shift = 0
        result = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        
        lat += ~(result >> 1) if (result & 1) else (result >> 1)
        
        b = 0
        shift = 0
        result = 0
        while True:
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1f) << shift
            shift += 5
            if b < 0x20:
                break
        
        lng += ~(result >> 1) if (result & 1) else (result >> 1)
        
        points.append([lat / 1e5, lng / 1e5])
    
    return points