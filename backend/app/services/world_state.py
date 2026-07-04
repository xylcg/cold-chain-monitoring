"""
统一数据模拟层 - 虚拟冷链世界状态
所有 API 端点共享同一个数据源，确保数据跨页面联通

模拟场景：30辆车正在全国冷链配送，5个冷库在运转
"""
import random
import math
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional

# 固定随机种子，保证同一分钟内数据一致性
def _seed():
    seed_val = int(datetime.utcnow().timestamp()) // 30
    random.seed(seed_val)

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

# ==================== 车辆路线 ====================
VEHICLE_ROUTES = [
    ["北京", "天津", "沈阳", "长春", "哈尔滨"],
    ["北京", "济南", "南京", "上海"],
    ["太原", "郑州", "合肥", "南京", "杭州"],
    ["石家庄", "北京", "沈阳", "大连"],
    ["北京", "郑州", "武汉", "长沙", "广州"],
    ["天津", "石家庄", "郑州", "武汉", "深圳"],
    ["北京", "郑州", "武汉", "长沙", "南宁"],
    ["北京", "呼和浩特", "银川", "兰州"],
    ["天津", "太原", "西安", "兰州", "乌鲁木齐"],
    ["北京", "西安", "成都", "昆明"],
    ["石家庄", "郑州", "西安", "成都", "拉萨"],
    ["上海", "杭州", "福州", "厦门", "深圳"],
    ["上海", "南昌", "长沙", "广州", "海口"],
    ["南京", "合肥", "南昌", "广州", "三亚"],
    ["上海", "杭州", "武汉", "长沙", "南宁"],
    ["上海", "南京", "武汉", "重庆", "成都"],
    ["杭州", "南昌", "长沙", "贵阳", "昆明"],
    ["南京", "合肥", "郑州", "西安"],
    ["武汉", "长沙", "广州", "深圳"],
    ["郑州", "武汉", "重庆", "成都"],
    ["武汉", "长沙", "南宁", "海口"],
    ["郑州", "西安", "成都", "贵阳", "南宁"],
    ["广州", "南宁", "贵阳", "重庆"],
    ["深圳", "广州", "南宁", "昆明"],
    ["乌鲁木齐", "兰州", "西安", "成都", "重庆"],
    ["西宁", "兰州", "西安", "武汉"],
    ["哈尔滨", "长春", "沈阳", "大连", "青岛", "上海"],
    ["沈阳", "大连", "济南", "南京", "杭州"],
    ["哈尔滨", "沈阳", "北京", "郑州", "武汉", "广州", "深圳"],
    ["乌鲁木齐", "兰州", "西安", "成都", "重庆", "贵阳", "南宁", "海口"],
]

# ==================== 货物类型 ====================
CARGO_TYPES = [
    {"name": "冷冻牛肉", "zone": "frozen", "target_temp": -20, "temp_range": (-22, -16)},
    {"name": "冷冻海鲜", "zone": "frozen", "target_temp": -22, "temp_range": (-24, -18)},
    {"name": "冰淇淋", "zone": "frozen", "target_temp": -25, "temp_range": (-26, -22)},
    {"name": "冷藏乳制品", "zone": "refrigerated", "target_temp": 2, "temp_range": (0, 4)},
    {"name": "冷藏水果", "zone": "refrigerated", "target_temp": 3, "temp_range": (1, 5)},
    {"name": "新鲜蔬菜", "zone": "refrigerated", "target_temp": 3, "temp_range": (2, 6)},
    {"name": "疫苗试剂", "zone": "refrigerated", "target_temp": 3, "temp_range": (2, 8)},
    {"name": "生物试剂", "zone": "refrigerated", "target_temp": 4, "temp_range": (2, 8)},
    {"name": "恒温药品", "zone": "ambient", "target_temp": 20, "temp_range": (15, 25)},
    {"name": "鲜花", "zone": "refrigerated", "target_temp": 2, "temp_range": (0, 5)},
    {"name": "巧克力", "zone": "ambient", "target_temp": 18, "temp_range": (15, 22)},
    {"name": "冷冻预制菜", "zone": "frozen", "target_temp": -18, "temp_range": (-20, -15)},
]

# ==================== 冷库数据 ====================
WAREHOUSES = [
    {"id": "WH-BJ-01", "name": "华北中心冷库", "location": "北京市大兴区", "lat": 39.72, "lng": 116.33,
     "frozen_slots": 200, "refrigerated_slots": 200, "ambient_slots": 100, "city": "北京"},
    {"id": "WH-SH-01", "name": "华东配送中心", "location": "上海市嘉定区", "lat": 31.38, "lng": 121.25,
     "frozen_slots": 350, "refrigerated_slots": 300, "ambient_slots": 150, "city": "上海"},
    {"id": "WH-GZ-01", "name": "华南前置仓", "location": "广州市白云区", "lat": 23.17, "lng": 113.27,
     "frozen_slots": 180, "refrigerated_slots": 150, "ambient_slots": 70, "city": "广州"},
    {"id": "WH-CD-01", "name": "西南冷链基地", "location": "成都市龙泉驿区", "lat": 30.57, "lng": 104.27,
     "frozen_slots": 250, "refrigerated_slots": 250, "ambient_slots": 100, "city": "成都"},
    {"id": "WH-WH-01", "name": "华中分拨中心", "location": "武汉市东西湖区", "lat": 30.62, "lng": 114.13,
     "frozen_slots": 200, "refrigerated_slots": 180, "ambient_slots": 70, "city": "武汉"},
]

# ==================== 冷机型号 ====================
REFRIGERATION_UNITS = {
    "Carrier-Transicold": {"brand": "Carrier", "model": "Transicold X4", "mtbf_hours": 8000, "typical_life_hours": 50000},
    "ThermoKing-SLXi": {"brand": "Thermo King", "model": "SLXi-400", "mtbf_hours": 7500, "typical_life_hours": 45000},
    "Mitsubishi-CS": {"brand": "Mitsubishi", "model": "CS-2200", "mtbf_hours": 9000, "typical_life_hours": 55000},
    "Daikin-LRY": {"brand": "Daikin", "model": "LRY-180", "mtbf_hours": 8500, "typical_life_hours": 50000},
    "国产瑞风-3000": {"brand": "瑞风", "model": "RF-3000", "mtbf_hours": 6500, "typical_life_hours": 40000},
}

# ==================== 车辆生成 ====================
def _generate_vehicle(index: int):
    """为索引 i 生成一辆一致的冷链车辆"""
    route_idx = index % len(VEHICLE_ROUTES)
    route = VEHICLE_ROUTES[route_idx]
    cargo = CARGO_TYPES[index % len(CARGO_TYPES)]
    unit_names = list(REFRIGERATION_UNITS.keys())
    unit_name = unit_names[index % len(unit_names)]
    unit_info = REFRIGERATION_UNITS[unit_name]

    # 在路线上确定当前位置
    progress = (index * 0.173 + random.random() * 0.3) % 1.0
    seg_idx = int(progress * (len(route) - 1))
    seg_idx = min(seg_idx, len(route) - 2)
    seg_progress = progress * (len(route) - 1) - seg_idx
    from_city = route[seg_idx]
    to_city = route[min(seg_idx + 1, len(route) - 1)]
    from_coord = CITY_COORDS.get(from_city, (39.9, 116.4))
    to_coord = CITY_COORDS.get(to_city, (39.9, 116.4))
    lat = from_coord[0] + (to_coord[0] - from_coord[0]) * seg_progress + random.uniform(-0.15, 0.15)
    lng = from_coord[1] + (to_coord[1] - from_coord[1]) * seg_progress + random.uniform(-0.15, 0.15)

    # 温度模拟（正常范围 + 偶尔异常）
    target = cargo["target_temp"]
    rng = cargo["temp_range"]
    temp = target + random.gauss(0, (rng[1] - rng[0]) / 6)
    # 5% 概率出现温度异常
    anomaly = random.random() < 0.05
    if anomaly:
        temp = target + random.choice([random.uniform(4, 10), random.uniform(-10, -4)])

    humidity = round(random.uniform(55, 75), 1)

    # 冷机健康度（weibull分布模拟）
    life_ratio = (index * 173 + random.randint(0, 5000)) % unit_info["typical_life_hours"] / unit_info["typical_life_hours"]
    health = max(0.3, 1.0 - life_ratio * random.uniform(0.8, 1.2))

    device_id = f"VEH-{index+1:04d}"
    plate = f"冷A-{index+1:04d}"

    return {
        "device_id": device_id,
        "plate_number": plate,
        "device_type": "vehicle",
        "online": True,
        "latitude": round(lat, 4),
        "longitude": round(lng, 4),
        "temperature": round(temp, 1),
        "humidity": humidity,
        "target_temperature": target,
        "external_temp": round(random.uniform(18, 38), 1),
        "vehicle_speed": round(random.uniform(0, 100), 1),
        "door_status": 1 if anomaly else 0,
        "vibration": round(random.uniform(0, 2), 2),
        "cold_car_status": 1 if health > 0.4 else 0,
        "cold_car_health": round(health, 2),
        "battery_level": round(random.uniform(50, 100), 1),
        "signal_strength": random.randint(3, 5),
        "route": route,
        "current_city": from_city,
        "cargo_type": cargo["name"],
        "cargo_zone": cargo["zone"],
        "waybill_no": f"WB-{datetime.utcnow().strftime('%Y%m%d')}-{index+1:04d}",
        "refrigeration_unit": unit_name,
        "refrigeration_brand": unit_info["brand"],
        "refrigeration_model": unit_info["model"],
        "active_alerts": random.randint(1, 3) if anomaly else 0,
        "last_update": datetime.utcnow().isoformat(),
        "temperature_compliant": not anomaly,
    }


# ==================== 冷机维护数据 ====================
def _generate_maintenance_data(vehicle: dict):
    """为车辆生成冷机维护预测数据"""
    _seed()
    index = int(vehicle["device_id"].split("-")[1]) - 1
    unit_info = REFRIGERATION_UNITS.get(
        vehicle.get("refrigeration_unit", "Carrier-Transicold"),
        REFRIGERATION_UNITS["Carrier-Transicold"]
    )

    total_hours = (index * 173 + random.randint(0, 5000)) % unit_info["typical_life_hours"]
    remaining_life = max(0, unit_info["typical_life_hours"] - total_hours)
    health = max(0.3, 1.0 - total_hours / unit_info["typical_life_hours"])

    # 故障概率（基于Weibull分布）
    shape = 2.5
    scale = unit_info["mtbf_hours"]
    failure_prob = 1 - math.exp(-(total_hours / scale) ** shape)
    failure_prob = min(0.95, failure_prob * random.uniform(0.8, 1.2))

    if failure_prob < 0.3:
        risk_level = "low"
    elif failure_prob < 0.6:
        risk_level = "medium"
    else:
        risk_level = "high"

    # 特征重要性
    feature_importance = {
        "压缩机运行时长": round(random.uniform(0.25, 0.40), 3),
        "冷凝器温度": round(random.uniform(0.12, 0.22), 3),
        "制冷剂压力": round(random.uniform(0.10, 0.18), 3),
        "振动幅度": round(random.uniform(0.08, 0.15), 3),
        "环境温度": round(random.uniform(0.05, 0.10), 3),
        "电源稳定性": round(random.uniform(0.03, 0.08), 3),
        "累计启停次数": round(random.uniform(0.05, 0.12), 3),
        "保养间隔天数": round(random.uniform(0.02, 0.06), 3),
    }

    return {
        "device_id": vehicle["device_id"],
        "plate_number": vehicle["plate_number"],
        "refrigeration_unit": vehicle.get("refrigeration_unit", "Carrier-Transicold"),
        "brand": unit_info["brand"],
        "model": unit_info["model"],
        "total_operating_hours": total_hours,
        "remaining_life_hours": remaining_life,
        "health_score": round(health * 100, 1),
        "failure_probability": round(failure_prob * 100, 1),
        "risk_level": risk_level,
        "feature_importance": feature_importance,
        "predicted_failure_mode": random.choice(["压缩机磨损", "冷凝器堵塞", "制冷剂泄漏", "电气故障", "轴承磨损"]),
        "recommended_action": "建议在24小时内安排检修" if risk_level == "high"
        else "建议在一周内安排保养" if risk_level == "medium"
        else "运行正常，按计划保养即可",
        "current_params": {
            "compressor_temp_c": round(random.uniform(40, 85), 1),
            "condenser_pressure_bar": round(random.uniform(8, 25), 1),
            "refrigerant_level_pct": round(random.uniform(60, 100), 1),
            "vibration_mm_s": round(random.uniform(0.5, 4.5), 2),
            "power_consumption_kw": round(random.uniform(2, 8), 1),
            "ambient_temp_c": round(random.uniform(20, 38), 1),
        },
        "maintenance_history": _generate_maintenance_history(vehicle["device_id"]),
    }


def _generate_maintenance_history(device_id: str):
    """生成维护历史"""
    _seed()
    idx = int(device_id.split("-")[1]) if "-" in device_id else 0
    now = datetime.utcnow()
    history = []
    for i in range(random.randint(1, 5)):
        days_ago = random.randint(10, 400)
        history.append({
            "date": (now - timedelta(days=days_ago)).strftime("%Y-%m-%d"),
            "type": random.choice(["定期保养", "故障维修", "零件更换", "紧急检修"]),
            "description": random.choice(["更换滤芯", "补充制冷剂", "压缩机检修", "电气线路检查", "冷凝器清洗"]),
            "cost_yuan": random.randint(500, 8000),
            "technician": random.choice(["张工", "李工", "王工", "赵工"]),
            "duration_hours": random.randint(2, 48),
        })
    return sorted(history, key=lambda x: x["date"], reverse=True)


# ==================== 告警数据 ====================
def _generate_alerts_for_vehicle(vehicle: dict) -> list:
    """为车辆生成告警数据"""
    _seed()
    alerts = []
    if vehicle.get("active_alerts", 0) > 0:
        severity = random.choice(["normal", "severe", "critical"]) if vehicle["cold_car_health"] < 0.5 else "normal"
        alert_types = {
            "normal": "温度轻微偏离设定值",
            "severe": "温度持续偏高，建议检查冷机",
            "critical": "温度严重超标！冷机可能故障，立即处理",
        }
        alerts.append({
            "alert_id": f"{vehicle['device_id']}:temp-{random.randint(1, 999)}",
            "device_id": vehicle["device_id"],
            "type": "temperature_anomaly",
            "severity": severity,
            "message": alert_types[severity],
            "temperature": vehicle["temperature"],
            "threshold": vehicle["target_temperature"],
            "timestamp": datetime.utcnow().isoformat(),
            "acknowledged": False,
        })

    if vehicle.get("cold_car_status", 1) == 0:
        alerts.append({
            "alert_id": f"{vehicle['device_id']}:coldcar-{random.randint(1, 999)}",
            "device_id": vehicle["device_id"],
            "type": "cold_car_failure",
            "severity": "critical",
            "message": "冷机故障停机，车厢温度快速上升！",
            "temperature": vehicle["temperature"],
            "timestamp": datetime.utcnow().isoformat(),
            "acknowledged": False,
        })
    return alerts


# ==================== 品质评估数据 ====================
QUALITY_PRODUCTS = [
    {"key": "apple", "name": "苹果", "category": "水果", "freshness_days": 30, "storage_temp": 2},
    {"key": "strawberry", "name": "草莓", "category": "水果", "freshness_days": 5, "storage_temp": 2},
    {"key": "beef", "name": "牛肉", "category": "肉类", "freshness_days": 21, "storage_temp": -18},
    {"key": "lettuce", "name": "生菜", "category": "蔬菜", "freshness_days": 7, "storage_temp": 3},
    {"key": "salmon", "name": "三文鱼", "category": "海鲜", "freshness_days": 10, "storage_temp": -20},
    {"key": "milk", "name": "鲜奶", "category": "乳制品", "freshness_days": 7, "storage_temp": 2},
    {"key": "vaccine", "name": "疫苗", "category": "医药制品", "freshness_days": 90, "storage_temp": 3},
    {"key": "shrimp", "name": "虾仁", "category": "海鲜", "freshness_days": 15, "storage_temp": -22},
    {"key": "pork", "name": "猪肉", "category": "肉类", "freshness_days": 14, "storage_temp": -18},
    {"key": "spinach", "name": "菠菜", "category": "蔬菜", "freshness_days": 5, "storage_temp": 3},
    {"key": "yogurt", "name": "酸奶", "category": "乳制品", "freshness_days": 14, "storage_temp": 2},
    {"key": "flower", "name": "玫瑰", "category": "花卉", "freshness_days": 10, "storage_temp": 2},
]

QUALITY_BATCHES = []


def _generate_quality_batches():
    """生成品质批次数据"""
    global QUALITY_BATCHES
    if QUALITY_BATCHES:
        return QUALITY_BATCHES
    _seed()
    origins = ["山东寿光", "云南昆明", "海南三亚", "内蒙古呼和浩特", "辽宁大连", "福建厦门", "新疆乌鲁木齐", "广东湛江"]
    grades = ["S", "A", "A", "A", "B", "B", "B", "B", "C", "D"]

    for i in range(25):
        product = QUALITY_PRODUCTS[i % len(QUALITY_PRODUCTS)]
        grade = grades[i % len(grades)]
        storage_days = random.randint(1, product["freshness_days"])
        remaining = max(0, product["freshness_days"] - storage_days)

        scores = {"S": 95, "A": 85, "B": 70, "C": 55, "D": 35}
        base_score = scores.get(grade, 70)
        score = base_score + random.randint(-5, 5)

        QUALITY_BATCHES.append({
            "batch_id": f"BATCH-{datetime.utcnow().strftime('%Y%m')}-{i+1:04d}",
            "product_type": product["name"],
            "category": product["category"],
            "grade": grade,
            "quality_score": score,
            "origin": origins[i % len(origins)],
            "quantity_kg": random.randint(200, 5000),
            "storage_days": storage_days,
            "storage_temp_c": product["storage_temp"],
            "total_freshness_days": product["freshness_days"],
            "remaining_shelf_life_days": remaining,
            "status": "in_storage" if remaining > 0 else "expired",
            "overall_score": score,
            "defect_detected": grade in ("C", "D"),
            "defects": ["轻微变色", "表面水分流失"] if grade == "C" else ["明显腐烂", "异味"] if grade == "D" else [],
        })
    return QUALITY_BATCHES


# ==================== 全局世界状态获取 ====================
_world_cache = {}
_cache_time = 0


def get_world_state():
    """获取全局世界状态（缓存30秒）"""
    global _world_cache, _cache_time
    now = datetime.utcnow().timestamp()

    if _world_cache and now - _cache_time < 30:
        return _world_cache

    _seed()

    # 生成30辆活跃车辆
    vehicles = [_generate_vehicle(i) for i in range(30)]

    # 生成告警
    all_alerts = []
    for v in vehicles:
        all_alerts.extend(_generate_alerts_for_vehicle(v))

    # 生成冷库利用率
    warehouse_utils = []
    for wh in WAREHOUSES:
        frozen_used = int(wh["frozen_slots"] * random.uniform(0.5, 0.95))
        refrig_used = int(wh["refrigerated_slots"] * random.uniform(0.5, 0.9))
        ambient_used = int(wh["ambient_slots"] * random.uniform(0.4, 0.85))
        total_slots = wh["frozen_slots"] + wh["refrigerated_slots"] + wh["ambient_slots"]
        total_used = frozen_used + refrig_used + ambient_used
        warehouse_utils.append({
            **wh,
            "frozen_used": frozen_used,
            "refrigerated_used": refrig_used,
            "ambient_used": ambient_used,
            "total_slots": total_slots,
            "total_used": total_used,
            "utilization": round(total_used / total_slots * 100, 1),
            "frozen_util": round(frozen_used / wh["frozen_slots"] * 100, 1),
            "refrigerated_util": round(refrig_used / wh["refrigerated_slots"] * 100, 1),
            "ambient_util": round(ambient_used / wh["ambient_slots"] * 100, 1),
        })

    # 生成品质批次
    quality_batches = _generate_quality_batches()

    # 生成运单数据
    waybills = {}
    for v in vehicles:
        wb_id = v["waybill_no"]
        origin_city = v["route"][0]
        dest_city = v["route"][-1]
        records = []
        for i in range(144):  # 24小时，每10分钟一条
            ts = now - 24 * 3600 + i * 600
            temp = v["temperature"] + random.gauss(0, 0.5)
            door = 1 if i % 36 == 0 else 0
            if door:
                temp += random.uniform(1, 3)
            records.append({
                "timestamp": datetime.fromtimestamp(ts).isoformat(),
                "temperature": round(temp, 1),
                "humidity": round(v["humidity"] + random.gauss(0, 2), 1),
                "door_status": door,
                "location": v["route"][min(i * len(v["route"]) // 144, len(v["route"]) - 1)],
            })

        temps = [r["temperature"] for r in records]
        waybills[wb_id] = {
            "waybill_id": wb_id,
            "cargo_type": v["cargo_type"],
            "temperature_requirement": f"{v['cargo_zone']} ({min(temps):.0f}°C ~ {max(temps):.0f}°C)",
            "origin": origin_city,
            "destination": dest_city,
            "departure_time": datetime.fromtimestamp(now - 24 * 3600).isoformat(),
            "estimated_arrival": datetime.fromtimestamp(now + random.randint(2, 8) * 3600).isoformat(),
            "current_status": "运输中",
            "records": records,
            "current_temperature": temps[-1],
            "avg_temperature": round(sum(temps) / len(temps), 1),
            "temperature_range": f"{min(temps):.1f}°C ~ {max(temps):.1f}°C",
            "is_compliant": all(abs(t - v["target_temperature"]) < 6 for t in temps),
        }

    # KPI 汇总
    online_count = len(vehicles)
    compliant_count = sum(1 for v in vehicles if v["temperature_compliant"])
    critical_count = sum(1 for a in all_alerts if a["severity"] == "critical")
    avg_temp = sum(v["temperature"] for v in vehicles) / online_count if online_count > 0 else 0
    avg_humidity = sum(v["humidity"] for v in vehicles) / online_count if online_count > 0 else 0

    # 资源利用统计
    total_wh_slots = sum(wh["total_slots"] for wh in warehouse_utils)
    total_wh_used = sum(wh["total_used"] for wh in warehouse_utils)
    fleet_size = 50  # 总车队规模

    kpi = {
        "total_devices": 110,
        "online_devices": online_count,
        "online_rate": round(online_count / 110 * 100, 1),
        "temperature_compliance_rate": round(compliant_count / online_count * 100, 1) if online_count > 0 else 0,
        "active_alerts": len(all_alerts),
        "critical_alerts": critical_count,
        "avg_temperature": round(avg_temp, 1),
        "avg_humidity": round(avg_humidity, 1),
        "timestamp": datetime.utcnow().isoformat(),
        "data_source": "unified_simulation",
        # 额外数据
        "warehouse_utilization": round(total_wh_used / total_wh_slots * 100, 1) if total_wh_slots > 0 else 0,
        "fleet_online_rate": round(online_count / fleet_size * 100, 1),
        "total_waybills": len(waybills),
        "quality_batches": len(quality_batches),
    }

    _world_cache = {
        "vehicles": vehicles,
        "alerts": all_alerts,
        "warehouses": warehouse_utils,
        "quality_batches": quality_batches,
        "waybills": waybills,
        "kpi": kpi,
        "timestamp": datetime.utcnow().isoformat(),
    }
    _cache_time = now

    return _world_cache


def find_nearest_city(lat: float, lng: float) -> str:
    best_city = "北京"
    best_dist = float("inf")
    for city, (clat, clng) in CITY_COORDS.items():
        dlat = (lat - clat) ** 2
        dlng = ((lng - clng) * math.cos(math.radians((lat + clat) / 2))) ** 2
        dist = dlat + dlng
        if dist < best_dist:
            best_dist = dist
            best_city = city
    return best_city
