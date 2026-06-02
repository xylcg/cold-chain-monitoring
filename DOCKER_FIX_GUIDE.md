# Docker Desktop 修复指南

## 问题诊断

你的 Docker Desktop 出现了 "Linux VM backend is not running" 的问题。
症状：`docker ps` 返回 500 错误。

## 解决方案（按顺序尝试）

### 方案1: Docker Desktop 内置修复

1. 右键点击系统托盘中的 Docker 图标（鲸鱼图标）
2. 选择 **Troubleshoot** (故障排除)
3. 点击 **Restart Docker Desktop**
4. 等待 1-2 分钟让 Docker 完全启动
5. 打开命令行，运行 `docker ps` 确认正常

### 方案2: 重置 Docker Desktop

1. 打开 Docker Desktop
2. 点击右上角的 **设置齿轮** → **Troubleshoot**
3. 点击 **Clean / Purge data**
4. 勾选所有选项，点击 **Delete**
5. Docker 会自动重启并重新创建 VM
6. 等待完成后运行 `docker ps` 确认

### 方案3: 检查 WSL2

Docker Desktop 依赖 WSL2 运行 Linux VM：

1. 以**管理员身份**打开 PowerShell
2. 运行：`wsl --install`
3. 重启电脑
4. 重新打开 Docker Desktop

### 方案4: 检查虚拟化

1. 打开 **任务管理器** → **性能** → **CPU**
2. 查看右下角 **"虚拟化: 已启用"**
3. 如果是"已禁用"，需要在 BIOS 中启用 Intel VT-x / AMD-V

---

## Docker 恢复后启动项目

确认 `docker ps` 能正常运行后，按以下步骤操作：

### 步骤1: 启动 Docker 中间件

```bash
cd docker
docker-compose up -d
```

### 步骤2: 验证容器状态

```bash
docker ps
```

应该看到 5 个容器运行：
- coldchain-redis (6379端口)
- coldchain-postgres (5432端口)  
- coldchain-tdengine (6030-6043端口)
- coldchain-zookeeper (2181端口)
- coldchain-kafka (9092端口)

### 步骤3: 一键启动所有服务

双击项目根目录的 `start_all.bat`

或者手动依次启动：

```bash
# 终端1 - 后端
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 终端2 - 模拟器  
cd simulator
python sensor_simulator.py --vehicles 100 --cold-rooms 10 --interval 10

# 终端3 - 前端
cd frontend
npm run dev
```

### 步骤4: 验证数据

1. 访问 http://localhost:8000/health 确认 Redis 连接正常
2. 访问 http://localhost:8000/docs 查看 API 文档
3. 访问 http://localhost:3000 打开前端
4. 使用 admin/123456 登录
5. 等待 10-20 秒，数据会从模拟数据切换为 Redis 实时数据

### 数据流说明

```
模拟器(110设备) → 后端(8000) → Redis(实时数据) → Dashboard API → 前端(3000)
                               → TDengine(时序存储)
                               → Kafka(消息队列)
```

- 模拟器每 10 秒发送 110 条传感器数据
- Redis 缓存最新数据 + 设备在线状态
- Dashboard KPI 从 Redis 读取真实数据
- 如果 Redis 不可用，自动降级为模拟数据（data_source: "simulated"）
