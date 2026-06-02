from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "冷链物流智能监控平台"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "cold-chain-secret-key-change-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # TDengine
    TDENGINE_HOST: str = "localhost"
    TDENGINE_PORT: int = 6041
    TDENGINE_USER: str = "root"
    TDENGINE_PASSWORD: str = "taosdata"
    TDENGINE_DATABASE: str = "coldchain"

    # PostgreSQL
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "coldchain"
    POSTGRES_USER: str = "coldchain"
    POSTGRES_PASSWORD: str = "coldchain123"
    POSTGRES_URL: str = ""

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = "coldchain123"
    REDIS_DB: int = 0

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_SENSOR_TOPIC: str = "coldchain_sensor_data"
    KAFKA_ALERT_TOPIC: str = "coldchain_alerts"
    KAFKA_PREDICTION_TOPIC: str = "coldchain_predictions"

    # 模型
    ANOMALY_MODEL_PATH: str = "../models/lstm_anomaly_detector.pt"
    PREDICTION_MODEL_PATH: str = "../models/lstm_temperature_predictor.pt"
    ANOMALY_WINDOW_SIZE: int = 60
    PREDICTION_WINDOW_SIZE: int = 60
    PREDICTION_HORIZON: int = 30

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.POSTGRES_URL:
            self.POSTGRES_URL = (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
                f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
