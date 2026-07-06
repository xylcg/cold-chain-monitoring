"""
智能冷链物流监控平台 - FastAPI 主应用
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from loguru import logger

from .core.config import get_settings
from .services.redis_service import redis_service
from .services.tdengine_service import tdengine_service
from .api import sensors, alerts, temperature, dashboard, auth, websocket, geofence, traceability, customer, vehicles, maintenance, route_planning, dispatch, quality, resources, upload, driver

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    logger.info("=" * 60)
    logger.info(f"  {settings.APP_NAME} v{settings.APP_VERSION} 启动中...")
    logger.info("=" * 60)

    # 初始化服务
    try:
        await redis_service.connect()
        logger.info("Redis 连接成功")
    except Exception as e:
        logger.warning(f"Redis 连接失败 (系统将降级运行): {e}")

    try:
        tdengine_service.connect()
    except Exception as e:
        logger.warning(f"TDengine 连接失败 (将使用模拟模式): {e}")

    logger.info(f"Kafka 服务器: {settings.KAFKA_BOOTSTRAP_SERVERS}")
    logger.info(f"TDengine 数据库: {settings.TDENGINE_DATABASE}")
    logger.info(f"API 文档: http://localhost:8000/docs")
    logger.info(f"WebSocket: ws://localhost:8000/ws/")
    logger.info("=" * 60)

    yield

    # 清理
    await redis_service.close()
    tdengine_service.close()
    logger.info("应用已关闭")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## 基于深度学习的智能冷链物流监控平台

构建覆盖"产地预冷—冷藏运输—冷仓存储—末端配送"全链路的智能冷链监控平台。

### 已实现功能模块
- **模块1**: 多传感器数据采集 ✅
- **模块2**: 温度异常实时检测（LSTM自编码器）✅
- **模块3**: 温控趋势智能预测（LSTM/Transformer）✅
- **模块4**: 冷机故障预测性维护 ✅
- **模块5**: 冷链路径智能规划 ✅
- **模块6**: 多温区车厢智能调度 ✅
- **模块7**: 生鲜品质AI评估 ✅
- **模块8**: 冷链电子围栏管理 ✅
- **模块9**: 全程冷链追溯链（含区块链存证）✅
- **模块10**: 冷链资源智能调度 ✅
- **模块11**: 移动端冷链监控 ✅
- **模块12**: 运营管理后台 ✅
- **模块13**: 智能预警与应急处置 ✅
- **模块14**: 客户温控查询服务 ✅

### 技术栈
FastAPI + Vue3 + TDengine + PostgreSQL + Redis + Kafka + PyTorch
    """,
    lifespan=lifespan,
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router)
app.include_router(sensors.router)
app.include_router(alerts.router)
app.include_router(temperature.router)
app.include_router(dashboard.router)
app.include_router(websocket.router)
app.include_router(geofence.router)
app.include_router(traceability.router)
app.include_router(customer.router)
app.include_router(vehicles.router)
app.include_router(maintenance.router)
app.include_router(route_planning.router)
app.include_router(dispatch.router)
app.include_router(quality.router)
app.include_router(resources.router)
app.include_router(upload.router)
app.include_router(driver.router)

# 静态文件服务 - 上传的图片
uploads_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "ws_docs": "ws://localhost:8000/ws/",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    online_devices = 0
    try:
        online_devices = len(await redis_service.get_online_devices())
    except Exception:
        pass

    return {
        "status": "healthy",
        "redis": "connected" if redis_service._redis else "disconnected",
        "tdengine": "connected" if tdengine_service._conn else "simulated",
        "online_devices": online_devices,
        "active_connections": 0,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
