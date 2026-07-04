"""
冷链资源智能调度 API
模块10: 冷链资源智能调度
使用统一世界状态，确保数据跨页面联通
"""
import random
import math
import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..core.security import get_current_user
from ..services.world_state import get_world_state

logger = logging.getLogger(__name__)

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
    """获取冷库列表及利用率 - 来自统一世界状态"""
    ws = get_world_state()
    result = []
    total_used = 0
    total_slots = 0

    for wh in ws["warehouses"]:
        result.append({
            "warehouse_id": wh["id"],
            "warehouse_name": wh["name"],
            "location": wh["location"],
            "slots": {
                "frozen": {"total": wh["frozen_slots"], "used": wh["frozen_used"], "rate": wh["frozen_util"]},
                "refrigerated": {"total": wh["refrigerated_slots"], "used": wh["refrigerated_used"], "rate": wh["refrigerated_util"]},
                "ambient": {"total": wh["ambient_slots"], "used": wh["ambient_used"], "rate": wh["ambient_util"]},
            },
            "total_used": wh["total_used"],
            "total_slots": wh["total_slots"],
            "overall_utilization": wh["utilization"],
            "updated_at": ws["timestamp"],
        })
        total_used += wh["total_used"]
        total_slots += wh["total_slots"]

    return {
        "total_warehouses": len(ws["warehouses"]),
        "total_slots": total_slots,
        "total_used": total_used,
        "overall_utilization": round(total_used / total_slots * 100, 1) if total_slots > 0 else 0,
        "warehouses": result,
        "data_source": "unified",
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
    """综合资源利用率统计 - 来自统一世界状态"""
    ws = get_world_state()

    # 冷库利用率
    avg_wh_util = round(sum(w["utilization"] for w in ws["warehouses"]) / max(len(ws["warehouses"]), 1), 1)

    # 车辆利用率
    vehicles = FLEET_VEHICLES
    total_vehicles = len(vehicles)
    in_use = len(ws["vehicles"])
    fleet_util = round(in_use / total_vehicles * 100, 1)

    # 蓄冷板利用率
    total_plate = sum(cp["stock"] for cp in COLD_PLATES)
    in_use_plate = sum(cp["in_use"] for cp in COLD_PLATES)
    plate_util = round(in_use_plate / (total_plate + in_use_plate) * 100, 1)

    # 能耗统计（基于车辆数据）
    now = datetime.utcnow()
    energy_trend = []
    for i in range(24):
        hour = (now - timedelta(hours=23 - i)).hour
        base = 180 + 80 * math.sin((hour - 6) * math.pi / 12)
        energy_trend.append({
            "hour": f"{hour:02d}:00",
            "power_kwh": round(base + random.uniform(-20, 30), 1),
        })

    return {
        "cold_storage": {
            "avg_utilization": avg_wh_util,
            "total_slots": sum(w["total_slots"] for w in ws["warehouses"]),
            "details": [{"name": w["name"], "utilization": w["utilization"]} for w in ws["warehouses"]],
        },
        "fleet": {
            "utilization": fleet_util,
            "total": total_vehicles,
            "in_use": in_use,
            "available": total_vehicles - in_use,
        },
        "cold_plates": {
            "utilization": plate_util,
            "total": total_plate,
            "in_use": in_use_plate,
        },
        "energy": {
            "total_kwh_today": round(sum(e["power_kwh"] for e in energy_trend), 1),
            "avg_power_kw": round(sum(e["power_kwh"] for e in energy_trend) / 24, 1),
            "trend_24h": energy_trend,
        },
        "updated_at": now.isoformat(),
        "data_source": "unified",
    }


@router.post("/allocate")
async def allocate_resource(
    resource_type: str = Query(..., description="资源类型: warehouse_slot/vehicle/cold_plate"),
    warehouse_id: Optional[str] = Query(None),
    quantity: int = 1,
    user: dict = Depends(get_current_user),
):
    """智能资源分配（基于利用率 + 距离优先）"""
    if resource_type == "warehouse_slot":
        wh = next((w for w in WAREHOUSES if w["id"] == warehouse_id), None)
        if not wh:
            # 自动选择利用率最低的冷库
            wh_utils = [(w, _get_warehouse_utilization(w["id"])) for w in WAREHOUSES]
            wh_utils.sort(key=lambda x: x[1]["overall_utilization"])
            wh, util = wh_utils[0]
        else:
            util = _get_warehouse_utilization(warehouse_id)

        # 选择最空闲的温区
        slots = util["slots"]
        best_slot = min(slots.keys(), key=lambda s: slots[s]["rate"])
        remaining = slots[best_slot]["total"] - slots[best_slot]["used"]
        if remaining < quantity * 5:
            raise HTTPException(status_code=400, detail=f"{best_slot}区剩余库位不足")

        return {
            "status": "success",
            "message": f"已分配{wh['name']} {best_slot}区 {quantity * 5}个库位",
            "warehouse": wh["name"],
            "assigned_zone": best_slot,
            "quantity": quantity * 5,
            "remaining_slots": remaining - quantity * 5,
            "warehouse_utilization": util["overall_utilization"],
        }

    elif resource_type == "vehicle":
        available = [v for v in FLEET_VEHICLES if v["status"] == "available"]
        if not available:
            raise HTTPException(status_code=400, detail="无可用车辆")
        # 按容量优先分配
        available.sort(key=lambda v: -v["capacity_kg"])
        assigned = available[0]
        return {
            "status": "success",
            "message": f"已分配车辆 {assigned['plate']} ({assigned['type']}, {assigned['capacity_kg']}kg)",
            "assigned_vehicle": assigned,
            "remaining_available": len(available) - 1,
        }

    elif resource_type == "cold_plate":
        # 根据温区需求分配
        demand_temp = -18 if random.random() < 0.3 else 0  # 模拟温区需求
        matching = [cp for cp in COLD_PLATES if abs(cp["phase_change_temp_c"] - demand_temp) < 10]
        if not matching:
            cp = random.choice(COLD_PLATES)
        else:
            cp = matching[0]
        allocate_qty = min(quantity * 10, cp["stock"] - cp["in_use"])
        if allocate_qty <= 0:
            raise HTTPException(status_code=400, detail=f"{cp['name']}库存不足")
        return {
            "status": "success",
            "message": f"已分配{cp['name']} ({cp['type']}) x {allocate_qty}块",
            "assigned_plate": cp["name"],
            "quantity": allocate_qty,
            "demand_temp_c": demand_temp,
            "remaining_stock": cp["stock"] - cp["in_use"] - allocate_qty,
        }
    else:
        raise HTTPException(status_code=400, detail=f"不支持的资源类型: {resource_type}")


@router.get("/forecast")
async def get_resource_forecast(
    hours_ahead: int = 24,
    user: dict = Depends(get_current_user),
):
    """冷链资源需求预测（未来24小时）"""
    random.seed(datetime.utcnow().hour)
    forecast = []
    now = datetime.utcnow()
    for i in range(hours_ahead):
        hour = (now + timedelta(hours=i)).hour
        # 模拟昼夜需求波动（三角函数）
        base_demand = 60 + 20 * math.sin((hour - 6) * math.pi / 12)
        forecast.append({
            "time": (now + timedelta(hours=i)).strftime("%H:00"),
            "warehouse_demand": round(base_demand + random.uniform(-5, 10), 0),
            "vehicle_demand": round(base_demand * 0.3 + random.uniform(-2, 5), 0),
            "cold_plate_demand": round(base_demand * 0.5 + random.uniform(-3, 8), 0),
        })

    total_wh_capacity = sum(w["total_slots"] for w in WAREHOUSES)
    total_vehicles = len(FLEET_VEHICLES)
    total_plates = sum(cp["stock"] for cp in COLD_PLATES)

    return {
        "forecast_hours": hours_ahead,
        "total_warehouse_capacity": total_wh_capacity,
        "total_vehicle_fleet": total_vehicles,
        "total_cold_plate_stock": total_plates,
        "peak_demand_hour": max(forecast, key=lambda f: f["warehouse_demand"])["time"],
        "forecast_data": forecast,
    }


# ==================== 仓库入库/出库/盘点 API（仓管功能） ====================

# 内存存储库存记录
warehouse_inventory = []
_inv_counter = 0


def _init_inventory():
    """初始化仓库库存模拟数据"""
    global warehouse_inventory, _inv_counter
    if warehouse_inventory:
        return
    products = [
        ("冷冻牛肉", "frozen", "肉类", -20), ("冷冻海鲜", "frozen", "海鲜", -22),
        ("冰淇淋", "frozen", "乳制品", -18), ("速冻水饺", "frozen", "面食", -18),
        ("鲜牛奶", "refrigerated", "乳制品", 2), ("草莓", "refrigerated", "水果", 1),
        ("三文鱼", "refrigerated", "海鲜", 0), ("鲜切花", "refrigerated", "花卉", 3),
        ("苹果", "ambient", "水果", 18), ("土豆", "ambient", "蔬菜", 16),
        ("巧克力", "ambient", "零食", 20), ("药品", "ambient", "医药", 20),
    ]
    now = datetime.utcnow()
    for i, (name, zone, cat, temp) in enumerate(products):
        for wh in WAREHOUSES:
            _inv_counter += 1
            warehouse_inventory.append({
                "id": f"INV-{_inv_counter:04d}",
                "warehouse_id": wh["id"],
                "warehouse_name": wh["name"],
                "product_name": name,
                "category": cat,
                "zone": zone,
                "zone_label": {"frozen": "冷冻区", "refrigerated": "冷藏区", "ambient": "恒温区"}[zone],
                "target_temp_c": temp,
                "quantity_kg": random.randint(500, 8000),
                "unit": "kg",
                "shelf_life_days": random.randint(5, 180),
                "production_date": (now - timedelta(days=random.randint(1, 60))).strftime("%Y-%m-%d"),
                "expiry_date": (now + timedelta(days=random.randint(3, 120))).strftime("%Y-%m-%d"),
                "status": "normal",  # normal / near_expiry / expired
                "last_updated": now.isoformat(),
            })

    # 标记部分临近过期
    for item in warehouse_inventory[:6]:
        item["status"] = "near_expiry"
        item["expiry_date"] = (now + timedelta(days=random.randint(1, 5))).strftime("%Y-%m-%d")

_init_inventory()


@router.get("/warehouse-inventory")
async def get_warehouse_inventory(
    warehouse_id: str = Query(default=""),
    zone: str = Query(default=""),
    status: str = Query(default=""),
    keyword: str = Query(default=""),
    user: dict = Depends(get_current_user),
):
    """获取仓库库存列表 - 支持按仓库/温区/状态/关键词筛选"""
    items = warehouse_inventory
    if warehouse_id:
        items = [i for i in items if i["warehouse_id"] == warehouse_id]
    if zone:
        items = [i for i in items if i["zone"] == zone]
    if status:
        items = [i for i in items if i["status"] == status]
    if keyword:
        kw = keyword.lower()
        items = [i for i in items if kw in i["product_name"].lower() or kw in i["category"].lower()]

    # 统计
    total_qty = sum(i["quantity_kg"] for i in items)
    normal_count = sum(1 for i in items if i["status"] == "normal")
    near_expiry_count = sum(1 for i in items if i["status"] == "near_expiry")
    expired_count = sum(1 for i in items if i["status"] == "expired")

    return {
        "code": 200,
        "message": "查询成功",
        "data": {
            "total": len(items),
            "total_quantity_kg": total_qty,
            "stats": {
                "normal": normal_count,
                "near_expiry": near_expiry_count,
                "expired": expired_count,
            },
            "items": sorted(items, key=lambda x: x["last_updated"], reverse=True),
        },
    }


class StockOperation(BaseModel):
    warehouse_id: str
    product_name: str
    zone: str  # frozen/refrigerated/ambient
    category: str = ""
    quantity_kg: float
    target_temp_c: float = 0
    shelf_life_days: int = 30
    notes: str = ""


@router.post("/warehouse-inbound")
async def warehouse_inbound(
    body: StockOperation,
    user: dict = Depends(get_current_user),
):
    """仓库入库操作"""
    global _inv_counter
    wh = next((w for w in WAREHOUSES if w["id"] == body.warehouse_id), None)
    if not wh:
        return JSONResponse(status_code=404, content={"code": 404, "message": "冷库不存在"})

    now = datetime.utcnow()
    zone_label = {"frozen": "冷冻区", "refrigerated": "冷藏区", "ambient": "恒温区"}.get(body.zone, body.zone)
    _inv_counter += 1

    item = {
        "id": f"INV-{_inv_counter:04d}",
        "warehouse_id": body.warehouse_id,
        "warehouse_name": wh["name"],
        "product_name": body.product_name,
        "category": body.category or "其他",
        "zone": body.zone,
        "zone_label": zone_label,
        "target_temp_c": body.target_temp_c,
        "quantity_kg": body.quantity_kg,
        "unit": "kg",
        "shelf_life_days": body.shelf_life_days,
        "production_date": now.strftime("%Y-%m-%d"),
        "expiry_date": (now + timedelta(days=body.shelf_life_days)).strftime("%Y-%m-%d"),
        "status": "normal",
        "last_updated": now.isoformat(),
    }
    warehouse_inventory.append(item)
    logger.info(f"入库: {body.product_name} x {body.quantity_kg}kg → {wh['name']} {zone_label}")

    return {
        "code": 200,
        "message": f"入库成功：{body.product_name} {body.quantity_kg}kg → {wh['name']} {zone_label}",
        "data": item,
    }


@router.post("/warehouse-outbound")
async def warehouse_outbound(
    inventory_id: str = Query(...),
    quantity_kg: float = Query(...),
    notes: str = Query(default=""),
    user: dict = Depends(get_current_user),
):
    """仓库出库操作"""
    target = None
    for item in warehouse_inventory:
        if item["id"] == inventory_id:
            target = item
            break
    if not target:
        return JSONResponse(status_code=404, content={"code": 404, "message": "库存记录不存在"})

    if quantity_kg > target["quantity_kg"]:
        return JSONResponse(status_code=400, content={"code": 400, "message": f"库存不足，当前仅剩 {target['quantity_kg']}kg"})

    target["quantity_kg"] -= quantity_kg
    target["last_updated"] = datetime.utcnow().isoformat()

    if target["quantity_kg"] <= 0:
        warehouse_inventory.remove(target)
        logger.info(f"出库清空: {target['product_name']} {quantity_kg}kg ← {target['warehouse_name']}")
        return {
            "code": 200,
            "message": f"出库成功（库存已清空）：{target['product_name']} {quantity_kg}kg ← {target['warehouse_name']}",
            "data": {"remaining_kg": 0},
        }

    logger.info(f"出库: {target['product_name']} {quantity_kg}kg ← {target['warehouse_name']}，剩余 {target['quantity_kg']}kg")
    return {
        "code": 200,
        "message": f"出库成功：{target['product_name']} {quantity_kg}kg ← {target['warehouse_name']}，剩余 {target['quantity_kg']}kg",
        "data": {"remaining_kg": target["quantity_kg"]},
    }


@router.get("/warehouse-inventory-summary")
async def warehouse_inventory_summary(
    user: dict = Depends(get_current_user),
):
    """仓库库存总览 - 各仓库各温区库存汇总"""
    summary = {}
    for item in warehouse_inventory:
        wh_id = item["warehouse_id"]
        if wh_id not in summary:
            wh = next((w for w in WAREHOUSES if w["id"] == wh_id), None)
            summary[wh_id] = {
                "warehouse_id": wh_id,
                "warehouse_name": wh["name"] if wh else wh_id,
                "location": wh["location"] if wh else "",
                "frozen_kg": 0, "refrigerated_kg": 0, "ambient_kg": 0,
                "frozen_count": 0, "refrigerated_count": 0, "ambient_count": 0,
                "near_expiry_count": 0, "expired_count": 0,
            }
        s = summary[wh_id]
        s[f"{item['zone']}_kg"] += item["quantity_kg"]
        s[f"{item['zone']}_count"] += 1
        if item["status"] == "near_expiry":
            s["near_expiry_count"] += 1
        elif item["status"] == "expired":
            s["expired_count"] += 1

    result = list(summary.values())
    for s in result:
        s["total_kg"] = s["frozen_kg"] + s["refrigerated_kg"] + s["ambient_kg"]

    return {
        "code": 200,
        "message": "查询成功",
        "data": {
            "total_warehouses": len(result),
            "total_kg": sum(s["total_kg"] for s in result),
            "total_near_expiry": sum(s["near_expiry_count"] for s in result),
            "total_expired": sum(s["expired_count"] for s in result),
            "details": sorted(result, key=lambda x: -x["total_kg"]),
        },
    }


# ==================== 老板经营数据 API ====================

@router.get("/boss-finance")
async def get_boss_finance(
    user: dict = Depends(get_current_user),
):
    """老板经营看板 - 财务数据"""
    now = datetime.utcnow()
    random.seed(now.day)

    # 月度收入
    monthly_revenue = random.randint(2800000, 4200000)
    monthly_cost = random.randint(1800000, 2800000)
    monthly_profit = monthly_revenue - monthly_cost
    profit_margin = round(monthly_profit / monthly_revenue * 100, 1)

    # 本周每日收入趋势
    daily_revenue = []
    for i in range(7):
        d = now - timedelta(days=6 - i)
        daily_revenue.append({
            "date": d.strftime("%m/%d"),
            "weekday": ["日", "一", "二", "三", "四", "五", "六"][d.weekday()],
            "revenue": random.randint(350000, 650000),
            "orders": random.randint(18, 42),
            "cost": random.randint(220000, 420000),
        })

    # 成本构成
    cost_breakdown = [
        {"name": "车辆油耗", "amount": random.randint(400000, 600000), "pct": 0},
        {"name": "冷库电费", "amount": random.randint(300000, 500000), "pct": 0},
        {"name": "司机工资", "amount": random.randint(350000, 500000), "pct": 0},
        {"name": "维修保养", "amount": random.randint(150000, 300000), "pct": 0},
        {"name": "保险税费", "amount": random.randint(100000, 250000), "pct": 0},
        {"name": "仓储人工", "amount": random.randint(200000, 350000), "pct": 0},
        {"name": "蓄冷板耗材", "amount": random.randint(80000, 180000), "pct": 0},
        {"name": "其他运营", "amount": random.randint(100000, 200000), "pct": 0},
    ]
    total_cost = sum(c["amount"] for c in cost_breakdown)
    for c in cost_breakdown:
        c["pct"] = round(c["amount"] / total_cost * 100, 1)

    return {
        "code": 200,
        "message": "查询成功",
        "data": {
            "month": now.strftime("%Y年%m月"),
            "monthly_revenue": monthly_revenue,
            "monthly_cost": monthly_cost,
            "monthly_profit": monthly_profit,
            "profit_margin": profit_margin,
            "daily_revenue": daily_revenue,
            "cost_breakdown": cost_breakdown,
            "updated_at": now.isoformat(),
        },
    }


@router.get("/boss-driver-performance")
async def get_driver_performance(
    user: dict = Depends(get_current_user),
):
    """老板经营看板 - 司机绩效"""
    now = datetime.utcnow()
    random.seed(now.day)

    driver_names = ["张伟", "李强", "王磊", "赵明", "刘洋", "陈军", "周鹏", "吴斌",
                    "郑刚", "钱勇", "孙涛", "杨峰", "黄健", "林辉", "何勇", "马超"]
    drivers = []
    for i, name in enumerate(driver_names[:10]):
        total = random.randint(80, 150)
        on_time = random.randint(int(total * 0.75), total)
        drivers.append({
            "driver_id": f"DRV-{i+1:03d}",
            "name": name,
            "vehicle_plate": f"冷A-{8000 + i + 1}",
            "monthly_orders": total,
            "on_time_orders": on_time,
            "on_time_rate": round(on_time / total * 100, 1),
            "total_mileage_km": random.randint(3000, 12000),
            "fuel_cost_yuan": random.randint(8000, 25000),
            "customer_rating": round(random.uniform(4.2, 5.0), 1),
            "temp_violations": random.randint(0, 8),
            "performance_score": round(random.uniform(78, 98), 1),
        })

    drivers.sort(key=lambda d: -d["performance_score"])

    return {
        "code": 200,
        "message": "查询成功",
        "data": {
            "total_drivers": len(drivers),
            "avg_on_time_rate": round(sum(d["on_time_rate"] for d in drivers) / len(drivers), 1),
            "avg_rating": round(sum(d["customer_rating"] for d in drivers) / len(drivers), 1),
            "total_violations": sum(d["temp_violations"] for d in drivers),
            "drivers": drivers,
            "updated_at": now.isoformat(),
        },
    }


@router.get("/boss-customer-analysis")
async def get_customer_analysis(
    user: dict = Depends(get_current_user),
):
    """老板经营看板 - 客户分析"""
    now = datetime.utcnow()
    random.seed(now.day)

    customers = [
        {"name": "永辉超市", "industry": "连锁零售", "monthly_orders": random.randint(40, 80), "monthly_revenue": random.randint(400000, 900000)},
        {"name": "盒马鲜生", "industry": "新零售", "monthly_orders": random.randint(35, 70), "monthly_revenue": random.randint(350000, 850000)},
        {"name": "美团优选", "industry": "社区团购", "monthly_orders": random.randint(50, 100), "monthly_revenue": random.randint(300000, 700000)},
        {"name": "京东冷链", "industry": "电商物流", "monthly_orders": random.randint(30, 60), "monthly_revenue": random.randint(500000, 1000000)},
        {"name": "海底捞", "industry": "餐饮连锁", "monthly_orders": random.randint(20, 45), "monthly_revenue": random.randint(250000, 550000)},
        {"name": "百果园", "industry": "水果零售", "monthly_orders": random.randint(25, 55), "monthly_revenue": random.randint(200000, 450000)},
        {"name": "伊利集团", "industry": "乳制品", "monthly_orders": random.randint(15, 35), "monthly_revenue": random.randint(300000, 600000)},
        {"name": "国药集团", "industry": "医药", "monthly_orders": random.randint(10, 25), "monthly_revenue": random.randint(400000, 800000)},
    ]

    for c in customers:
        c["avg_order_value"] = round(c["monthly_revenue"] / max(c["monthly_orders"], 1), 0)

    customers.sort(key=lambda c: -c["monthly_revenue"])

    total_revenue = sum(c["monthly_revenue"] for c in customers)

    return {
        "code": 200,
        "message": "查询成功",
        "data": {
            "total_customers": len(customers),
            "total_monthly_revenue": total_revenue,
            "avg_order_value": round(sum(c["avg_order_value"] for c in customers) / len(customers), 0),
            "customers": customers,
            "updated_at": now.isoformat(),
        },
    }



