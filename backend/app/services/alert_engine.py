"""
智能预警引擎 - 三级告警分级与分发
"""
import json
import asyncio
from datetime import datetime
from typing import Optional
from loguru import logger

from ..core.config import get_settings
from ..schemas import AlertSeverity, TEMP_THRESHOLD
from .redis_service import redis_service
from .kafka_service import kafka_service

settings = get_settings()


class AlertEngine:
    """智能预警引擎"""

    # 默认告警规则
    DEFAULT_RULES = [
        {"field": "temperature", "op": ">", "value": TEMP_THRESHOLD["WARN_UPPER"],
         "severity": "severe", "type": "temperature_high", "msg": "温度超标"},
        {"field": "temperature", "op": ">", "value": TEMP_THRESHOLD["DANGER_UPPER"],
         "severity": "critical", "type": "temperature_critical", "msg": "温度严重超标"},
        {"field": "temperature", "op": "<", "value": TEMP_THRESHOLD["LOW_LIMIT"],
         "severity": "normal", "type": "temperature_low", "msg": "温度偏低"},
        {"field": "humidity", "op": ">", "value": TEMP_THRESHOLD["HUMIDITY_HIGH"],
         "severity": "normal", "type": "humidity_high", "msg": "湿度过高"},
        {"field": "vibration", "op": ">", "value": TEMP_THRESHOLD["VIBRATION_HIGH"],
         "severity": "normal", "type": "vibration_high", "msg": "振动异常"},
        {"field": "door_status", "op": "==", "value": 1, "severity": "normal",
         "type": "door_open", "msg": "车门开启"},
    ]

    # 三级预警分发策略
    SEVERITY_ROUTES = {
        "normal": ["driver"],           # 一般预警 → 配送员
        "severe": ["driver", "manager", "repair"],  # 严重预警 → 配送员+区域经理+维修
        "critical": ["driver", "manager", "repair", "customer"],  # 紧急预警 → 全部+客户
    }

    def __init__(self):
        self._rules = self.DEFAULT_RULES.copy()

    def evaluate(self, sensor_data: dict) -> list[dict]:
        """评估传感器数据，返回触发的告警列表"""
        alerts = []
        device_id = sensor_data.get("device_id", "unknown")

        for rule in self._rules:
            field = rule["field"]
            value = sensor_data.get(field)

            if value is None:
                continue

            triggered = False
            op = rule["op"]

            if op == ">" and value > rule["value"]:
                triggered = True
            elif op == "<" and value < rule["value"]:
                triggered = True
            elif op == "==" and value == rule["value"]:
                triggered = True
            elif op == ">=" and value >= rule["value"]:
                triggered = True
            elif op == "<=" and value <= rule["value"]:
                triggered = True

            if triggered:
                alert = {
                    "device_id": device_id,
                    "alert_type": rule["type"],
                    "severity": rule["severity"],
                    "message": f"{rule['msg']}: {field}={value}, 阈值={rule['value']}",
                    "sensor_value": value,
                    "threshold_value": rule["value"],
                    "timestamp": datetime.utcnow().isoformat(),
                    "targets": self.SEVERITY_ROUTES.get(rule["severity"], ["driver"]),
                }
                alerts.append(alert)

        return alerts

    async def process_alert(self, alert: dict) -> bool:
        """处理告警：冷却检查 + 存储 + 分发"""
        device_id = alert["device_id"]
        alert_type = alert["alert_type"]

        # 检查冷却期
        cooldown = TEMP_THRESHOLD["COOLDOWN_SECONDS"] if alert["severity"] != "critical" else TEMP_THRESHOLD["COOLDOWN_CRITICAL"]
        can_send = await redis_service.check_alert_cooldown(
            device_id, alert_type, cooldown
        )
        if not can_send:
            return False

        # 存储告警
        kafka_service.send_alert(alert)

        # 递增活跃告警计数
        await redis_service.incr_active_alerts(device_id)

        # 通过 Redis Pub/Sub 实时推送
        alert_json = json.dumps(alert, ensure_ascii=False)
        for target in alert["targets"]:
            await redis_service.publish(f"alerts:{target}", alert_json)
        await redis_service.publish(f"alerts:device:{device_id}", alert_json)

        severity = alert["severity"]
        logger.warning(
            f"[{severity.upper()}] 告警: {alert['message']} "
            f"→ 推送至 {alert['targets']}"
        )
        return True

    def add_rule(self, rule: dict):
        """动态添加告警规则"""
        self._rules.append(rule)

    def remove_rule(self, rule_type: str):
        """删除告警规则"""
        self._rules = [r for r in self._rules if r["type"] != rule_type]

    def get_rules(self) -> list[dict]:
        return self._rules.copy()


# 全局单例
alert_engine = AlertEngine()
