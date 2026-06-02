"""
冷机故障预测性维护 API
模块4: 冷机故障预测性维护
- 冷机运行参数分析
- 故障概率预测（基于梯度提升树/XGBoost模拟）
- 剩余使用寿命预估
- 维护提醒与历史记录
"""
import random
import math
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from ..core.security import get_current_user
from ..services.redis_service import redis_service

router = APIRouter(prefix="/api/v1/maintenance", tags=["故障预测维护"])

# ==================== 模拟冷机运行参数 ====================

# 冷机型号与基准参数
REFRIGERATION_UNITS = {
    "TK-800": {"brand": "冷王Thermo King", "power_kw": 8.5, "life_hours": 15000, "refrigerant": "R-404A"},
    "CR-500": {"brand": "开利Carrier", "power_kw": 12.0, "life_hours": 18000, "refrigerant": "R-452A"},
    "DF-300": {"brand": "大冷Dalian", "power_kw": 5.5, "life_hours": 12000, "refrigerant": "R-134a"},
    "SX-600": {"brand": "松下Panasonic", "power_kw": 7.0, "life_hours": 14000, "refrigerant": "R-410A"},
}

# 生成模拟维护历史
def _generate_maintenance_history(device_id: str) -> list:
    random.seed(hash(device_id) % 10000)
    history = []
    total_units = len(REFRIGERATION_UNITS)
    unit_idx = abs(hash(device_id)) % total_units
    unit_key = list(REFRIGERATION_UNITS.keys())[unit_idx]
    unit_info = REFRIGERATION_UNITS[unit_key]
    total_life = unit_info["life_hours"]

    now = datetime.utcnow()
    install_date = now - timedelta(days=random.randint(180, 900))
    run_hours = random.randint(2000, total_life - 1000)

    events = [
        {"type": "安装", "date": install_date, "notes": "冷机初始安装"},
        {"type": "例行保养", "date": install_date + timedelta(days=90), "notes": "更换滤芯、检查制冷剂"},
        {"type": "例行保养", "date": install_date + timedelta(days=180), "notes": "清洗冷凝器、检查压缩机"},
    ]

    if random.random() < 0.4:
        events.append({
            "type": "零部件更换",
            "date": install_date + timedelta(days=random.randint(200, 400)),
            "notes": random.choice(["更换蒸发器风扇", "更换膨胀阀", "更换温度传感器", "更换压缩机皮带"]),
        })

    if random.random() < 0.2:
        events.append({
            "type": "故障维修",
            "date": install_date + timedelta(days=random.randint(300, 600)),
            "notes": random.choice(["制冷剂泄漏修复", "压缩机故障修复", "控制器固件升级故障"]),
        })

    events.append({"type": "例行保养", "date": now - timedelta(days=random.randint(10, 60)), "notes": "常规检查"})

    for e in sorted(events, key=lambda x: x["date"]):
        history.append({
            "event_id": f"mh-{abs(hash(device_id + str(e['date']))) % 100000:05d}",
            "device_id": device_id,
            "event_type": e["type"],
            "event_date": e["date"].isoformat(),
            "notes": e["notes"],
            "technician": random.choice(["张工", "李工", "王工", "赵工"]),
            "cost_yuan": random.randint(300, 5000) if "维修" in e["type"] or "更换" in e["type"] else random.randint(100, 800),
        })
    return history


def _predict_failure(device_id: str) -> dict:
    """基于设备运行参数模拟故障预测（模拟XGBoost推理）"""
    random.seed(hash(device_id + datetime.utcnow().strftime("%Y%m%d")) % 10000)

    # 随机选择冷机型号
    unit_keys = list(REFRIGERATION_UNITS.keys())
    unit_key = random.choice(unit_keys)
    unit_info = REFRIGERATION_UNITS[unit_key]
    total_life = unit_info["life_hours"]

    # 模拟运行参数
    run_hours = random.randint(2000, total_life)
    remaining_life = total_life - run_hours

    # 模拟冷机关键参数
    compressor_starts_per_hour = round(random.uniform(1.5, 6.0), 1)
    refrigerant_pressure_bar = round(random.uniform(2.0, 4.5), 2)
    condenser_temp = round(random.uniform(28.0, 55.0), 1)
    discharge_temp = round(random.uniform(60.0, 95.0), 1)
    suction_temp = round(random.uniform(-15.0, 5.0), 1)
    oil_pressure_bar = round(random.uniform(1.0, 3.0), 2)
    vibration_level = round(random.uniform(0.5, 4.0), 2)
    current_draw_a = round(random.uniform(5.0, 18.0), 1)

    # 模拟特征工程 → 故障概率
    # 剩余寿命越少、压缩机启停越频繁、排气温度越高 → 故障概率越高
    wear_factor = 1 - (remaining_life / total_life)
    compressor_factor = min(compressor_starts_per_hour / 6.0, 1.0)
    temp_factor = max(0, (discharge_temp - 60) / 35.0)
    vibration_factor = vibration_level / 4.0

    # 加权计算故障概率（模拟XGBoost集成输出）
    base_prob = 0.02
    failure_probability = round(
        base_prob +
        wear_factor * 0.45 +
        compressor_factor * 0.20 +
        temp_factor * 0.20 +
        vibration_factor * 0.13 +
        random.uniform(-0.03, 0.03),
        4
    )
    failure_probability = max(0.01, min(0.98, failure_probability))

    # 风险等级
    if failure_probability < 0.15:
        risk_level = "low"
        risk_label = "低风险"
    elif failure_probability < 0.40:
        risk_level = "medium"
        risk_label = "中风险"
    elif failure_probability < 0.65:
        risk_level = "high"
        risk_label = "高风险"
    else:
        risk_level = "critical"
        risk_label = "紧急风险"

    # 预测故障类型
    if failure_probability > 0.3:
        failure_types = ["压缩机故障", "制冷剂泄漏", "冷凝器堵塞", "膨胀阀故障", "电气系统故障"]
        predicted_type = random.choice(failure_types[:min(int(failure_probability * 5) + 1, 5)])
    else:
        predicted_type = None

    # 建议维护时间
    if remaining_life < 168:
        next_maintenance_hours = max(4, remaining_life // 2)
        next_maintenance_label = "立即维护"
    elif failure_probability > 0.5:
        next_maintenance_hours = random.randint(24, 72)
        next_maintenance_label = "尽快维护"
    elif failure_probability > 0.25:
        next_maintenance_hours = random.randint(72, 168)
        next_maintenance_label = "计划维护"
    else:
        next_maintenance_hours = random.randint(168, 500)
        next_maintenance_label = "例行维护"

    return {
        "device_id": device_id,
        "unit_model": unit_key,
        "unit_brand": unit_info["brand"],
        "unit_power_kw": unit_info["power_kw"],
        "total_life_hours": total_life,
        "current_run_hours": run_hours,
        "remaining_life_hours": remaining_life,
        "remaining_life_days": round(remaining_life / 24, 1),
        "failure_probability": failure_probability,
        "risk_level": risk_level,
        "risk_label": risk_label,
        "predicted_failure_type": predicted_type,
        "next_maintenance_hours": next_maintenance_hours,
        "next_maintenance_label": next_maintenance_label,
        "feature_importance": {
            "运行时长占比": round(wear_factor * 100, 1),
            "压缩机启停频率": round(compressor_factor * 100, 1),
            "排气温度异常": round(temp_factor * 100, 1),
            "振动水平": round(vibration_factor * 100, 1),
        },
        "real_time_params": {
            "compressor_starts_per_hour": compressor_starts_per_hour,
            "refrigerant_pressure_bar": refrigerant_pressure_bar,
            "condenser_temp_c": condenser_temp,
            "discharge_temp_c": discharge_temp,
            "suction_temp_c": suction_temp,
            "oil_pressure_bar": oil_pressure_bar,
            "vibration_level": vibration_level,
            "current_draw_a": current_draw_a,
        },
        "predicted_at": datetime.utcnow().isoformat(),
    }


# ==================== API 接口 ====================

@router.get("/predict")
async def predict_all_devices(
    status: Optional[str] = Query(None, description="风险等级过滤: low/medium/high/critical"),
    user: dict = Depends(get_current_user),
):
    """对所有在线冷藏车进行冷机故障预测"""
    device_list = []
    try:
        # 优先从 Redis 获取在线设备
        online_devices = await redis_service.get_online_devices()
        device_list = online_devices if online_devices else []
    except Exception:
        pass

    # 如果没有在线设备数据，生成模拟数据
    if not device_list:
        device_list = [f"VEH-{i:04d}" for i in range(1, 51)]

    predictions = []
    for device_id in device_list[:50]:  # 最多50个设备
        pred = _predict_failure(device_id)
        if status and pred["risk_level"] != status:
            continue
        predictions.append(pred)

    # 排序：风险高的在前
    predictions.sort(key=lambda x: -x["failure_probability"])

    # 统计
    high_risk = sum(1 for p in predictions if p["risk_level"] in ("high", "critical"))
    medium_risk = sum(1 for p in predictions if p["risk_level"] == "medium")
    low_risk = sum(1 for p in predictions if p["risk_level"] == "low")

    return {
        "total_devices": len(predictions),
        "summary": {
            "critical_high": high_risk,
            "medium": medium_risk,
            "low": low_risk,
        },
        "predictions": predictions,
    }


@router.get("/predict/{device_id}")
async def predict_device(
    device_id: str,
    user: dict = Depends(get_current_user),
):
    """单个设备冷机故障预测"""
    pred = _predict_failure(device_id)
    history = _generate_maintenance_history(device_id)
    pred["maintenance_history"] = history
    return pred


@router.get("/status")
async def get_maintenance_status(
    user: dict = Depends(get_current_user),
):
    """获取所有设备的维护状态概览"""
    devices = [f"VEH-{i:04d}" for i in range(1, 31)]
    status_list = []
    critical = high = medium = low = 0

    for device_id in devices:
        pred = _predict_failure(device_id)
        if pred["risk_level"] == "critical":
            critical += 1
        elif pred["risk_level"] == "high":
            high += 1
        elif pred["risk_level"] == "medium":
            medium += 1
        else:
            low += 1

        status_list.append({
            "device_id": device_id,
            "unit_model": pred["unit_model"],
            "risk_level": pred["risk_level"],
            "failure_probability": pred["failure_probability"],
            "remaining_life_days": pred["remaining_life_days"],
            "next_maintenance_label": pred["next_maintenance_label"],
        })

    status_list.sort(key=lambda x: -x["failure_probability"])

    return {
        "total": len(status_list),
        "critical": critical,
        "high": high,
        "medium": medium,
        "low": low,
        "devices": status_list,
    }


@router.get("/history/{device_id}")
async def get_history(
    device_id: str,
    user: dict = Depends(get_current_user),
):
    """获取设备维护历史"""
    return {
        "device_id": device_id,
        "unit_model": list(REFRIGERATION_UNITS.keys())[abs(hash(device_id)) % len(REFRIGERATION_UNITS)],
        "history": _generate_maintenance_history(device_id),
    }
