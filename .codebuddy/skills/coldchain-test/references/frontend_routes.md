# 前端页面路由参考

使用 Hash 模式路由 (`createWebHashHistory`)

| 路径 | 组件 | 说明 |
|------|------|------|
| `/login` | Login.vue | 登录页（独立布局） |
| `/dashboard` | Dashboard.vue | 全局态势图 |
| `/monitor` | DeviceMonitor.vue | 设备监控 |
| `/alerts` | AlertCenter.vue | 告警中心 |
| `/temperature` | TemperatureTrend.vue | 温度趋势 |
| `/rules` | AlertRules.vue | 告警规则 |

## 页面功能说明

### Dashboard (全局态势图)
- KPI 指标卡片（设备总数、在线率、告警数、异常数）
- 设备状态分布图
- 实时告警列表
- 地图/图表展示

### DeviceMonitor (设备监控)
- 设备列表/表格
- 设备选择器
- 实时传感器数据展示
- 历史数据图表

### AlertCenter (告警中心)
- 告警列表/表格
- 按严重度筛选
- 告警确认操作

### TemperatureTrend (温度趋势)
- 温度变化曲线图
- 趋势预测图
- 异常检测标记

### AlertRules (告警规则)
- 规则列表/表格
- 添加/删除规则操作
- 规则启用/禁用
