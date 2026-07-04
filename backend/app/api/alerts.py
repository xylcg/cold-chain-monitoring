"""
告警管理 API
使用统一世界状态，确保数据跨页面联通
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional

from ..services.world_state import get_world_state
from ..schemas import AlertSeverity, AlertRuleCreate
from ..services.alert_engine import alert_engine
from ..core.security import get_current_user

router = APIRouter(prefix="/api/v1/alerts", tags=["告警管理"])

_notification_log: list[dict] = []


@router.get("")
async def get_alerts(
    severity: Optional[str] = None,
    device_id: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    limit: int = 50,
    user: dict = Depends(get_current_user),
):
    """查询告警列表 - 来自统一世界状态"""
    ws = get_world_state()
    alerts = ws["alerts"]

    if severity:
        alerts = [a for a in alerts if a.get("severity") == severity]
    if device_id:
        alerts = [a for a in alerts if a.get("device_id") == device_id]

    return {"count": len(alerts[:limit]), "alerts": alerts[:limit]}


@router.get("/active")
async def get_active_alerts(user: dict = Depends(get_current_user)):
    """获取当前活跃告警 - 来自统一世界状态"""
    ws = get_world_state()
    alerts = ws["alerts"]

    device_alerts = {}
    for a in alerts:
        did = a["device_id"]
        if did not in device_alerts:
            device_alerts[did] = []
        device_alerts[did].append(a)

    active_summary = []
    for did, alist in device_alerts.items():
        vehicle = next((v for v in ws["vehicles"] if v["device_id"] == did), None)
        active_summary.append({
            "device_id": did,
            "active_alerts": len(alist),
            "alerts": alist,
            "last_temperature": vehicle["temperature"] if vehicle else None,
            "last_update": vehicle["last_update"] if vehicle else None,
        })

    return {
        "total_devices_with_alerts": len(active_summary),
        "devices": active_summary,
    }


@router.get("/stats")
async def get_alert_stats(hours: int = 24, user: dict = Depends(get_current_user)):
    """告警统计 - 来自统一世界状态"""
    ws = get_world_state()
    alerts = ws["alerts"]

    severity_counts = {"normal": 0, "severe": 0, "critical": 0}
    for a in alerts:
        sev = a.get("severity", "normal")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    return {
        "period_hours": hours,
        "total_notifications": len(alerts),
        "by_severity": severity_counts,
        "by_channel": {"sms": len(alerts), "email": len(alerts), "websocket": len(alerts)},
    }


@router.post("/acknowledge/{alert_id}")
async def acknowledge_alert(
    alert_id: str, action: str = "acknowledged", notes: str = "",
    user: dict = Depends(get_current_user),
):
    """确认/处置告警"""
    username = user.get("sub", "unknown")
    return {
        "status": "ok", "alert_id": alert_id, "action": action,
        "acknowledged_by": username,
        "acknowledged_at": datetime.utcnow().isoformat(), "notes": notes,
    }


@router.get("/notifications")
async def get_notification_log(
    channel: Optional[str] = None, severity: Optional[str] = None,
    limit: int = 30, user: dict = Depends(get_current_user),
):
    """查询通知日志"""
    logs = _notification_log
    if channel:
        logs = [l for l in logs if l.get("channel") == channel]
    if severity:
        logs = [l for l in logs if l.get("severity") == severity]
    logs = sorted(logs, key=lambda l: l.get("timestamp", ""), reverse=True)
    return {"count": len(logs[:limit]), "notifications": logs[:limit]}


@router.get("/rules")
async def get_alert_rules(user: dict = Depends(get_current_user)):
    rules = alert_engine.get_rules()
    return {"count": len(rules), "rules": rules}


@router.post("/rules")
async def create_alert_rule(rule: AlertRuleCreate, user: dict = Depends(get_current_user)):
    rule_dict = {
        "field": rule.condition_field, "op": rule.condition_operator,
        "value": rule.condition_value, "severity": rule.severity.value,
        "type": rule.rule_type, "msg": f"{rule.rule_name}触发",
    }
    alert_engine.add_rule(rule_dict)
    return {"status": "ok", "rule": rule_dict}


@router.delete("/rules/{rule_type}")
async def delete_alert_rule(rule_type: str, user: dict = Depends(get_current_user)):
    alert_engine.remove_rule(rule_type)
    return {"status": "ok", "deleted": rule_type}
