"""
Kafka 服务 - 生产者与消费者
"""
import json
import asyncio
from typing import Optional, Callable
from kafka import KafkaProducer, KafkaConsumer
from loguru import logger
from ..core.config import get_settings

settings = get_settings()


class KafkaService:
    """Kafka 消息队列服务"""

    def __init__(self):
        self._producer: Optional[KafkaProducer] = None
        self._consumers: list[KafkaConsumer] = []

    @property
    def producer(self) -> KafkaProducer:
        if self._producer is None:
            self._producer = KafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode('utf-8'),
                acks='all',  # 保证消息不丢失
                retries=3,
                max_in_flight_requests_per_connection=1,
            )
        return self._producer

    def send_sensor_data(self, data: dict) -> bool:
        """发送传感器数据到 Kafka"""
        try:
            self.producer.send(
                settings.KAFKA_SENSOR_TOPIC,
                value=data,
                key=data.get("device_id", "unknown").encode(),
            )
            return True
        except Exception as e:
            logger.error(f"Kafka 发送失败: {e}")
            return False

    def send_alert(self, alert: dict) -> bool:
        """发送告警事件"""
        try:
            self.producer.send(
                settings.KAFKA_ALERT_TOPIC,
                value=alert,
                key=alert.get("device_id", "unknown").encode(),
            )
            return True
        except Exception as e:
            logger.error(f"告警发送失败: {e}")
            return False

    def send_prediction(self, prediction: dict) -> bool:
        """发送预测结果"""
        try:
            self.producer.send(
                settings.KAFKA_PREDICTION_TOPIC,
                value=prediction,
                key=prediction.get("device_id", "unknown").encode(),
            )
            return True
        except Exception as e:
            logger.error(f"预测结果发送失败: {e}")
            return False

    def create_consumer(self, topic: str, group_id: str) -> KafkaConsumer:
        """创建消费者"""
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=group_id,
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            auto_offset_reset='latest',
            enable_auto_commit=True,
        )
        self._consumers.append(consumer)
        return consumer

    def close(self):
        """关闭连接"""
        if self._producer:
            self._producer.flush()
            self._producer.close()
        for consumer in self._consumers:
            consumer.close()


# 全局单例
kafka_service = KafkaService()
