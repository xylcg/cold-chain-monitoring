"""
告警管理 API
模块13: 智能预警与应急处置
- 三级告警分级管理
- 告警确认/处置
- 通知渠道管理 (短信/邮件/WebSocket)
- 告警历史统计
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional

from ..schemas import AlertSeverity, AlertRuleCreate
from ..services.alert_engine import alert_engine
from ..services.redis_service import redis_service
from ..core.security import get_current_user

router = APIRouter(prefix="/api/v1/alerts", tags=["告警管理"])


# ==================== 告警通知渠道 ====================
# 模拟通知记录
_notification_log: list[dict] = []


async def _send_sms_notification(phone: str, message: str, severity: str):
    """模拟短信通知"""
    _notification_log.append({
        "channel": "sms",
        "recipient": phone,
        "message": message,
        "severity": severity,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "sent",
    })
    return True


async def _send_email_notification(email: str, message: str, severity: str):
    """模拟邮件通知"""
    _notification_log.append({
        "channel": "email",
        "recipient": email,
        "message": message,
        "severity": severity,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "sent",
    })
    return True


# 联系人配置（模拟数据）
EMERGENCY_CONTACTS = {
    "driver": {"phone": "13800001111", "email": "driver@coldchain.com"},
    "manager": {"phone": "13800002222", "email": "manager@coldchain.com"},
    "repair": {"phone": "13800003333", "email": "repair@coldchain.com"},
    "customer": {"phone": "13800004444", "email": "customer@example.com"},
}


# ==================== 告警查询 ====================

@router.get("")
async def get_alerts(
    severity: Optional[str] = None,
    device_id: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    limit: int = 50,
    user: dict = Depends(get_current_user),
):
    """查询告警列表"""
    try:
        online_devices = await redis_service.get_online_devices()
    except (RuntimeError, Exception):
        online_devices = set()

    alerts = []
    for did in online_devices:
        count = await redis_service.get_active_alerts(did)
        if count > 0:
            status = await redis_service.get_device_status(did)
            alert_info = {
                "device_id": did,
                "alert_count": count,
                "temperature": float(status.get("temperature", 0)) if status else None,
                "last_update": status.get("last_update") if status else None,
            }

            # 按严重等级过滤
            if severity:
                # 从最近告警通知中匹配
                matching = [n for n in _notification_log
                           if n.get("device_id") == did and n.get("severity") == severity]
                if not matching:
                    continue

            alerts.append(alert_info)

    return {
        "count": len(alerts[:limit]),
        "alerts": alerts[:limit],
    }


@router.get("/active")
async def get_active_alerts(user: dict = Depends(get_current_user)):
    """获取当前活跃告警"""
    try:
        online_devices = await redis_service.get_online_devices()
    except (RuntimeError, Exception):
        online_devices = set()

    active_summary = []
    for device_id in online_devices:
        count = await redis_service.get_active_alerts(device_id)
        if count > 0:
            status = await redis_service.get_device_status(device_id)
            active_summary.append({
                "device_id": device_id,
                "active_alerts": count,
                "last_temperature": float(status.get("temperature", 0)) if status else None,
                "last_update": status.get("last_update") if status else None,
            })

    return {
        "total_devices_with_alerts": len(active_summary),
        "devices": active_summary,
    }


@router.get("/severity/{severity}")
async def get_alerts_by_severity(
    severity: AlertSeverity,
    limit: int = 20,
    user: dict = Depends(get_current_user),
):
    """按严重等级查询告警"""
    matching = [n for n in _notification_log if n.get("severity") == severity.value]
    return {
        "severity": severity.value,
        "count": len(matching[:limit]),
        "alerts": matching[:limit],
    }


# ==================== 告警处置 ====================

@router.post("/acknowledge/{alert_id}")
async def acknowledge_alert(
    alert_id: str,
    action: str = "acknowledged",
    notes: str = "",
    user: dict = Depends(get_current_user),
):
    """
    确认/处置告警
    支持三级处置动作: acknowledged(已知晓), processing(处理中), resolved(已解决)
    """
    username = user.get("sub", "unknown")

    # 更新通知记录中的状态
    for n in _notification_log:
        if n.get("alert_id") == alert_id:
            n["status"] = action
            n["acknowledged_by"] = username
            n["acknowledged_at"] = datetime.utcnow().isoformat()
            n["notes"] = notes

    # 减少 Redis 活跃告警计数
    device_id = alert_id.split(":")[0] if ":" in alert_id else alert_id
    try:
        await redis_service.decr_active_alerts(device_id)
    except Exception:
        pass

    return {
        "status": "ok",
        "alert_id": alert_id,
        "action": action,
        "acknowledged_by": username,
        "acknowledged_at": datetime.utcnow().isoformat(),
        "notes": notes,
    }


@router.post("/dispatch/{alert_id}")
async def dispatch_emergency(
    alert_id: str,
    notify_channels: List[str] = ["sms", "email"],
    user: dict = Depends(get_current_user),
):
    """
    应急处置：按严重等级多通道通知
    normal → 仅配送员终端
    severe → 配送员 + 区域经理 + 维修团队
    critical → 全部 + 客户 + 启动应急预案
    """
    # 获取告警信息
    alert_info = None
    for n in _notification_log:
        if n.get("alert_id") == alert_id:
            alert_info = n
            break

    if not alert_info:
        raise HTTPException(status_code=404, detail="告警不存在")

    severity = alert_info.get("severity", "normal")
    targets = alert_engine.SEVERITY_ROUTES.get(severity, ["driver"])

    dispatch_results = []
    for target in targets:
        contact = EMERGENCY_CONTACTS.get(target)
        if not contact:
            continue

        message = f"[{severity.upper()}] {alert_info.get('message', '冷链告警')}"

        if "sms" in notify_channels and contact.get("phone"):
            await _send_sms_notification(contact["phone"], message, severity)
            dispatch_results.append({"channel": "sms", "target": target, "status": "sent"})

        if "email" in notify_channels and contact.get("email"):
            await _send_email_notification(contact["email"], message, severity)
            dispatch_results.append({"channel": "email", "target": target, "status": "sent"})

    return {
        "alert_id": alert_id,
        "severity": severity,
        "targets": targets,
        "dispatch_results": dispatch_results,
    }


# ==================== 通知日志 ====================

@router.get("/notifications")
async def get_notification_log(
    channel: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 30,
    user: dict = Depends(get_current_user),
):
    """查询通知发送日志"""
    logs = _notification_log
    if channel:
        logs = [l for l in logs if l.get("channel") == channel]
    if severity:
        logs = [l for l in logs if l.get("severity") == severity]

    logs = sorted(logs, key=lambda l: l.get("timestamp", ""), reverse=True)
    return {"count": len(logs[:limit]), "notifications": logs[:limit]}


# ==================== 告警统计 ====================

@router.get("/stats")
async def get_alert_stats(
    hours: int = 24,
    user: dict = Depends(get_current_user),
):
    """获取告警统计（用于仪表盘）"""
    cutoff = datetime.utcnow().isoformat()
    recent = [n for n in _notification_log if n.get("timestamp", "") >= cutoff]

    severity_counts = {"normal": 0, "severe": 0, "critical": 0}
    channel_counts = {"sms": 0, "email": 0, "websocket": 0}

    for n in recent:
        sev = n.get("severity", "normal")
        if sev in severity_counts:
            severity_counts[sev] += 1
        ch = n.get("channel", "")
        if ch in channel_counts:
            channel_counts[ch] += 1

    return {
        "period_hours": hours,
        "total_notifications": len(recent),
        "by_severity": severity_counts,
        "by_channel": channel_counts,
    }


# ==================== 告警规则管理 ====================

@router.get("/rules")
async def get_alert_rules(user: dict = Depends(get_current_user)):
    """获取告警规则列表"""
    rules = alert_engine.get_rules()
    return {"count": len(rules), "rules": rules}


@router.post("/rules")
async def create_alert_rule(
    rule: AlertRuleCreate,
    user: dict = Depends(get_current_user),
):
    """创建告警规则"""
    rule_dict = {
        "field": rule.condition_field,
        "op": rule.condition_operator,
        "value": rule.condition_value,
        "severity": rule.severity.value,
        "type": rule.rule_type,
        "msg": f"{rule.rule_name}触发",
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
