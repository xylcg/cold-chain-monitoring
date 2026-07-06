"""
冷机故障预测性维护 API
使用统一世界状态，确保数据跨页面联通
"""
import random
from datetime import datetime
from fastapi import APIRouter, Depends, Query

from ..services.world_state import get_world_state, _generate_maintenance_data
from ..core.security import get_current_user

router = APIRouter(prefix="/api/v1/maintenance", tags=["故障预测维护"])


@router.get("/predict")
async def predict_all(
    risk_level: str = Query(None),
    user: dict = Depends(get_current_user),
):
    """对所有设备进行冷机故障预测 - 基于统一世界状态"""
    ws = get_world_state()
    results = []

    for v in ws["vehicles"]:
        data = _generate_maintenance_data(v)
        if risk_level and data.get("risk_level") != risk_level:
            continue
        results.append(data)

    results.sort(key=lambda x: x.get("failure_probability", 0), reverse=True)
    
    high_count = sum(1 for r in results if r.get("risk_level") == "high")
    medium_count = sum(1 for r in results if r.get("risk_level") == "medium")
    low_count = sum(1 for r in results if r.get("risk_level") == "low")
    
    return {
        "total_devices": len(ws["vehicles"]),
        "analyzed": len(results),
        "predictions": results,
        "summary": {
            "critical_high": high_count,
            "high_risk": high_count,
            "medium": medium_count,
            "medium_risk": medium_count,
            "low": low_count,
            "low_risk": low_count,
            "normal": max(0, len(ws["vehicles"]) - high_count - medium_count - low_count),
        },
    }


@router.get("/predict/{device_id}")
async def predict_device(device_id: str, user: dict = Depends(get_current_user)):
    """单个设备预测 - 基于统一世界状态"""
    ws = get_world_state()
    vehicle = next((v for v in ws["vehicles"] if v["device_id"] == device_id), None)
    if not vehicle:
        # fallback
        from ..services.world_state import _generate_vehicle
        idx = int(device_id.split("-")[1]) - 1 if "-" in device_id else 0
        vehicle = _generate_vehicle(idx)
    return _generate_maintenance_data(vehicle)


@router.get("/status")
async def get_status(user: dict = Depends(get_current_user)):
    """维护状态概览 - 基于统一世界状态"""
    ws = get_world_state()
    results = [_generate_maintenance_data(v) for v in ws["vehicles"]]

    return {
        "total_devices": len(ws["vehicles"]),
        "high_risk": sum(1 for r in results if r.get("risk_level") == "high"),
        "medium_risk": sum(1 for r in results if r.get("risk_level") == "medium"),
        "low_risk": sum(1 for r in results if r.get("risk_level") == "low"),
        "avg_health_score": round(sum(r.get("health_score", 0) for r in results) / max(len(results), 1), 1),
        "devices_need_maintenance": [r for r in results if r.get("risk_level") in ("high", "medium")],
        "timestamp": ws["timestamp"],
    }


@router.get("/history/{device_id}")
async def get_history(device_id: str, user: dict = Depends(get_current_user)):
    """设备维护历史 - 基于统一世界状态"""
    data = _generate_maintenance_data({"device_id": device_id, "refrigeration_unit": "Carrier-Transicold"})
    return {
        "device_id": device_id,
        "history": data.get("maintenance_history", []),
    }
