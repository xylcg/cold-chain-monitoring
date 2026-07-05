import random
import math
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from ..schemas.route_planning import (
    TransportMode, TemperatureSensitivity, NodeLevel,
    RouteNode, RouteSegment, RoutePlanRequest, RoutePlanResponse,
    RoutePlanComparison, RouteExecutionStatus
)
from ..schemas.geofence import FenceCreate, FenceType, FenceCategory, AlertLevel
from ..services.fence_store import create_fence
from ..services.world_state import CITY_COORDS

TEMP_SENSITIVITY_CONFIG = {
    TemperatureSensitivity.HIGH: {
        "name": "高敏物资",
        "description": "疫苗、生物制剂、医用试剂",
        "temp_range": (-20, 10),
        "priority_strategy": "时效优先",
        "strategy_desc": "最短时效策略：配送时效设为最高优先级，优先筛选行驶里程最短、通行效率最高、中转节点最少的运输路线",
        "safety_weight": 0.10,
        "time_weight": 0.55,
        "cost_weight": 0.05,
        "distance_weight": 0.05,
        "temp_weight": 0.25,
        "max_stops": 1,
        "avoid_high_temp": True,
        "avoid_congestion": True,
        "avoid_remote": True,
        "max_delay_h": 1.0,
    },
    TemperatureSensitivity.MEDIUM: {
        "name": "中敏物资",
        "description": "鲜肉、海鲜、高端鲜果",
        "temp_range": (-15, 8),
        "priority_strategy": "温控优先",
        "strategy_desc": "温控优先时效均衡策略：以环境温度适配为核心规划依据，动态规避日间高温城区与闷热拥堵路段，优先选择夜间通行、高速通风路线",
        "safety_weight": 0.20,
        "time_weight": 0.20,
        "cost_weight": 0.15,
        "distance_weight": 0.10,
        "temp_weight": 0.35,
        "max_stops": 3,
        "avoid_high_temp": True,
        "avoid_congestion": True,
        "avoid_remote": False,
        "max_delay_h": 2.0,
    },
    TemperatureSensitivity.LOW: {
        "name": "低敏物资",
        "description": "冷冻肉类、速冻食品",
        "temp_range": (-25, -10),
        "priority_strategy": "成本最优",
        "strategy_desc": "成本最优全局均衡策略：在满足基础冷链温控标准的前提下，重点倾斜油价能耗与通行成本优化，合并同方向配送订单提升满载率",
        "safety_weight": 0.15,
        "time_weight": 0.15,
        "cost_weight": 0.40,
        "distance_weight": 0.15,
        "temp_weight": 0.15,
        "max_stops": 5,
        "avoid_high_temp": False,
        "avoid_congestion": False,
        "avoid_remote": False,
        "max_delay_h": 4.0,
    },
}

CARGO_TYPE_MAP = {
    "疫苗医药": TemperatureSensitivity.HIGH,
    "生物试剂": TemperatureSensitivity.HIGH,
    "医用试剂": TemperatureSensitivity.HIGH,
    "冷藏生鲜": TemperatureSensitivity.MEDIUM,
    "鲜肉": TemperatureSensitivity.MEDIUM,
    "海鲜": TemperatureSensitivity.MEDIUM,
    "高端鲜果": TemperatureSensitivity.MEDIUM,
    "冷冻食品": TemperatureSensitivity.LOW,
    "冷冻肉类": TemperatureSensitivity.LOW,
    "速冻食品": TemperatureSensitivity.LOW,
    "巧克力": TemperatureSensitivity.MEDIUM,
    "鲜花": TemperatureSensitivity.MEDIUM,
    "恒温药品": TemperatureSensitivity.HIGH,
}

PROVINCIAL_HUBS = ["北京", "上海", "广州", "成都", "武汉", "西安", "沈阳", "南京", "杭州", "重庆"]
REGIONAL_DISTRIBUTION = ["天津", "石家庄", "郑州", "长沙", "深圳", "济南", "合肥", "福州", "昆明", "兰州"]


def haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    straight_distance = R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    road_factor = 1.3
    return round(straight_distance * road_factor, 1)


def simulate_cnn_lstm_prediction(from_city: str, to_city: str, hour_of_day: int, sensitivity: TemperatureSensitivity) -> Dict[str, float]:
    seed = hash(f"{from_city}{to_city}{hour_of_day}{sensitivity.value}")
    random.seed(seed % 10000)
    
    base_congestion = 0.2 + (hour_of_day >= 7 and hour_of_day <= 9) * 0.4 + (hour_of_day >= 17 and hour_of_day <= 19) * 0.35
    
    base_temp = 15 + random.uniform(-5, 10)
    if from_city in ["广州", "深圳", "南宁", "海口", "三亚"]:
        base_temp += 5
    if from_city in ["哈尔滨", "长春", "沈阳", "呼和浩特"]:
        base_temp -= 8
    
    heat_risk = 0.1
    if base_temp > 30:
        heat_risk = 0.6 + random.uniform(0, 0.3)
    elif base_temp > 25:
        heat_risk = 0.3 + random.uniform(0, 0.2)
    
    if sensitivity == TemperatureSensitivity.HIGH:
        heat_risk = min(1.0, heat_risk * 1.5)
    
    return {
        "congestion_probability": round(min(1.0, base_congestion + random.uniform(-0.1, 0.2)), 3),
        "heat_risk_probability": round(heat_risk, 3),
        "predicted_avg_temp": round(base_temp, 1),
        "predicted_delay_h": round(random.uniform(0, base_congestion * 2), 1),
        "energy_consumption_factor": round(1.0 + heat_risk * 0.3 + base_congestion * 0.2, 3),
    }


def generate_route_nodes(origin: str, destination: str, mode: TransportMode, sensitivity: TemperatureSensitivity, multi_drop_points: List[Dict[str, Any]] = None) -> List[RouteNode]:
    nodes = []
    node_idx = 0
    
    o_coord = CITY_COORDS.get(origin, (39.9, 116.4))
    d_coord = CITY_COORDS.get(destination, (31.2, 121.5))
    
    config = TEMP_SENSITIVITY_CONFIG[sensitivity]
    
    HIGH_TEMP_CITIES = ["广州", "深圳", "南宁", "海口", "三亚", "福州", "厦门"]
    HIGH_CONGESTION_CITIES = ["北京", "上海", "广州", "深圳", "成都", "重庆"]
    HIGHWAY_CITIES = ["石家庄", "郑州", "武汉", "合肥", "南京", "济南", "西安"]
    
    if mode == TransportMode.DIRECT:
        nodes.append(RouteNode(
            node_id=f"NODE-{node_idx:03d}",
            name=f"{origin}起点仓",
            city=origin,
            level=NodeLevel.END_NODE,
            lat=o_coord[0],
            lng=o_coord[1],
            type="warehouse",
            stop_duration_min=30,
        ))
        node_idx += 1
        
        nodes.append(RouteNode(
            node_id=f"NODE-{node_idx:03d}",
            name=f"{destination}终点仓",
            city=destination,
            level=NodeLevel.END_NODE,
            lat=d_coord[0],
            lng=d_coord[1],
            type="warehouse",
            stop_duration_min=30,
        ))
        node_idx += 1
        
    elif mode == TransportMode.HUB_DISTRIBUTION:
        mid_lat = (o_coord[0] + d_coord[0]) / 2
        mid_lng = (o_coord[1] + d_coord[1]) / 2
        
        hub_candidates = [h for h in PROVINCIAL_HUBS if h != origin and h != destination]
        
        if sensitivity == TemperatureSensitivity.HIGH:
            hub_candidates = [h for h in hub_candidates if h not in HIGH_TEMP_CITIES]
            if not hub_candidates:
                hub_candidates = PROVINCIAL_HUBS[:]
            hub_candidates.sort(key=lambda h: haversine(o_coord[0], o_coord[1], CITY_COORDS.get(h, (0, 0))[0], CITY_COORDS.get(h, (0, 0))[1]))
        elif sensitivity == TemperatureSensitivity.LOW:
            hub_candidates = [h for h in hub_candidates if h not in HIGH_CONGESTION_CITIES]
            hub_candidates.sort(key=lambda h: haversine(mid_lat, mid_lng, CITY_COORDS.get(h, (0, 0))[0], CITY_COORDS.get(h, (0, 0))[1]))
        else:
            hub_candidates.sort(key=lambda h: haversine(mid_lat, mid_lng, CITY_COORDS.get(h, (0, 0))[0], CITY_COORDS.get(h, (0, 0))[1]))
        
        hub = hub_candidates[0] if hub_candidates else "武汉"
        hub_coord = CITY_COORDS.get(hub, (30.6, 114.3))
        
        dist_candidates = [d for d in REGIONAL_DISTRIBUTION if d != origin and d != destination and d != hub]
        
        if sensitivity == TemperatureSensitivity.HIGH:
            dist_candidates = [d for d in dist_candidates if d not in HIGH_TEMP_CITIES]
            dist_candidates.sort(key=lambda d: haversine(hub_coord[0], hub_coord[1], CITY_COORDS.get(d, (0, 0))[0], CITY_COORDS.get(d, (0, 0))[1]))
        elif sensitivity == TemperatureSensitivity.LOW:
            dist_candidates.sort(key=lambda d: haversine(hub_coord[0], hub_coord[1], CITY_COORDS.get(d, (0, 0))[0], CITY_COORDS.get(d, (0, 0))[1]))
        else:
            dist_candidates.sort(key=lambda d: haversine(hub_coord[0], hub_coord[1], CITY_COORDS.get(d, (0, 0))[0], CITY_COORDS.get(d, (0, 0))[1]))
        
        dist_city = dist_candidates[0] if dist_candidates else destination
        dist_coord = CITY_COORDS.get(dist_city, d_coord)
        
        nodes.append(RouteNode(
            node_id=f"NODE-{node_idx:03d}",
            name=f"{origin}产地预冷仓",
            city=origin,
            level=NodeLevel.END_NODE,
            lat=o_coord[0],
            lng=o_coord[1],
            type="warehouse",
            stop_duration_min=60,
        ))
        node_idx += 1
        
        nodes.append(RouteNode(
            node_id=f"NODE-{node_idx:03d}",
            name=f"{hub}省级枢纽分拨中心",
            city=hub,
            level=NodeLevel.HUB_PROVINCIAL,
            lat=hub_coord[0],
            lng=hub_coord[1],
            type="hub",
            stop_duration_min=180,
        ))
        node_idx += 1
        
        if dist_city != destination:
            nodes.append(RouteNode(
                node_id=f"NODE-{node_idx:03d}",
                name=f"{dist_city}地市二级分拨仓",
                city=dist_city,
                level=NodeLevel.DISTRIBUTION_CITY,
                lat=dist_coord[0],
                lng=dist_coord[1],
                type="distribution",
                stop_duration_min=60,
            ))
            node_idx += 1
        
        nodes.append(RouteNode(
            node_id=f"NODE-{node_idx:03d}",
            name=f"{destination}末端网点",
            city=destination,
            level=NodeLevel.END_NODE,
            lat=d_coord[0],
            lng=d_coord[1],
            type="warehouse",
            stop_duration_min=30,
        ))
        node_idx += 1
        
    elif mode == TransportMode.MULTI_DROP:
        nodes.append(RouteNode(
            node_id=f"NODE-{node_idx:03d}",
            name=f"{origin}配送中心",
            city=origin,
            level=NodeLevel.END_NODE,
            lat=o_coord[0],
            lng=o_coord[1],
            type="warehouse",
            stop_duration_min=45,
        ))
        node_idx += 1
        
        if multi_drop_points:
            for i, point in enumerate(multi_drop_points):
                drop_city = point.get("city", "")
                if not drop_city or drop_city not in CITY_COORDS:
                    continue
                drop_coord = CITY_COORDS.get(drop_city, (30.0, 115.0))
                point_name = point.get("name", f"{drop_city}门店{i+1}")
                stop_duration = point.get("stop_duration_min", 15)
                
                nodes.append(RouteNode(
                    node_id=f"NODE-{node_idx:03d}",
                    name=point_name,
                    city=drop_city,
                    level=NodeLevel.END_NODE,
                    lat=drop_coord[0],
                    lng=drop_coord[1],
                    type="store",
                    stop_duration_min=stop_duration,
                ))
                node_idx += 1
        else:
            drop_cities = []
            all_cities = [c for c in CITY_COORDS.keys() if c != origin and c != destination]
            
            if sensitivity == TemperatureSensitivity.HIGH:
                all_cities = [c for c in all_cities if c not in HIGH_TEMP_CITIES]
                all_cities.sort(key=lambda c: haversine(o_coord[0], o_coord[1], CITY_COORDS.get(c, (0, 0))[0], CITY_COORDS.get(c, (0, 0))[1]))
            elif sensitivity == TemperatureSensitivity.LOW:
                all_cities = [c for c in all_cities if c not in HIGH_CONGESTION_CITIES]
                all_cities.sort(key=lambda c: haversine(o_coord[0], o_coord[1], CITY_COORDS.get(c, (0, 0))[0], CITY_COORDS.get(c, (0, 0))[1]))
            else:
                all_cities = [c for c in all_cities if c not in HIGH_TEMP_CITIES]
                all_cities.sort(key=lambda c: haversine(o_coord[0], o_coord[1], CITY_COORDS.get(c, (0, 0))[0], CITY_COORDS.get(c, (0, 0))[1]))
            
            num_drops = min(config["max_stops"], len(all_cities))
            
            drop_cities = all_cities[:num_drops]
            
            for i, drop_city in enumerate(drop_cities):
                drop_coord = CITY_COORDS.get(drop_city, (30.0, 115.0))
                nodes.append(RouteNode(
                    node_id=f"NODE-{node_idx:03d}",
                    name=f"{drop_city}门店{i+1}",
                    city=drop_city,
                    level=NodeLevel.END_NODE,
                    lat=drop_coord[0],
                    lng=drop_coord[1],
                    type="store",
                    stop_duration_min=15,
                ))
                node_idx += 1
        
        nodes.append(RouteNode(
            node_id=f"NODE-{node_idx:03d}",
            name=f"{destination}终点门店",
            city=destination,
            level=NodeLevel.END_NODE,
            lat=d_coord[0],
            lng=d_coord[1],
            type="store",
            stop_duration_min=20,
        ))
        node_idx += 1
    
    return nodes


def create_segment_fences(segment: RouteSegment, sensitivity: TemperatureSensitivity) -> List[str]:
    fence_ids = []
    
    from_coord = CITY_COORDS.get(segment.from_city, (39.9, 116.4))
    to_coord = CITY_COORDS.get(segment.to_city, (31.2, 121.5))
    
    mid_lat = (from_coord[0] + to_coord[0]) / 2
    mid_lng = (from_coord[1] + to_coord[1]) / 2
    
    buffer_meters = 100 if sensitivity == TemperatureSensitivity.HIGH else 150
    
    line_fence = FenceCreate(
        name=f"{segment.from_city}-{segment.to_city}干线围栏",
        fence_type=FenceType.LINE_BUFFER,
        category=FenceCategory.ROUTE_SEGMENT,
        data={
            "points": [
                {"lat": from_coord[0], "lng": from_coord[1]},
                {"lat": mid_lat, "lng": mid_lng},
                {"lat": to_coord[0], "lng": to_coord[1]},
            ],
            "buffer_meters": buffer_meters,
            "start_city": segment.from_city,
            "end_city": segment.to_city,
        },
        description=f"{segment.from_city}到{segment.to_city}规划行驶路线围栏",
        active=True,
        alert_level=AlertLevel.SEVERE,
        tags=["route", segment.from_city, segment.to_city, segment.segment_id],
        route_id=segment.segment_id.split("-")[0],
    )
    fence = create_fence(line_fence)
    fence_ids.append(fence.fence_id)
    
    return fence_ids


def calculate_segment_costs(segment: RouteSegment, sensitivity: TemperatureSensitivity, prediction: Dict[str, float]) -> Dict[str, float]:
    config = TEMP_SENSITIVITY_CONFIG[sensitivity]
    
    base_speed = 85 if config["avoid_congestion"] else 70
    speed = base_speed * (1 - prediction["congestion_probability"] * 0.3)
    
    duration = segment.distance_km / speed + prediction["predicted_delay_h"]
    
    toll_rate = 0.6 if config["avoid_congestion"] else 0.3
    toll_cost = segment.distance_km * toll_rate * random.uniform(0.9, 1.1)
    
    energy_factor = prediction["energy_consumption_factor"]
    base_energy = segment.distance_km * 0.3
    avg_temp = (config["temp_range"][0] + config["temp_range"][1]) / 2
    cooling_load = abs(avg_temp - prediction["predicted_avg_temp"]) * 0.02
    energy_consumption = base_energy * (1 + cooling_load) * energy_factor
    
    diesel_price = random.uniform(7.2, 8.0)
    fuel_cost = energy_consumption * diesel_price
    
    carbon_emission = (energy_consumption * 0.27 + segment.distance_km * 0.6) * 2.68
    
    risk_level = "low"
    if prediction["heat_risk_probability"] > 0.7 or prediction["congestion_probability"] > 0.7:
        risk_level = "high"
    elif prediction["heat_risk_probability"] > 0.4 or prediction["congestion_probability"] > 0.4:
        risk_level = "medium"
    
    return {
        "duration_h": round(duration, 1),
        "speed_kmh": round(speed, 0),
        "toll_cost_yuan": round(toll_cost, 0),
        "fuel_cost_yuan": round(fuel_cost, 0),
        "energy_consumption_kwh": round(energy_consumption, 1),
        "carbon_emission_kg": round(carbon_emission, 1),
        "risk_level": risk_level,
        "congestion_probability": prediction["congestion_probability"],
        "heat_risk_probability": prediction["heat_risk_probability"],
    }


def compute_multi_objective_score(plan: RoutePlanResponse, sensitivity: TemperatureSensitivity) -> float:
    config = TEMP_SENSITIVITY_CONFIG[sensitivity]
    
    max_distance = 3000
    max_duration = 48
    max_cost = 50000
    
    distance_norm = 1 - (plan.estimated_total_distance_km / max_distance)
    duration_norm = 1 - (plan.estimated_total_duration_h / max_duration)
    cost_norm = 1 - (plan.estimated_total_cost_yuan / max_cost)
    risk_norm = 1 - (plan.overall_risk_score / 100)
    
    avg_heat_risk = plan.risk_report.get("avg_heat_risk", 0)
    temp_score = 1 - avg_heat_risk
    
    safety_score = risk_norm * 0.5 + temp_score * 0.5
    
    total_weight = config["safety_weight"] + config["time_weight"] + config["cost_weight"] + config["distance_weight"] + config["temp_weight"]
    
    composite = (
        safety_score * config["safety_weight"] * 100 +
        duration_norm * config["time_weight"] * 100 +
        cost_norm * config["cost_weight"] * 100 +
        distance_norm * config["distance_weight"] * 100 +
        temp_score * config["temp_weight"] * 100
    ) / total_weight
    
    return round(composite, 1)


def generate_risk_report(nodes: List[RouteNode], segments: List[RouteSegment], sensitivity: TemperatureSensitivity) -> Dict[str, Any]:
    high_risk_segments = [s for s in segments if s.risk_level == "high"]
    medium_risk_segments = [s for s in segments if s.risk_level == "medium"]
    
    avg_congestion = sum(s.congestion_probability for s in segments) / max(len(segments), 1)
    avg_heat_risk = sum(s.heat_risk_probability for s in segments) / max(len(segments), 1)
    
    risk_items = []
    for seg in high_risk_segments:
        reasons = []
        if seg.congestion_probability > 0.7:
            reasons.append(f"拥堵概率高({seg.congestion_probability*100:.0f}%)")
        if seg.heat_risk_probability > 0.7:
            reasons.append(f"高温风险高({seg.heat_risk_probability*100:.0f}%)")
        risk_items.append(f"{seg.from_city}-{seg.to_city}: {', '.join(reasons)}")
    
    overall_score = 100 - (len(high_risk_segments) * 20 + len(medium_risk_segments) * 10 + avg_congestion * 20 + avg_heat_risk * 30)
    
    return {
        "overall_risk_score": round(max(0, overall_score), 1),
        "high_risk_segment_count": len(high_risk_segments),
        "medium_risk_segment_count": len(medium_risk_segments),
        "avg_congestion_probability": round(avg_congestion, 3),
        "avg_heat_risk_probability": round(avg_heat_risk, 3),
        "risk_segments": risk_items,
        "sensitivity_level": sensitivity.value,
        "recommended_actions": [
            "避开高温时段通行" if avg_heat_risk > 0.5 else None,
            "准备备用路线" if avg_congestion > 0.5 else None,
            "加强温控监测" if sensitivity == TemperatureSensitivity.HIGH else None,
        ],
    }


def plan_route(request: RoutePlanRequest) -> RoutePlanResponse:
    plan_id = f"PLAN-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.utcnow()
    
    sensitivity = CARGO_TYPE_MAP.get(request.cargo_type, request.temperature_sensitivity)
    config = TEMP_SENSITIVITY_CONFIG[sensitivity]
    
    nodes = generate_route_nodes(request.origin, request.destination, request.transport_mode, sensitivity, request.multi_drop_points)
    
    segments = []
    total_distance = 0
    total_duration = 0
    total_toll = 0
    total_fuel = 0
    total_energy = 0
    total_carbon = 0
    
    for i in range(len(nodes) - 1):
        from_node = nodes[i]
        to_node = nodes[i + 1]
        
        distance = haversine(from_node.lat, from_node.lng, to_node.lat, to_node.lng)
        hour_of_day = (now.hour + i * 2) % 24
        
        prediction = simulate_cnn_lstm_prediction(from_node.city, to_node.city, hour_of_day, sensitivity)
        costs = calculate_segment_costs(
            RouteSegment(segment_id=f"{plan_id}-SEG{i:02d}", from_node_id=from_node.node_id, to_node_id=to_node.node_id,
                         from_city=from_node.city, to_city=to_node.city, distance_km=distance, estimated_duration_h=0,
                         speed_kmh=0, toll_cost_yuan=0, fuel_cost_yuan=0, energy_consumption_kwh=0,
                         carbon_emission_kg=0, temperature_min=config["temp_range"][0],
                         temperature_max=config["temp_range"][1]),
            sensitivity,
            prediction
        )
        
        fence_ids = create_segment_fences(
            RouteSegment(segment_id=f"{plan_id}-SEG{i:02d}", from_node_id=from_node.node_id, to_node_id=to_node.node_id,
                         from_city=from_node.city, to_city=to_node.city, distance_km=round(distance, 1),
                         estimated_duration_h=costs["duration_h"], speed_kmh=costs["speed_kmh"],
                         toll_cost_yuan=costs["toll_cost_yuan"], fuel_cost_yuan=costs["fuel_cost_yuan"],
                         energy_consumption_kwh=costs["energy_consumption_kwh"],
                         carbon_emission_kg=costs["carbon_emission_kg"],
                         temperature_min=config["temp_range"][0], temperature_max=config["temp_range"][1],
                         risk_level=costs["risk_level"], congestion_probability=costs["congestion_probability"],
                         heat_risk_probability=costs["heat_risk_probability"]),
            sensitivity
        )
        
        segment = RouteSegment(
            segment_id=f"{plan_id}-SEG{i:02d}",
            from_node_id=from_node.node_id,
            to_node_id=to_node.node_id,
            from_city=from_node.city,
            to_city=to_node.city,
            distance_km=round(distance, 1),
            estimated_duration_h=costs["duration_h"],
            speed_kmh=costs["speed_kmh"],
            toll_cost_yuan=costs["toll_cost_yuan"],
            fuel_cost_yuan=costs["fuel_cost_yuan"],
            energy_consumption_kwh=costs["energy_consumption_kwh"],
            carbon_emission_kg=costs["carbon_emission_kg"],
            temperature_min=config["temp_range"][0],
            temperature_max=config["temp_range"][1],
            risk_level=costs["risk_level"],
            congestion_probability=costs["congestion_probability"],
            heat_risk_probability=costs["heat_risk_probability"],
            fence_ids=fence_ids,
        )
        segments.append(segment)
        
        total_distance += segment.distance_km
        total_duration += segment.estimated_duration_h
        total_toll += segment.toll_cost_yuan
        total_fuel += segment.fuel_cost_yuan
        total_energy += segment.energy_consumption_kwh
        total_carbon += segment.carbon_emission_kg
    
    stop_time_h = sum(n.stop_duration_min for n in nodes) / 60
    total_duration += stop_time_h
    
    driver_count = 1 if total_duration <= 8 else 2
    rest_stops = []
    if driver_count == 2:
        rest_stops = [f"服务区{i+1}" for i in range(math.ceil(total_duration / 4))]
    
    risk_report = generate_risk_report(nodes, segments, sensitivity)
    
    total_fence_count = sum(len(s.fence_ids) for s in segments)
    fence_summary = {
        "total_fence_count": total_fence_count,
        "segment_fences": len(segments),
        "node_fences": len(nodes),
        "fences_created": [fid for s in segments for fid in s.fence_ids],
    }
    
    plan = RoutePlanResponse(
        plan_id=plan_id,
        origin=request.origin,
        destination=request.destination,
        transport_mode=request.transport_mode,
        temperature_sensitivity=sensitivity,
        cargo_type=request.cargo_type,
        cargo_weight_kg=request.cargo_weight_kg,
        created_at=now,
        estimated_total_duration_h=round(total_duration, 1),
        estimated_total_distance_km=round(total_distance, 1),
        estimated_total_cost_yuan=round(total_toll + total_fuel, 0),
        total_energy_consumption_kwh=round(total_energy, 1),
        total_carbon_emission_kg=round(total_carbon, 1),
        overall_risk_score=risk_report["overall_risk_score"],
        composite_score=0,
        nodes=nodes,
        segments=segments,
        vehicle_allocation={
            "recommended_model": "45ft冷藏挂车" if request.cargo_weight_kg > 10000 else "20ft冷藏柜",
            "capacity_kg": 20000 if request.cargo_weight_kg > 10000 else 8000,
            "cooling_system": "双压缩机独立制冷",
            "temperature_range": f"{config['temp_range'][0]}°C ~ {config['temp_range'][1]}°C",
        },
        driver_schedule={
            "driver_count": driver_count,
            "shift_hours": 4,
            "rest_stops": rest_stops,
            "total_driving_h": round(total_duration - stop_time_h, 1),
        },
        risk_report=risk_report,
        fence_summary=fence_summary,
        scores={},
    )
    
    plan.composite_score = compute_multi_objective_score(plan, sensitivity)
    
    plan.scores = {
        "温控安全评分": round(risk_report["overall_risk_score"], 1),
        "时效评分": round(max(0, 100 - (plan.estimated_total_duration_h / 48) * 50), 1),
        "成本评分": round(max(0, 100 - (plan.estimated_total_cost_yuan / 30000) * 40), 1),
        "里程评分": round(max(0, 100 - (plan.estimated_total_distance_km / 3000) * 30), 1),
        "综合评分": plan.composite_score,
    }
    
    return plan


def generate_comparison_plans(request: RoutePlanRequest) -> RoutePlanComparison:
    plans = []
    
    sensitivity = CARGO_TYPE_MAP.get(request.cargo_type, request.temperature_sensitivity)
    config = TEMP_SENSITIVITY_CONFIG[sensitivity]
    strategy = config["priority_strategy"]
    
    modes = [request.transport_mode]
    
    for mode in modes:
        req_copy = RoutePlanRequest(**request.dict())
        req_copy.transport_mode = mode
        plan = plan_route(req_copy)
        plans.append(plan)
    
    if strategy == "时效优先":
        plans.sort(key=lambda x: x.estimated_total_duration_h)
    elif strategy == "温控优先":
        plans.sort(key=lambda x: -x.risk_report["overall_risk_score"])
    else:
        plans.sort(key=lambda x: x.estimated_total_cost_yuan)
    
    for p in plans:
        p.recommended = True
    
    comparison_metrics = {
        "avg_distance_km": round(sum(p.estimated_total_distance_km for p in plans) / len(plans), 1),
        "avg_duration_h": round(sum(p.estimated_total_duration_h for p in plans) / len(plans), 1),
        "avg_cost_yuan": round(sum(p.estimated_total_cost_yuan for p in plans) / len(plans), 0),
        "best_cost_plan_id": min(plans, key=lambda x: x.estimated_total_cost_yuan).plan_id,
        "best_time_plan_id": min(plans, key=lambda x: x.estimated_total_duration_h).plan_id,
        "best_risk_plan_id": max(plans, key=lambda x: x.overall_risk_score).plan_id,
    }
    
    return RoutePlanComparison(
        plans=plans,
        best_plan_id=plans[0].plan_id,
        comparison_metrics=comparison_metrics,
    )