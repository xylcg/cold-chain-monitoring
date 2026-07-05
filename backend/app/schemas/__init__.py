from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from enum import Enum, IntEnum
import uuid


# ==================== 温控常量 ====================
# 统一温度阈值定义，所有模块引用此处

TEMP_THRESHOLD = {
    "DANGER_UPPER": 15.0,       # 严重超标上限（°C）
    "WARN_UPPER": 8.0,          # 预警上限（°C）
    "LOW_LIMIT": -25.0,         # 低温下限（°C）
    "COMPLIANCE_MIN": -25.0,    # 达标温度下限（°C）
    "COMPLIANCE_MAX": 8.0,      # 达标温度上限（°C）
    "HUMIDITY_HIGH": 95.0,      # 湿度过高阈值（%RH）
    "VIBRATION_HIGH": 5.0,      # 振动异常阈值（g）
    "COOLDOWN_SECONDS": 300,    # 告警冷却期（秒）
    "COOLDOWN_CRITICAL": 60,    # 紧急告警冷却期（秒）
    "DOOR_TIMEOUT_SECONDS": 300, # 车门超时开启阈值（秒，5分钟）
    "DATA_QUALITY_LOW": 0.5,     # 数据质量低阈值
    "TEMP_SPIKE_RATE": 3.0,      # 温度骤变阈值（°C/分钟）
    "DEVICE_OFFLINE_SECONDS": 60, # 设备离线判定（秒，心跳超时）
}


# ==================== 枚举类型 ====================

class DeviceType(str, Enum):
    """设备类型"""
    VEHICLE = "vehicle"
    COLD_ROOM = "cold_room"
    FREEZER = "freezer"


class DeviceTypeCode(IntEnum):
    """设备类型编码（对应数据字典整型）"""
    VEHICLE = 1
    COLD_ROOM = 2
    FREEZER = 3


class AlertSeverity(str, Enum):
    """告警等级（字符串，兼容现有代码）"""
    NORMAL = "normal"
    SEVERE = "severe"
    CRITICAL = "critical"


class AlarmLevel(IntEnum):
    """预警等级（整型，对应数据字典）"""
    NORMAL = 1       # 一般
    SEVERE = 2       # 严重
    CRITICAL = 3     # 紧急


class AlarmType(IntEnum):
    """异常预警类型编码"""
    TEMPERATURE_OVERRUN = 1    # 温度越限
    HUMIDITY_OVERRUN = 2       # 湿度越限
    DOOR_TIMEOUT = 3           # 车门超时开启
    COLD_CAR_FAILURE = 4       # 冷机故障
    DEVICE_OFFLINE = 5         # 设备离线
    VIBRATION_ABNORMAL = 6     # 振动异常
    DATA_QUALITY_LOW = 7       # 数据质量异常
    TEMPERATURE_SPIKE = 8      # 温度骤变


class CargoCategory(IntEnum):
    """货物品类"""
    FROZEN_FOOD = 1        # 冷冻食品
    COLD_FRESH = 2          # 冷藏生鲜
    VACCINE_MEDICINE = 3    # 疫苗医药
    CHEMICAL_REAGENT = 4    # 化工制剂
    OTHER = 5               # 其他


class DeviceStatus(IntEnum):
    """设备状态"""
    DISABLED = 0    # 停用
    ONLINE = 1      # 正常在线
    OFFLINE = 2     # 离线
    FAULT = 3       # 故障


class HandleResult(IntEnum):
    """告警处置结果"""
    RECOVERED = 1       # 已恢复
    FALSE_ALARM = 2     # 误报消除
    TO_MAINTENANCE = 3  # 转维修
    FOLLOW_UP = 4       # 待跟进


class RiskLevel(IntEnum):
    """越限风险等级"""
    SAFE = 0        # 安全
    LOW = 1         # 低风险
    MEDIUM = 2      # 中风险
    HIGH = 3        # 高风险


# ==================== 表 1：传感器实时采集数据 ====================

class SensorData(BaseModel):
    """传感器上报数据（对应 TDengine sensor_data 超级表）"""
    device_id: str
    device_type: DeviceType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    temperature: float                                      # 实时采集环境温度（℃）
    target_temperature: Optional[float] = None              # 目标设定温度（℃）
    humidity: float                                          # 实时采集环境湿度（%RH）
    latitude: Optional[float] = None                        # GPS 纬度
    longitude: Optional[float] = None                       # GPS 经度
    vehicle_speed: Optional[float] = None                   # 车辆行驶速度（km/h）
    door_status: int = 0                                    # 车门状态：0关闭，1开启
    vibration: float = 0.0                                  # 振动加速度幅值（g）
    data_quality: float = 1.0                               # 数据质量评分（0~1）
    battery_level: Optional[float] = None                   # 传感器电池电量（%）
    signal_strength: Optional[int] = None                   # 设备信号强度（dBm）
    cold_car_status: int = 1                                # 冷机运行状态：0故障，1正常运行
    external_temp: Optional[float] = None                   # 外部环境温度（℃）
    waybill_no: str = ""                                    # 关联订单运单唯一编号


class SensorDataBatch(BaseModel):
    """批量传感器数据"""
    records: List[SensorData]


# ==================== 表 2：设备台账信息 ====================

class DeviceInfo(BaseModel):
    """设备台账信息（对应 PostgreSQL devices 表）"""
    device_id: str                                           # 设备唯一编码
    device_name: str                                         # 设备名称
    device_type: int = 1                                     # 设备类型：1冷藏车，2冷库，3冷柜
    zone_id: Optional[str] = None                           # 所属区域/园区编码
    cargo_category: Optional[int] = None                    # 货物品类：1冷冻食品，2冷藏生鲜，3疫苗医药，4化工制剂，5其他
    temp_lower_limit: float                                  # 温控下限阈值（℃）
    temp_upper_limit: float                                  # 温控上限阈值（℃）
    humidity_lower_limit: Optional[float] = None            # 湿度下限阈值（%RH）
    humidity_upper_limit: Optional[float] = None            # 湿度上限阈值（%RH）
    install_date: date = Field(default_factory=date.today)  # 安装/注册日期
    last_maintenance_date: Optional[date] = None            # 最近一次维护日期
    status: int = 1                                          # 设备状态：0停用，1正常在线，2离线，3故障
    remark: Optional[str] = None                            # 备注说明

    class Config:
        from_attributes = True


class DeviceCreate(BaseModel):
    """创建/注册设备"""
    device_id: str
    device_name: str
    device_type: int = 1
    zone_id: Optional[str] = None
    cargo_category: Optional[int] = None
    temp_lower_limit: float
    temp_upper_limit: float
    humidity_lower_limit: Optional[float] = None
    humidity_upper_limit: Optional[float] = None
    install_date: date = Field(default_factory=date.today)
    remark: Optional[str] = None


class DeviceUpdate(BaseModel):
    """更新设备信息"""
    device_name: Optional[str] = None
    zone_id: Optional[str] = None
    cargo_category: Optional[int] = None
    temp_lower_limit: Optional[float] = None
    temp_upper_limit: Optional[float] = None
    humidity_lower_limit: Optional[float] = None
    humidity_upper_limit: Optional[float] = None
    last_maintenance_date: Optional[date] = None
    status: Optional[int] = None
    remark: Optional[str] = None


class DeviceRuntimeStatus(BaseModel):
    """设备实时运行状态（Redis 缓存 + API 返回）"""
    device_id: str
    device_name: str
    device_type: int
    online: bool
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    door_status: int = 0
    cold_car_status: int = 1
    last_update: Optional[datetime] = None
    alerts_active: int = 0


# ==================== 表 3：告警事件记录 ====================

class AlertEvent(BaseModel):
    """告警事件（对应 PostgreSQL alert_events 表）"""
    alert_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    device_id: str
    alarm_type: int                                          # 1温度越限 2湿度越限 3车门超时开启 4冷机故障 5设备离线 6振动异常 7数据质量异常 8温度骤变
    alarm_level: int = 1                                     # 1一般 2严重 3紧急
    alert_message: str                                       # 告警描述文本
    sensor_value: float                                      # 告警触发时刻传感器实际读数
    threshold_value: float                                   # 触发告警的阈值边界值
    alert_time: datetime = Field(default_factory=datetime.utcnow)
    handler: Optional[str] = None                           # 处置人姓名/工号
    handle_time: Optional[datetime] = None                  # 确认处置时间
    handle_result: Optional[int] = None                     # 1已恢复 2误报消除 3转维修 4待跟进
    handle_remark: Optional[str] = None                     # 处置备注
    resolved_time: Optional[datetime] = None                # 告警解决/关闭时间

    class Config:
        from_attributes = True


class AlertHandleRequest(BaseModel):
    """告警处置请求"""
    handler: str
    handle_result: int   # 1已恢复 2误报消除 3转维修 4待跟进
    handle_remark: Optional[str] = None


class AlertQuery(BaseModel):
    """告警查询参数"""
    device_id: Optional[str] = None
    alarm_type: Optional[int] = None
    alarm_level: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    is_handled: Optional[bool] = None  # None=全部, True=已处置, False=未处置
    page: int = 1
    page_size: int = 20


# ==================== 表 4：温控预测结果 ====================

class TemperaturePrediction(BaseModel):
    """温控预测结果（对应 PostgreSQL temperature_predictions 表）"""
    prediction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    device_id: str
    predict_time: datetime = Field(default_factory=datetime.utcnow)
    horizon_minutes: int = 30                                # 预测时间窗口长度（分钟）
    predicted_values: List[float]                            # 未来每分钟温度预测值序列
    confidence_upper: List[float]                            # 置信区间上界序列
    confidence_lower: List[float]                            # 置信区间下界序列
    risk_level: int = 0                                      # 0安全 1低风险 2中风险 3高风险

    class Config:
        from_attributes = True


# ==================== 认证相关 ====================

class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_role: str
    username: str


# ==================== 告警规则配置 ====================

class AlertRuleCreate(BaseModel):
    rule_name: str
    rule_type: str
    condition_field: str
    condition_operator: str
    condition_value: float
    severity: AlertSeverity
    cooldown_seconds: int = 300
    enabled: bool = True


# ==================== 仪表盘 KPI ====================

class DashboardKPI(BaseModel):
    """仪表盘KPI"""
    total_devices: int
    online_devices: int
    temperature_compliance_rate: float
    active_alerts: int
    critical_alerts: int
    avg_temperature: float
    avg_humidity: float
