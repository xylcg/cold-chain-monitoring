"""
运营管理后台 API
模块12: 运营管理后台
使用统一世界状态，确保数据跨页面联通
"""
from datetime import datetime
from fastapi import APIRouter, Depends

from ..services.world_state import get_world_state
from ..core.security import get_current_user

router = APIRouter(prefix="/api/v1/dashboard", tags=["管理后台"])


@router.get("/kpi")
async def get_kpi(user: dict = Depends(get_current_user)):
    """获取 KPI 仪表盘数据 - 来自统一世界状态"""
    ws = get_world_state()
    return ws["kpi"]


@router.get("/devices")
async def get_devices_status(user: dict = Depends(get_current_user)):
    """获取所有设备状态列表 - 来自统一世界状态"""
    ws = get_world_state()
    devices = ws["vehicles"]
    devices.sort(key=lambda x: x["active_alerts"], reverse=True)
    return {"total": len(devices), "devices": devices, "data_source": "unified"}


@router.get("/overview")
async def get_overview(user: dict = Depends(get_current_user)):
    """获取全局态势图数据 - 来自统一世界状态"""
    ws = get_world_state()
    vehicles = ws["vehicles"]
    return {
        "vehicles": {"count": len(vehicles), "data": vehicles},
        "cold_rooms": {"count": len(ws["warehouses"]), "data": ws["warehouses"]},
        "total_online": len(vehicles),
        "timestamp": ws["timestamp"],
    }


@router.get("/alerts/summary")
async def get_alerts_summary(user: dict = Depends(get_current_user)):
    """获取告警摘要统计 - 来自统一世界状态"""
    ws = get_world_state()
    alerts = ws["alerts"]
    devices_with_alerts = len(set(a["device_id"] for a in alerts))
    return {
        "total_alerts": len(alerts),
        "devices_with_alerts": devices_with_alerts,
        "total_devices_online": len(ws["vehicles"]),
        "alert_rate": round(devices_with_alerts / max(len(ws["vehicles"]), 1) * 100, 1),
        "timestamp": ws["timestamp"],
    }
