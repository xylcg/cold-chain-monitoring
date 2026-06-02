"""
TDengine 时序数据库服务
"""
import json
import socket
from typing import Optional
from datetime import datetime
from loguru import logger
from ..core.config import get_settings

settings = get_settings()


def _port_open(host: str, port: int, timeout: float = 2.0) -> bool:
    """快速检测端口是否可达"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False


class TDengineService:
    """TDengine 时序数据存储服务"""

    def __init__(self):
        self._conn = None
        self._database = settings.TDENGINE_DATABASE

    def connect(self):
        """连接 TDengine"""
        # 快速预检：端口不可达直接降级，避免长时间阻塞
        if not _port_open(settings.TDENGINE_HOST, settings.TDENGINE_PORT, timeout=2.0):
            logger.warning("TDengine 端口不可达 (将使用模拟模式)")
            self._conn = None
            return

        try:
            import taos
            self._conn = taos.connect(
                host=settings.TDENGINE_HOST,
                port=settings.TDENGINE_PORT,
                user=settings.TDENGINE_USER,
                password=settings.TDENGINE_PASSWORD,
            )
            self._create_database()
            self._create_tables()
            logger.info("TDengine 连接成功")
        except ImportError:
            logger.warning("taospy 未安装，使用模拟模式")
            self._conn = None
        except Exception as e:
            logger.warning(f"TDengine 连接失败 (将使用模拟模式): {e}")
            self._conn = None

    def _create_database(self):
        if not self._conn:
            return
        try:
            self._conn.execute(f"CREATE DATABASE IF NOT EXISTS {self._database} "
                               f"KEEP 180 DURATION 10 BUFFER 256")
            self._conn.execute(f"USE {self._database}")
        except Exception as e:
            logger.warning(f"创建数据库失败: {e}")

    def _create_tables(self):
        """创建超级表和子表"""
        if not self._conn:
            return
        try:
            self._conn.execute(f"USE {self._database}")

            # 创建传感器数据超级表（对应数据字典表1）
            self._conn.execute("""
                CREATE STABLE IF NOT EXISTS sensor_data (
                    ts               TIMESTAMP,
                    temperature      FLOAT,
                    target_temp      FLOAT,
                    humidity         FLOAT,
                    latitude         FLOAT,
                    longitude        FLOAT,
                    vehicle_speed    FLOAT,
                    door_status      INT,
                    vibration        FLOAT,
                    data_quality     FLOAT,
                    battery_level    FLOAT,
                    signal_strength  INT,
                    cold_car_status  INT,
                    external_temp    FLOAT,
                    waybill_no       BINARY(64)
                ) TAGS (
                    device_id        BINARY(20),
                    device_type      BINARY(10)
                )
            """)

            # 创建告警事件表（对应数据字典表3，TDengine 侧时序存储）
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS alert_events (
                    ts               TIMESTAMP,
                    alert_id         BINARY(36),
                    device_id        BINARY(20),
                    alarm_type       INT,
                    alarm_level      INT,
                    alert_message    BINARY(500),
                    sensor_value     FLOAT,
                    threshold_value  FLOAT,
                    handler          BINARY(50),
                    handle_result    INT,
                    resolved_time    TIMESTAMP
                )
            """)

            # 创建温度预测结果表（对应数据字典表4，TDengine 侧时序存储）
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS temperature_predictions (
                    ts               TIMESTAMP,
                    prediction_id    BINARY(36),
                    device_id        BINARY(20),
                    horizon_minutes  INT,
                    risk_level       INT
                )
            """)

            logger.info("TDengine 表结构创建成功")
        except Exception as e:
            logger.warning(f"创建表结构失败: {e}")

    def insert_sensor_data(self, data: dict) -> bool:
        """插入传感器数据（对应数据字典表1）"""
        if not self._conn:
            self._mock_insert(data)
            return True

        try:
            device_id = data["device_id"]
            table_name = f"sensor_{device_id.replace('-', '_').lower()}"

            # 确保子表存在
            self._conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name}
                USING sensor_data TAGS ('{device_id}', '{data.get("device_type", "unknown")}')
            """)

            # 插入数据
            ts = data.get("timestamp", datetime.utcnow().isoformat())
            sql = f"""
                INSERT INTO {table_name} VALUES (
                    '{ts}',
                    {data.get('temperature', 0)},
                    {data.get('target_temperature', 'NULL') if data.get('target_temperature') is None else data.get('target_temperature')},
                    {data.get('humidity', 0)},
                    {data.get('latitude', 0) or 0},
                    {data.get('longitude', 0) or 0},
                    {data.get('vehicle_speed', 'NULL') if data.get('vehicle_speed') is None else data.get('vehicle_speed')},
                    {data.get('door_status', 0)},
                    {data.get('vibration', 0)},
                    {data.get('data_quality', 1.0)},
                    {data.get('battery_level', 'NULL') if data.get('battery_level') is None else data.get('battery_level')},
                    {data.get('signal_strength', -1)},
                    {data.get('cold_car_status', 1)},
                    {data.get('external_temp', 'NULL') if data.get('external_temp') is None else data.get('external_temp')},
                    '{data.get('waybill_no', '')}'
                )
            """
            self._conn.execute(sql)
            return True
        except Exception as e:
            logger.error(f"TDengine 写入失败: {e}")
            return False

    def insert_alert(self, alert: dict) -> bool:
        """插入告警事件（对应数据字典表3）"""
        if not self._conn:
            return True

        try:
            ts = alert.get("timestamp", datetime.utcnow().isoformat())
            sql = f"""
                INSERT INTO alert_events VALUES (
                    '{ts}',
                    '{alert.get("alert_id", "")}',
                    '{alert.get("device_id", "")}',
                    {alert.get("alarm_type", 1)},
                    {alert.get("alarm_level", 1)},
                    '{alert.get("alert_message", alert.get("message", ""))}',
                    {alert.get("sensor_value", 0)},
                    {alert.get("threshold_value", 0)},
                    '{alert.get("handler", "")}',
                    {alert.get("handle_result", 'NULL') if alert.get('handle_result') is None else alert.get('handle_result')},
                    {f"'{alert.get('resolved_time')}'" if alert.get('resolved_time') else 'NULL'}
                )
            """
            self._conn.execute(sql)
            return True
        except Exception as e:
            logger.error(f"告警写入失败: {e}")
            return False

    def insert_prediction(self, prediction: dict) -> bool:
        """插入温度预测结果（对应数据字典表4）"""
        if not self._conn:
            return True

        try:
            ts = prediction.get("predict_time", datetime.utcnow().isoformat())
            sql = f"""
                INSERT INTO temperature_predictions VALUES (
                    '{ts}',
                    '{prediction.get("prediction_id", "")}',
                    '{prediction.get("device_id", "")}',
                    {prediction.get("horizon_minutes", 30)},
                    {prediction.get("risk_level", 0)}
                )
            """
            self._conn.execute(sql)
            return True
        except Exception as e:
            logger.error(f"预测结果写入失败: {e}")
            return False

    def query_history(self, device_id: str, start: str, end: str,
                      limit: int = 100) -> list:
        """查询历史数据"""
        if not self._conn:
            return []

        try:
            table_name = f"sensor_{device_id.replace('-', '_').lower()}"
            sql = f"""
                SELECT ts, temperature, humidity, door_status, vibration
                FROM {table_name}
                WHERE ts >= '{start}' AND ts <= '{end}'
                ORDER BY ts DESC
                LIMIT {limit}
            """
            result = self._conn.query(sql)
            return [
                {
                    "ts": row[0],
                    "temperature": row[1],
                    "humidity": row[2],
                    "door_status": row[3],
                    "vibration": row[4],
                }
                for row in result
            ]
        except Exception as e:
            logger.error(f"查询历史数据失败: {e}")
            return []

    def _mock_insert(self, data: dict):
        """模拟模式 - 仅打印日志"""
        pass

    def close(self):
        if self._conn:
            self._conn.close()


# 全局单例
tdengine_service = TDengineService()
