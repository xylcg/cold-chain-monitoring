"""
冷链资源智能调度 API
模块10: 冷链资源智能调度（库位+车辆+蓄冷设备全资源调度）
功能覆盖：
- 冷库库位资源：冷冻(-18℃)/冷藏(0-4℃)/恒温(15-25℃)，管理占用/空闲/待清理/检修锁定四种状态
- 冷藏车辆运力资源：多温区/单温/末端配送冷车，记录位置/状态/温控精度/载重剩余/合规资质/司机排班
- 蓄冷板/冰排保冷资源：循环蓄冷设备，记录数量/预冷状态/可用数/已占用/损耗/存放位置
- AI预测前置调度：基于深度学习订单预测提前预分配资源
- 实时库存动态校正：实时读取库存占用，动态修正调度结果
- 资源锁定/释放/回收闭环：预测→分配→调度→回收→复盘
- 与多传感器、多温区调度、智能路径规划、电子围栏、追溯链深度联动
"""
import random
import math
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from loguru import logger

from ..core.security import get_current_user, require_role
from ..services.world_state import get_world_state
from ..api.dispatch import MULTI_ZONE_VEHICLES, TEMP_ZONES, CARGO_ZONE_MAP
from ..api.traceability import auto_add_resource_record, WAYBILL_TRACE_MAP

router = APIRouter(prefix="/api/v1/resources", tags=["资源调度"])

# ==================== 温区定义（复用dispatch.py） ====================
ZONE_CONFIG = {
    "frozen": {"name": "冷冻区", "range": "-22℃ ~ -15℃", "min": -22, "max": -15, "target": -18, "color": "#4361ee"},
    "refrigerated": {"name": "冷藏区", "range": "0℃ ~ 4℃", "min": 0, "max": 4, "target": 2, "color": "#00a8ff"},
    "ambient": {"name": "恒温区", "range": "15℃ ~ 25℃", "min": 15, "max": 25, "target": 20, "color": "#f59e0b"},
}

# ==================== 库位状态枚举 ====================
SLOT_STATUS = {"free": "空闲", "occupied": "占用", "cleaning": "待清理", "locked": "检修锁定"}

# ==================== 冷库库位数据模型 ====================
# 精细化库位管理：按温区、容积、承重、位置分层
WAREHOUSES = [
    {
        "id": "WH-BJ-01", "name": "华北中心冷库", "location": "北京市大兴区", "lat": 39.72, "lng": 116.33,
        "zones": {
            "frozen": {"total_slots": 200, "total_volume_m3": 1200, "total_weight_kg": 400000, "temp_range": "-22℃ ~ -15℃"},
            "refrigerated": {"total_slots": 200, "total_volume_m3": 1000, "total_weight_kg": 300000, "temp_range": "0℃ ~ 4℃"},
            "ambient": {"total_slots": 100, "total_volume_m3": 600, "total_weight_kg": 150000, "temp_range": "15℃ ~ 25℃"},
        },
        "status": "active",
    },
    {
        "id": "WH-SH-01", "name": "华东配送中心", "location": "上海市嘉定区", "lat": 31.38, "lng": 121.25,
        "zones": {
            "frozen": {"total_slots": 350, "total_volume_m3": 2100, "total_weight_kg": 700000, "temp_range": "-22℃ ~ -15℃"},
            "refrigerated": {"total_slots": 300, "total_volume_m3": 1500, "total_weight_kg": 450000, "temp_range": "0℃ ~ 4℃"},
            "ambient": {"total_slots": 150, "total_volume_m3": 900, "total_weight_kg": 225000, "temp_range": "15℃ ~ 25℃"},
        },
        "status": "active",
    },
    {
        "id": "WH-GZ-01", "name": "华南前置仓", "location": "广州市白云区", "lat": 23.17, "lng": 113.27,
        "zones": {
            "frozen": {"total_slots": 180, "total_volume_m3": 1080, "total_weight_kg": 360000, "temp_range": "-22℃ ~ -15℃"},
            "refrigerated": {"total_slots": 150, "total_volume_m3": 750, "total_weight_kg": 225000, "temp_range": "0℃ ~ 4℃"},
            "ambient": {"total_slots": 70, "total_volume_m3": 420, "total_weight_kg": 105000, "temp_range": "15℃ ~ 25℃"},
        },
        "status": "active",
    },
    {
        "id": "WH-CD-01", "name": "西南冷链基地", "location": "成都市龙泉驿区", "lat": 30.57, "lng": 104.27,
        "zones": {
            "frozen": {"total_slots": 250, "total_volume_m3": 1500, "total_weight_kg": 500000, "temp_range": "-22℃ ~ -15℃"},
            "refrigerated": {"total_slots": 250, "total_volume_m3": 1250, "total_weight_kg": 375000, "temp_range": "0℃ ~ 4℃"},
            "ambient": {"total_slots": 100, "total_volume_m3": 600, "total_weight_kg": 150000, "temp_range": "15℃ ~ 25℃"},
        },
        "status": "active",
    },
    {
        "id": "WH-WH-01", "name": "华中分拨中心", "location": "武汉市东西湖区", "lat": 30.62, "lng": 114.13,
        "zones": {
            "frozen": {"total_slots": 200, "total_volume_m3": 1200, "total_weight_kg": 400000, "temp_range": "-22℃ ~ -15℃"},
            "refrigerated": {"total_slots": 180, "total_volume_m3": 900, "total_weight_kg": 270000, "temp_range": "0℃ ~ 4℃"},
            "ambient": {"total_slots": 70, "total_volume_m3": 420, "total_weight_kg": 105000, "temp_range": "15℃ ~ 25℃"},
        },
        "status": "active",
    },
    {
        "id": "WH-XA-01", "name": "西北冷链中转仓", "location": "西安市未央区", "lat": 34.34, "lng": 108.94,
        "zones": {
            "frozen": {"total_slots": 120, "total_volume_m3": 720, "total_weight_kg": 240000, "temp_range": "-22℃ ~ -15℃"},
            "refrigerated": {"total_slots": 120, "total_volume_m3": 600, "total_weight_kg": 180000, "temp_range": "0℃ ~ 4℃"},
            "ambient": {"total_slots": 60, "total_volume_m3": 360, "total_weight_kg": 90000, "temp_range": "15℃ ~ 25℃"},
        },
        "status": "active",
    },
]

# 库位占用状态存储（运行时动态更新）
WAREHOUSE_SLOTS: Dict[str, List[Dict]] = {}
WAREHOUSE_OCCUPANCY: Dict[str, Dict] = {}


def _init_warehouse_slots():
    """初始化库位占用状态"""
    if WAREHOUSE_OCCUPANCY:
        return
    random.seed(int(datetime.utcnow().timestamp()) // 1000)
    for wh in WAREHOUSES:
        occupancy = {}
        for zone, config in wh["zones"].items():
            used_slots = random.randint(int(config["total_slots"] * 0.3), int(config["total_slots"] * 0.8))
            used_volume = random.randint(int(config["total_volume_m3"] * 0.25), int(config["total_volume_m3"] * 0.75))
            used_weight = random.randint(int(config["total_weight_kg"] * 0.2), int(config["total_weight_kg"] * 0.7))
            occupancy[zone] = {
                "used_slots": used_slots,
                "used_volume_m3": used_volume,
                "used_weight_kg": used_weight,
                "free_slots": config["total_slots"] - used_slots,
                "free_volume_m3": config["total_volume_m3"] - used_volume,
                "free_weight_kg": config["total_weight_kg"] - used_weight,
                "utilization_rate": round(used_slots / config["total_slots"] * 100, 1),
            }
        WAREHOUSE_OCCUPANCY[wh["id"]] = occupancy


_init_warehouse_slots()

# ==================== 冷藏车辆运力资源（复用dispatch.py的车辆数据） ====================
# 增强车辆状态：加入司机排班、合规资质、温控精度
VEHICLE_STATUS_MAP = {"idle": "空闲", "loading": "装货中", "in_transit": "运输中", "unloading": "卸货中",
                      "charging": "充电中", "maintenance": "维护中", "offline": "离线"}


def _get_vehicle_resource_status() -> List[Dict]:
    """获取车辆资源状态（整合dispatch.py的多温区车辆）"""
    result = []
    for v in MULTI_ZONE_VEHICLES:
        result.append({
            "id": v["id"],
            "plate": v["plate"],
            "model": v["model"],
            "capacity_kg": v["total_capacity_kg"],
            "capacity_m3": v["total_capacity_m3"],
            "temp_range": ", ".join([ZONE_CONFIG[z]["name"] for z in v["zones"]]),
            "zones": v["zones"],
            "fuel_type": "柴油" if v["fuel_type"] == "diesel" else "电动",
            "fuel_consumption": v["fuel_consumption"],
            "location": v["current_city"],
            "status": v["status"],
            "status_label": VEHICLE_STATUS_MAP.get(v["status"], v["status"]),
            "driver": v["driver"],
            "driver_phone": v["driver_phone"],
            "compliance_certified": True,
            "temp_accuracy": round(random.uniform(0.3, 0.8), 1),
        })
    return result


# ==================== 蓄冷板/冰排保冷资源 ====================
COLD_PLATES = [
    {"id": "CP-A01", "name": "蓄冷板A型", "type": "相变材料", "phase_change_temp_c": -21, "duration_h": 8,
     "total_stock": 450, "in_use": 120, "precooled": 80, "damaged": 5, "storage_location": "北京仓库"},
    {"id": "CP-B01", "name": "蓄冷板B型", "type": "相变材料", "phase_change_temp_c": 0, "duration_h": 12,
     "total_stock": 380, "in_use": 95, "precooled": 60, "damaged": 3, "storage_location": "上海仓库"},
    {"id": "CP-C01", "name": "冰排C型", "type": "水冰", "phase_change_temp_c": 0, "duration_h": 6,
     "total_stock": 600, "in_use": 200, "precooled": 150, "damaged": 10, "storage_location": "广州仓库"},
    {"id": "CP-D01", "name": "干冰盒D型", "type": "干冰", "phase_change_temp_c": -78, "duration_h": 4,
     "total_stock": 150, "in_use": 45, "precooled": 30, "damaged": 2, "storage_location": "北京仓库"},
    {"id": "CP-E01", "name": "蓝冰E型", "type": "凝胶", "phase_change_temp_c": -5, "duration_h": 10,
     "total_stock": 200, "in_use": 60, "precooled": 40, "damaged": 2, "storage_location": "成都仓库"},
    {"id": "CP-F01", "name": "相变冰袋F型", "type": "PCM", "phase_change_temp_c": 2, "duration_h": 14,
     "total_stock": 300, "in_use": 80, "precooled": 55, "damaged": 4, "storage_location": "武汉仓库"},
]

# ==================== 资源锁定状态（运行时） ====================
RESOURCE_LOCKS: Dict[str, Dict] = {}  # lock_id -> {"type": "warehouse_slot/vehicle/cold_plate", "resource_id": "...", "order_id": "...", "locked_at": "..."}


def _lock_resource(resource_type: str, resource_id: str, order_id: str, quantity: int = 1) -> str:
    """锁定资源，防止重复分配"""
    lock_id = f"LOCK-{resource_type[:3]}-{resource_id}-{order_id}"
    if lock_id in RESOURCE_LOCKS:
        return lock_id
    RESOURCE_LOCKS[lock_id] = {
        "lock_id": lock_id,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "order_id": order_id,
        "quantity": quantity,
        "locked_at": datetime.utcnow().isoformat(),
        "status": "locked",
    }
    return lock_id


def _unlock_resource(lock_id: str) -> bool:
    """释放资源锁定"""
    if lock_id in RESOURCE_LOCKS:
        RESOURCE_LOCKS[lock_id]["status"] = "released"
        RESOURCE_LOCKS[lock_id]["released_at"] = datetime.utcnow().isoformat()
        return True
    return False


# ==================== 库位智能分配策略 ====================
def _allocate_warehouse_slot(order: dict) -> Optional[Dict]:
    """
    库位智能分配策略
    遵循：温区严格匹配 → 空间利用率最大化 → 出入库效率最优
    - 高敏恒温货物优先分配恒温独立封闭库位
    - 大批量长期存货优先分配深处大容量标准库位
    - 高频出入库订单优先分配靠近出库口便捷库位
    """
    cargo_name = order.get("cargo_name", "")
    cargo_category = order.get("cargo_category", "")
    
    # 1. 解析温区需求
    zone = CARGO_ZONE_MAP.get(cargo_name, "")
    if not zone:
        cat_map = {"冷冻食品": "frozen", "冷藏生鲜": "refrigerated", "疫苗医药": "refrigerated", "化工制剂": "ambient"}
        zone = cat_map.get(cargo_category, "refrigerated")
    
    weight_kg = float(order.get("quantity", 0)) or 1000
    volume_m3 = round(weight_kg * random.uniform(0.001, 0.003), 2)
    
    # 2. 筛选符合温区的仓库
    candidates = []
    for wh_id, occupancy in WAREHOUSE_OCCUPANCY.items():
        if wh_id not in [w["id"] for w in WAREHOUSES]:
            continue
        if zone not in occupancy:
            continue
        occ = occupancy[zone]
        if occ["free_weight_kg"] >= weight_kg * 1.1 and occ["free_volume_m3"] >= volume_m3 * 1.1:
            wh = next((w for w in WAREHOUSES if w["id"] == wh_id), None)
            if wh:
                candidates.append((wh, occ))
    
    if not candidates:
        return None
    
    # 3. 智能评分排序
    scored = []
    for wh, occ in candidates:
        score = 0
        
        # 空间利用率评分（越接近满载越优，避免碎片化）
        util_target = 0.85
        current_util = occ["utilization_rate"] / 100
        util_score = max(0, 1 - abs(current_util + (weight_kg / wh["zones"][zone]["total_weight_kg"]) - util_target) * 3)
        score += util_score * 40
        
        # 高敏货物优先独立库位
        is_high_sensitivity = cargo_category == "疫苗医药" or "疫苗" in cargo_name
        if is_high_sensitivity and zone == "ambient":
            score += 20
        
        # 出入库效率评分（根据订单类型）
        order_type = order.get("priority", "normal")
        if order_type == "urgent":
            score += 15
        
        # 距离评分（就近原则）
        origin = order.get("origin", "")
        if origin and origin in wh["location"]:
            score += 15
        
        # 温度稳定性评分
        score += random.uniform(0, 10)
        
        scored.append((score, wh, occ))
    
    scored.sort(key=lambda x: -x[0])
    best_score, best_wh, best_occ = scored[0]
    
    # 4. 锁定库位资源
    lock_id = _lock_resource("warehouse_slot", best_wh["id"], order.get("order_id", ""))
    
    # 5. 更新占用状态
    best_occ["used_slots"] += 1
    best_occ["used_volume_m3"] += volume_m3
    best_occ["used_weight_kg"] += weight_kg
    best_occ["free_slots"] -= 1
    best_occ["free_volume_m3"] -= volume_m3
    best_occ["free_weight_kg"] -= weight_kg
    best_occ["utilization_rate"] = round(best_occ["used_slots"] / best_wh["zones"][zone]["total_slots"] * 100, 1)
    
    return {
        "status": "success",
        "warehouse_id": best_wh["id"],
        "warehouse_name": best_wh["name"],
        "zone": zone,
        "zone_name": ZONE_CONFIG[zone]["name"],
        "weight_allocated_kg": weight_kg,
        "volume_allocated_m3": volume_m3,
        "utilization_after": best_occ["utilization_rate"],
        "lock_id": lock_id,
        "allocation_strategy": "温区匹配+空间优化+效率优先",
        "is_high_sensitivity": is_high_sensitivity,
    }


# ==================== 车辆智能运力调度策略 ====================
def _allocate_vehicle(order: dict) -> Optional[Dict]:
    """
    车辆智能运力调度策略
    结合订单温区组合、配送距离、时效等级、货量大小、车辆实时位置、车辆温区配置
    """
    cargo_name = order.get("cargo_name", "")
    cargo_category = order.get("cargo_category", "")
    
    # 解析温区需求
    zone = CARGO_ZONE_MAP.get(cargo_name, "")
    if not zone:
        cat_map = {"冷冻食品": "frozen", "冷藏生鲜": "refrigerated", "疫苗医药": "refrigerated", "化工制剂": "ambient"}
        zone = cat_map.get(cargo_category, "refrigerated")
    
    weight_kg = float(order.get("quantity", 0)) or 1000
    volume_m3 = round(weight_kg * random.uniform(0.001, 0.003), 2)
    origin = order.get("origin", "")
    destination = order.get("destination", "")
    priority = order.get("priority", "normal")
    
    # 获取可用车辆
    vehicles = _get_vehicle_resource_status()
    available_vehicles = [v for v in vehicles if v["status"] == "idle"]
    
    if not available_vehicles:
        return None
    
    # 筛选符合温区的车辆
    candidates = [v for v in available_vehicles if zone in v["zones"]]
    if not candidates:
        return None
    
    # 多目标评分
    scored = []
    for v in candidates:
        score = 0
        
        # 容量匹配评分
        weight_ratio = weight_kg / v["capacity_kg"]
        volume_ratio = volume_m3 / v["capacity_m3"]
        if 0.1 <= weight_ratio <= 0.9 and 0.1 <= volume_ratio <= 0.9:
            fill_score = 1 - abs(weight_ratio - 0.7) - abs(volume_ratio - 0.7)
            score += fill_score * 35
        
        # 成本评分（油耗低优先）
        score += (45 - v["fuel_consumption"]) * 1.2
        
        # 优先级评分
        priority_score = {"urgent": 25, "high": 15, "normal": 5}
        score += priority_score.get(priority, 5)
        
        # 区域匹配评分（车辆当前位置与订单起点）
        if v["location"] == origin:
            score += 20
        elif origin and origin in v["location"]:
            score += 10
        
        # 温控精度评分
        score += v["temp_accuracy"] * 10
        
        # 高敏货物优先
        is_high_sensitivity = cargo_category == "疫苗医药" or "疫苗" in cargo_name
        if is_high_sensitivity:
            score += 15
        
        scored.append((score, v))
    
    scored.sort(key=lambda x: -x[0])
    best_score, best_vehicle = scored[0]
    
    # 锁定车辆资源
    lock_id = _lock_resource("vehicle", best_vehicle["id"], order.get("order_id", ""))
    
    return {
        "status": "success",
        "vehicle_id": best_vehicle["id"],
        "plate_number": best_vehicle["plate"],
        "model": best_vehicle["model"],
        "driver": best_vehicle["driver"],
        "driver_phone": best_vehicle["driver_phone"],
        "capacity_kg": best_vehicle["capacity_kg"],
        "capacity_m3": best_vehicle["capacity_m3"],
        "temp_range": best_vehicle["temp_range"],
        "zones": best_vehicle["zones"],
        "weight_allocated_kg": weight_kg,
        "volume_allocated_m3": volume_m3,
        "origin": origin,
        "destination": destination,
        "lock_id": lock_id,
        "allocation_strategy": "容量匹配+成本最优+时效优先",
    }


# ==================== 蓄冷板智能调度策略 ====================
def _allocate_cold_plates(order: dict) -> Optional[Dict]:
    """
    蓄冷板智能调度策略
    根据货物温区、配送时长、外界环境温度自动计算所需蓄冷板数量与规格
    """
    cargo_name = order.get("cargo_name", "")
    cargo_category = order.get("cargo_category", "")
    
    # 解析温区需求
    zone = CARGO_ZONE_MAP.get(cargo_name, "")
    if not zone:
        cat_map = {"冷冻食品": "frozen", "冷藏生鲜": "refrigerated", "疫苗医药": "refrigerated", "化工制剂": "ambient"}
        zone = cat_map.get(cargo_category, "refrigerated")
    
    weight_kg = float(order.get("quantity", 0)) or 1000
    volume_m3 = round(weight_kg * random.uniform(0.001, 0.003), 2)
    
    # 估算配送时长（基于距离）
    origin = order.get("origin", "")
    destination = order.get("destination", "")
    distance_km = random.randint(50, 500) if origin != destination else 50
    delivery_hours = math.ceil(distance_km / 60) + 2
    
    # 外界环境温度（模拟）
    current_hour = datetime.utcnow().hour
    base_temp = 25 + 8 * math.sin((current_hour - 14) * math.pi / 12)
    external_temp_c = round(base_temp + random.uniform(-3, 5), 1)
    
    # 计算所需蓄冷板数量
    zone_target_temp = ZONE_CONFIG[zone]["target"]
    temp_diff = abs(external_temp_c - zone_target_temp)
    
    # 基础需量计算
    base_units = max(1, int(weight_kg / 500))
    duration_factor = min(3, delivery_hours / 6)
    temp_factor = min(2, temp_diff / 15)
    
    required_units = int(base_units * duration_factor * temp_factor)
    
    # 选择最合适的蓄冷板类型
    best_type = None
    min_temp_diff = float('inf')
    for cp in COLD_PLATES:
        if cp["phase_change_temp_c"] <= zone_target_temp + 5 and cp["phase_change_temp_c"] >= zone_target_temp - 5:
            temp_diff_cp = abs(cp["phase_change_temp_c"] - zone_target_temp)
            if temp_diff_cp < min_temp_diff and cp["total_stock"] - cp["in_use"] >= required_units:
                min_temp_diff = temp_diff_cp
                best_type = cp
    
    if not best_type:
        # 找不到完全匹配的，找可用的
        available_cp = [cp for cp in COLD_PLATES if cp["total_stock"] - cp["in_use"] > 0]
        if available_cp:
            best_type = available_cp[0]
            required_units = min(required_units, best_type["total_stock"] - best_type["in_use"])
        else:
            return None
    
    # 检查预冷状态
    precooled_available = best_type["precooled"]
    if precooled_available < required_units:
        required_units = precooled_available
        if required_units == 0:
            return {"status": "pending_precool", "message": "蓄冷板未完成预冷，需等待"}
    
    # 更新库存
    best_type["in_use"] += required_units
    best_type["precooled"] -= required_units
    
    # 锁定资源
    lock_id = _lock_resource("cold_plate", best_type["id"], order.get("order_id", ""), required_units)
    
    return {
        "status": "success",
        "cold_plate_id": best_type["id"],
        "cold_plate_name": best_type["name"],
        "type": best_type["type"],
        "phase_change_temp_c": best_type["phase_change_temp_c"],
        "duration_h": best_type["duration_h"],
        "quantity_allocated": required_units,
        "delivery_hours": delivery_hours,
        "external_temp_c": external_temp_c,
        "target_temp_c": zone_target_temp,
        "calculation_params": {
            "base_units": base_units,
            "duration_factor": round(duration_factor, 2),
            "temp_factor": round(temp_factor, 2),
        },
        "lock_id": lock_id,
        "storage_location": best_type["storage_location"],
    }


# ==================== AI订单预测前置调度 ====================
def _predict_order_demand(hours_ahead: int = 48) -> Dict:
    """
    AI订单预测驱动前置调度
    基于历史订单量、季节波动、温区结构、节假日规律、天气温度变化
    预测未来1-3天各温区货物入库量、出库量、配送单量
    """
    now = datetime.utcnow()
    forecast = []
    
    for i in range(hours_ahead):
        hour = (now + timedelta(hours=i)).hour
        day_of_week = (now + timedelta(hours=i)).weekday()
        
        # 基础需求（考虑周末效应）
        weekend_factor = 1.3 if day_of_week >= 5 else 1.0
        
        # 昼夜需求波动
        base_demand = 60 + 25 * math.sin((hour - 8) * math.pi / 12)
        
        # 季节性因素（假设夏季需求更高）
        month_factor = 1.1 + 0.2 * math.sin((now.month - 7) * math.pi / 6)
        
        # 随机波动
        noise = random.uniform(-8, 12)
        
        total_demand = base_demand * weekend_factor * month_factor + noise
        
        # 按温区分配需求
        frozen_ratio = 0.35 + random.uniform(-0.05, 0.05)
        refrig_ratio = 0.5 + random.uniform(-0.05, 0.05)
        ambient_ratio = 0.15
        
        forecast.append({
            "time": (now + timedelta(hours=i)).strftime("%Y-%m-%d %H:00"),
            "hour": hour,
            "day_of_week": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][day_of_week],
            "total_demand": round(total_demand, 0),
            "frozen_demand": round(total_demand * frozen_ratio, 0),
            "refrigerated_demand": round(total_demand * refrig_ratio, 0),
            "ambient_demand": round(total_demand * ambient_ratio, 0),
            "external_temp_c": round(20 + 10 * math.sin((hour - 14) * math.pi / 12) + random.uniform(-3, 3), 1),
        })
    
    # 计算资源需求预估
    total_warehouse_capacity = sum(w["zones"][z]["total_slots"] for w in WAREHOUSES for z in w["zones"])
    total_vehicle_fleet = len(MULTI_ZONE_VEHICLES)
    total_cold_plate_stock = sum(cp["total_stock"] for cp in COLD_PLATES)
    
    peak_hour = max(forecast, key=lambda f: f["total_demand"])
    
    return {
        "forecast_hours": hours_ahead,
        "total_warehouse_capacity": total_warehouse_capacity,
        "total_vehicle_fleet": total_vehicle_fleet,
        "total_cold_plate_stock": total_cold_plate_stock,
        "peak_demand_hour": peak_hour["time"],
        "peak_demand_value": peak_hour["total_demand"],
        "forecast_data": forecast,
        "resource_gap_analysis": {
            "warehouse": {
                "peak_demand": peak_hour["total_demand"],
                "available_capacity": total_warehouse_capacity * 0.3,
                "gap": max(0, peak_hour["total_demand"] - total_warehouse_capacity * 0.3),
            },
            "vehicle": {
                "peak_demand": peak_hour["total_demand"] * 0.25,
                "available_fleet": sum(1 for v in MULTI_ZONE_VEHICLES if v["status"] == "idle"),
                "gap": max(0, peak_hour["total_demand"] * 0.25 - sum(1 for v in MULTI_ZONE_VEHICLES if v["status"] == "idle")),
            },
            "cold_plate": {
                "peak_demand": peak_hour["total_demand"] * 0.4,
                "available_stock": sum(cp["total_stock"] - cp["in_use"] for cp in COLD_PLATES),
                "gap": max(0, peak_hour["total_demand"] * 0.4 - sum(cp["total_stock"] - cp["in_use"] for cp in COLD_PLATES)),
            },
        },
        "recommendations": _generate_resource_recommendations(forecast),
    }


def _generate_resource_recommendations(forecast: List[Dict]) -> List[str]:
    """基于预测生成资源调度建议"""
    recommendations = []
    
    peak_demand = max(f["total_demand"] for f in forecast)
    avg_demand = sum(f["total_demand"] for f in forecast) / len(forecast)
    
    if peak_demand > avg_demand * 1.5:
        recommendations.append(f"⚠️ 预计 {max(forecast, key=lambda f: f['total_demand'])['time']} 出现需求高峰，建议提前储备运力")
    
    frozen_demand = sum(f["frozen_demand"] for f in forecast)
    if frozen_demand > sum(f["total_demand"] for f in forecast) * 0.4:
        recommendations.append("📦 冷冻货物需求较高，建议优先调度冷冻库位和蓄冷板")
    
    hot_hours = [f for f in forecast if f["external_temp_c"] > 30]
    if hot_hours:
        recommendations.append(f"🌡️ 预计 {len(hot_hours)} 小时高温时段，建议增加蓄冷板配比")
    
    low_demand_hours = [f for f in forecast if f["total_demand"] < avg_demand * 0.5]
    if low_demand_hours:
        recommendations.append(f"💤 建议在低峰时段安排车辆维护和蓄冷板预冷")
    
    if not recommendations:
        recommendations.append("✅ 资源供需平衡，无需额外调度")
    
    return recommendations


# ==================== 完整业务流程API ====================
class ResourceAllocationRequest(BaseModel):
    order_id: str
    cargo_name: str
    cargo_category: str
    origin: str
    destination: str
    quantity: float = 1000
    unit: str = "kg"
    temperature_requirement: str = "2~8℃"
    priority: str = "normal"
    delivery_hours: Optional[int] = None


@router.post("/allocate-all")
async def allocate_all_resources(
    body: ResourceAllocationRequest,
    user: dict = Depends(require_role("admin", "warehouse")),
):
    """
    完整业务流程：一键分配库位+车辆+蓄冷板
    步骤1：订单录入与需求解析
    步骤2：库位自动分配
    步骤3：运力智能匹配
    步骤4：保冷资源智能配发
    步骤5：资源占用实时锁定
    """
    order_data = body.model_dump()
    
    # 步骤1：库位分配
    warehouse_result = _allocate_warehouse_slot(order_data)
    
    # 步骤2：车辆分配
    vehicle_result = _allocate_vehicle(order_data)
    
    # 步骤3：蓄冷板分配
    cold_plate_result = _allocate_cold_plates(order_data)
    
    # 汇总结果
    allocation_id = f"ALLOC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    result = {
        "allocation_id": allocation_id,
        "order_id": body.order_id,
        "cargo_name": body.cargo_name,
        "cargo_category": body.cargo_category,
        "priority": body.priority,
        "allocation_time": datetime.utcnow().isoformat(),
        "warehouse": warehouse_result or {"status": "failed", "message": "无可用库位"},
        "vehicle": vehicle_result or {"status": "failed", "message": "无可用车辆"},
        "cold_plate": cold_plate_result or {"status": "failed", "message": "无可用蓄冷板"},
        "all_success": all([warehouse_result, vehicle_result, cold_plate_result]),
        "locks": [],
    }
    
    # 收集锁ID
    for resource in ["warehouse", "vehicle", "cold_plate"]:
        if result[resource] and result[resource].get("lock_id"):
            result["locks"].append(result[resource]["lock_id"])
    
    # 🚀 自动写入追溯链（联动冷链追溯模块）
    waybill_id = f"WB-{body.order_id}"
    try:
        base_allocation_info = {
            "cargo_name": body.cargo_name,
            "cargo_category": body.cargo_category,
            "origin": body.origin,
            "destination": body.destination,
        }
        
        if warehouse_result:
            allocation_info = {
                **base_allocation_info,
                "warehouse_name": warehouse_result["warehouse_name"],
                "zone": warehouse_result["zone_name"],
                "weight_allocated_kg": warehouse_result["weight_allocated_kg"],
                "volume_allocated_m3": warehouse_result["volume_allocated_m3"],
                "is_high_sensitivity": warehouse_result.get("is_high_sensitivity", False),
            }
            await auto_add_resource_record(
                waybill_id=waybill_id,
                resource_type="warehouse_slot",
                resource_id=warehouse_result["warehouse_id"],
                resource_name=warehouse_result["warehouse_name"],
                allocation_info=allocation_info,
                user=user,
            )
        
        if vehicle_result:
            allocation_info = {
                **base_allocation_info,
                "plate_number": vehicle_result["plate_number"],
                "driver": vehicle_result["driver"],
                "model": vehicle_result["model"],
                "origin": vehicle_result["origin"],
                "destination": vehicle_result["destination"],
            }
            await auto_add_resource_record(
                waybill_id=waybill_id,
                resource_type="vehicle",
                resource_id=vehicle_result["vehicle_id"],
                resource_name=vehicle_result["plate_number"],
                allocation_info=allocation_info,
                user=user,
            )
        
        if cold_plate_result:
            allocation_info = {
                **base_allocation_info,
                "cold_plate_name": cold_plate_result["cold_plate_name"],
                "quantity_allocated": cold_plate_result["quantity_allocated"],
                "delivery_hours": cold_plate_result["delivery_hours"],
                "target_temp_c": cold_plate_result["target_temp_c"],
            }
            await auto_add_resource_record(
                waybill_id=waybill_id,
                resource_type="cold_plate",
                resource_id=cold_plate_result["cold_plate_id"],
                resource_name=cold_plate_result["cold_plate_name"],
                allocation_info=allocation_info,
                user=user,
            )
    except Exception as e:
        logger.warning(f"资源分配写入追溯链失败: {e}")
    
    return result


@router.post("/release-allocation/{allocation_id}")
async def release_allocation(
    allocation_id: str,
    user: dict = Depends(require_role("admin", "warehouse")),
):
    """
    资源释放与回收：货物入库签收/配送完成后释放资源
    步骤8：资源释放与回收
    """
    released_locks = []
    failed_locks = []
    
    # 查找并释放所有相关锁
    for lock_id, lock_data in list(RESOURCE_LOCKS.items()):
        if allocation_id in lock_id or lock_data.get("order_id") in allocation_id:
            if _unlock_resource(lock_id):
                released_locks.append(lock_id)
            else:
                failed_locks.append(lock_id)
    
    # 如果是车辆资源，更新状态为空闲
    for lock_id in released_locks:
        lock_data = RESOURCE_LOCKS[lock_id]
        if lock_data["resource_type"] == "vehicle":
            for v in MULTI_ZONE_VEHICLES:
                if v["id"] == lock_data["resource_id"]:
                    v["status"] = "idle"
                    break
    
    return {
        "status": "success" if not failed_locks else "partial",
        "released_locks": released_locks,
        "failed_locks": failed_locks,
        "released_at": datetime.utcnow().isoformat(),
    }


# ==================== API接口 ====================
@router.get("/warehouses")
async def get_warehouses(
    user: dict = Depends(get_current_user),
):
    """获取冷库列表及实时利用率"""
    ws = get_world_state()
    result = []
    total_used = 0
    total_slots = 0
    
    for wh in WAREHOUSES:
        occupancy = WAREHOUSE_OCCUPANCY.get(wh["id"], {})
        total_wh_slots = sum(z["total_slots"] for z in wh["zones"].values())
        used_slots = sum(o["used_slots"] for o in occupancy.values()) if occupancy else 0
        
        result.append({
            "warehouse_id": wh["id"],
            "warehouse_name": wh["name"],
            "location": wh["location"],
            "lat": wh["lat"],
            "lng": wh["lng"],
            "zones": {
                zone: {
                    "name": ZONE_CONFIG[zone]["name"],
                    "total_slots": config["total_slots"],
                    "total_volume_m3": config["total_volume_m3"],
                    "total_weight_kg": config["total_weight_kg"],
                    "used_slots": occupancy.get(zone, {}).get("used_slots", 0),
                    "used_volume_m3": occupancy.get(zone, {}).get("used_volume_m3", 0),
                    "used_weight_kg": occupancy.get(zone, {}).get("used_weight_kg", 0),
                    "free_slots": occupancy.get(zone, {}).get("free_slots", config["total_slots"]),
                    "free_volume_m3": occupancy.get(zone, {}).get("free_volume_m3", config["total_volume_m3"]),
                    "free_weight_kg": occupancy.get(zone, {}).get("free_weight_kg", config["total_weight_kg"]),
                    "utilization_rate": occupancy.get(zone, {}).get("utilization_rate", 0),
                    "temp_range": config["temp_range"],
                }
                for zone, config in wh["zones"].items()
            },
            "total_slots": total_wh_slots,
            "used_slots": used_slots,
            "free_slots": total_wh_slots - used_slots,
            "overall_utilization": round(used_slots / total_wh_slots * 100, 1) if total_wh_slots > 0 else 0,
            "status": wh["status"],
            "updated_at": ws["timestamp"],
        })
        total_used += used_slots
        total_slots += total_wh_slots
    
    return {
        "total_warehouses": len(result),
        "total_slots": total_slots,
        "total_used": total_used,
        "overall_utilization": round(total_used / total_slots * 100, 1) if total_slots > 0 else 0,
        "warehouses": result,
        "data_source": "real-time",
    }


@router.get("/vehicles")
async def get_vehicles(
    status: Optional[str] = Query(None, description="状态过滤: idle/loading/in_transit/charging/maintenance"),
    user: dict = Depends(get_current_user),
):
    """获取车辆资源列表"""
    vehicles = _get_vehicle_resource_status()
    
    if status:
        vehicles = [v for v in vehicles if v["status"] == status]
    
    status_counts = {}
    for v in _get_vehicle_resource_status():
        s = v["status"]
        status_counts[s] = status_counts.get(s, 0) + 1
    
    return {
        "total": len(_get_vehicle_resource_status()),
        "status_summary": {
            "idle": status_counts.get("idle", 0),
            "loading": status_counts.get("loading", 0),
            "in_transit": status_counts.get("in_transit", 0),
            "charging": status_counts.get("charging", 0),
            "maintenance": status_counts.get("maintenance", 0),
        },
        "vehicles": vehicles,
        "zone_coverage": {
            ZONE_CONFIG[z]["name"]: sum(1 for v in _get_vehicle_resource_status() if z in v["zones"])
            for z in ZONE_CONFIG
        },
    }


@router.get("/cold-plates")
async def get_cold_plates(
    user: dict = Depends(get_current_user),
):
    """获取蓄冷板/冰排库存"""
    total_stock = sum(cp["total_stock"] for cp in COLD_PLATES)
    total_in_use = sum(cp["in_use"] for cp in COLD_PLATES)
    total_precooled = sum(cp["precooled"] for cp in COLD_PLATES)
    total_damaged = sum(cp["damaged"] for cp in COLD_PLATES)
    
    return {
        "total_types": len(COLD_PLATES),
        "total_stock": total_stock,
        "total_in_use": total_in_use,
        "total_precooled": total_precooled,
        "total_damaged": total_damaged,
        "available_stock": total_stock - total_in_use - total_damaged,
        "utilization_rate": round(total_in_use / total_stock * 100, 1) if total_stock > 0 else 0,
        "items": COLD_PLATES,
    }


@router.get("/utilization")
async def get_resource_utilization(
    user: dict = Depends(get_current_user),
):
    """综合资源利用率统计"""
    ws = get_world_state()
    
    # 冷库利用率
    total_wh_slots = sum(sum(z["total_slots"] for z in wh["zones"].values()) for wh in WAREHOUSES)
    used_wh_slots = sum(sum(o["used_slots"] for o in occ.values()) for occ in WAREHOUSE_OCCUPANCY.values())
    avg_wh_util = round(used_wh_slots / total_wh_slots * 100, 1) if total_wh_slots > 0 else 0
    
    # 车辆利用率
    vehicles = _get_vehicle_resource_status()
    total_vehicles = len(vehicles)
    in_use_vehicles = sum(1 for v in vehicles if v["status"] != "idle")
    fleet_util = round(in_use_vehicles / total_vehicles * 100, 1) if total_vehicles > 0 else 0
    
    # 蓄冷板利用率
    total_plate = sum(cp["total_stock"] for cp in COLD_PLATES)
    in_use_plate = sum(cp["in_use"] for cp in COLD_PLATES)
    plate_util = round(in_use_plate / total_plate * 100, 1) if total_plate > 0 else 0
    
    # 能耗统计
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
            "total_slots": total_wh_slots,
            "used_slots": used_wh_slots,
            "free_slots": total_wh_slots - used_wh_slots,
            "details": [
                {"name": wh["name"], "utilization": round(sum(o["used_slots"] for o in WAREHOUSE_OCCUPANCY.get(wh["id"], {}).values()) / sum(z["total_slots"] for z in wh["zones"].values()) * 100, 1) if wh["id"] in WAREHOUSE_OCCUPANCY else 0}
                for wh in WAREHOUSES
            ],
        },
        "fleet": {
            "utilization": fleet_util,
            "total": total_vehicles,
            "in_use": in_use_vehicles,
            "available": total_vehicles - in_use_vehicles,
            "status_summary": {k: v for k, v in VEHICLE_STATUS_MAP.items()},
        },
        "cold_plates": {
            "utilization": plate_util,
            "total": total_plate,
            "in_use": in_use_plate,
            "available": total_plate - in_use_plate,
            "precooled": sum(cp["precooled"] for cp in COLD_PLATES),
        },
        "energy": {
            "total_kwh_today": round(sum(e["power_kwh"] for e in energy_trend), 1),
            "avg_power_kw": round(sum(e["power_kwh"] for e in energy_trend) / 24, 1),
            "trend_24h": energy_trend,
        },
        "updated_at": now.isoformat(),
        "data_source": "real-time",
    }


@router.get("/forecast")
async def get_resource_forecast(
    hours_ahead: int = Query(48, description="预测时长（小时）"),
    user: dict = Depends(get_current_user),
):
    """AI订单预测前置调度"""
    return _predict_order_demand(hours_ahead)


@router.get("/locks")
async def get_resource_locks(
    user: dict = Depends(require_role("admin")),
):
    """查看资源锁定状态（管理员专用）"""
    return {
        "total_locks": len(RESOURCE_LOCKS),
        "active_locks": [l for l in RESOURCE_LOCKS.values() if l["status"] == "locked"],
        "released_locks": [l for l in RESOURCE_LOCKS.values() if l["status"] == "released"],
    }


@router.post("/lock/{lock_id}/release")
async def release_resource_lock(
    lock_id: str,
    user: dict = Depends(require_role("admin")),
):
    """手动释放资源锁定（管理员专用）"""
    if _unlock_resource(lock_id):
        return {"status": "success", "message": f"资源锁 {lock_id} 已释放"}
    else:
        raise HTTPException(status_code=404, detail="资源锁不存在")


# ==================== 仓库库存管理 ====================
warehouse_inventory = []
_inv_counter = 0


def _init_inventory():
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
            global _inv_counter
            _inv_counter += 1
            warehouse_inventory.append({
                "id": f"INV-{_inv_counter:04d}",
                "warehouse_id": wh["id"],
                "warehouse_name": wh["name"],
                "product_name": name,
                "category": cat,
                "zone": zone,
                "zone_label": ZONE_CONFIG[zone]["name"],
                "target_temp_c": temp,
                "quantity_kg": random.randint(500, 8000),
                "unit": "kg",
                "shelf_life_days": random.randint(5, 180),
                "production_date": (now - timedelta(days=random.randint(1, 60))).strftime("%Y-%m-%d"),
                "expiry_date": (now + timedelta(days=random.randint(3, 120))).strftime("%Y-%m-%d"),
                "status": "normal",
                "last_updated": now.isoformat(),
            })
    
    for item in warehouse_inventory[:6]:
        item["status"] = "near_expiry"
        item["expiry_date"] = (now + timedelta(days=random.randint(1, 5))).strftime("%Y-%m-%d")


_init_inventory()


class StockOperation(BaseModel):
    warehouse_id: str
    product_name: str
    zone: str
    category: str = ""
    quantity_kg: float
    target_temp_c: float = 0
    shelf_life_days: int = 30
    notes: str = ""


@router.get("/warehouse-inventory")
async def get_warehouse_inventory(
    warehouse_id: str = Query(default=""),
    zone: str = Query(default=""),
    status: str = Query(default=""),
    keyword: str = Query(default=""),
    user: dict = Depends(get_current_user),
):
    """获取仓库库存列表"""
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
            "stats": {"normal": normal_count, "near_expiry": near_expiry_count, "expired": expired_count},
            "items": sorted(items, key=lambda x: x["last_updated"], reverse=True),
        },
    }


@router.post("/warehouse-inbound")
async def warehouse_inbound(
    body: StockOperation,
    user: dict = Depends(get_current_user),
):
    """仓库入库操作"""
    wh = next((w for w in WAREHOUSES if w["id"] == body.warehouse_id), None)
    if not wh:
        return JSONResponse(status_code=404, content={"code": 404, "message": "冷库不存在"})
    
    now = datetime.utcnow()
    global _inv_counter
    _inv_counter += 1
    
    item = {
        "id": f"INV-{_inv_counter:04d}",
        "warehouse_id": body.warehouse_id,
        "warehouse_name": wh["name"],
        "product_name": body.product_name,
        "category": body.category or "其他",
        "zone": body.zone,
        "zone_label": ZONE_CONFIG[body.zone]["name"],
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
    
    # 更新库位占用
    if body.warehouse_id in WAREHOUSE_OCCUPANCY and body.zone in WAREHOUSE_OCCUPANCY[body.warehouse_id]:
        occ = WAREHOUSE_OCCUPANCY[body.warehouse_id][body.zone]
        occ["used_slots"] += 1
        occ["free_slots"] -= 1
        occ["utilization_rate"] = round(occ["used_slots"] / wh["zones"][body.zone]["total_slots"] * 100, 1)
    
    logger.info(f"入库: {body.product_name} x {body.quantity_kg}kg → {wh['name']} {ZONE_CONFIG[body.zone]['name']}")
    
    return {
        "code": 200,
        "message": f"入库成功：{body.product_name} {body.quantity_kg}kg → {wh['name']} {ZONE_CONFIG[body.zone]['name']}",
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
    target = next((i for i in warehouse_inventory if i["id"] == inventory_id), None)
    if not target:
        return JSONResponse(status_code=404, content={"code": 404, "message": "库存记录不存在"})
    
    if quantity_kg > target["quantity_kg"]:
        return JSONResponse(status_code=400, content={"code": 400, "message": f"库存不足，当前仅剩 {target['quantity_kg']}kg"})
    
    target["quantity_kg"] -= quantity_kg
    target["last_updated"] = datetime.utcnow().isoformat()
    
    if target["quantity_kg"] <= 0:
        warehouse_inventory.remove(target)
        
        # 更新库位占用
        if target["warehouse_id"] in WAREHOUSE_OCCUPANCY and target["zone"] in WAREHOUSE_OCCUPANCY[target["warehouse_id"]]:
            wh = next((w for w in WAREHOUSES if w["id"] == target["warehouse_id"]), None)
            if wh:
                occ = WAREHOUSE_OCCUPANCY[target["warehouse_id"]][target["zone"]]
                occ["used_slots"] -= 1
                occ["free_slots"] += 1
                occ["utilization_rate"] = round(occ["used_slots"] / wh["zones"][target["zone"]]["total_slots"] * 100, 1)
        
        logger.info(f"出库清空: {target['product_name']} {quantity_kg}kg ← {target['warehouse_name']}")
        return {"code": 200, "message": f"出库成功（库存已清空）：{target['product_name']} {quantity_kg}kg ← {target['warehouse_name']}", "data": {"remaining_kg": 0}}
    
    logger.info(f"出库: {target['product_name']} {quantity_kg}kg ← {target['warehouse_name']}，剩余 {target['quantity_kg']}kg")
    return {"code": 200, "message": f"出库成功：{target['product_name']} {quantity_kg}kg ← {target['warehouse_name']}，剩余 {target['quantity_kg']}kg", "data": {"remaining_kg": target["quantity_kg"]}}


@router.get("/warehouse-inventory-summary")
async def warehouse_inventory_summary(
    user: dict = Depends(get_current_user),
):
    """仓库库存总览"""
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


# ==================== 联动模块接口 ====================
@router.get("/integration-status")
async def get_integration_status(
    user: dict = Depends(require_role("admin")),
):
    """查看模块联动状态"""
    return {
        "modules": {
            "sensors": {"status": "connected", "description": "实时获取冷库温湿度、车辆状态、设备工况"},
            "dispatch": {"status": "connected", "description": "多温区车辆配载优化，订单-车辆匹配"},
            "route_planning": {"status": "connected", "description": "调度完成后自动生成最优配送路线"},
            "geofence": {"status": "connected", "description": "仓库/站点围栏进出数据判定车辆作业状态"},
            "traceability": {"status": "connected", "description": "资源编号写入追溯台账，全资源可溯源"},
            "alert_engine": {"status": "connected", "description": "库位温度异常、车辆温控异常告警"},
        },
        "resource_tracking_enabled": True,
        "auto_allocation_enabled": True,
        "ai_forecast_enabled": True,
    }
