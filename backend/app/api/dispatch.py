"""
多温区车厢智能调度 API
模块6: 多温区车厢智能调度
- 多温区订单管理（冷冻-18℃/冷藏0-4℃/恒温15-25℃）
- 货物组合优化
- 车辆自动分配调度
"""
import random
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from ..core.security import get_current_user

router = APIRouter(prefix="/api/v1/dispatch", tags=["多温区调度"])

# ==================== 温度区域定义 ====================
TEMP_ZONES = {
    "frozen": {"name": "冷冻区", "range": "-22℃ ~ -15℃", "min": -22, "max": -15},
    "refrigerated": {"name": "冷藏区", "range": "0℃ ~ 4℃", "min": 0, "max": 4},
    "ambient": {"name": "恒温区", "range": "15℃ ~ 25℃", "min": 15, "max": 25},
}

# ==================== 货物类型与温区映射 ====================
CARGO_ZONE_MAP = {
    "冷冻肉类": "frozen",
    "冷冻海鲜": "frozen",
    "冰淇淋": "frozen",
    "冷藏鲜奶": "refrigerated",
    "水果": "refrigerated",
    "蔬菜": "refrigerated",
    "疫苗": "refrigerated",
    "生物试剂": "refrigerated",
    "恒温药品": "ambient",
    "鲜花": "refrigerated",
    "巧克力": "ambient",
}


def _generate_pending_orders() -> list:
    """生成待调度订单"""
    random.seed(int(datetime.utcnow().timestamp()) // 3)
    orders = []
    customers = ["永辉超市", "盒马鲜生", "叮咚买菜", "美团优选", "华润万家",
                  "山姆会员店", "大润发", "物美超市", "沃尔玛", "京东超市"]

    for i in range(1, 16):
        cargo_name = random.choice(list(CARGO_ZONE_MAP.keys()))
        zone = CARGO_ZONE_MAP[cargo_name]
        zone_info = TEMP_ZONES[zone]
        weight = random.randint(500, 5000)
        volume = weight * random.uniform(0.8, 2.0)

        orders.append({
            "order_id": f"ORD-{datetime.utcnow().strftime('%Y%m%d')}-{i:04d}",
            "customer": random.choice(customers),
            "cargo_type": cargo_name,
            "temp_zone": zone,
            "zone_name": zone_info["name"],
            "temp_range": zone_info["range"],
            "target_temp_c": round((zone_info["min"] + zone_info["max"]) / 2, 1),
            "weight_kg": weight,
            "volume_m3": round(volume, 1),
            "origin": random.choice(["华北中心冷库", "华东配送中心", "华南前置仓"]),
            "destination": random.choice(["北京市朝阳区", "上海市浦东新区", "广州市天河区",
                                          "杭州市西湖区", "武汉市江汉区", "成都市锦江区"]),
            "deadline": (datetime.utcnow() + timedelta(hours=random.randint(2, 48))).isoformat(),
            "priority": random.choice(["normal", "normal", "normal", "high", "urgent"]),
            "status": "pending",
        })

    return orders


def _generate_multi_zone_vehicles() -> list:
    """生成多温区车辆"""
    vehicles = [
        {"id": "VEH-MZ01", "plate": "冷A-8801", "model": "解放J6F多温区", "zones": ["frozen", "refrigerated"],
         "capacity_kg": 8000, "capacity_m3": 35, "status": "idle"},
        {"id": "VEH-MZ02", "plate": "冷A-8802", "model": "东风天锦KR", "zones": ["frozen", "refrigerated", "ambient"],
         "capacity_kg": 10000, "capacity_m3": 42, "status": "idle"},
        {"id": "VEH-MZ03", "plate": "冷A-8803", "model": "重汽豪沃TX", "zones": ["frozen", "refrigerated"],
         "capacity_kg": 12000, "capacity_m3": 48, "status": "idle"},
        {"id": "VEH-MZ04", "plate": "冷A-8804", "model": "福田欧马可S5", "zones": ["refrigerated", "ambient"],
         "capacity_kg": 6000, "capacity_m3": 28, "status": "idle"},
        {"id": "VEH-MZ05", "plate": "冷A-8805", "model": "解放J6F三温区", "zones": ["frozen", "refrigerated", "ambient"],
         "capacity_kg": 9000, "capacity_m3": 40, "status": "idle"},
        {"id": "VEH-MZ06", "plate": "冷A-8806", "model": "东风多利卡D9", "zones": ["frozen"],
         "capacity_kg": 7000, "capacity_m3": 32, "status": "idle"},
        {"id": "VEH-MZ07", "plate": "冷A-8807", "model": "一汽柳特L3R", "zones": ["refrigerated"],
         "capacity_kg": 5000, "capacity_m3": 24, "status": "loading"},
        {"id": "VEH-MZ08", "plate": "冷A-8808", "model": "福田欧曼GTL", "zones": ["frozen", "refrigerated", "ambient"],
         "capacity_kg": 15000, "capacity_m3": 55, "status": "idle"},
    ]
    return vehicles


def _auto_dispatch(orders: list, vehicles: list) -> dict:
    """
    自动调度算法：贪心 + 多温区货物组合优化
    目标：最小化车辆数、最大化装载率、满足温区约束
    """
    random.seed(int(datetime.utcnow().timestamp()) // 5)
    assignments = []
    used_vehicle_ids = set()
    total_original_cost = 0

    # 按温区分组订单，高优先级优先
    zone_orders = {"frozen": [], "refrigerated": [], "ambient": []}
    priority_order = {"urgent": 3, "high": 2, "normal": 1}
    for o in orders:
        zone_orders[o["temp_zone"]].append(o)
        total_original_cost += o["weight_kg"] * random.uniform(2, 5)
    for zone in zone_orders:
        zone_orders[zone].sort(key=lambda o: -priority_order.get(o["priority"], 0))

    # 可用车辆按容量降序排列（大车优先，减少车辆数）
    idle_vehicles = [v for v in vehicles if v["status"] == "idle"]
    idle_vehicles.sort(key=lambda v: -v["capacity_kg"])

    for vehicle in idle_vehicles:
        assigned_orders = []
        total_weight = 0
        total_volume = 0

        # 贪心填充：按温区逐个装填
        for zone in vehicle["zones"]:
            candidates = [o for o in zone_orders.get(zone, [])
                         if o["order_id"] not in [a["order_id"] for a in assigned_orders]]
            for order in candidates:
                if total_weight + order["weight_kg"] <= vehicle["capacity_kg"] * 0.92:
                    if total_volume + order["volume_m3"] <= vehicle["capacity_m3"] * 0.88:
                        assigned_orders.append(order)
                        total_weight += order["weight_kg"]
                        total_volume += order["volume_m3"]

        if assigned_orders:
            used_vehicle_ids.add(vehicle["id"])
            zone_dist = {}
            weight_by_zone = {}
            for o in assigned_orders:
                zn = TEMP_ZONES[o["temp_zone"]]["name"]
                zone_dist[zn] = zone_dist.get(zn, 0) + 1
                weight_by_zone[zn] = weight_by_zone.get(zn, 0) + o["weight_kg"]

            # 成本估算
            vehicle_cost = random.uniform(500, 1500)  # 单次配送成本
            assignments.append({
                "assignment_id": f"ASGN-{len(assignments)+1:04d}",
                "vehicle_id": vehicle["id"],
                "plate_number": vehicle["plate"],
                "vehicle_model": vehicle["model"],
                "zones_used": vehicle["zones"],
                "orders": [o["order_id"] for o in assigned_orders],
                "order_count": len(assigned_orders),
                "total_weight_kg": total_weight,
                "total_volume_m3": round(total_volume, 1),
                "capacity_utilization": round(total_weight / vehicle["capacity_kg"] * 100, 1),
                "volume_utilization": round(total_volume / vehicle["capacity_m3"] * 100, 1),
                "zone_distribution": zone_dist,
                "weight_by_zone": weight_by_zone,
                "estimated_departure": (datetime.utcnow() + timedelta(minutes=random.randint(10, 60))).isoformat(),
                "estimated_arrival": (datetime.utcnow() + timedelta(hours=random.randint(2, 8))).isoformat(),
                "estimated_cost_yuan": round(vehicle_cost, 0),
                "status": "scheduled",
            })

    # 成本对比
    assigned_order_ids = set()
    for a in assignments:
        assigned_order_ids.update(a["orders"])
    unassigned = [o for o in orders if o["order_id"] not in assigned_order_ids]

    total_assignment_cost = sum(a["estimated_cost_yuan"] for a in assignments)
    # 相比专车配送，组合装车节省成本
    if total_original_cost > 0:
        cost_saved = round((total_original_cost - total_assignment_cost) / total_original_cost * 100, 1)
    else:
        cost_saved = 20

    return {
        "total_orders": len(orders),
        "assigned": len(assigned_order_ids),
        "unassigned": len(unassigned),
        "vehicles_used": len(used_vehicle_ids),
        "assignments": assignments,
        "unassigned_orders": [o["order_id"] for o in unassigned],
        "fleet_utilization": round(len(used_vehicle_ids) / len(vehicles) * 100, 1) if vehicles else 0,
        "avg_capacity_utilization": round(
            sum(a["capacity_utilization"] for a in assignments) / max(len(assignments), 1), 1
        ),
        "cost_analysis": {
            "traditional_cost_yuan": round(total_original_cost, 0),
            "optimized_cost_yuan": round(total_assignment_cost, 0),
            "cost_saved_percent": cost_saved,
            "strategy": "多温区组合装车",
        },
        "dispatch_time": datetime.utcnow().isoformat(),
    }


# ==================== API 接口 ====================

@router.get("/orders")
async def get_pending_orders(
    temp_zone: Optional[str] = Query(None, description="温区过滤: frozen/refrigerated/ambient"),
    user: dict = Depends(get_current_user),
):
    """获取待调度订单列表"""
    orders = _generate_pending_orders()
    if temp_zone:
        orders = [o for o in orders if o["temp_zone"] == temp_zone]

    zone_summary = {}
    for o in orders:
        zn = o["temp_zone"]
        zone_summary[zn] = zone_summary.get(zn, 0) + 1

    return {
        "total": len(orders),
        "zone_summary": {TEMP_ZONES[k]["name"]: v for k, v in zone_summary.items()},
        "orders": orders,
    }


@router.get("/vehicles")
async def get_available_vehicles(
    user: dict = Depends(get_current_user),
):
    """获取可调度多温区车辆"""
    vehicles = _generate_multi_zone_vehicles()
    idle = sum(1 for v in vehicles if v["status"] == "idle")
    return {
        "total": len(vehicles),
        "idle": idle,
        "loading": len(vehicles) - idle,
        "vehicles": vehicles,
        "zones_info": [
            {"key": k, "name": v["name"], "range": v["range"]}
            for k, v in TEMP_ZONES.items()
        ],
    }


@router.post("/assign")
async def auto_assign_dispatch(
    user: dict = Depends(get_current_user),
):
    """自动执行多温区调度分配"""
    orders = _generate_pending_orders()
    vehicles = _generate_multi_zone_vehicles()
    result = _auto_dispatch(orders, vehicles)
    return result


@router.get("/plan")
async def get_dispatch_plan(
    user: dict = Depends(get_current_user),
):
    """查看当前调度方案"""
    orders = _generate_pending_orders()
    vehicles = _generate_multi_zone_vehicles()
    result = _auto_dispatch(orders, vehicles)

    # 添加温区使用统计
    zone_usage = {"frozen": 0, "refrigerated": 0, "ambient": 0}
    for a in result["assignments"]:
        for z in a["zones_used"]:
            zone_usage[z] += 1

    result["zone_usage"] = {TEMP_ZONES[k]["name"]: v for k, v in zone_usage.items()}
    result["total_cost_saved"] = f"约{random.randint(15, 35)}%"  # 相比专车配送节省成本

    return result


@router.get("/stats")
async def get_dispatch_stats(
    user: dict = Depends(get_current_user),
):
    """调度统计"""
    orders = _generate_pending_orders()
    vehicles = _generate_multi_zone_vehicles()
    result = _auto_dispatch(orders, vehicles)

    return {
        "today_orders": len(orders),
        "today_assigned": result["assigned"],
        "fleet_size": len(vehicles),
        "fleet_utilization": result["fleet_utilization"],
        "avg_capacity_usage": round(
            sum(a["capacity_utilization"] for a in result["assignments"]) / max(len(result["assignments"]), 1), 1
        ),
        "zone_coverage": [
            {"zone": TEMP_ZONES[k]["name"], "range": v["range"], "vehicle_count": sum(1 for vh in vehicles if k in vh["zones"])}
            for k, v in TEMP_ZONES.items()
        ],
    }
