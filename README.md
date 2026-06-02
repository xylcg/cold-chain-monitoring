# 基于深度学习的智能冷链物流监控平台

## 项目概述

构建覆盖"产地预冷—冷藏运输—冷仓存储—末端配送"全链路的智能冷链监控平台，基于深度学习、物联网感知和边缘计算技术，实现冷链环境的实时感知、智能预测和主动调控。

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    前端展示层                            │
│    Vue3 (Web 管理后台)  +  微信小程序 (移动端 APP)       │
├─────────────────────────────────────────────────────────┤
│                   API 服务层 (FastAPI)                    │
│    REST API  │  WebSocket  │  JWT 认证                  │
├─────────────────────────────────────────────────────────┤
│              流处理 & 推理引擎                           │
│    Kafka Consumer  │  LSTM 异常检测  │  温度预测          │
├─────────────────────────────────────────────────────────┤
│              消息队列 & 缓存                             │
│    Kafka  │  Redis  │  TDengine  │  PostgreSQL          │
└─────────────────────────────────────────────────────────┘
```

## 项目结构

```
├── backend/                 # 后端服务 (FastAPI)
│   ├── app/
│   │   ├── api/            # API 路由
│   │   │   ├── sensors.py      # 传感器数据接入 (模块1)
│   │   │   ├── temperature.py  # 温度监控/异常检测/预测 (模块2/3)
│   │   │   ├── alerts.py       # 告警管理 (模块13)
│   │   │   ├── dashboard.py    # 运营管理后台 (模块12)
│   │   │   ├── auth.py         # 认证服务
│   │   │   ├── websocket.py    # WebSocket 实时推送
│   │   │   ├── geofence.py     # 电子围栏管理
│   │   │   ├── traceability.py # 冷链追溯链
│   │   │   └── customer.py     # 客户温控查询
│   │   ├── core/           # 核心配置
│   │   │   ├── config.py       # 配置管理
│   │   │   └── security.py     # JWT/认证
│   │   ├── services/       # 服务层
│   │   │   ├── kafka_service.py    # Kafka 消息队列
│   │   │   ├── redis_service.py    # Redis 缓存
│   │   │   ├── tdengine_service.py # TDengine 时序存储
│   │   │   ├── alert_engine.py     # 告警引擎
│   │   │   ├── model_service.py    # 模型推理服务
│   │   │   └── websocket_manager.py # WebSocket 管理
│   │   ├── schemas/        # Pydantic 数据模型
│   │   └── main.py         # FastAPI 应用入口
│   └── requirements.txt
├── frontend/               # 前端 (Vue3 + Element Plus)
│   ├── src/
│   │   ├── views/          # 页面
│   │   │   ├── Login.vue          # 登录页
│   │   │   ├── Dashboard.vue      # 全局态势图
│   │   │   ├── DeviceMonitor.vue  # 设备监控
│   │   │   ├── TemperatureTrend.vue # 温度趋势预测
│   │   │   ├── AlertCenter.vue    # 告警中心
│   │   │   ├── AlertRules.vue     # 告警规则配置
│   │   │   ├── GeofenceManager.vue # 电子围栏管理
│   │   │   ├── Traceability.vue   # 冷链追溯
│   │   │   └── CustomerQuery.vue  # 客户查询
│   │   ├── api/            # API 接口层
│   │   ├── stores/         # Pinia 状态管理
│   │   ├── utils/          # 共享工具函数
│   │   ├── router/         # 路由
│   │   ├── layouts/        # 布局
│   │   └── styles/         # 样式
│   ├── package.json
│   └── vite.config.ts
├── simulator/              # 传感器数据模拟器
│   └── sensor_simulator.py # 100辆车 + 10个冷库模拟
├── models/                 # 深度学习模型
│   ├── lstm_anomaly_detector.py  # LSTM 异常检测
│   └── temperature_predictor.py  # LSTM/Transformer 温度预测
├── docker/                 # Docker 部署配置
│   ├── Dockerfile.backend     # 后端镜像
│   ├── Dockerfile.frontend    # 前端镜像
│   ├── Dockerfile.simulator   # 模拟器镜像
│   ├── nginx.conf             # Nginx 代理配置
│   └── init-postgres.sql      # PostgreSQL 初始化
├── docker-compose.yml      # Docker Compose 编排文件（根目录）
└── 需求分析.md             # 产品需求文档
```

## 快速开始

### 1. 环境要求

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose

### 2. 启动中间件

```bash
cd docker
docker-compose up -d
```

### 3. 启动后端

```bash
cd backend
pip install -r requirements.txt
python -m app.main
```

访问 API 文档: http://localhost:8000/docs

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

访问管理后台: http://localhost:3000

### 5. 启动数据模拟器

```bash
cd simulator
python sensor_simulator.py --vehicles 100 --cold-rooms 10 --interval 10
```

### 6. 训练模型

```bash
# 训练异常检测模型
cd models
python lstm_anomaly_detector.py

# 训练温度预测模型
python temperature_predictor.py
```

## 测试账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | 123456 | 系统管理员 |
| driver01 | 123456 | 配送员 |
| manager01 | 123456 | 区域经理 |

## MVP 功能模块

| 模块 | 名称 | 状态 |
|------|------|------|
| 1 | 多传感器数据采集 | ✅ |
| 2 | 温度异常实时检测 (LSTM) | ✅ |
| 3 | 温控趋势智能预测 (LSTM/Transformer) | ✅ |
| 11 | 移动端冷链监控 APP | 🚧 基础版 |
| 12 | 运营管理后台 (Web) | ✅ |
| 13 | 智能预警与应急处置 | ✅ |

## 技术栈

- **后端**: FastAPI (Python)
- **前端**: Vue3 + Element Plus + ECharts
- **移动端**: 微信小程序
- **数据库**: TDengine (时序) + PostgreSQL (业务) + Redis (缓存)
- **消息队列**: Kafka
- **深度学习**: PyTorch (LSTM/Transformer)
- **部署**: Docker + Kubernetes
