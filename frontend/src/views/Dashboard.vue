<template>
  <div class="dashboard">
    <div class="page-header">
      <h2 class="page-title">运营调度中心 · 全局态势图</h2>
      <div class="header-meta">
        <div class="live-indicator">
          <span class="live-dot"></span>
          <span>实时监控中</span>
        </div>
        <span class="update-time">更新间隔 10s</span>
      </div>
    </div>

    <!-- KPI 卡片 -->
    <div class="kpi-grid">
      <div class="kpi-card kpi-card--blue">
        <div class="kpi-icon-box blue">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
        </div>
        <div class="kpi-body">
          <div class="kpi-label">设备在线率</div>
          <div class="kpi-value">
            <span class="kpi-number">{{ store.kpi.online_devices }}</span>
            <span class="kpi-unit">/ {{ store.kpi.total_devices }}</span>
          </div>
          <div class="kpi-bar">
            <div class="kpi-fill blue-fill" :style="{ width: store.kpi.online_rate + '%' }"></div>
          </div>
        </div>
      </div>

      <div class="kpi-card kpi-card--green">
        <div class="kpi-icon-box green">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
        </div>
        <div class="kpi-body">
          <div class="kpi-label">温控达标率</div>
          <div class="kpi-value">
            <span class="kpi-number" :class="store.kpi.temperature_compliance_rate >= 95 ? 'text-teal' : 'text-amber'">
              {{ store.kpi.temperature_compliance_rate }}
            </span>
            <span class="kpi-unit">%</span>
          </div>
          <div class="kpi-bar">
            <div class="kpi-fill green-fill" :style="{ width: store.kpi.temperature_compliance_rate + '%' }"></div>
          </div>
        </div>
      </div>

      <div class="kpi-card kpi-card--red" v-if="store.kpi.active_alerts > 0">
        <div class="kpi-icon-box red">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
        </div>
        <div class="kpi-body">
          <div class="kpi-label">活跃告警</div>
          <div class="kpi-value">
            <span class="kpi-number text-red">{{ store.kpi.active_alerts }}</span>
            <span class="kpi-unit">条</span>
          </div>
          <span class="kpi-tag tag-red">需处理</span>
        </div>
      </div>

      <div class="kpi-card kpi-card--clean" v-else>
        <div class="kpi-icon-box green">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
        </div>
        <div class="kpi-body">
          <div class="kpi-label">活跃告警</div>
          <div class="kpi-value">
            <span class="kpi-number text-teal">0</span>
            <span class="kpi-unit">条</span>
          </div>
          <span class="kpi-tag tag-teal">全部正常</span>
        </div>
      </div>

      <div class="kpi-card kpi-card--dual">
        <div class="kpi-dual">
          <div class="kpi-half">
            <div class="kpi-label">平均温度</div>
            <div class="kpi-value-sm">
              <span class="kpi-number-sm">{{ store.kpi.avg_temperature }}</span>
              <span class="kpi-unit-sm">°C</span>
            </div>
          </div>
          <div class="kpi-v-divider"></div>
          <div class="kpi-half">
            <div class="kpi-label">平均湿度</div>
            <div class="kpi-value-sm">
              <span class="kpi-number-sm">{{ store.kpi.avg_humidity }}</span>
              <span class="kpi-unit-sm">%</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 第二行 KPI：资源调度看板 -->
    <div class="kpi-grid kpi-grid--small">
      <div class="kpi-card kpi-card--sm">
        <div class="kpi-icon-box accent">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>
        </div>
        <div class="kpi-body">
          <div class="kpi-label">可调度车辆</div>
          <div class="kpi-value-sm">
            <span class="kpi-number-sm">{{ resourceStats.availableVehicles }}</span>
            <span class="kpi-unit-sm">辆</span>
          </div>
        </div>
      </div>

      <div class="kpi-card kpi-card--sm">
        <div class="kpi-icon-box accent2">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
        </div>
        <div class="kpi-body">
          <div class="kpi-label">可用冷库</div>
          <div class="kpi-value-sm">
            <span class="kpi-number-sm">{{ resourceStats.availableWarehouses }}</span>
            <span class="kpi-unit-sm">座</span>
          </div>
        </div>
      </div>

      <div class="kpi-card kpi-card--sm">
        <div class="kpi-icon-box warn">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
        </div>
        <div class="kpi-body">
          <div class="kpi-label">今日订单</div>
          <div class="kpi-value-sm">
            <span class="kpi-number-sm">{{ resourceStats.todayOrders }}</span>
            <span class="kpi-unit-sm">单</span>
          </div>
        </div>
      </div>

      <div class="kpi-card kpi-card--sm">
        <div class="kpi-icon-box energy">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
        </div>
        <div class="kpi-body">
          <div class="kpi-label">今日能耗</div>
          <div class="kpi-value-sm">
            <span class="kpi-number-sm">{{ resourceStats.energyUsage }}</span>
            <span class="kpi-unit-sm">kWh</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 快捷操作 -->
    <div class="quick-actions">
      <div class="qa-header">
        <h3>{{ roleInfo.label }}工作台</h3>
        <span class="qa-tips">{{ roleInfo.tips }}</span>
      </div>
      <div class="qa-grid">
        <div v-for="action in quickActions" :key="action.path" class="qa-card" @click="router.push(action.path)">
          <div class="qa-icon" :style="{ background: action.color + '18', color: action.color, borderColor: action.color + '33' }">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <g v-html="action.icon"></g>
            </svg>
          </div>
          <span class="qa-label">{{ action.label }}</span>
          <svg class="qa-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
        </div>
      </div>
    </div>

    <!-- 两栏布局：订单聚合 + 资源协调 -->
    <div class="dashboard-grid">
      <!-- 订单聚合看板 -->
      <div class="glass-card">
        <div class="card-header-row">
          <div>
            <h3>订单聚合看板 <span class="card-badge badge-blue">功能6</span></h3>
            <span class="card-sub">多温区智能匹配 · 实时订单调度</span>
          </div>
          <button class="btn-sm btn-primary" @click="router.push('/dispatch')">去调度</button>
        </div>
        <div class="order-stats-row">
          <div class="order-stat">
            <span class="os-num text-accent">{{ orderStats.pending }}</span>
            <span class="os-label">待分配</span>
          </div>
          <div class="order-stat">
            <span class="os-num text-amber">{{ orderStats.matching }}</span>
            <span class="os-label">匹配中</span>
          </div>
          <div class="order-stat">
            <span class="os-num text-teal">{{ orderStats.inTransit }}</span>
            <span class="os-label">运输中</span>
          </div>
          <div class="order-stat">
            <span class="os-num text-muted">{{ orderStats.completed }}</span>
            <span class="os-label">已完成</span>
          </div>
        </div>
        <div class="zone-match">
          <h4>温区车辆匹配</h4>
          <div class="zone-row">
            <div class="zone-tag zone-freeze">冷冻区 <span class="zone-cnt">{{ zoneMatch.freeze }}</span></div>
            <div class="zone-tag zone-chill">冷藏区 <span class="zone-cnt">{{ zoneMatch.chill }}</span></div>
            <div class="zone-tag zone-ambient">恒温区 <span class="zone-cnt">{{ zoneMatch.ambient }}</span></div>
          </div>
        </div>
      </div>

      <!-- 资源协调看板 -->
      <div class="glass-card">
        <div class="card-header-row">
          <div>
            <h3>资源协调看板 <span class="card-badge badge-purple">功能10</span></h3>
            <span class="card-sub">动态资源调配 · 智能匹配</span>
          </div>
          <button class="btn-sm btn-secondary" @click="refreshResources">刷新</button>
        </div>
        <div class="resource-list">
          <div class="resource-item" v-for="r in resourceList" :key="r.id">
            <div class="res-info">
              <div class="res-icon" :class="r.type">
                <svg v-if="r.type==='vehicle'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>
                <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
              </div>
              <div class="res-detail">
                <span class="res-name">{{ r.name }}</span>
                <span class="res-desc">{{ r.type === 'vehicle' ? '多温区冷藏车' : '智能冷库' }} · {{ r.location }}</span>
              </div>
            </div>
            <div class="res-status">
              <span class="res-dot" :class="r.status === 'idle' ? 'green' : r.status === 'busy' ? 'amber' : 'red'"></span>
              <span>{{ r.status === 'idle' ? '空闲' : r.status === 'busy' ? '运输中' : '维护中' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 设备实时状态 -->
    <div class="glass-card">
      <div class="card-header-row">
        <div>
          <h3>设备实时状态</h3>
          <span class="card-sub">共 {{ store.devices.length }} 台设备在线监控</span>
        </div>
        <div class="legend-row">
          <span class="legend-it"><span class="legend-dot green-dot"></span>正常</span>
          <span class="legend-it"><span class="legend-dot amber-dot"></span>预警</span>
          <span class="legend-it"><span class="legend-dot red-dot"></span>告警</span>
        </div>
      </div>
      <div class="table-box">
        <el-table :data="store.devices" stripe style="width: 100%" :max-height="400">
          <el-table-column prop="device_id" label="设备 ID" width="130">
            <template #default="{ row }">
              <code class="cell-id">{{ row.device_id }}</code>
            </template>
          </el-table-column>
          <el-table-column prop="device_type" label="类型" width="80">
            <template #default="{ row }">
              <span class="type-tag" :class="row.device_type">
                {{ row.device_type === 'vehicle' ? '车辆' : '冷库' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="temperature" label="温度" width="90" sortable>
            <template #default="{ row }">
              <span class="temp-val" :class="getTempClass(row.temperature)">{{ row.temperature }}°C</span>
            </template>
          </el-table-column>
          <el-table-column prop="humidity" label="湿度" width="80" />
          <el-table-column prop="door_status" label="车门" width="80">
            <template #default="{ row }">
              <span class="door-badge" :class="{ open: row.door_status }">
                {{ row.door_status ? '开启' : '关闭' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="active_alerts" label="告警" width="70">
            <template #default="{ row }">
              <span v-if="row.active_alerts > 0" class="alert-badge">{{ row.active_alerts }}</span>
              <span v-else class="none-text">—</span>
            </template>
          </el-table-column>
          <el-table-column prop="last_update" label="最后更新" min-width="150">
            <template #default="{ row }">
              <span class="time-text">{{ row.last_update }}</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAppStore } from '@/stores/app'
import { useRouter } from 'vue-router'
import { getTempClass } from '@/utils'
import { computed, reactive, onMounted } from 'vue'

const store = useAppStore()
const router = useRouter()

const role = computed(() => store.userRole || 'admin')
const roleInfo = computed(() => {
  const m: Record<string, any> = {
    admin: { label: '管理员', tips: '配置规则、规划路径、调度资源，统筹冷链运营' },
    manager: { label: '经理', tips: '查看全局态势、审核追溯链路、评估生鲜品质' },
    driver: { label: '司机', tips: '查看配送路线、监控车辆温度、及时处理告警' },
  }
  return m[role.value] || m.admin
})

const quickActions = computed(() => {
  const actions: Record<string, { path: string; label: string; icon: string; color: string }[]> = {
    admin: [
      { path: '/routes', label: '路径规划', icon: '<polyline points="3 12 7 5 17 19 21 12"/>', color: '#00a8ff' },
      { path: '/dispatch', label: '多温区调度', icon: '<rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/>', color: '#7c3aed' },
      { path: '/rules', label: '告警规则', icon: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09A1.65 1.65 0 0 0 19.4 15z"/>', color: '#f59e0b' },
      { path: '/alerts', label: '告警中心', icon: '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>', color: '#ef4444' },
    ],
    manager: [
      { path: '/temperature', label: '温度趋势', icon: '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>', color: '#00a8ff' },
      { path: '/traceability', label: '追溯查询', icon: '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>', color: '#7c3aed' },
      { path: '/quality', label: '品质评估', icon: '<path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>', color: '#f59e0b' },
      { path: '/alerts', label: '告警中心', icon: '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>', color: '#ef4444' },
    ],
    driver: [
      { path: '/routes', label: '配送路线', icon: '<polyline points="3 12 7 5 17 19 21 12"/>', color: '#00a8ff' },
      { path: '/tracking', label: '车辆追踪', icon: '<circle cx="12" cy="10" r="3"/><path d="M12 21.7C17.3 17 20 13 20 10a8 8 0 1 0-16 0c0 3 2.7 7 8 11.7z"/>', color: '#7c3aed' },
      { path: '/alerts', label: '告警处理', icon: '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>', color: '#ef4444' },
      { path: '/mobile', label: '移动端', icon: '<rect x="5" y="2" width="14" height="20" rx="2"/><line x1="12" y1="18" x2="12.01" y2="18"/>', color: '#0ea5e9' },
    ],
  }
  return actions[role.value] || actions.admin
})

// 资源统计
const resourceStats = reactive({
  availableVehicles: 12,
  availableWarehouses: 4,
  todayOrders: 28,
  energyUsage: 342,
})

// 订单统计
const orderStats = reactive({
  pending: 5,
  matching: 8,
  inTransit: 10,
  completed: 5,
})

// 温区匹配
const zoneMatch = reactive({
  freeze: 4,
  chill: 6,
  ambient: 8,
})

// 资源列表
const resourceList = reactive([
  { id: 'V001', name: '冷链车 A-01', type: 'vehicle', location: '上海仓', status: 'idle' },
  { id: 'V002', name: '冷链车 A-02', type: 'vehicle', location: '上海仓', status: 'busy' },
  { id: 'V003', name: '冷链车 A-03', type: 'vehicle', location: '杭州仓', status: 'idle' },
  { id: 'W001', name: '上海冷库 1号', type: 'warehouse', location: '浦东新区', status: 'idle' },
  { id: 'W002', name: '杭州冷库 2号', type: 'warehouse', location: '余杭区', status: 'busy' },
])

function refreshResources() {
  // 模拟刷新资源数据
  resourceStats.availableVehicles = 10 + Math.floor(Math.random() * 6)
  resourceStats.todayOrders = 25 + Math.floor(Math.random() * 10)
  resourceStats.energyUsage = 320 + Math.floor(Math.random() * 50)
}

onMounted(() => {
  store.startAutoRefresh(10000)
})
</script>

<style scoped>
.dashboard { animation: fadeInUp 0.45s ease-out; }

.header-meta { display: flex; align-items: center; gap: 14px; }
.live-indicator {
  display: flex; align-items: center; gap: 6px;
  font-size: 12px; color: var(--teal); font-family: var(--font-mono); font-weight: 500;
}
.live-dot {
  width: 7px; height: 7px; border-radius: 50%; background: var(--teal);
  animation: pulse-ring 2s ease-out infinite;
}
.update-time {
  font-size: 11px; color: var(--text-muted); font-family: var(--font-mono);
  background: var(--bg-input); padding: 3px 10px; border-radius: 20px;
}

/* --- KPI --- */
.kpi-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 0.8fr;
  gap: 14px;
  margin-bottom: 22px;
}
.kpi-card {
  background: var(--bg-card);
  backdrop-filter: var(--blur-card);
  -webkit-backdrop-filter: var(--blur-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-lg);
  padding: 18px 20px;
  display: flex; gap: 14px;
  transition: all 0.3s ease;
  box-shadow: var(--shadow-sm);
}
.kpi-card:hover { box-shadow: var(--shadow); transform: translateY(-2px); }
.kpi-card--red { border-color: rgba(239,68,68,0.2); }

.kpi-icon-box {
  width: 44px; height: 44px; border-radius: var(--radius);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.kpi-icon-box.blue { background: var(--accent-bg); color: var(--accent); }
.kpi-icon-box.green { background: var(--teal-bg); color: var(--teal); }
.kpi-icon-box.red { background: var(--red-bg); color: var(--red); }

.kpi-body { flex: 1; min-width: 0; }
.kpi-label { font-size: 11px; color: var(--text-muted); letter-spacing: 0.03em; margin-bottom: 4px; }
.kpi-value { display: flex; align-items: baseline; gap: 3px; margin-bottom: 8px; }
.kpi-number { font-family: var(--font-display); font-size: 28px; font-weight: 800; color: var(--text-title); line-height: 1; }
.kpi-unit { font-size: 12px; color: var(--text-muted); font-family: var(--font-body); }
.text-teal { color: var(--teal) !important; }
.text-amber { color: var(--amber) !important; }
.text-red { color: var(--red) !important; }


.kpi-bar { height: 3px; background: var(--bg-input); border-radius: 3px; overflow: hidden; }
.kpi-fill { height: 100%; border-radius: 3px; transition: width 0.8s ease; }
.blue-fill { background: linear-gradient(90deg, var(--accent), var(--accent-light)); }
.green-fill { background: linear-gradient(90deg, var(--teal), var(--teal-light)); }

.kpi-tag {
  display: inline-block; font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 20px;
  font-family: var(--font-mono); letter-spacing: 0.04em; text-transform: uppercase;
}
.tag-red { background: var(--red-bg); color: var(--red); }
.tag-teal { background: var(--teal-bg); color: var(--teal); }

/* Dual KPI */
.kpi-dual { display: flex; align-items: center; width: 100%; }
.kpi-half { flex: 1; text-align: center; }
.kpi-v-divider { width: 1px; height: 32px; background: var(--border-light); }
.kpi-value-sm { display: flex; align-items: baseline; justify-content: center; gap: 2px; }
.kpi-number-sm { font-family: var(--font-display); font-size: 24px; font-weight: 800; color: var(--text-title); }
.kpi-unit-sm { font-size: 11px; color: var(--text-muted); }

/* Table */
.card-header-row {
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;
}
.card-header-row h3 { font-size: 15px; font-weight: 700; color: var(--text-title); }
.card-sub { font-size: 12px; color: var(--text-muted); margin-left: 8px; }
.legend-row { display: flex; gap: 16px; align-items: center; }
.legend-it { font-size: 11px; color: var(--text-muted); display: flex; align-items: center; gap: 5px; }
.legend-dot { width: 6px; height: 6px; border-radius: 50%; }
.green-dot { background: var(--teal); }
.amber-dot { background: var(--amber); }
.red-dot { background: var(--red); }

.table-box { overflow-x: auto; }
.cell-id {
  font-family: var(--font-mono); font-size: 11px; color: var(--accent);
  background: var(--accent-bg); padding: 2px 8px; border-radius: 4px; font-weight: 500;
}
.type-tag {
  font-size: 11px; padding: 2px 8px; border-radius: 20px; font-weight: 600;
}
.type-tag.vehicle { background: var(--accent-bg); color: var(--accent); }
.type-tag.cold_room { background: var(--teal-bg); color: var(--teal); }
.temp-val { font-family: var(--font-mono); font-weight: 600; font-size: 13px; }
.door-badge { font-size: 11px; padding: 2px 8px; border-radius: 12px; background: var(--bg-input); color: var(--text-secondary); }
.door-badge.open { background: var(--amber-bg); color: var(--amber); }
.alert-badge {
  font-family: var(--font-mono); font-size: 11px; font-weight: 700;
  background: var(--red); color: #fff; padding: 2px 7px; border-radius: 10px;
}
.none-text { color: var(--teal); font-weight: 600; }
.time-text { font-family: var(--font-mono); font-size: 11px; color: var(--text-muted); }

@media (max-width: 1200px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }

/* Dashboard grid */
.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 22px;
  margin-bottom: 22px;
}
@media (max-width: 1024px) {
  .dashboard-grid { grid-template-columns: 1fr; }
}

/* Order stats */
.order-stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 20px;
}
.order-stat {
  background: var(--bg-input);
  border-radius: var(--radius);
  padding: 16px;
  text-align: center;
}
.os-num {
  display: block;
  font-family: var(--font-display);
  font-size: 26px;
  font-weight: 800;
  line-height: 1;
  margin-bottom: 6px;
}
.os-label {
  font-size: 12px;
  color: var(--text-muted);
}

/* Zone match */
.zone-match h4 {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 10px;
}
.zone-row {
  display: flex;
  gap: 10px;
}
.zone-tag {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-radius: var(--radius);
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  background: var(--bg-input);
}
.zone-cnt {
  font-family: var(--font-display);
  font-weight: 700;
  color: var(--text-title);
}
.zone-freeze { border-left: 3px solid var(--accent); }
.zone-chill { border-left: 3px solid var(--teal); }
.zone-ambient { border-left: 3px solid var(--amber); }

/* Resource list */
.resource-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.resource-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px;
  background: var(--bg-input);
  border-radius: var(--radius);
}
.res-info {
  display: flex;
  align-items: center;
  gap: 12px;
}
.res-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}
.res-icon.vehicle { background: linear-gradient(135deg, var(--accent), var(--accent-light)); }
.res-icon.warehouse { background: linear-gradient(135deg, var(--aurora), var(--aurora-light)); }
.res-detail {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.res-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-title);
}
.res-desc {
  font-size: 11px;
  color: var(--text-muted);
}
.res-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--text-secondary);
}
.res-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
}
.res-dot.green { background: var(--teal); }
.res-dot.amber { background: var(--amber); }
.res-dot.red { background: var(--red); }

/* Quick Actions */
.kpi-icon-box.accent { background: var(--accent-bg); color: var(--accent); }
.kpi-icon-box.accent2 { background: var(--aurora-bg); color: var(--aurora); }
.kpi-icon-box.warn { background: var(--amber-bg); color: var(--amber); }
.kpi-icon-box.energy { background: rgba(0, 210, 160, 0.08); color: var(--teal); }
.kpi-card--sm {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius);
  padding: 14px 18px;
  display: flex; gap: 12px;
  box-shadow: var(--shadow-xs);
}
.text-accent { color: var(--accent) !important; }

/* Temp classes */
.temp-normal { color: var(--teal) !important; }
.temp-warn { color: var(--amber) !important; }
.temp-danger { color: var(--red) !important; }

/* Quick Actions */
.quick-actions {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-lg);
  padding: 20px 22px;
  margin-bottom: 22px;
  box-shadow: var(--shadow-sm);
}
.qa-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 16px;
}
.qa-header h3 {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-title);
}
.qa-tips {
  font-size: 12px;
  color: var(--text-muted);
}
.qa-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 10px;
}
.qa-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border-radius: 10px;
  border: 1px solid var(--border);
  cursor: pointer;
  transition: all 0.2s;
  background: var(--bg-page);
}
.qa-card:hover {
  background: var(--bg-input);
  border-color: var(--border-light);
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}
.qa-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid;
  flex-shrink: 0;
}
.qa-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  flex: 1;
}
.qa-card:hover .qa-label {
  color: var(--text-title);
}
.qa-arrow {
  color: var(--text-muted);
  opacity: 0;
  transition: all 0.2s;
}
.qa-card:hover .qa-arrow {
  opacity: 1;
}
</style>
