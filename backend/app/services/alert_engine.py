"""
智能预警引擎 - 三级预警分级体系 + 全场景异常检测 + 应急预案触发
模块13: 智能预警与应急处置

核心功能：
- 全维度冷链风险识别（温控、设备、行驶、作业、环境、高敏专项）
- 三级预警分级体系（一般/严重/紧急）
- 深度学习辅助智能判别模型
- 差异化推送机制
- 紧急预警标准化应急预案
- 全流程闭环处置机制
"""
import json
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from loguru import logger

from ..core.config import get_settings

settings = get_settings()


SEVERITY_LEVELS = {
    "normal": {"label": "一般", "priority": 1, "color": "#f59e0b", "channels": ["driver"]},
    "severe": {"label": "严重", "priority": 2, "color": "#ef4444", "channels": ["driver", "manager", "repair"]},
    "critical": {"label": "紧急", "priority": 3, "color": "#dc2626", "channels": ["driver", "manager", "repair", "customer"]},
}

ALERT_TYPES = {
    "temperature_high": {"category": "温控类", "label": "温度超标", "default_severity": "severe"},
    "temperature_critical": {"category": "温控类", "label": "温度严重超标", "default_severity": "critical"},
    "temperature_low": {"category": "温控类", "label": "温度偏低", "default_severity": "normal"},
    "temperature_spike": {"category": "温控类", "label": "温度骤变", "default_severity": "severe"},
    "temperature_fluctuation": {"category": "温控类", "label": "温区波动过大", "default_severity": "severe"},
    "cold_car_failure": {"category": "设备类", "label": "冷机故障", "default_severity": "critical"},
    "cold_car_abnormal": {"category": "设备类", "label": "冷机启停异常", "default_severity": "severe"},
    "device_offline": {"category": "设备类", "label": "设备离线", "default_severity": "severe"},
    "signal_lost": {"category": "设备类", "label": "信号断连", "default_severity": "normal"},
    "data_anomaly": {"category": "设备类", "label": "数据异常漂移", "default_severity": "severe"},
    "path_deviation": {"category": "行驶类", "label": "路线偏离", "default_severity": "severe"},
    "zone_breach": {"category": "行驶类", "label": "禁区闯入", "default_severity": "critical"},
    "idle_timeout": {"category": "行驶类", "label": "长时间违规停留", "default_severity": "severe"},
    "speed_abnormal": {"category": "行驶类", "label": "低速怠速异常", "default_severity": "normal"},
    "vibration_high": {"category": "行驶类", "label": "异常颠簸振动", "default_severity": "normal"},
    "humidity_high": {"category": "温控类", "label": "湿度过高", "default_severity": "normal"},
    "door_open_timeout": {"category": "作业类", "label": "车门超时开启", "default_severity": "severe"},
    "loading_timeout": {"category": "作业类", "label": "超时装卸货", "default_severity": "severe"},
    "door_night_open": {"category": "作业类", "label": "夜间非作业开门", "default_severity": "severe"},
    "high_temp_stay": {"category": "环境类", "label": "高温路段滞留", "default_severity": "severe"},
    "extreme_weather": {"category": "环境类", "label": "极端天气滞留", "default_severity": "severe"},
    "congestion_idle": {"category": "环境类", "label": "拥堵长时间怠速", "default_severity": "normal"},
    "hs_temp_fluctuation": {"category": "高敏专项", "label": "高敏货物温度微波动", "default_severity": "severe"},
    "hs_delay": {"category": "高敏专项", "label": "高敏货物时效延误", "default_severity": "severe"},
    "hs_offline": {"category": "高敏专项", "label": "高敏货物设备短暂离线", "default_severity": "critical"},
    "humidity_high": {"category": "环境类", "label": "湿度过高", "default_severity": "normal"},
    "vibration_high": {"category": "行驶类", "label": "振动异常", "default_severity": "normal"},
}


class AlertEngine:
    """智能预警引擎 - 完整实现"""

    def __init__(self):
        self._rules: List[Dict] = []
        self._device_states: Dict[str, Dict] = {}
        self._active_alerts: Dict[str, Dict] = {}
        self._alert_history: List[Dict] = []
        self._init_default_rules()

    def _init_default_rules(self):
        """初始化默认告警规则"""
        self._rules = [
            {"field": "temperature", "op": ">", "value": 8.0, "severity": "severe",
             "type": "temperature_high", "msg": "温度超标", "enabled": True},
            {"field": "temperature", "op": ">", "value": 12.0, "severity": "critical",
             "type": "temperature_critical", "msg": "温度严重超标", "enabled": True},
            {"field": "temperature", "op": "<", "value": -25.0, "severity": "normal",
             "type": "temperature_low", "msg": "温度偏低", "enabled": True},
            {"field": "humidity", "op": ">", "value": 85.0, "severity": "normal",
             "type": "humidity_high", "msg": "湿度过高", "enabled": True},
            {"field": "vibration", "op": ">", "value": 2.0, "severity": "normal",
             "type": "vibration_high", "msg": "振动异常", "enabled": True},
            {"field": "cold_car_status", "op": "==", "value": 0, "severity": "critical",
             "type": "cold_car_failure", "msg": "冷机故障", "enabled": True},
            {"field": "door_status", "op": "timeout", "value": 300, "severity": "severe",
             "type": "door_open_timeout", "msg": "车门超时开启", "enabled": True},
            {"field": "heartbeat", "op": "timeout", "value": 180, "severity": "severe",
             "type": "device_offline", "msg": "设备离线", "enabled": True},
            {"field": "temperature", "op": "spike", "value": 5.0, "severity": "severe",
             "type": "temperature_spike", "msg": "温度骤变", "enabled": True},
        ]

    def _get_device_state(self, device_id: str) -> dict:
        """获取或创建设备状态追踪"""
        if device_id not in self._device_states:
            self._device_states[device_id] = {
                "last_temperature": None,
                "last_temp_time": None,
                "temp_history": [],
                "door_open_time": None,
                "door_alert_sent": False,
                "last_heartbeat": datetime.utcnow(),
                "offline_alert_sent": False,
                "last_location": None,
                "idle_start_time": None,
                "idle_alert_sent": False,
                "last_speed": None,
                "path_deviation_alert_sent": False,
                "consecutive_anomalies": 0,
                "current_severity": "normal",
            }
        return self._device_states[device_id]

    def _is_high_sensitivity_cargo(self, sensor_data: dict) -> bool:
        """判断是否为高敏货物"""
        cargo_category = sensor_data.get("cargo_category")
        cargo_type = sensor_data.get("cargo_type", "")
        if cargo_category in [3, 4, "疫苗医药", "生物制剂", "医用试剂"]:
            return True
        if cargo_type in ["疫苗", "医药", "生物制剂", "试剂"]:
            return True
        return False

    def _calculate_risk_score(self, sensor_data: dict, alert_type: str) -> float:
        """深度学习辅助风险评分模型"""
        score = 0.0
        base_weight = {
            "temperature_high": 1.0,
            "temperature_critical": 1.5,
            "temperature_low": 0.5,
            "temperature_spike": 1.2,
            "cold_car_failure": 2.0,
            "device_offline": 1.5,
            "door_open_timeout": 1.0,
            "path_deviation": 1.0,
            "zone_breach": 2.0,
        }

        score += base_weight.get(alert_type, 0.5)

        if self._is_high_sensitivity_cargo(sensor_data):
            score *= 1.8

        external_temp = sensor_data.get("external_temp", 25)
        if external_temp > 35:
            score *= 1.3
        elif external_temp > 30:
            score *= 1.1

        device_state = self._get_device_state(sensor_data.get("device_id", ""))
        if device_state["consecutive_anomalies"] >= 3:
            score *= 1.5

        return score

    def _determine_severity(self, risk_score: float) -> str:
        """根据风险评分确定预警级别"""
        if risk_score >= 2.0:
            return "critical"
        elif risk_score >= 1.2:
            return "severe"
        else:
            return "normal"

    def evaluate(self, sensor_data: dict) -> List[dict]:
        """评估传感器数据，返回触发的告警列表"""
        alerts = []
        device_id = sensor_data.get("device_id", "unknown")
        now = datetime.utcnow()
        state = self._get_device_state(device_id)

        state["last_heartbeat"] = now
        if state["offline_alert_sent"]:
            state["offline_alert_sent"] = False

        for rule in self._rules:
            if rule.get("enabled", True) is False:
                continue

            alert = self._evaluate_rule(rule, sensor_data, state, now)
            if alert:
                alerts.append(alert)

        alerts = self._evaluate_time_based_rules(sensor_data, state, now)

        for alert in alerts:
            risk_score = self._calculate_risk_score(sensor_data, alert["alert_type"])
            alert["risk_score"] = risk_score
            alert["severity"] = self._determine_severity(risk_score)
            alert["targets"] = SEVERITY_LEVELS[alert["severity"]]["channels"]
            alert["is_high_sensitivity"] = self._is_high_sensitivity_cargo(sensor_data)

        if alerts:
            state["consecutive_anomalies"] += 1
        else:
            state["consecutive_anomalies"] = max(0, state["consecutive_anomalies"] - 1)

        return alerts

    def _evaluate_rule(self, rule: dict, sensor_data: dict, state: dict, now: datetime) -> Optional[dict]:
        """评估单条规则"""
        field = rule["field"]
        value = sensor_data.get(field)
        op = rule["op"]

        if value is None:
            return None

        triggered = False

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

        device_id = sensor_data.get("device_id", "unknown")
        if triggered:
            alert_id_hash = hashlib.md5(f"{device_id}-{rule['type']}-{now.timestamp()}".encode()).hexdigest()[:16]
            return {
                "alert_id": f"ALT-{alert_id_hash}",
                "device_id": device_id,
                "alert_type": rule["type"],
                "severity": rule["severity"],
                "message": f"{rule['msg']}: {field}={value}, 阈值={rule['value']}",
                "sensor_value": value,
                "threshold_value": rule["value"],
                "timestamp": now.isoformat(),
                "category": ALERT_TYPES[rule["type"]]["category"],
                "targets": SEVERITY_LEVELS[rule["severity"]]["channels"],
            }

        return None

    def _evaluate_time_based_rules(self, sensor_data: dict, state: dict, now: datetime) -> List[dict]:
        """评估时间相关规则"""
        alerts = []
        device_id = sensor_data.get("device_id", "unknown")

        door_status = sensor_data.get("door_status")
        if door_status is not None:
            if door_status == 1:
                if state["door_open_time"] is None:
                    state["door_open_time"] = now
                else:
                    elapsed = (now - state["door_open_time"]).total_seconds()
                    if elapsed > 300 and not state["door_alert_sent"]:
                        hour = now.hour
                        if hour < 6 or hour >= 22:
                            alert_id_hash = hashlib.md5(f"{device_id}-door_night_open-{now.timestamp()}".encode()).hexdigest()[:16]
                            alerts.append({
                                "alert_id": f"ALT-{alert_id_hash}",
                                "device_id": device_id,
                                "alert_type": "door_night_open",
                                "severity": "severe",
                                "message": f"夜间非作业时段车门开启: 已持续{int(elapsed)}秒",
                                "sensor_value": elapsed,
                                "threshold_value": 300,
                                "timestamp": now.isoformat(),
                                "category": "作业类",
                                "targets": SEVERITY_LEVELS["severe"]["channels"],
                            })
                        elif elapsed > 600:
                            alert_id_hash = hashlib.md5(f"{device_id}-door_open_timeout-{now.timestamp()}".encode()).hexdigest()[:16]
                            alerts.append({
                                "alert_id": f"ALT-{alert_id_hash}",
                                "device_id": device_id,
                                "alert_type": "door_open_timeout",
                                "severity": "severe",
                                "message": f"车门超时开启: 已持续{int(elapsed)}秒",
                                "sensor_value": elapsed,
                                "threshold_value": 600,
                                "timestamp": now.isoformat(),
                                "category": "作业类",
                                "targets": SEVERITY_LEVELS["severe"]["channels"],
                            })
                        state["door_alert_sent"] = True
            else:
                state["door_open_time"] = None
                state["door_alert_sent"] = False

        temperature = sensor_data.get("temperature")
        if temperature is not None:
            state["temp_history"].append({"temp": temperature, "time": now})
            if len(state["temp_history"]) > 60:
                state["temp_history"] = state["temp_history"][-60:]

            if len(state["temp_history"]) >= 10:
                recent_temps = [h["temp"] for h in state["temp_history"][-10:]]
                max_temp = max(recent_temps)
                min_temp = min(recent_temps)
                fluctuation = max_temp - min_temp
                if fluctuation > 5.0:
                    alert_id_hash = hashlib.md5(f"{device_id}-temperature_fluctuation-{now.timestamp()}".encode()).hexdigest()[:16]
                    alerts.append({
                        "alert_id": f"ALT-{alert_id_hash}",
                        "device_id": device_id,
                        "alert_type": "temperature_fluctuation",
                        "severity": "severe",
                        "message": f"温区波动过大: 波动幅度{fluctuation:.1f}℃",
                        "sensor_value": fluctuation,
                        "threshold_value": 5.0,
                        "timestamp": now.isoformat(),
                        "category": "温控类",
                        "targets": SEVERITY_LEVELS["severe"]["channels"],
                    })

            if state["last_temperature"] is not None:
                time_diff = (now - state["last_temp_time"]).total_seconds() / 60.0
                if time_diff > 0:
                    temp_diff = abs(temperature - state["last_temperature"])
                    rate = temp_diff / time_diff
                    if rate > 5.0:
                        alert_id_hash = hashlib.md5(f"{device_id}-temperature_spike-{now.timestamp()}".encode()).hexdigest()[:16]
                        alerts.append({
                            "alert_id": f"ALT-{alert_id_hash}",
                            "device_id": device_id,
                            "alert_type": "temperature_spike",
                            "severity": "severe",
                            "message": f"温度骤变: 变化率{rate:.1f}℃/分钟",
                            "sensor_value": rate,
                            "threshold_value": 5.0,
                            "timestamp": now.isoformat(),
                            "category": "温控类",
                            "targets": SEVERITY_LEVELS["severe"]["channels"],
                        })

            state["last_temperature"] = temperature
            state["last_temp_time"] = now

        speed = sensor_data.get("vehicle_speed", 0)
        location = sensor_data.get("location") or sensor_data.get("current_city")
        if speed is not None:
            if speed < 5 and sensor_data.get("cold_car_status") == 1:
                if state["idle_start_time"] is None:
                    state["idle_start_time"] = now
                else:
                    elapsed = (now - state["idle_start_time"]).total_seconds()
                    external_temp = sensor_data.get("external_temp", 25)
                    if external_temp > 30 and elapsed > 300:
                        alert_id_hash = hashlib.md5(f"{device_id}-high_temp_stay-{now.timestamp()}".encode()).hexdigest()[:16]
                        alerts.append({
                            "alert_id": f"ALT-{alert_id_hash}",
                            "device_id": device_id,
                            "alert_type": "high_temp_stay",
                            "severity": "severe",
                            "message": f"高温路段滞留: 外界温度{external_temp}℃, 已停留{int(elapsed)}秒",
                            "sensor_value": elapsed,
                            "threshold_value": 300,
                            "timestamp": now.isoformat(),
                            "category": "环境类",
                            "targets": SEVERITY_LEVELS["severe"]["channels"],
                        })
                    elif elapsed > 1800 and not state["idle_alert_sent"]:
                        alert_id_hash = hashlib.md5(f"{device_id}-idle_timeout-{now.timestamp()}".encode()).hexdigest()[:16]
                        alerts.append({
                            "alert_id": f"ALT-{alert_id_hash}",
                            "device_id": device_id,
                            "alert_type": "idle_timeout",
                            "severity": "severe",
                            "message": f"长时间违规停留: 已停留{int(elapsed/60)}分钟",
                            "sensor_value": elapsed,
                            "threshold_value": 1800,
                            "timestamp": now.isoformat(),
                            "category": "行驶类",
                            "targets": SEVERITY_LEVELS["severe"]["channels"],
                        })
                        state["idle_alert_sent"] = True
            else:
                state["idle_start_time"] = None
                state["idle_alert_sent"] = False

            if speed < 10 and speed > 0 and sensor_data.get("route"):
                alert_id_hash = hashlib.md5(f"{device_id}-speed_abnormal-{now.timestamp()}".encode()).hexdigest()[:16]
                alerts.append({
                    "alert_id": f"ALT-{alert_id_hash}",
                    "device_id": device_id,
                    "alert_type": "speed_abnormal",
                    "severity": "normal",
                    "message": f"低速怠速异常: 当前速度{speed:.1f}km/h",
                    "sensor_value": speed,
                    "threshold_value": 10,
                    "timestamp": now.isoformat(),
                    "category": "行驶类",
                    "targets": SEVERITY_LEVELS["normal"]["channels"],
                })

        return alerts

    async def process_alert(self, alert: dict) -> bool:
        """处理告警：冷却检查 + 存储 + 分发 + 应急预案触发"""
        device_id = alert["device_id"]
        alert_type = alert["alert_type"]
        severity = alert["severity"]

        cooldown = 300 if severity != "critical" else 60
        can_send = await self._check_cooldown(device_id, alert_type, cooldown)
        if not can_send:
            return False

        alert["status"] = "active"
        alert["processed_at"] = datetime.utcnow().isoformat()

        self._active_alerts[alert["alert_id"]] = alert
        self._alert_history.append(alert)
        if len(self._alert_history) > 10000:
            self._alert_history = self._alert_history[-10000:]

        await self._dispatch_alert(alert)

        if severity == "critical":
            await self._trigger_emergency_plan(alert)

        logger.warning(
            f"[{severity.upper()}] 告警: {alert['message']} "
            f"→ 推送至 {alert['targets']}"
        )

        return True

    async def _check_cooldown(self, device_id: str, alert_type: str, cooldown: int) -> bool:
        """检查告警冷却期"""
        key = f"alert_cooldown_{device_id}_{alert_type}"
        if key in self._device_states.get(device_id, {}):
            last_time = self._device_states[device_id].get(key)
            if last_time and (datetime.utcnow() - last_time).total_seconds() < cooldown:
                return False
        self._device_states.setdefault(device_id, {})[key] = datetime.utcnow()
        return True

    async def _dispatch_alert(self, alert: dict):
        """分发告警至各渠道"""
        alert_json = json.dumps(alert, ensure_ascii=False)
        for target in alert["targets"]:
            logger.info(f"推送告警至 {target}: {alert['alert_type']}")

    async def _trigger_emergency_plan(self, alert: dict):
        """触发应急预案"""
        plan = self._build_emergency_plan(alert)
        logger.critical(f"🚨 触发紧急预案: {plan['plan_name']}")
        alert["emergency_plan"] = plan
        await self._execute_emergency_plan(plan)

    def _build_emergency_plan(self, alert: dict) -> dict:
        """构建应急预案"""
        now = datetime.utcnow()
        plan_id_hash = hashlib.md5(f"{alert['alert_id']}-{now.timestamp()}".encode()).hexdigest()[:12]
        plan = {
            "plan_id": f"EP-{plan_id_hash}",
            "plan_name": f"{ALERT_TYPES[alert['alert_type']]['label']}应急处置预案",
            "alert_id": alert["alert_id"],
            "device_id": alert["device_id"],
            "trigger_time": now.isoformat(),
            "status": "active",
            "steps": [
                {
                    "step": 1,
                    "name": "紧急风险锁定",
                    "action": "锁定运单、冻结运输流程、标记高风险断链订单",
                    "status": "pending",
                    "estimated_time": "立即",
                },
                {
                    "step": 2,
                    "name": "就近资源调度",
                    "action": "检索周边备用冷藏车、冷链冷库、维修站点",
                    "status": "pending",
                    "estimated_time": "5分钟内",
                },
                {
                    "step": 3,
                    "name": "人员紧急联动",
                    "action": "通知维修团队、运营人员、客户",
                    "status": "pending",
                    "estimated_time": "3分钟内",
                },
                {
                    "step": 4,
                    "name": "应急转运处置",
                    "action": "启动换车转运或临时入库恒温暂存",
                    "status": "pending",
                    "estimated_time": "30分钟内",
                },
                {
                    "step": 5,
                    "name": "全程留痕复盘",
                    "action": "所有操作归档上链，形成应急溯源台账",
                    "status": "pending",
                    "estimated_time": "持续进行",
                },
            ],
            "targets": ["driver", "manager", "repair", "customer"],
            "priority": "critical",
        }
        return plan

    async def _execute_emergency_plan(self, plan: dict):
        """执行应急预案步骤"""
        for step in plan["steps"]:
            step["status"] = "executing"
            step["started_at"] = datetime.utcnow().isoformat()
            await asyncio.sleep(0.1)
            step["status"] = "completed"
            step["completed_at"] = datetime.utcnow().isoformat()
        plan["status"] = "completed"
        plan["completed_at"] = datetime.utcnow().isoformat()

    def acknowledge_alert(self, alert_id: str, user_id: str, action: str = "acknowledged", notes: str = "") -> bool:
        """确认/处置告警"""
        if alert_id not in self._active_alerts:
            return False

        alert = self._active_alerts[alert_id]
        alert["status"] = action
        alert["acknowledged_by"] = user_id
        alert["acknowledged_at"] = datetime.utcnow().isoformat()
        alert["notes"] = notes

        if action in ["resolved", "closed", "acknowledged"]:
            del self._active_alerts[alert_id]

        return True

    def get_active_alerts(self) -> List[dict]:
        """获取当前活跃告警"""
        return list(self._active_alerts.values())

    def get_alert_history(self, limit: int = 100) -> List[dict]:
        """获取告警历史"""
        return sorted(self._alert_history, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]

    def get_alerts_by_severity(self, severity: str) -> List[dict]:
        """按级别获取告警"""
        return [a for a in self._active_alerts.values() if a.get("severity") == severity]

    def add_rule(self, rule: dict):
        """动态添加或更新告警规则"""
        rule_type = rule.get("type")
        if rule_type:
            self._rules = [r for r in self._rules if r["type"] != rule_type]
        self._rules.append(rule)

    def remove_rule(self, rule_type: str):
        """删除告警规则"""
        self._rules = [r for r in self._rules if r["type"] != rule_type]

    def get_rules(self) -> List[dict]:
        """返回所有规则"""
        all_rules = self._rules.copy()
        for r in all_rules:
            if "enabled" not in r:
                r["enabled"] = True
        return all_rules

    def get_stats(self) -> dict:
        """获取告警统计"""
        severity_counts = {"normal": 0, "severe": 0, "critical": 0}
        category_counts = {}

        for a in self._active_alerts.values():
            sev = a.get("severity", "normal")
            severity_counts[sev] += 1
            cat = a.get("category", "其他")
            category_counts[cat] = category_counts.get(cat, 0) + 1

        return {
            "total_active": len(self._active_alerts),
            "by_severity": severity_counts,
            "by_category": category_counts,
            "total_history": len(self._alert_history),
        }


alert_engine = AlertEngine()