"""
智能预警与应急处置 API
模块13: 智能预警与应急处置

核心功能：
- 三级预警分级管理（一般/严重/紧急）
- 全场景异常告警查询
- 差异化推送管理
- 紧急预警标准化应急预案
- 全流程闭环处置机制
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Dict

from ..services.alert_engine import alert_engine, ALERT_TYPES, SEVERITY_LEVELS
from ..services.world_state import get_world_state
from ..core.security import get_current_user, require_role

router = APIRouter(prefix="/api/v1/alerts", tags=["智能预警与应急处置"])

_notification_log: List[Dict] = []


def _add_notification(alert: dict, channel: str = "api"):
    """记录告警通知日志"""
    _notification_log.append({
        "alert_id": alert.get("alert_id", alert.get("device_id", "") + "-" + datetime.utcnow().isoformat()),
        "device_id": alert.get("device_id", ""),
        "severity": alert.get("severity", "normal"),
        "message": alert.get("message", ""),
        "channel": channel,
        "timestamp": datetime.utcnow().isoformat(),
    })
    if len(_notification_log) > 500:
        _notification_log[:] = _notification_log[-500:]


# ==================== 预警查询接口 ====================

@router.get("")
async def get_alerts(
    severity: Optional[str] = None,
    category: Optional[str] = None,
    device_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    user: dict = Depends(get_current_user),
):
    """查询告警列表"""
    alerts = alert_engine.get_alert_history(limit=limit * 2)

    if severity:
        alerts = [a for a in alerts if a.get("severity") == severity]
    if category:
        alerts = [a for a in alerts if a.get("category") == category]
    if device_id:
        alerts = [a for a in alerts if a.get("device_id") == device_id]
    if status:
        alerts = [a for a in alerts if a.get("status") == status]

    return {"count": len(alerts[:limit]), "alerts": alerts[:limit]}


@router.get("/active")
async def get_active_alerts(
    severity: Optional[str] = None,
    category: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    """获取当前活跃告警"""
    alerts = alert_engine.get_active_alerts()

    if severity:
        alerts = [a for a in alerts if a.get("severity") == severity]
    if category:
        alerts = [a for a in alerts if a.get("category") == category]

    device_alerts = {}
    for a in alerts:
        did = a["device_id"]
        if did not in device_alerts:
            device_alerts[did] = []
        device_alerts[did].append(a)

    active_summary = []
    ws = get_world_state()
    for did, alist in device_alerts.items():
        vehicle = next((v for v in ws["vehicles"] if v["device_id"] == did), None)
        active_summary.append({
            "device_id": did,
            "active_alerts": len(alist),
            "alerts": alist,
            "last_temperature": vehicle["temperature"] if vehicle else None,
            "last_update": vehicle["last_update"] if vehicle else None,
            "vehicle_info": vehicle if vehicle else None,
        })

    return {
        "total_devices_with_alerts": len(active_summary),
        "total_active_alerts": len(alerts),
        "devices": active_summary,
    }


@router.get("/active/{alert_id}")
async def get_active_alert_detail(alert_id: str, user: dict = Depends(get_current_user)):
    """获取单个活跃告警详情"""
    alerts = alert_engine.get_active_alerts()
    alert = next((a for a in alerts if a.get("alert_id") == alert_id), None)
    if not alert:
        raise HTTPException(status_code=404, detail="告警不存在或已处理")
    return alert


# ==================== 分级预警查询 ====================

@router.get("/level/normal")
async def get_normal_alerts(user: dict = Depends(get_current_user)):
    """获取一般预警（司机自主处理）"""
    alerts = alert_engine.get_alerts_by_severity("normal")
    return {"count": len(alerts), "alerts": alerts}


@router.get("/level/severe")
async def get_severe_alerts(user: dict = Depends(get_current_user)):
    """获取严重预警（需人工介入）"""
    alerts = alert_engine.get_alerts_by_severity("severe")
    return {"count": len(alerts), "alerts": alerts}


@router.get("/level/critical")
async def get_critical_alerts(user: dict = Depends(get_current_user)):
    """获取紧急预警（启动应急预案）"""
    alerts = alert_engine.get_alerts_by_severity("critical")
    return {"count": len(alerts), "alerts": alerts}


# ==================== 司机专属告警 ====================

@router.get("/driver")
async def get_driver_alerts(
    device_id: str = None,
    limit: int = 20,
    user: dict = Depends(require_role("driver", "admin", "warehouse")),
):
    """司机查看自己车辆的告警列表"""
    ws = get_world_state()
    all_alerts = alert_engine.get_alert_history(limit=limit * 2)
    driver_name = user.get("sub", "")
    role = user.get("role", "")

    if role == "driver" or device_id:
        if not device_id:
            driver_vehicles = [
                v for v in ws["vehicles"]
                if v.get("driver_name", "") == driver_name or v.get("driver_id", "") == driver_name
            ]
            if driver_vehicles:
                device_ids = set(v["device_id"] for v in driver_vehicles)
                all_alerts = [a for a in all_alerts if a.get("device_id") in device_ids]
        else:
            all_alerts = [a for a in all_alerts if a.get("device_id") == device_id]

    all_alerts.sort(key=lambda a: a.get("timestamp", ""), reverse=True)
    result = all_alerts[:limit]

    for a in result:
        _add_notification(a, channel="driver_query")

    return {"count": len(result), "alerts": result, "driver": driver_name}


# ==================== 告警统计 ====================

@router.get("/stats")
async def get_alert_stats(
    hours: int = 24,
    user: dict = Depends(get_current_user),
):
    """告警统计"""
    stats = alert_engine.get_stats()
    ws = get_world_state()
    ws_alerts = ws.get("alerts", [])

    severity_counts = {"normal": 0, "severe": 0, "critical": 0}
    for a in ws_alerts:
        sev = a.get("severity", "normal")
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    return {
        "period_hours": hours,
        "total_notifications": len(ws_alerts),
        "by_severity": {**severity_counts, **stats.get("by_severity", {})},
        "by_category": stats.get("by_category", {}),
        "total_active": stats.get("total_active", 0),
        "total_history": stats.get("total_history", 0),
        "by_channel": {"sms": len(ws_alerts), "email": len(ws_alerts), "websocket": len(ws_alerts)},
    }


# ==================== 告警闭环处置 ====================

@router.post("/acknowledge/{alert_id}")
async def acknowledge_alert(
    alert_id: str,
    action: str = "acknowledged",
    notes: str = "",
    user: dict = Depends(get_current_user),
):
    """确认/处置告警"""
    username = user.get("sub", "unknown")
    success = alert_engine.acknowledge_alert(alert_id, username, action, notes)

    if not success:
        raise HTTPException(status_code=404, detail="告警不存在或已处理")

    _add_notification({
        "alert_id": alert_id, "device_id": "", "severity": "normal",
        "message": f"告警已{action} by {username}"
    }, channel="acknowledge")

    return {
        "status": "ok", "alert_id": alert_id, "action": action,
        "acknowledged_by": username,
        "acknowledged_at": datetime.utcnow().isoformat(), "notes": notes,
    }


@router.post("/resolve/{alert_id}")
async def resolve_alert(
    alert_id: str,
    resolution: str = "",
    notes: str = "",
    user: dict = Depends(get_current_user),
):
    """解决告警（标记为已解决）"""
    username = user.get("sub", "unknown")
    success = alert_engine.acknowledge_alert(alert_id, username, "resolved", notes)

    if not success:
        raise HTTPException(status_code=404, detail="告警不存在或已处理")

    return {
        "status": "ok", "alert_id": alert_id,
        "action": "resolved",
        "resolution": resolution,
        "resolved_by": username,
        "resolved_at": datetime.utcnow().isoformat(),
        "notes": notes,
    }


# ==================== 应急预案管理 ====================

@router.get("/emergency/plans")
async def get_emergency_plans(
    status: Optional[str] = None,
    limit: int = 50,
    user: dict = Depends(require_role("admin", "manager")),
):
    """获取应急预案列表"""
    alerts = alert_engine.get_alert_history(limit=limit * 2)
    plans = []

    for alert in alerts:
        plan = alert.get("emergency_plan")
        if plan:
            if status and plan.get("status") != status:
                continue
            plans.append({
                "plan_id": plan["plan_id"],
                "plan_name": plan["plan_name"],
                "alert_id": plan["alert_id"],
                "device_id": plan["device_id"],
                "trigger_time": plan["trigger_time"],
                "status": plan["status"],
                "priority": plan["priority"],
                "steps_completed": sum(1 for s in plan["steps"] if s.get("status") == "completed"),
                "total_steps": len(plan["steps"]),
            })

    return {"count": len(plans), "plans": plans[:limit]}


@router.get("/emergency/plan/{plan_id}")
async def get_emergency_plan_detail(
    plan_id: str,
    user: dict = Depends(require_role("admin", "manager")),
):
    """获取应急预案详情"""
    alerts = alert_engine.get_alert_history(limit=100)
    for alert in alerts:
        plan = alert.get("emergency_plan")
        if plan and plan.get("plan_id") == plan_id:
            return plan

    raise HTTPException(status_code=404, detail="应急预案不存在")


@router.post("/emergency/trigger/{alert_id}")
async def trigger_emergency_plan(
    alert_id: str,
    user: dict = Depends(require_role("admin", "manager")),
):
    """手动触发应急预案"""
    alerts = alert_engine.get_active_alerts()
    alert = next((a for a in alerts if a.get("alert_id") == alert_id), None)

    if not alert:
        raise HTTPException(status_code=404, detail="告警不存在")

    if alert.get("severity") != "critical":
        raise HTTPException(status_code=400, detail="只有紧急告警才能触发应急预案")

    if alert.get("emergency_plan"):
        return {"status": "ok", "message": "应急预案已触发", "plan": alert["emergency_plan"]}

    from ..services.alert_engine import alert_engine as engine
    plan = engine._build_emergency_plan(alert)
    alert["emergency_plan"] = plan

    return {
        "status": "ok",
        "message": "应急预案已触发",
        "plan": plan,
    }


@router.post("/emergency/plan/{plan_id}/step/{step_num}")
async def update_emergency_step(
    plan_id: str,
    step_num: int,
    status: str = "completed",
    notes: str = "",
    user: dict = Depends(require_role("admin", "manager")),
):
    """更新应急预案步骤状态"""
    alerts = alert_engine.get_alert_history(limit=100)
    for alert in alerts:
        plan = alert.get("emergency_plan")
        if plan and plan.get("plan_id") == plan_id:
            step = next((s for s in plan["steps"] if s.get("step") == step_num), None)
            if not step:
                raise HTTPException(status_code=404, detail="步骤不存在")

            step["status"] = status
            step["updated_by"] = user.get("sub", "unknown")
            step["updated_at"] = datetime.utcnow().isoformat()
            if notes:
                step["notes"] = notes

            completed_steps = sum(1 for s in plan["steps"] if s.get("status") == "completed")
            if completed_steps == len(plan["steps"]):
                plan["status"] = "completed"
                plan["completed_at"] = datetime.utcnow().isoformat()

            return {"status": "ok", "plan": plan}

    raise HTTPException(status_code=404, detail="应急预案不存在")


# ==================== 告警规则管理 ====================

@router.get("/rules")
async def get_alert_rules(user: dict = Depends(get_current_user)):
    """获取告警规则"""
    rules = alert_engine.get_rules()
    for rule in rules:
        rule["alert_label"] = ALERT_TYPES.get(rule.get("type", ""), {}).get("label", rule.get("msg", ""))
        rule["category"] = ALERT_TYPES.get(rule.get("type", ""), {}).get("category", "其他")
    return {"count": len(rules), "rules": rules}


@router.post("/rules")
async def create_alert_rule(
    rule: dict,
    user: dict = Depends(get_current_user),
):
    """创建/更新告警规则"""
    rule_dict = {
        "field": rule.get("condition_field", rule.get("field", "temperature")),
        "op": rule.get("condition_operator", rule.get("op", ">")),
        "value": rule.get("condition_value", rule.get("value", 8.0)),
        "severity": rule.get("severity", "severe"),
        "type": rule.get("rule_type", rule.get("type", "custom")),
        "msg": rule.get("rule_name", rule.get("msg", "自定义告警")),
        "enabled": rule.get("enabled", True),
    }
    alert_engine.add_rule(rule_dict)
    return {"status": "ok", "rule": rule_dict}


@router.delete("/rules/{rule_type}")
async def delete_alert_rule(
    rule_type: str,
    user: dict = Depends(get_current_user),
):
    """删除告警规则"""
    alert_engine.remove_rule(rule_type)
    return {"status": "ok", "deleted": rule_type}


# ==================== 预警类型与级别配置 ====================

@router.get("/config/types")
async def get_alert_types(user: dict = Depends(get_current_user)):
    """获取所有告警类型配置"""
    return {"types": ALERT_TYPES}


@router.get("/config/severity")
async def get_severity_config(user: dict = Depends(get_current_user)):
    """获取三级预警级别配置"""
    return {"levels": SEVERITY_LEVELS}


# ==================== 通知日志 ====================

@router.get("/notifications")
async def get_notification_log(
    channel: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 30,
    user: dict = Depends(get_current_user),
):
    """查询通知日志"""
    logs = _notification_log
    if channel:
        logs = [l for l in logs if l.get("channel") == channel]
    if severity:
        logs = [l for l in logs if l.get("severity") == severity]
    logs = sorted(logs, key=lambda l: l.get("timestamp", ""), reverse=True)
    return {"count": len(logs[:limit]), "notifications": logs[:limit]}