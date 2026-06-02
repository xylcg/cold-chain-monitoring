---
name: coldchain-test
description: >
  冷链物流智能监控平台的自动化测试套件。包含后端 API 测试和前端 E2E 测试。
  当用户请求测试冷链物流平台、验证 API 端点、检查前端页面功能、
  运行回归测试、排查系统故障、或提到"测试"、"验证"、"检查"平台功能时使用此技能。
  支持独立运行后端测试或前端测试，也可一键运行全量测试。
---

# 冷链物流监控平台测试套件

## 概述

此测试套件包含两个测试脚本：

1. **`scripts/test_api.py`** - 后端 API 测试（无需浏览器）
2. **`scripts/test_frontend.py`** - 前端 E2E 测试（需要 Playwright/Chromium）

## 快速开始

### 运行后端 API 测试

```bash
# 默认测试 localhost:8000
python scripts/test_api.py

# 指定后端地址
python scripts/test_api.py --host 192.168.1.100 --port 8080

# JSON 格式输出
python scripts/test_api.py --json
```

### 运行前端 E2E 测试

```bash
# 默认测试 localhost:3000（无头模式）
python scripts/test_frontend.py

# 指定前端地址
python scripts/test_frontend.py --url http://localhost:5173

# 可视化模式（可看到浏览器操作）
python scripts/test_frontend.py --headed
```

### 前提条件

- **API 测试**: `pip install httpx`
- **前端测试**: `pip install playwright && playwright install chromium`
- 后端服务运行在 `localhost:8000`，前端服务运行在 `localhost:3000`

## 测试覆盖范围

### API 测试覆盖（28+ 个测试用例）

| 模块 | 测试内容 |
|------|---------|
| Health | GET /, GET /health 健康检查 |
| Auth | 登录（正确/错误密码）、获取用户信息 |
| Dashboard | KPI、设备列表、全局态势、告警摘要 |
| Sensors | 单条上报、批量上报、最新数据、历史数据 |
| Temperature | 当前温度、趋势预测、历史温度、异常检测 |
| Alerts | 告警列表、活跃告警、规则 CRUD |
| AuthCheck | 未认证请求是否正确返回 401 |

### 前端 E2E 测试覆盖（20+ 个测试用例）

| 页面 | 测试内容 |
|------|---------|
| Login | 登录表单元素、登录流程验证 |
| Dashboard | KPI 卡片、图表、表格、标题 |
| DeviceMonitor | 设备列表、选择器 |
| AlertCenter | 告警列表/表格 |
| TemperatureTrend | 温度图表 |
| AlertRules | 规则表格、操作按钮 |
| Navigation | 侧边栏菜单项 |
| Responsive | 桌面/平板/手机三端适配 |

## 测试流程

### 全量测试流程

1. 确保后端和前端服务已启动
2. 运行 API 测试：`python scripts/test_api.py`
3. 运行前端测试：`python scripts/test_frontend.py`
4. 检查测试报告中的失败项并修复

### 单模块测试

如只需测试某个模块，直接查看对应脚本中的 `test_*` 方法并单独调用。

## 故障排查

### 后端连接超时
- 检查后端是否运行：`netstat -ano | findstr :8000`
- 检查是否因 Docker 中间件缺失导致超时（部分端点依赖 Redis/TDengine）

### 前端测试 Chromium 错误
- 运行 `playwright install chromium` 安装浏览器
- 如果下载慢，设置镜像：`set PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/`

### 登录测试失败
- 确认测试账号存在：admin / 123456
- 检查 JWT token 是否正确获取

## 参考文档

- API 端点详情：参见 `references/api_endpoints.md`
- 前端路由详情：参见 `references/frontend_routes.md`
