"""
冷链资源智能调度 API
模块10: 冷链资源智能调度
- 冷库库位管理
- 冷藏车辆资源池
- 蓄冷板/冰排管理
- 资源利用统计
"""
import random
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..core.security import get_current_user

router = APIRouter(prefix="/api/v1/resources", tags=["资源调度"])

# ==================== 模拟冷库数据 ====================

WAREHOUSES = [
    {"id": "WH-BJ-01", "name": "华北中心冷库", "location": "北京市大兴区", "lat": 39.72, "lng": 116.33,
     "total_slots": 500, "frozen_slots": 200, "refrigerated_slots": 200, "ambient_slots": 100, "status": "active"},
    {"id": "WH-SH-01", "name": "华东配送中心", "location": "上海市嘉定区", "lat": 31.38, "lng": 121.25,
     "total_slots": 800, "frozen_slots": 350, "refrigerated_slots": 300, "ambient_slots": 150, "status": "active"},
    {"id": "WH-GZ-01", "name": "华南前置仓", "location": "广州市白云区", "lat": 23.17, "lng": 113.27,
     "total_slots": 400, "frozen_slots": 180, "refrigerated_slots": 150, "ambient_slots": 70, "status": "active"},
    {"id": "WH-CD-01", "name": "西南冷链基地", "location": "成都市龙泉驿区", "lat": 30.57, "lng": 104.27,
     "total_slots": 600, "frozen_slots": 250, "refrigerated_slots": 250, "ambient_slots": 100, "status": "active"},
    {"id": "WH-WH-01", "name": "华中分拨中心", "location": "武汉市东西湖区", "lat": 30.62, "lng": 114.13,
     "total_slots": 450, "frozen_slots": 200, "refrigerated_slots": 180, "ambient_slots": 70, "status": "active"},
    {"id": "WH-XA-01", "name": "西北冷链中转仓", "location": "西安市未央区", "lat": 34.34, "lng": 108.94,
     "total_slots": 300, "frozen_slots": 120, "refrigerated_slots": 120, "ambient_slots": 60, "status": "active"},
]

FLEET_VEHICLES = [
    {"id": "VH-001", "plate": "冷A-1001", "type": "4.2m冷藏车", "capacity_m3": 18, "capacity_kg": 3000, "temp_range": "-22℃ ~ 4℃",
     "fuel_type": "柴油", "location": "北京", "status": "available"},
    {"id": "VH-002", "plate": "冷A-1002", "type": "6.8m冷藏车", "capacity_m3": 35, "capacity_kg": 7000, "temp_range": "-22℃ ~ 4℃",
     "fuel_type": "柴油", "location": "上海", "status": "available"},
    {"id": "VH-003", "plate": "冷A-1003", "type": "9.6m冷藏车", "capacity_m3": 55, "capacity_kg": 12000, "temp_range": "-25℃ ~ 4℃",
     "fuel_type": "柴油", "location": "广州", "status": "in_use"},
    {"id": "VH-004", "plate": "冷A-1004", "type": "4.2m电动冷藏", "capacity_m3": 16, "capacity_kg": 2500, "temp_range": "-18℃ ~ 4℃",
     "fuel_type": "电动", "location": "北京", "status": "charging"},
    {"id": "VH-005", "plate": "冷A-1005", "type": "9.6m冷藏车", "capacity_m3": 55, "capacity_kg": 12000, "temp_range": "-25℃ ~ 4℃",
     "fuel_type": "柴油", "location": "成都", "status": "available"},
    {"id": "VH-006", "plate": "冷A-1006", "type": "6.8m冷藏车", "capacity_m3": 35, "capacity_kg": 7000, "temp_range": "-22℃ ~ 4℃",
     "fuel_type": "柴油", "location": "武汉", "status": "available"},
    {"id": "VH-007", "plate": "冷A-1007", "type": "4.2m冷藏车", "capacity_m3": 18, "capacity_kg": 3000, "temp_range": "-22℃ ~ 4℃",
     "fuel_type": "柴油", "location": "西安", "status": "maintenance"},
    {"id": "VH-008", "plate": "冷A-1008", "type": "13m半挂冷藏", "capacity_m3": 85, "capacity_kg": 25000, "temp_range": "-25℃ ~ 4℃",
     "fuel_type": "柴油", "location": "上海", "status": "available"},
]

COLD_PLATES = [
    {"id": "CP-001", "name": "蓄冷板A型", "type": "相变材料", "phase_change_temp_c": -21, "duration_h": 8, "stock": 450, "in_use": 120},
    {"id": "CP-002", "name": "蓄冷板B型", "type": "相变材料", "phase_change_temp_c": 0, "duration_h": 12, "stock": 380, "in_use": 95},
    {"id": "CP-003", "name": "冰排C型", "type": "水冰", "phase_change_temp_c": 0, "duration_h": 6, "stock": 600, "in_use": 200},
    {"id": "CP-004", "name": "干冰盒D型", "type": "干冰", "phase_change_temp_c": -78, "duration_h": 4, "stock": 150, "in_use": 45},
]


def _get_warehouse_utilization(warehouse_id: str) -> dict:
    """计算冷库利用率"""
    random.seed(hash(f"{warehouse_id}{datetime.utcnow().hour}") % 10000)
    wh = next((w for w in WAREHOUSES if w["id"] == warehouse_id), WAREHOUSES[0])
    frozen_used = random.randint(50, wh["frozen_slots"])
    refrig_used = random.randint(50, wh["refrigerated_slots"])
    ambient_used = random.randint(30, wh["ambient_slots"])

    return {
        "warehouse_id": wh["id"],
        "warehouse_name": wh["name"],
        "location": wh["location"],
        "slots": {
            "frozen": {"total": wh["frozen_slots"], "used": frozen_used, "rate": round(frozen_used / wh["frozen_slots"] * 100, 1)},
            "refrigerated": {"total": wh["refrigerated_slots"], "used": refrig_used, "rate": round(refrig_used / wh["refrigerated_slots"] * 100, 1)},
            "ambient": {"total": wh["ambient_slots"], "used": ambient_used, "rate": round(ambient_used / wh["ambient_slots"] * 100, 1)},
        },
        "total_used": frozen_used + refrig_used + ambient_used,
        "total_slots": wh["total_slots"],
        "overall_utilization": round((frozen_used + refrig_used + ambient_used) / wh["total_slots"] * 100, 1),
        "updated_at": datetime.utcnow().isoformat(),
    }


# ==================== API 接口 ====================

@router.get("/warehouses")
async def get_warehouses(
    user: dict = Depends(get_current_user),
):
    """获取冷库列表及利用率"""
    result = []
    total_used = 0
    total_slots = 0

    for wh in WAREHOUSES:
        util = _get_warehouse_utilization(wh["id"])
        result.append(util)
        total_used += util["total_used"]
        total_slots += util["total_slots"]

    return {
        "total_warehouses": len(WAREHOUSES),
        "total_slots": total_slots,
        "total_used": total_used,
        "overall_utilization": round(total_used / total_slots * 100, 1) if total_slots > 0 else 0,
        "warehouses": result,
    }


@router.get("/warehouses/{warehouse_id}")
async def get_warehouse_detail(
    warehouse_id: str,
    user: dict = Depends(get_current_user),
):
    """获取单个冷库详情"""
    wh = next((w for w in WAREHOUSES if w["id"] == warehouse_id), None)
    if not wh:
        raise HTTPException(status_code=404, detail="冷库不存在")

    util = _get_warehouse_utilization(warehouse_id)

    # 生成入库出库记录
    random.seed(hash(warehouse_id) % 10000)
    now = datetime.utcnow()
    recent_activities = []
    for i in range(8):
        recent_activities.append({
            "time": (now - timedelta(hours=random.randint(1, 72))).isoformat(),
            "type": random.choice(["入库", "出库", "移库"]),
            "batch_id": f"BATCH-{now.strftime('%Y%m')}-{random.randint(1, 50):04d}",
            "product": random.choice(["苹果", "草莓", "牛肉", "三文鱼", "鲜奶", "菠菜"]),
            "quantity_kg": random.randint(200, 3000),
            "zone": random.choice(["冷冻区", "冷藏区", "恒温区"]),
        })

    util["recent_activities"] = sorted(recent_activities, key=lambda x: x["time"], reverse=True)
    util["temperature_monitoring"] = {
        "frozen_avg": round(random.uniform(-21, -16), 1),
        "refrigerated_avg": round(random.uniform(0, 4), 1),
        "ambient_avg": round(random.uniform(18, 24), 1),
    }
    util["alarms_today"] = random.randint(0, 3)
    return util


@router.get("/vehicles")
async def get_fleet_vehicles(
    status: Optional[str] = Query(None, description="状态过滤: available/in_use/charging/maintenance"),
    user: dict = Depends(get_current_user),
):
    """获取车队车辆资源"""
    vehicles = FLEET_VEHICLES
    if status:
        vehicles = [v for v in vehicles if v["status"] == status]

    status_counts = {}
    for v in FLEET_VEHICLES:
        s = v["status"]
        status_counts[s] = status_counts.get(s, 0) + 1

    return {
        "total": len(FLEET_VEHICLES),
        "status_summary": {
            "available": status_counts.get("available", 0),
            "in_use": status_counts.get("in_use", 0),
            "charging": status_counts.get("charging", 0),
            "maintenance": status_counts.get("maintenance", 0),
        },
        "vehicles": vehicles,
    }


@router.get("/cold-plates")
async def get_cold_plates(
    user: dict = Depends(get_current_user),
):
    """获取蓄冷板/冰排库存"""
    total_stock = sum(cp["stock"] for cp in COLD_PLATES)
    total_in_use = sum(cp["in_use"] for cp in COLD_PLATES)

    return {
        "total_types": len(COLD_PLATES),
        "total_stock": total_stock,
        "total_in_use": total_in_use,
        "utilization_rate": round(total_in_use / (total_stock + total_in_use) * 100, 1),
        "items": COLD_PLATES,
    }


@router.get("/utilization")
async def get_resource_utilization(
    user: dict = Depends(get_current_user),
):
    """综合资源利用率统计"""
    # 冷库利用率
    wh_utils = [_get_warehouse_utilization(wh["id"]) for wh in WAREHOUSES]
    avg_wh_util = round(sum(w["overall_utilization"] for w in wh_utils) / len(wh_utils), 1)

    # 车辆利用率
    vehicles = FLEET_VEHICLES
    total_vehicles = len(vehicles)
    in_use = sum(1 for v in vehicles if v["status"] == "in_use")
    available = sum(1 for v in vehicles if v["status"] == "available")
    fleet_util = round(in_use / total_vehicles * 100, 1)

    # 蓄冷板利用率
    total_plate = sum(cp["stock"] for cp in COLD_PLATES)
    in_use_plate = sum(cp["in_use"] for cp in COLD_PLATES)
    plate_util = round(in_use_plate / (total_plate + in_use_plate) * 100, 1)

    # 模拟能耗统计
    now = datetime.utcnow()
    energy_trend = []
    for i in range(24):
        hour = (now - timedelta(hours=23 - i)).hour
        energy_trend.append({
            "hour": f"{hour:02d}:00",
            "power_kwh": round(random.uniform(180, 350), 1),
        })

    return {
        "cold_storage": {
            "avg_utilization": avg_wh_util,
            "total_slots": sum(w["total_slots"] for w in WAREHOUSES),
            "details": [{"name": w["name"], "utilization": w["overall_utilization"]} for w in wh_utils],
        },
        "fleet": {
            "utilization": fleet_util,
            "total": total_vehicles,
            "in_use": in_use,
            "available": available,
        },
        "cold_plates": {
            "utilization": plate_util,
            "total": total_plate,
            "in_use": in_use_plate,
        },
        "energy": {
            "total_kwh_today": round(random.uniform(4000, 6000), 1),
            "avg_power_kw": round(random.uniform(200, 280), 1),
            "trend_24h": energy_trend,
        },
        "updated_at": now.isoformat(),
    }


@router.post("/allocate")
async def allocate_resource(
    resource_type: str = Query(..., description="资源类型: warehouse_slot/vehicle/cold_plate"),
    warehouse_id: Optional[str] = Query(None),
    user: dict = Depends(get_current_user),
):
    """模拟资源分配"""
    if resource_type == "warehouse_slot":
        wh = next((w for w in WAREHOUSES if w["id"] == warehouse_id), None)
        if not wh:
            raise HTTPException(status_code=404, detail="冷库不存在")
        util = _get_warehouse_utilization(warehouse_id)
        slot = random.choice(["frozen", "refrigerated", "ambient"])
        return {
            "status": "success",
            "message": f"已分配{warehouse_id} {slot}区库位",
            "assigned_slot": slot,
            "remaining_slots": util["slots"][slot]["total"] - util["slots"][slot]["used"],
        }

    elif resource_type == "vehicle":
        available = [v for v in FLEET_VEHICLES if v["status"] == "available"]
        if not available:
            raise HTTPException(status_code=400, detail="无可用车辆")
        assigned = random.choice(available)
        return {
            "status": "success",
            "message": f"已分配车辆 {assigned['plate']} ({assigned['type']})",
            "assigned_vehicle": assigned,
        }

    elif resource_type == "cold_plate":
        cp = random.choice(COLD_PLATES)
        return {
            "status": "success",
            "message": f"已分配{cp['name']} ({cp['type']}) x 10块",
            "assigned_plate": cp["name"],
            "remaining_stock": cp["stock"] - cp["in_use"] - 10,
        }
    else:
        raise HTTPException(status_code=400, detail=f"不支持的资源类型: {resource_type}")
