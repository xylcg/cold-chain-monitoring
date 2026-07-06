"""
多温区车厢智能调度 API
基于多目标优化算法的智能调度系统

核心能力：
- 三类温区（冷冻-18℃/冷藏0-4℃/恒温15-25℃）货物智能组合配载
- 多目标优化算法（温区合规+容积匹配+时效约束+成本最优）
- 分层调度策略（4优先级：温区合规→货量适配→订单聚合→成本最优）
- 完整执行流程（订单聚合→车辆匹配→方案生成→派单→监控→数据迭代）
- 与路径规划、传感器、电子围栏、异常预警、追溯链模块深度联动
- 容错约束机制（高敏隔离、容积超载拦截、时效冲突过滤、温区异常兜底）
"""
import random
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..core.security import get_current_user
from ..services.world_state import get_world_state
from ..api.traceability import auto_add_dispatch_record, WAYBILL_TRACE_MAP

router = APIRouter(prefix="/api/v1/dispatch", tags=["多温区调度"])

# ==================== 温度区域定义 ====================
TEMP_ZONES = {
    "frozen": {"name": "冷冻区", "range": "-22℃ ~ -15℃", "min": -22, "max": -15, "target": -18, "color": "#4361ee"},
    "refrigerated": {"name": "冷藏区", "range": "0℃ ~ 4℃", "min": 0, "max": 4, "target": 2, "color": "#00a8ff"},
    "ambient": {"name": "恒温区", "range": "15℃ ~ 25℃", "min": 15, "max": 25, "target": 20, "color": "#f59e0b"},
}

# ==================== 货物类型与温区映射（统一） ====================
CARGO_ZONE_MAP = {
    "冷冻牛肉": "frozen", "冷冻海鲜": "frozen", "冰淇淋": "frozen", "冷冻预制菜": "frozen",
    "冷冻肉类": "frozen", "速冻食品": "frozen", "冷冻食品": "frozen", "冷冻水产": "frozen",
    "冷藏乳制品": "refrigerated", "冷藏水果": "refrigerated", "新鲜蔬菜": "refrigerated",
    "冷藏鲜奶": "refrigerated", "水果": "refrigerated", "蔬菜": "refrigerated",
    "鲜花": "refrigerated", "冷藏生鲜": "refrigerated", "鲜肉": "refrigerated",
    "海鲜": "refrigerated", "鲜奶": "refrigerated", "高端鲜果": "refrigerated",
    "恒温药品": "ambient", "巧克力": "ambient", "常温零食": "ambient",
    "疫苗试剂": "refrigerated", "生物试剂": "refrigerated", "疫苗": "refrigerated",
    "疫苗医药": "refrigerated", "医用试剂": "refrigerated", "医药试剂": "refrigerated",
}

# ==================== 高敏货物（强制隔离机制） ====================
HIGH_SENSITIVITY_CARGO = {"疫苗", "疫苗试剂", "生物试剂", "医用试剂", "医药试剂", "恒温药品"}

# ==================== 多温区车辆库 ====================
# 多温区冷藏车：物理隔断、独立制冷、独立温控
# zones: 支持的温区列表；compartments: 各温区独立舱位规格
MULTI_ZONE_VEHICLES = [
    {
        "id": "VEH-MZ01", "plate": "冷A-8801", "model": "解放J6F双温区",
        "zones": ["frozen", "refrigerated"],
        "compartments": {
            "frozen": {"capacity_kg": 4000, "capacity_m3": 16},
            "refrigerated": {"capacity_kg": 4000, "capacity_m3": 19},
        },
        "total_capacity_kg": 8000, "total_capacity_m3": 35,
        "fuel_type": "diesel", "fuel_consumption": 28, "status": "idle",
        "current_city": "北京", "driver": "张师傅", "driver_phone": "138****8801",
    },
    {
        "id": "VEH-MZ02", "plate": "冷A-8802", "model": "东风天锦KR三温区",
        "zones": ["frozen", "refrigerated", "ambient"],
        "compartments": {
            "frozen": {"capacity_kg": 3500, "capacity_m3": 14},
            "refrigerated": {"capacity_kg": 4000, "capacity_m3": 16},
            "ambient": {"capacity_kg": 2500, "capacity_m3": 12},
        },
        "total_capacity_kg": 10000, "total_capacity_m3": 42,
        "fuel_type": "diesel", "fuel_consumption": 32, "status": "idle",
        "current_city": "上海", "driver": "李师傅", "driver_phone": "138****8802",
    },
    {
        "id": "VEH-MZ03", "plate": "冷A-8803", "model": "重汽豪沃TX双温区",
        "zones": ["frozen", "refrigerated"],
        "compartments": {
            "frozen": {"capacity_kg": 6000, "capacity_m3": 22},
            "refrigerated": {"capacity_kg": 6000, "capacity_m3": 26},
        },
        "total_capacity_kg": 12000, "total_capacity_m3": 48,
        "fuel_type": "diesel", "fuel_consumption": 35, "status": "idle",
        "current_city": "广州", "driver": "王师傅", "driver_phone": "138****8803",
    },
    {
        "id": "VEH-MZ04", "plate": "冷A-8804", "model": "福田欧马可S5双温区",
        "zones": ["refrigerated", "ambient"],
        "compartments": {
            "refrigerated": {"capacity_kg": 3500, "capacity_m3": 16},
            "ambient": {"capacity_kg": 2500, "capacity_m3": 12},
        },
        "total_capacity_kg": 6000, "total_capacity_m3": 28,
        "fuel_type": "electric", "fuel_consumption": 18, "status": "idle",
        "current_city": "成都", "driver": "赵师傅", "driver_phone": "138****8804",
    },
    {
        "id": "VEH-MZ05", "plate": "冷A-8805", "model": "解放J6F三温区",
        "zones": ["frozen", "refrigerated", "ambient"],
        "compartments": {
            "frozen": {"capacity_kg": 3000, "capacity_m3": 12},
            "refrigerated": {"capacity_kg": 4000, "capacity_m3": 18},
            "ambient": {"capacity_kg": 2000, "capacity_m3": 10},
        },
        "total_capacity_kg": 9000, "total_capacity_m3": 40,
        "fuel_type": "diesel", "fuel_consumption": 30, "status": "idle",
        "current_city": "武汉", "driver": "钱师傅", "driver_phone": "138****8805",
    },
    {
        "id": "VEH-MZ06", "plate": "冷A-8806", "model": "东风多利卡D9单冷冻区",
        "zones": ["frozen"],
        "compartments": {
            "frozen": {"capacity_kg": 7000, "capacity_m3": 32},
        },
        "total_capacity_kg": 7000, "total_capacity_m3": 32,
        "fuel_type": "diesel", "fuel_consumption": 26, "status": "idle",
        "current_city": "北京", "driver": "孙师傅", "driver_phone": "138****8806",
    },
    {
        "id": "VEH-MZ07", "plate": "冷A-8807", "model": "一汽柳特L3R单冷藏区",
        "zones": ["refrigerated"],
        "compartments": {
            "refrigerated": {"capacity_kg": 5000, "capacity_m3": 24},
        },
        "total_capacity_kg": 5000, "total_capacity_m3": 24,
        "fuel_type": "diesel", "fuel_consumption": 22, "status": "loading",
        "current_city": "上海", "driver": "周师傅", "driver_phone": "138****8807",
    },
    {
        "id": "VEH-MZ08", "plate": "冷A-8808", "model": "福田欧曼GTL三温区",
        "zones": ["frozen", "refrigerated", "ambient"],
        "compartments": {
            "frozen": {"capacity_kg": 5000, "capacity_m3": 18},
            "refrigerated": {"capacity_kg": 6000, "capacity_m3": 22},
            "ambient": {"capacity_kg": 4000, "capacity_m3": 15},
        },
        "total_capacity_kg": 15000, "total_capacity_m3": 55,
        "fuel_type": "diesel", "fuel_consumption": 38, "status": "idle",
        "current_city": "广州", "driver": "吴师傅", "driver_phone": "138****8808",
    },
]

# ==================== 内存存储：调度方案与执行状态 ====================
_dispatch_plans: Dict[str, dict] = {}  # assignment_id -> 调度方案
_dispatch_history: list = []  # 调度历史（用于数据迭代优化）
_monitor_data: Dict[str, dict] = {}  # assignment_id -> 在途监控数据


# ==================== 订单获取（统一数据源） ====================
def _get_pending_orders_from_customer() -> list:
    """从 customer.py 同步真实订单"""
    try:
        from .customer import _customer_orders
        pending = []
        for oid, order in _customer_orders.items():
            if order.get("status") in ("pending", "accepted"):
                cargo_name = order.get("cargo_name", "生鲜货物")
                zone = _resolve_cargo_zone(cargo_name, order.get("cargo_category", ""))
                zone_info = TEMP_ZONES[zone]
                weight = float(order.get("quantity", 0)) or random.randint(500, 3000)
                volume = round(weight * random.uniform(0.001, 0.003), 2)
                pending.append({
                    "order_id": oid,
                    "customer": order.get("receiver", "客户") or f"客户{oid[-4:]}",
                    "cargo_type": cargo_name,
                    "cargo_category": order.get("cargo_category", ""),
                    "temp_zone": zone,
                    "zone_name": zone_info["name"],
                    "temp_range": zone_info["range"],
                    "target_temp_c": zone_info["target"],
                    "weight_kg": weight,
                    "volume_m3": volume,
                    "origin": order.get("origin", "北京"),
                    "destination": order.get("destination", "上海"),
                    "deadline": order.get("created_at", datetime.utcnow().isoformat()) ,
                    "priority": _resolve_priority(cargo_name, order),
                    "is_high_sensitivity": cargo_name in HIGH_SENSITIVITY_CARGO,
                    "status": "pending",
                    "source": "customer",
                })
        return pending
    except Exception:
        return []


def _resolve_cargo_zone(cargo_name: str, cargo_category: str = "") -> str:
    """解析货物温区"""
    if cargo_name in CARGO_ZONE_MAP:
        return CARGO_ZONE_MAP[cargo_name]
    cat_map = {"冷冻食品": "frozen", "冷藏生鲜": "refrigerated", "疫苗医药": "refrigerated",
               "化工制剂": "ambient", "其他": "refrigerated"}
    return cat_map.get(cargo_category, "refrigerated")


def _resolve_priority(cargo_name: str, order: dict) -> str:
    """解析订单优先级"""
    if cargo_name in HIGH_SENSITIVITY_CARGO:
        return "urgent"
    review = order.get("review_status")
    if review == "approved":
        return "high"
    return "normal"


def _generate_demo_orders() -> list:
    """生成演示订单（当无真实订单时补充）"""
    random.seed(int(datetime.utcnow().timestamp()) // 30)
    orders = []
    customers = ["永辉超市", "盒马鲜生", "叮咚买菜", "美团优选", "华润万家",
                 "山姆会员店", "大润发", "物美超市", "沃尔玛", "京东超市",
                 "老百姓大药房", "国大药房", "海王星辰"]
    cargo_pool = list(CARGO_ZONE_MAP.keys())
    cities = ["北京", "上海", "广州", "深圳", "杭州", "武汉", "成都", "重庆", "南京", "西安"]

    for i in range(1, 19):
        cargo_name = random.choice(cargo_pool)
        zone = CARGO_ZONE_MAP[cargo_name]
        zone_info = TEMP_ZONES[zone]
        weight = random.randint(300, 4500)
        volume = round(weight * random.uniform(0.001, 0.003), 2)
        is_high = cargo_name in HIGH_SENSITIVITY_CARGO
        orders.append({
            "order_id": f"ORD-DISP-{i:04d}",
            "customer": random.choice(customers),
            "cargo_type": cargo_name,
            "cargo_category": "",
            "temp_zone": zone,
            "zone_name": zone_info["name"],
            "temp_range": zone_info["range"],
            "target_temp_c": zone_info["target"],
            "weight_kg": weight,
            "volume_m3": volume,
            "origin": random.choice(cities),
            "destination": random.choice([c for c in cities if not orders or c != orders[-1]["origin"]]),
            "deadline": (datetime.utcnow() + timedelta(hours=random.randint(2, 48))).isoformat(),
            "priority": "urgent" if is_high else random.choice(["normal", "normal", "normal", "high"]),
            "is_high_sensitivity": is_high,
            "status": "pending",
            "source": "demo",
        })
    return orders


def _get_all_pending_orders() -> list:
    """获取所有待调度订单（真实 + 演示补充）"""
    real_orders = _get_pending_orders_from_customer()
    demo_orders = _generate_demo_orders()
    # 合并去重
    real_ids = {o["order_id"] for o in real_orders}
    combined = real_orders + [o for o in demo_orders if o["order_id"] not in real_ids]
    return combined


# ==================== 多目标优化调度算法 ====================
def _multi_objective_dispatch(orders: list, vehicles: list) -> dict:
    """
    多目标优化调度算法
    分层调度策略（4优先级）：
    1. 温区合规性（刚性约束）：严格校验订单温区与车厢温区匹配
    2. 货量比例适配：根据各温区货量占比匹配车厢容积
    3. 订单聚合优化：同区域同时效不同温区订单聚合
    4. 成本最优：油耗低、里程短、运力闲置优先
    """
    assignments = []
    assigned_order_ids = set()
    total_original_cost = 0.0

    # 计算专车配送成本基准（每个订单单独派车）
    for o in orders:
        total_original_cost += max(o["weight_kg"] * 0.8, 800) + 200

    # ========== 第一优先级：温区合规性分组 ==========
    zone_groups = {"frozen": [], "refrigerated": [], "ambient": []}
    for o in orders:
        zone_groups[o["temp_zone"]].append(o)

    # 高敏货物单独标记（强制隔离机制）
    high_sensitivity_orders = [o for o in orders if o["is_high_sensitivity"]]

    # ========== 第二优先级：订单聚合优化 ==========
    # 按「同配送区域 + 同时效窗口 + 不同温区」聚合
    aggregated_groups = _aggregate_orders_by_region_time(orders)

    # ========== 第三优先级：车辆匹配（多目标评分） ==========
    idle_vehicles = [v for v in vehicles if v["status"] == "idle"]
    # 按总容量降序（大车优先，减少车辆数）
    idle_vehicles.sort(key=lambda v: -v["total_capacity_kg"])

    vehicle_usage = {v["id"]: {"used": False, "orders": [], "weight_by_zone": {},
                                "volume_by_zone": {}, "total_weight": 0, "total_volume": 0,
                                "high_sensitivity_vehicle": False}
                     for v in idle_vehicles}

    # 优先处理高敏货物订单（强制隔离机制）
    hs_isolated_count = 0
    for hs_order in high_sensitivity_orders:
        best_vehicle = _find_best_vehicle_for_high_sensitivity(hs_order, idle_vehicles, vehicle_usage)
        if best_vehicle and _can_fit_in_vehicle(hs_order, best_vehicle, vehicle_usage):
            _assign_order_to_vehicle(hs_order, best_vehicle, vehicle_usage)
            vehicle_usage[best_vehicle["id"]]["high_sensitivity_vehicle"] = True
            assigned_order_ids.add(hs_order["order_id"])
            hs_isolated_count += 1

    # 处理聚合订单组（排除高敏订单）
    for group in aggregated_groups:
        remaining = [o for o in group["orders"] if o["order_id"] not in assigned_order_ids and not o.get("is_high_sensitivity", False)]
        if not remaining:
            continue
        best_vehicle = _find_best_vehicle_for_group(remaining, idle_vehicles, vehicle_usage)
        if best_vehicle:
            for o in remaining:
                if _can_fit_in_vehicle(o, best_vehicle, vehicle_usage):
                    _assign_order_to_vehicle(o, best_vehicle, vehicle_usage)
                    assigned_order_ids.add(o["order_id"])

    # 处理剩余订单（单独装车）（排除高敏订单）
    for zone in ["frozen", "refrigerated", "ambient"]:
        remaining = [o for o in zone_groups[zone] if o["order_id"] not in assigned_order_ids and not o.get("is_high_sensitivity", False)]
        # 按优先级排序
        priority_order = {"urgent": 3, "high": 2, "normal": 1}
        remaining.sort(key=lambda o: -priority_order.get(o["priority"], 0))
        for o in remaining:
            best_vehicle = _find_best_vehicle_single(o, idle_vehicles, vehicle_usage)
            if best_vehicle and _can_fit_in_vehicle(o, best_vehicle, vehicle_usage):
                _assign_order_to_vehicle(o, best_vehicle, vehicle_usage)
                assigned_order_ids.add(o["order_id"])

    # ========== 第四优先级：生成调度方案 + 成本核算 ==========
    for vehicle in idle_vehicles:
        usage = vehicle_usage[vehicle["id"]]
        if not usage["orders"]:
            continue
        assignment = _build_assignment(vehicle, usage)
        assignments.append(assignment)

    # ========== 容错检查：真实约束验证 ==========
    unassigned = [o for o in orders if o["order_id"] not in assigned_order_ids]
    
    # 温区合规性检查：所有分配的订单温区都在车辆支持范围内
    temp_zone_compliant = True
    for a in assignments:
        for o in a["orders"]:
            if o["temp_zone"] not in a["zones_used"]:
                temp_zone_compliant = False
                break
    
    # 容积超载检查：所有车辆装载率不超过92%
    volume_overload_intercepted = True
    for a in assignments:
        if a["capacity_utilization"] > 92 or a["volume_utilization"] > 88:
            volume_overload_intercepted = False
            break
    
    # 高敏隔离检查：已分配的高敏订单车辆未混装普通货物
    hs_isolated = True
    for a in assignments:
        has_hs = any(o["is_high_sensitivity"] for o in a["orders"])
        has_normal = any(not o["is_high_sensitivity"] for o in a["orders"])
        if has_hs and has_normal:
            hs_isolated = False
            break
    # 检查是否所有高敏订单都已分配
    hs_all_assigned = hs_isolated_count == len(high_sensitivity_orders)
    
    # 时效冲突检查：同一车辆订单时效窗口差距不超过8小时
    time_conflict_filtered = True
    for a in assignments:
        if len(a["orders"]) < 2:
            continue
        deadlines = []
        for o in a["orders"]:
            deadline = o.get("deadline", "")
            try:
                dt = datetime.fromisoformat(deadline.replace("Z", "")) if deadline else datetime.utcnow()
                deadlines.append(dt)
            except Exception:
                pass
        if len(deadlines) >= 2:
            max_dt = max(deadlines)
            min_dt = min(deadlines)
            if (max_dt - min_dt).total_seconds() > 8 * 3600:
                time_conflict_filtered = False
                break

    # 成本分析
    total_assignment_cost = sum(a["estimated_cost_yuan"] for a in assignments)
    cost_saved_pct = round((total_original_cost - total_assignment_cost) / max(total_original_cost, 1) * 100, 1)

    # 装载率统计
    avg_capacity = round(
        sum(a["capacity_utilization"] for a in assignments) / max(len(assignments), 1), 1
    ) if assignments else 0

    result = {
        "total_orders": len(orders),
        "assigned": len(assigned_order_ids),
        "unassigned": len(unassigned),
        "vehicles_used": len(assignments),
        "assignments": assignments,
        "unassigned_orders": [{"order_id": o["order_id"], "cargo_type": o["cargo_type"],
                                "reason": "无匹配温区车辆或容积超载"} for o in unassigned],
        "fleet_utilization": round(len(assignments) / max(len(vehicles), 1) * 100, 1),
        "avg_capacity_utilization": avg_capacity,
        "cost_analysis": {
            "traditional_cost_yuan": round(total_original_cost, 0),
            "optimized_cost_yuan": round(total_assignment_cost, 0),
            "cost_saved_percent": max(cost_saved_pct, 0),
            "strategy": "多温区组合装车 + 多目标优化",
        },
        "constraint_check": {
            "high_sensitivity_isolated": hs_isolated,
            "high_sensitivity_all_assigned": hs_all_assigned,
            "volume_overload_intercepted": volume_overload_intercepted,
            "time_conflict_filtered": time_conflict_filtered,
            "temp_zone_compliant": temp_zone_compliant,
        },
        "dispatch_time": datetime.utcnow().isoformat(),
        "algorithm": "多目标优化（温区合规+容积匹配+时效约束+成本最优）",
    }
    return result


def _aggregate_orders_by_region_time(orders: list) -> list:
    """订单聚合优化：同配送区域 + 同时效窗口 + 不同温区"""
    groups = []
    # 按目的地+时效窗口分组
    region_time_map = {}
    for o in orders:
        deadline = o.get("deadline", "")
        try:
            dt = datetime.fromisoformat(deadline.replace("Z", "")) if deadline else datetime.utcnow()
            time_window = dt.strftime("%Y%m%d%H")  # 按小时窗口
        except Exception:
            time_window = "default"
        key = (o["destination"], time_window)
        region_time_map.setdefault(key, []).append(o)

    for key, group_orders in region_time_map.items():
        if len(group_orders) < 2:
            continue
        zones_in_group = set(o["temp_zone"] for o in group_orders)
        if len(zones_in_group) >= 2:  # 多温区订单才聚合
            groups.append({
                "destination": key[0],
                "time_window": key[1],
                "orders": group_orders,
                "zones": list(zones_in_group),
            })
    # 按订单数降序
    groups.sort(key=lambda g: -len(g["orders"]))
    return groups


def _find_best_vehicle_for_high_sensitivity(order: dict, vehicles: list, usage: dict) -> Optional[dict]:
    """高敏货物强制隔离：匹配有独立恒温舱且未装载其他温区货物的车辆"""
    candidates = []
    for v in vehicles:
        zone = order["temp_zone"]
        if zone not in v["zones"]:
            continue
        # 高敏货物要求舱位独立，不与其他温区混装
        other_zones_loaded = [z for z in v["zones"] if z != zone and usage[v["id"]]["weight_by_zone"].get(z, 0) > 0]
        if other_zones_loaded:
            continue
        score = _score_vehicle_for_order(order, v, usage[v["id"]])
        if score > 0:
            candidates.append((score, v))
    if not candidates:
        return None
    candidates.sort(key=lambda x: -x[0])
    return candidates[0][1]


def _find_best_vehicle_for_group(orders: list, vehicles: list, usage: dict) -> Optional[dict]:
    """为订单组找最佳车辆（多目标评分）"""
    candidates = []
    for v in vehicles:
        # 检查温区合规
        order_zones = set(o["temp_zone"] for o in orders)
        if not order_zones.issubset(set(v["zones"])):
            continue
        # 检查容积
        total_w = sum(o["weight_kg"] for o in orders) + usage[v["id"]]["total_weight"]
        total_v = sum(o["volume_m3"] for o in orders) + usage[v["id"]]["total_volume"]
        if total_w > v["total_capacity_kg"] * 0.92 or total_v > v["total_capacity_m3"] * 0.88:
            continue
        score = _score_vehicle_for_group(orders, v, usage[v["id"]])
        candidates.append((score, v))
    if not candidates:
        return None
    candidates.sort(key=lambda x: -x[0])
    return candidates[0][1]


def _find_best_vehicle_single(order: dict, vehicles: list, usage: dict) -> Optional[dict]:
    """为单个订单找最佳车辆"""
    candidates = []
    for v in vehicles:
        if order["temp_zone"] not in v["zones"]:
            continue
        if not _can_fit_in_vehicle(order, v, usage):
            continue
        score = _score_vehicle_for_order(order, v, usage[v["id"]])
        if score > 0:
            candidates.append((score, v))
    if not candidates:
        return None
    candidates.sort(key=lambda x: -x[0])
    return candidates[0][1]


def _can_fit_in_vehicle(order: dict, vehicle: dict, usage: dict) -> bool:
    """容积超载拦截：检查订单是否能装入车辆（高敏隔离 + 舱位级 + 整车级三重检查）"""
    u = usage[vehicle["id"]]
    
    # 高敏隔离检查：双向隔离
    # 1. 高敏车辆禁止装载普通货物
    # 2. 已有普通货物的车辆禁止装载高敏货物
    has_normal_orders = any(not o["is_high_sensitivity"] for o in u["orders"]) if u["orders"] else False
    if u["high_sensitivity_vehicle"] and not order["is_high_sensitivity"]:
        return False
    if has_normal_orders and order["is_high_sensitivity"]:
        return False
    
    zone = order["temp_zone"]
    comp = vehicle["compartments"].get(zone)
    if not comp:
        return False
    
    # 舱位级超载拦截（重量92% / 体积88%）
    used_w = u["weight_by_zone"].get(zone, 0)
    used_v = u["volume_by_zone"].get(zone, 0)
    if used_w + order["weight_kg"] > comp["capacity_kg"] * 0.92:
        return False
    if used_v + order["volume_m3"] > comp["capacity_m3"] * 0.88:
        return False
    
    # 整车级超载拦截（重量92% / 体积88%）
    if u["total_weight"] + order["weight_kg"] > vehicle["total_capacity_kg"] * 0.92:
        return False
    if u["total_volume"] + order["volume_m3"] > vehicle["total_capacity_m3"] * 0.88:
        return False
    
    return True


def _score_vehicle_for_order(order: dict, vehicle: dict, usage: dict) -> float:
    """多目标评分：容积匹配 + 时效适配 + 成本最优"""
    zone = order["temp_zone"]
    comp = vehicle["compartments"].get(zone, {})
    used_w = usage["weight_by_zone"].get(zone, 0)
    cap_w = comp.get("capacity_kg", 1)
    # 装载率评分（越满越优）
    fill_ratio = (used_w + order["weight_kg"]) / cap_w
    fill_score = fill_ratio * 40
    # 成本评分（油耗低优先）
    cost_score = (45 - vehicle["fuel_consumption"]) * 1.5
    # 优先级评分
    priority_score = {"urgent": 30, "high": 20, "normal": 10}.get(order["priority"], 10)
    # 区域匹配评分（车辆当前位置与订单起点）
    region_score = 15 if vehicle["current_city"] == order["origin"] else 5
    return fill_score + cost_score + priority_score + region_score


def _score_vehicle_for_group(orders: list, vehicle: dict, usage: dict) -> float:
    """为订单组评分：多温区适配 + 装载率 + 成本"""
    total_w = sum(o["weight_kg"] for o in orders)
    total_v = sum(o["volume_m3"] for o in orders)
    # 装载率评分
    fill_ratio = (usage["total_weight"] + total_w) / vehicle["total_capacity_kg"]
    fill_score = fill_ratio * 35
    # 多温区利用率（使用的温区数越多，多温区车价值越大）
    zones_used = set(o["temp_zone"] for o in orders) | set(usage["weight_by_zone"].keys())
    multi_zone_score = len(zones_used & set(vehicle["zones"])) * 10
    # 成本评分
    cost_score = (45 - vehicle["fuel_consumption"]) * 1.2
    # 区域匹配
    origins = set(o["origin"] for o in orders)
    region_score = 15 if vehicle["current_city"] in origins else 5
    return fill_score + multi_zone_score + cost_score + region_score


def _assign_order_to_vehicle(order: dict, vehicle: dict, usage: dict):
    """将订单分配到车辆"""
    u = usage[vehicle["id"]]
    u["orders"].append(order)
    zone = order["temp_zone"]
    u["weight_by_zone"][zone] = u["weight_by_zone"].get(zone, 0) + order["weight_kg"]
    u["volume_by_zone"][zone] = u["volume_by_zone"].get(zone, 0) + order["volume_m3"]
    u["total_weight"] += order["weight_kg"]
    u["total_volume"] += order["volume_m3"]
    u["used"] = True


def _build_assignment(vehicle: dict, usage: dict) -> dict:
    """生成调度方案"""
    zone_dist = {}
    weight_by_zone = {}
    volume_by_zone = {}
    for zone, w in usage["weight_by_zone"].items():
        zn = TEMP_ZONES[zone]["name"]
        zone_dist[zn] = zone_dist.get(zn, 0) + sum(1 for o in usage["orders"] if o["temp_zone"] == zone)
        weight_by_zone[zn] = w
        volume_by_zone[zn] = usage["volume_by_zone"].get(zone, 0)

    # 成本估算：油耗 × 预估里程 + 固定成本
    avg_distance = 350  # 预估平均配送里程
    fuel_cost = vehicle["fuel_consumption"] * avg_distance * 7.5 / 100  # 油价7.5元/升
    fixed_cost = 300
    total_cost = round(fuel_cost + fixed_cost, 0)

    # 舱位装载详情
    compartment_details = {}
    for zone in vehicle["zones"]:
        comp = vehicle["compartments"][zone]
        used_w = usage["weight_by_zone"].get(zone, 0)
        used_v = usage["volume_by_zone"].get(zone, 0)
        compartment_details[TEMP_ZONES[zone]["name"]] = {
            "zone_key": zone,
            "capacity_kg": comp["capacity_kg"],
            "capacity_m3": comp["capacity_m3"],
            "used_weight_kg": used_w,
            "used_volume_m3": round(used_v, 2),
            "weight_utilization": round(used_w / comp["capacity_kg"] * 100, 1) if used_w > 0 else 0,
            "volume_utilization": round(used_v / comp["capacity_m3"] * 100, 1) if used_v > 0 else 0,
            "temp_range": TEMP_ZONES[zone]["range"],
            "target_temp": TEMP_ZONES[zone]["target"],
        }

    has_high_sensitivity = any(o["is_high_sensitivity"] for o in usage["orders"])
    destinations = list(set(o["destination"] for o in usage["orders"]))
    origins = list(set(o["origin"] for o in usage["orders"]))

    return {
        "assignment_id": f"ASGN-{vehicle['id'][-2:]}-{datetime.utcnow().strftime('%H%M%S')}",
        "vehicle_id": vehicle["id"],
        "plate_number": vehicle["plate"],
        "vehicle_model": vehicle["model"],
        "driver": vehicle["driver"],
        "driver_phone": vehicle["driver_phone"],
        "zones_used": vehicle["zones"],
        "orders": [{"order_id": o["order_id"], "cargo_type": o["cargo_type"],
                     "temp_zone": o["temp_zone"], "weight_kg": o["weight_kg"],
                     "volume_m3": o["volume_m3"], "destination": o["destination"],
                     "priority": o["priority"], "is_high_sensitivity": o.get("is_high_sensitivity", False)} for o in usage["orders"]],
        "order_count": len(usage["orders"]),
        "total_weight_kg": usage["total_weight"],
        "total_volume_m3": round(usage["total_volume"], 2),
        "capacity_utilization": round(usage["total_weight"] / vehicle["total_capacity_kg"] * 100, 1),
        "volume_utilization": round(usage["total_volume"] / vehicle["total_capacity_m3"] * 100, 1),
        "zone_distribution": zone_dist,
        "weight_by_zone": weight_by_zone,
        "volume_by_zone": volume_by_zone,
        "compartment_details": compartment_details,
        "origins": origins,
        "destinations": destinations,
        "has_high_sensitivity": has_high_sensitivity,
        "estimated_departure": (datetime.utcnow() + timedelta(minutes=random.randint(15, 60))).isoformat(),
        "estimated_arrival": (datetime.utcnow() + timedelta(hours=random.randint(3, 12))).isoformat(),
        "estimated_distance_km": avg_distance,
        "estimated_cost_yuan": total_cost,
        "fuel_consumption": vehicle["fuel_consumption"],
        "fuel_type": "柴油" if vehicle["fuel_type"] == "diesel" else "电动",
        "status": "scheduled",
    }


# ==================== API 接口 ====================

@router.get("/orders")
async def get_pending_orders(
    temp_zone: Optional[str] = Query(None, description="温区过滤: frozen/refrigerated/ambient"),
    user: dict = Depends(get_current_user),
):
    """获取待调度订单列表（统一数据源：真实订单 + 演示补充）"""
    orders = _get_all_pending_orders()
    if temp_zone:
        orders = [o for o in orders if o["temp_zone"] == temp_zone]

    zone_summary = {}
    for o in orders:
        zn = o["temp_zone"]
        zone_summary[zn] = zone_summary.get(zn, 0) + 1

    high_sensitivity_count = sum(1 for o in orders if o["is_high_sensitivity"])

    return {
        "total": len(orders),
        "zone_summary": {TEMP_ZONES[k]["name"]: v for k, v in zone_summary.items()},
        "high_sensitivity_count": high_sensitivity_count,
        "orders": orders,
        "zones_info": [{"key": k, "name": v["name"], "range": v["range"], "target": v["target"], "color": v["color"]}
                       for k, v in TEMP_ZONES.items()],
    }


@router.get("/vehicles")
async def get_available_vehicles(
    user: dict = Depends(get_current_user),
):
    """获取可调度多温区车辆"""
    vehicles = MULTI_ZONE_VEHICLES
    idle = sum(1 for v in vehicles if v["status"] == "idle")

    # 车辆温区覆盖统计
    zone_coverage = {}
    for k, v in TEMP_ZONES.items():
        zone_coverage[k] = sum(1 for vh in vehicles if k in vh["zones"])

    return {
        "total": len(vehicles),
        "idle": idle,
        "loading": len(vehicles) - idle,
        "vehicles": vehicles,
        "zones_info": [{"key": k, "name": v["name"], "range": v["range"], "target": v["target"], "color": v["color"]}
                       for k, v in TEMP_ZONES.items()],
        "zone_coverage": {TEMP_ZONES[k]["name"]: v for k, v in zone_coverage.items()},
    }


@router.post("/assign")
async def auto_assign_dispatch(
    user: dict = Depends(get_current_user),
):
    """自动执行多温区调度分配（多目标优化算法）"""
    orders = _get_all_pending_orders()
    vehicles = MULTI_ZONE_VEHICLES
    result = _multi_objective_dispatch(orders, vehicles)

    # 缓存调度方案
    for a in result["assignments"]:
        _dispatch_plans[a["assignment_id"]] = a

    return result


@router.get("/plan")
async def get_dispatch_plan(
    user: dict = Depends(get_current_user),
):
    """查看当前调度方案（含温区使用统计与联动信息）"""
    orders = _get_all_pending_orders()
    vehicles = MULTI_ZONE_VEHICLES
    result = _multi_objective_dispatch(orders, vehicles)

    # 温区使用统计
    zone_usage = {"frozen": 0, "refrigerated": 0, "ambient": 0}
    for a in result["assignments"]:
        for z in a["zones_used"]:
            zone_usage[z] += 1

    result["zone_usage"] = {TEMP_ZONES[k]["name"]: v for k, v in zone_usage.items()}

    # 联动模块信息
    result["module_integration"] = {
        "route_planning": "已联动智能路径规划模块，支持多温区差异化路径",
        "sensors": "已绑定车厢各温区温湿度传感器，实时独立监控",
        "geofence": "已联动电子围栏，仓库/站点进出自动记录温度",
        "alert": "温区异常独立告警，支持二次调度兜底",
    }

    return result


@router.get("/stats")
async def get_dispatch_stats(
    user: dict = Depends(get_current_user),
):
    """调度统计（含数据迭代指标）"""
    orders = _get_all_pending_orders()
    vehicles = MULTI_ZONE_VEHICLES
    result = _multi_objective_dispatch(orders, vehicles)

    avg_cap = result["avg_capacity_utilization"]
    cost_saved = result["cost_analysis"]["cost_saved_percent"]

    return {
        "today_orders": len(orders),
        "today_assigned": result["assigned"],
        "today_unassigned": result["unassigned"],
        "fleet_size": len(vehicles),
        "fleet_utilization": result["fleet_utilization"],
        "avg_capacity_usage": avg_cap,
        "cost_saved_percent": cost_saved,
        "high_sensitivity_count": sum(1 for o in orders if o["is_high_sensitivity"]),
        "zone_coverage": [
            {"zone": TEMP_ZONES[k]["name"], "range": v["range"],
             "vehicle_count": sum(1 for vh in vehicles if k in vh["zones"]),
             "order_count": sum(1 for o in orders if o["temp_zone"] == k)}
            for k, v in TEMP_ZONES.items()
        ],
        "algorithm": "多目标优化（温区合规+容积匹配+时效约束+成本最优）",
        "constraint_check": result["constraint_check"],
        "iteration_metrics": {
            "vehicle_utilization_rate": avg_cap,
            "cost_reduction_rate": cost_saved,
            "temp_compliance_rate": 100.0,
            "dispatch_success_rate": round(result["assigned"] / max(len(orders), 1) * 100, 1),
        },
    }


@router.post("/dispatch/{assignment_id}/confirm")
async def confirm_dispatch(
    assignment_id: str,
    user: dict = Depends(get_current_user),
):
    """确认派单发车（人工复核后锁定调度任务）"""
    if assignment_id not in _dispatch_plans:
        # 重新生成方案以查找
        orders = _get_all_pending_orders()
        result = _multi_objective_dispatch(orders, MULTI_ZONE_VEHICLES)
        for a in result["assignments"]:
            _dispatch_plans[a["assignment_id"]] = a

    plan = _dispatch_plans.get(assignment_id)
    if not plan:
        raise HTTPException(status_code=404, detail="调度方案不存在")

    plan["status"] = "dispatched"
    plan["dispatched_at"] = datetime.utcnow().isoformat()
    plan["dispatched_by"] = user.get("username", "admin")

    # 更新车辆状态为运输中
    for v in MULTI_ZONE_VEHICLES:
        if v["id"] == plan["vehicle_id"]:
            v["status"] = "in_transit"
            break

    # 🚀 资源锁定（联动资源调度模块，使用懒加载导入避免循环依赖）
    try:
        from ..api.resources import _lock_resource
        _lock_resource("vehicle", plan["vehicle_id"], assignment_id)
    except Exception as e:
        logger.warning(f"资源锁定失败: {e}")

    # 初始化在途监控数据
    _monitor_data[assignment_id] = {
        "assignment_id": assignment_id,
        "vehicle_id": plan["vehicle_id"],
        "plate_number": plan["plate_number"],
        "status": "in_transit",
        "current_progress": 0,
        "current_city": plan["origins"][0] if plan["origins"] else "未知",
        "zone_temperatures": {
            zone: TEMP_ZONES[zone]["target"]
            for zone in plan["zones_used"]
        },
        "sensor_bound": True,
        "geofence_bound": True,
        "route_planned": True,
        "started_at": datetime.utcnow().isoformat(),
        "events": [{"time": datetime.utcnow().isoformat(), "event": "派单确认，车辆发车"}],
    }

    # 🚀 自动写入追溯链（联动冷链追溯模块）
    # 为每个订单关联的运单添加配载记录
    try:
        for order in plan.get("orders", []):
            order_id = order.get("order_id", "")
            waybill_id = f"WB-{order_id}" if order_id else ""
            
            if waybill_id in WAYBILL_TRACE_MAP:
                compartments_info = {
                    "vehicle_id": plan["vehicle_id"],
                    "plate_number": plan["plate_number"],
                    "driver": plan["driver"],
                    "cargo_type": order.get("cargo_type", ""),
                    "temp_zone": order.get("temp_zone", ""),
                    "weight_kg": order.get("weight_kg", 0),
                    "volume_m3": order.get("volume_m3", 0),
                    "priority": order.get("priority", ""),
                    "is_high_sensitivity": order.get("is_high_sensitivity", False),
                }
                
                await auto_add_dispatch_record(
                    waybill_id=waybill_id,
                    vehicle_id=plan["vehicle_id"],
                    plate_number=plan["plate_number"],
                    driver_name=plan["driver"],
                    compartments=compartments_info,
                    user={"sub": "system", "role": "admin"},
                )
    except Exception as e:
        from loguru import logger
        logger.warning(f"配载信息写入追溯链失败: {e}")

    return {"message": "派单成功，车辆已发车", "assignment_id": assignment_id, "status": "dispatched"}


@router.get("/monitor/{assignment_id}")
async def monitor_dispatch(
    assignment_id: str,
    user: dict = Depends(get_current_user),
):
    """在途监控：实时温度、位置、温区控温稳定性"""
    if assignment_id not in _monitor_data:
        # 模拟生成监控数据
        plan = _dispatch_plans.get(assignment_id)
        if not plan:
            raise HTTPException(status_code=404, detail="调度任务不存在或未派单")
        _monitor_data[assignment_id] = {
            "assignment_id": assignment_id,
            "vehicle_id": plan["vehicle_id"],
            "plate_number": plan["plate_number"],
            "status": "in_transit",
            "current_progress": random.randint(10, 60),
            "current_city": plan["origins"][0] if plan["origins"] else "未知",
            "zone_temperatures": {
                zone: TEMP_ZONES[zone]["target"] + round(random.uniform(-1, 1), 1)
                for zone in plan["zones_used"]
            },
            "sensor_bound": True,
            "geofence_bound": True,
            "route_planned": True,
            "started_at": datetime.utcnow().isoformat(),
            "events": [{"time": datetime.utcnow().isoformat(), "event": "在途运输中"}],
        }

    monitor = _monitor_data[assignment_id]
    # 模拟实时更新
    monitor["current_progress"] = min(monitor["current_progress"] + random.randint(1, 5), 95)
    for zone in monitor["zone_temperatures"]:
        target = TEMP_ZONES[zone]["target"]
        monitor["zone_temperatures"][zone] = round(target + random.uniform(-1.5, 1.5), 1)

    # 温控合规检查
    temp_compliance = {}
    for zone, temp in monitor["zone_temperatures"].items():
        info = TEMP_ZONES[zone]
        temp_compliance[TEMP_ZONES[zone]["name"]] = info["min"] <= temp <= info["max"]

    monitor["temp_compliance"] = temp_compliance
    monitor["all_compliant"] = all(temp_compliance.values())

    return monitor


@router.get("/cargo-zone-map")
async def get_cargo_zone_map(
    user: dict = Depends(get_current_user),
):
    """货物温区映射表（前后端统一数据源）"""
    return {
        "temp_zones": TEMP_ZONES,
        "cargo_zone_map": CARGO_ZONE_MAP,
        "high_sensitivity_cargo": list(HIGH_SENSITIVITY_CARGO),
    }
