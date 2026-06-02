# 冷链物流监控平台 API 端点参考

## 认证模块 (/api/v1/auth)

| 方法 | 路径 | 认证 | 说明 |
|------|------|------|------|
| POST | /auth/login | 否 | 用户登录，Body: {username, password} |
| GET | /auth/me | 是 | 获取当前用户信息 |

**测试账号**: admin / 123456

## 仪表盘模块 (/api/v1/dashboard)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /dashboard/kpi | 运营 KPI 数据 |
| GET | /dashboard/devices | 设备列表 |
| GET | /dashboard/overview | 全局态势 |
| GET | /dashboard/alerts/summary | 告警摘要 |

## 传感器模块 (/api/v1/sensors)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /sensors/data | 上报单条传感器数据 |
| POST | /sensors/data/batch | 批量上报传感器数据 |
| GET | /sensors/latest/{device_id} | 获取设备最新数据 |
| GET | /sensors/history/{device_id} | 获取设备历史数据 |

## 温度模块 (/api/v1/temperature)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /temperature/current/{device_id} | 当前温度 |
| GET | /temperature/trend/{device_id} | 温度趋势预测 |
| GET | /temperature/history/{device_id} | 历史温度 |
| GET | /temperature/anomaly/{device_id} | 异常检测 |

## 告警模块 (/api/v1/alerts)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /alerts | 告警列表 |
| GET | /alerts/active | 活跃告警 |
| POST | /alerts/acknowledge/{alert_id} | 确认告警 |
| GET | /alerts/rules | 告警规则列表 |
| POST | /alerts/rules | 创建告警规则 |
| DELETE | /alerts/rules/{rule_type} | 删除告警规则 |

## WebSocket (/ws)

| 路径 | 说明 |
|------|------|
| /ws/device/{device_id} | 设备实时数据推送 |
| /ws/alerts | 告警实时推送 |
| /ws/dashboard | 大屏实时数据推送 |
