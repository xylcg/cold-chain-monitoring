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

    # 默认告警规则（即时触发类）
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
        {"field": "cold_car_status", "op": "==", "value": 0,
         "severity": "severe", "type": "cold_car_failure", "msg": "冷机故障"},
        {"field": "data_quality", "op": "<", "value": TEMP_THRESHOLD["DATA_QUALITY_LOW"],
         "severity": "normal", "type": "data_quality_low", "msg": "数据质量异常"},
    ]

    # 三级预警分发策略
    SEVERITY_ROUTES = {
        "normal": ["driver"],           # 一般预警 → 配送员
        "severe": ["driver", "manager", "repair"],  # 严重预警 → 配送员+区域经理+维修
        "critical": ["driver", "manager", "repair", "customer"],  # 紧急预警 → 全部+客户
    }

    def __init__(self):
        self._rules = self.DEFAULT_RULES.copy()
        # 设备状态追踪（用于时间相关规则）
        self._device_states: dict[str, dict] = {}

    def _get_device_state(self, device_id: str) -> dict:
        """获取或创建设备状态追踪"""
        if device_id not in self._device_states:
            self._device_states[device_id] = {
                "last_temperature": None,
                "last_temp_time": None,
                "door_open_time": None,
                "door_alert_sent": False,
                "last_heartbeat": datetime.utcnow(),
                "offline_alert_sent": False,
            }
        return self._device_states[device_id]

    def evaluate(self, sensor_data: dict) -> list[dict]:
        """评估传感器数据，返回触发的告警列表"""
        alerts = []
        device_id = sensor_data.get("device_id", "unknown")
        now = datetime.utcnow()
        state = self._get_device_state(device_id)

        # 更新心跳时间
        state["last_heartbeat"] = now
        if state["offline_alert_sent"]:
            state["offline_alert_sent"] = False

        # 1. 即时触发类规则
        for rule in self._rules:
            if rule.get("enabled", True) is False:
                continue
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
                    "timestamp": now.isoformat(),
                    "targets": self.SEVERITY_ROUTES.get(rule["severity"], ["driver"]),
                }
                alerts.append(alert)

        # 2. 车门超时开启规则（持续时间判断）
        door_rule_enabled = any(r["type"] == "door_open_timeout" and r.get("enabled", True) for r in self._rules)
        door_status = sensor_data.get("door_status")
        if door_rule_enabled and door_status is not None:
            if door_status == 1:
                if state["door_open_time"] is None:
                    state["door_open_time"] = now
                else:
                    elapsed = (now - state["door_open_time"]).total_seconds()
                    if elapsed > TEMP_THRESHOLD["DOOR_TIMEOUT_SECONDS"] and not state["door_alert_sent"]:
                        alerts.append({
                            "device_id": device_id,
                            "alert_type": "door_open_timeout",
                            "severity": "normal",
                            "message": f"车门超时开启: 已持续{int(elapsed)}秒, 阈值={TEMP_THRESHOLD['DOOR_TIMEOUT_SECONDS']}秒",
                            "sensor_value": elapsed,
                            "threshold_value": TEMP_THRESHOLD["DOOR_TIMEOUT_SECONDS"],
                            "timestamp": now.isoformat(),
                            "targets": self.SEVERITY_ROUTES["normal"],
                        })
                        state["door_alert_sent"] = True
            else:
                state["door_open_time"] = None
                state["door_alert_sent"] = False

        # 3. 温度骤变规则（变化率判断）
        spike_rule_enabled = any(r["type"] == "temperature_spike" and r.get("enabled", True) for r in self._rules)
        temperature = sensor_data.get("temperature")
        if spike_rule_enabled and temperature is not None and state["last_temperature"] is not None:
            time_diff = (now - state["last_temp_time"]).total_seconds() / 60.0
            if time_diff > 0:
                temp_diff = abs(temperature - state["last_temperature"])
                rate = temp_diff / time_diff
                if rate > TEMP_THRESHOLD["TEMP_SPIKE_RATE"]:
                    alerts.append({
                        "device_id": device_id,
                        "alert_type": "temperature_spike",
                        "severity": "severe",
                        "message": f"温度骤变: 变化率{rate:.1f}°C/分钟, 阈值={TEMP_THRESHOLD['TEMP_SPIKE_RATE']}°C/分钟",
                        "sensor_value": rate,
                        "threshold_value": TEMP_THRESHOLD["TEMP_SPIKE_RATE"],
                        "timestamp": now.isoformat(),
                        "targets": self.SEVERITY_ROUTES["severe"],
                    })

        if temperature is not None:
            state["last_temperature"] = temperature
            state["last_temp_time"] = now

        # 4. 设备离线规则（心跳超时判断）
        offline_rule_enabled = any(r["type"] == "device_offline" and r.get("enabled", True) for r in self._rules)
        offline_seconds = (now - state["last_heartbeat"]).total_seconds()
        if offline_rule_enabled and offline_seconds > TEMP_THRESHOLD["DEVICE_OFFLINE_SECONDS"] and not state["offline_alert_sent"]:
            alerts.append({
                "device_id": device_id,
                "alert_type": "device_offline",
                "severity": "severe",
                "message": f"设备离线: 已断联{int(offline_seconds)}秒, 阈值={TEMP_THRESHOLD['DEVICE_OFFLINE_SECONDS']}秒",
                "sensor_value": offline_seconds,
                "threshold_value": TEMP_THRESHOLD["DEVICE_OFFLINE_SECONDS"],
                "timestamp": now.isoformat(),
                "targets": self.SEVERITY_ROUTES["severe"],
            })
            state["offline_alert_sent"] = True

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
        """动态添加或更新告警规则"""
        rule_type = rule.get("type")
        if rule_type:
            self._rules = [r for r in self._rules if r["type"] != rule_type]
        self._rules.append(rule)

    def remove_rule(self, rule_type: str):
        """删除告警规则"""
        self._rules = [r for r in self._rules if r["type"] != rule_type]

    def get_rules(self) -> list[dict]:
        """返回所有规则，包括即时规则和时间相关内置规则"""
        all_rules = self._rules.copy()
        for r in all_rules:
            if "enabled" not in r:
                r["enabled"] = True
        all_rules.extend([
            {"field": "door_status", "op": "持续>", "value": TEMP_THRESHOLD["DOOR_TIMEOUT_SECONDS"],
             "severity": "normal", "type": "door_open_timeout", "msg": "车门超时开启", "enabled": True},
            {"field": "temperature", "op": "变化率>", "value": TEMP_THRESHOLD["TEMP_SPIKE_RATE"],
             "severity": "severe", "type": "temperature_spike", "msg": "温度骤变", "enabled": True},
            {"field": "heartbeat", "op": "超时>", "value": TEMP_THRESHOLD["DEVICE_OFFLINE_SECONDS"],
             "severity": "severe", "type": "device_offline", "msg": "设备离线", "enabled": True},
        ])
        return all_rules


# 全局单例
alert_engine = AlertEngine()
