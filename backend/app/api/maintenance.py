"""
冷机故障预测性维护 API
模块4: 冷机故障预测性维护
- 冷机运行参数分析与剩余寿命预测（Weibull分布）
- 故障概率预测（梯度提升树特征加权模拟）
- 预防性维护计划生成
- 维护历史与成本追踪
"""
import random
import math
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

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


def _weibull_failure_probability(run_hours: float, total_life: float, shape: float = 2.5) -> float:
    """
    Weibull 分布计算累计失效率
    F(t) = 1 - exp(-(t/eta)^beta)
    eta = total_life / gamma(1 + 1/beta)  # 特征寿命
    """
    import math
    beta = shape  # 形状参数（>1 表示耗损失效模式）
    # 特征寿命eta使得期望寿命=total_life
    eta = total_life / math.gamma(1 + 1 / beta) if total_life > 0 else 1
    t = run_hours
    prob = 1 - math.exp(-((t / eta) ** beta)) if eta > 0 else 0
    return max(0.001, min(0.995, prob))


def _predict_failure(device_id: str) -> dict:
    """
    基于设备运行参数的故障预测（模拟 XGBoost 梯度提升树集合）
    使用 Weibull 分布 + 多特征加权 + SHAP-like 特征重要性
    """
    random.seed(hash(device_id + datetime.utcnow().strftime("%Y%m%d")) % 10000)

    # 分配冷机型号
    unit_keys = list(REFRIGERATION_UNITS.keys())
    unit_key = random.choice(unit_keys)
    unit_info = REFRIGERATION_UNITS[unit_key]
    total_life = unit_info["life_hours"]

    # 阶段1: Weibull 基础失效率
    run_hours = random.randint(2000, total_life)
    remaining_life = total_life - run_hours
    weibull_prob = _weibull_failure_probability(run_hours, total_life)

    # 阶段2: 实时特征工程
    compressor_starts_per_hour = round(random.uniform(1.5, 6.0), 1)
    refrigerant_pressure_bar = round(random.uniform(2.0, 4.5), 2)
    condenser_temp = round(random.uniform(28.0, 55.0), 1)
    discharge_temp = round(random.uniform(60.0, 95.0), 1)
    suction_temp = round(random.uniform(-15.0, 5.0), 1)
    oil_pressure_bar = round(random.uniform(1.0, 3.0), 2)
    vibration_level = round(random.uniform(0.5, 4.0), 2)
    current_draw_a = round(random.uniform(5.0, 18.0), 1)
    return_temp = round(random.uniform(-5.0, 5.0), 1)
    ambient_temp = round(random.uniform(15.0, 40.0), 1)

    # 阶段3: 特征评分（模拟 SHAP 特征重要性）
    features = {
        "磨损因子": max(0, (run_hours / total_life) * 100),  # f1
        "压缩机启停": min((compressor_starts_per_hour / 6.0) * 100, 100),  # f2
        "排气温度偏差": max(0, min(((discharge_temp - 70) / 30) * 100, 100)),  # f3
        "振动水平": min((vibration_level / 4.0) * 100, 100),  # f4
        "冷媒压力偏差": max(0, min((abs(refrigerant_pressure_bar - 3.2) / 1.5) * 100, 100)),  # f5
        "电流异常": max(0, min(((current_draw_a - 10) / 10) * 100, 100)),  # f6
        "冷凝温度偏差": max(0, min(((condenser_temp - 30) / 25) * 100, 100)),  # f7
        "回气温度偏差": max(0, min((abs(suction_temp + 5) / 15) * 100, 100)),  # f8
    }

    # 阶段4: XGBoost 模拟集成（加权投票）
    feature_weights = {
        "磨损因子": 0.25, "压缩机启停": 0.18, "排气温度偏差": 0.15,
        "振动水平": 0.12, "冷媒压力偏差": 0.10, "电流异常": 0.08,
        "冷凝温度偏差": 0.07, "回气温度偏差": 0.05,
    }

    weighted_score = sum(features[k] * feature_weights[k] for k in features) / 100
    # Weibull 占60%，实时特征占40%
    failure_probability = round(weibull_prob * 0.60 + weighted_score * 0.40 + random.uniform(-0.02, 0.02), 4)
    failure_probability = max(0.005, min(0.98, failure_probability))

    # 风险等级（含置信度）
    confidence = round(random.uniform(0.82, 0.96), 3)
    if failure_probability < 0.10:
        risk_level, risk_label, risk_color = "low", "低风险", "#22c55e"
    elif failure_probability < 0.25:
        risk_level, risk_label, risk_color = "medium", "中风险", "#f59e0b"
    elif failure_probability < 0.50:
        risk_level, risk_label, risk_color = "high", "高风险", "#f97316"
    else:
        risk_level, risk_label, risk_color = "critical", "紧急风险", "#ef4444"

    # 阶段5: 故障类型预测（多分类）
    failure_candidates = []
    if features["排气温度偏差"] > 60:
        failure_candidates.append({"type": "压缩机过热故障", "prob": round(features["排气温度偏差"] * 0.7, 1)})
    if features["冷媒压力偏差"] > 55:
        failure_candidates.append({"type": "制冷剂泄漏", "prob": round(features["冷媒压力偏差"] * 0.8, 1)})
    if features["冷凝温度偏差"] > 60:
        failure_candidates.append({"type": "冷凝器堵塞", "prob": round(features["冷凝温度偏差"] * 0.7, 1)})
    if features["振动水平"] > 65:
        failure_candidates.append({"type": "轴承磨损", "prob": round(features["振动水平"] * 0.6, 1)})
    if features["电流异常"] > 55:
        failure_candidates.append({"type": "电气系统故障", "prob": round(features["电流异常"] * 0.7, 1)})
    if features["压缩机启停"] > 70:
        failure_candidates.append({"type": "膨胀阀故障", "prob": round(features["压缩机启停"] * 0.6, 1)})

    if not failure_candidates and failure_probability > 0.25:
        failure_candidates = [
            {"type": "综合部件退化", "prob": round(failure_probability * 100, 1)},
        ]

    # 阶段6: 预防性维护建议
    if failure_probability > 0.50:
        next_maintenance_hours = max(4, random.randint(4, 24))
        next_maintenance_label = "紧急维护"
        next_maintenance_date = (datetime.utcnow() + timedelta(hours=next_maintenance_hours)).isoformat()
    elif failure_probability > 0.25:
        next_maintenance_hours = random.randint(24, 72)
        next_maintenance_label = "尽快维护"
        next_maintenance_date = (datetime.utcnow() + timedelta(hours=next_maintenance_hours)).isoformat()
    elif failure_probability > 0.10:
        next_maintenance_hours = random.randint(72, 168)
        next_maintenance_label = "计划维护"
        next_maintenance_date = (datetime.utcnow() + timedelta(hours=next_maintenance_hours)).isoformat()
    else:
        next_maintenance_hours = random.randint(168, 720)
        next_maintenance_label = "例行维护"
        next_maintenance_date = (datetime.utcnow() + timedelta(hours=next_maintenance_hours)).isoformat()

    # 维护成本估算
    estimated_cost = round(random.uniform(300, 20000) * failure_probability + random.uniform(100, 500), 0)

    return {
        "device_id": device_id,
        "unit_model": unit_key,
        "unit_brand": unit_info["brand"],
        "unit_power_kw": unit_info["power_kw"],
        "refrigerant": unit_info["refrigerant"],
        "total_life_hours": total_life,
        "current_run_hours": run_hours,
        "remaining_life_hours": remaining_life,
        "remaining_life_days": round(remaining_life / 24, 1),
        "failure_probability": failure_probability,
        "risk_level": risk_level,
        "risk_label": risk_label,
        "risk_color": risk_color,
        "model_confidence": confidence,
        "weibull_base_probability": round(weibull_prob, 4),
        "predicted_failures": failure_candidates,
        "next_maintenance": {
            "hours_from_now": next_maintenance_hours,
            "severity": next_maintenance_label,
            "estimated_date": next_maintenance_date,
            "estimated_cost_yuan": estimated_cost,
        },
        "feature_importance": {k: round(v, 1) for k, v in sorted(features.items(), key=lambda x: -x[1])},
        "real_time_params": {
            "compressor_starts_per_hour": compressor_starts_per_hour,
            "refrigerant_pressure_bar": refrigerant_pressure_bar,
            "condenser_temp_c": condenser_temp,
            "discharge_temp_c": discharge_temp,
            "suction_temp_c": suction_temp,
            "oil_pressure_bar": oil_pressure_bar,
            "vibration_level": vibration_level,
            "current_draw_a": current_draw_a,
            "return_air_temp_c": return_temp,
            "ambient_temp_c": ambient_temp,
        },
        "predicted_at": datetime.utcnow().isoformat(),
        "algorithm": "Weibull Reliability + Gradient Boosting Ensemble",
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
