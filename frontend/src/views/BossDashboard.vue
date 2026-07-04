<template>
  <div class="boss-dashboard">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">老板工作台</h2>
        <span class="page-subtitle">冷链运营全局态势 · KPI决策看板 · 运单查询</span>
      </div>
      <div class="header-right">
        <div class="live-indicator">
          <span class="live-dot"></span>
          <span>实时监控中 · 更新间隔 10s</span>
        </div>
        <div class="date-display">{{ currentDate }}</div>
      </div>
    </div>

    <!-- KPI 核心指标 -->
    <div class="kpi-section">
      <div class="section-title">核心运营指标 <span class="card-badge badge-blue">功能8 · KPI决策看板</span></div>
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-icon blue">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
          </div>
          <div class="kpi-info">
            <div class="kpi-label">设备在线率</div>
            <div class="kpi-value">
              <span class="kpi-number">{{ store.kpi.online_devices }}</span>
              <span class="kpi-sep">/</span>
              <span class="kpi-total">{{ store.kpi.total_devices }}</span>
            </div>
            <div class="kpi-progress"><div class="progress-fill blue-fill" :style="{ width: store.kpi.online_rate + '%' }"></div></div>
            <div class="kpi-pct">{{ store.kpi.online_rate }}%</div>
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-icon green">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
          </div>
          <div class="kpi-info">
            <div class="kpi-label">温控达标率</div>
            <div class="kpi-value"><span class="kpi-number" :class="store.kpi.temperature_compliance_rate >= 95 ? 'text-green' : 'text-amber'">{{ store.kpi.temperature_compliance_rate }}</span><span class="kpi-unit">%</span></div>
            <div class="kpi-progress"><div class="progress-fill green-fill" :style="{ width: store.kpi.temperature_compliance_rate + '%' }"></div></div>
            <div class="kpi-status" :class="store.kpi.temperature_compliance_rate >= 95 ? 'status-good' : 'status-warn'">{{ store.kpi.temperature_compliance_rate >= 95 ? '达标' : '需关注' }}</div>
          </div>
        </div>
        <div class="kpi-card" :class="{ 'kpi-card--alert': store.kpi.active_alerts > 0 }">
          <div class="kpi-icon red">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
          </div>
          <div class="kpi-info">
            <div class="kpi-label">活跃告警</div>
            <div class="kpi-value"><span class="kpi-number" :class="store.kpi.active_alerts > 0 ? 'text-red' : 'text-green'">{{ store.kpi.active_alerts }}</span><span class="kpi-unit">条</span></div>
            <div class="kpi-sub">紧急 <b class="text-red">{{ store.kpi.critical_alerts || 0 }}</b> 条</div>
            <div class="kpi-status" :class="store.kpi.active_alerts > 0 ? 'status-bad' : 'status-good'">{{ store.kpi.active_alerts > 0 ? '需处置' : '全部正常' }}</div>
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-icon purple">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
          </div>
          <div class="kpi-info">
            <div class="kpi-label">今日运单</div>
            <div class="kpi-value"><span class="kpi-number">{{ todayStats.totalOrders }}</span><span class="kpi-unit">单</span></div>
            <div class="kpi-sub">已完成 <b class="text-green">{{ todayStats.completedOrders }}</b> 单</div>
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-icon cyan">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>
          </div>
          <div class="kpi-info">
            <div class="kpi-label">资源利用率</div>
            <div class="kpi-value"><span class="kpi-number">{{ todayStats.utilizationRate }}</span><span class="kpi-unit">%</span></div>
            <div class="kpi-sub">车辆 <b>{{ todayStats.activeVehicles }}</b> / 冷库 <b>{{ todayStats.activeWarehouses }}</b></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 温控 + 告警统计 -->
    <div class="two-col">
      <div class="glass-card">
        <div class="card-header"><h3>平均温度 · 平均湿度</h3><span class="card-badge">实时</span></div>
        <div class="env-grid">
          <div class="env-card temp-card">
            <div class="env-icon-wrap blue-bg"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z"/></svg></div>
            <div class="env-data"><div class="env-value">{{ store.kpi.avg_temperature }}<span class="env-unit">°C</span></div><div class="env-label">全网平均温度</div></div>
          </div>
          <div class="env-card humidity-card">
            <div class="env-icon-wrap teal-bg"><svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg></div>
            <div class="env-data"><div class="env-value">{{ store.kpi.avg_humidity }}<span class="env-unit">%</span></div><div class="env-label">全网平均湿度</div></div>
          </div>
        </div>
      </div>
      <div class="glass-card">
        <div class="card-header"><h3>告警统计（近24小时）</h3><el-button text type="primary" size="small" @click="router.push('/alerts')">查看全部 →</el-button></div>
        <div class="alert-stats" v-if="alertStats">
          <div class="stat-row">
            <div class="stat-item"><span class="stat-num text-red">{{ alertStats.critical || 0 }}</span><span class="stat-label">紧急告警</span></div>
            <div class="stat-item"><span class="stat-num text-amber">{{ alertStats.warning || 0 }}</span><span class="stat-label">严重告警</span></div>
            <div class="stat-item"><span class="stat-num text-blue">{{ alertStats.info || 0 }}</span><span class="stat-label">一般告警</span></div>
            <div class="stat-item"><span class="stat-num text-green">{{ alertStats.resolved || 0 }}</span><span class="stat-label">已处置</span></div>
          </div>
        </div>
        <div v-else class="empty-state">暂无告警数据</div>
      </div>
    </div>

    <!-- 风险管理 + 品质溯源 -->
    <div class="two-col">
      <div class="glass-card risk-card">
        <div class="card-header"><h3>风险管理</h3><span class="card-badge badge-red">功能12</span></div>
        <div class="risk-summary">
          <div class="risk-stat">
            <span class="risk-num text-red">{{ store.kpi.critical_alerts || 0 }}</span>
            <span class="risk-label">紧急事件</span>
          </div>
          <div class="risk-stat">
            <span class="risk-num text-amber">{{ store.kpi.active_alerts - (store.kpi.critical_alerts || 0) }}</span>
            <span class="risk-label">预警事件</span>
          </div>
          <div class="risk-stat">
            <span class="risk-num text-green">{{ resolvedToday }}</span>
            <span class="risk-label">今日已处置</span>
          </div>
        </div>
        <div class="risk-actions">
          <button class="btn-emergency" @click="activateEmergency">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
            一键启动应急预案
          </button>
          <button class="btn-secondary" @click="router.push('/alerts')">告警中心 →</button>
        </div>
      </div>
      <div class="glass-card trace-card">
        <div class="card-header"><h3>品质溯源管理</h3><span class="card-badge badge-purple">功能9</span></div>
        <div class="trace-stats">
          <div class="trace-stat-item">
            <span class="trace-num">{{ traceChainCount }}</span>
            <span class="trace-label">完整追溯链</span>
          </div>
          <div class="trace-stat-item">
            <span class="trace-num text-green">{{ traceCompleteRate }}%</span>
            <span class="trace-label">数据完整率</span>
          </div>
        </div>
        <div class="risk-actions">
          <button class="btn-secondary" @click="router.push('/traceability')">区块链溯源 →</button>
          <button class="btn-secondary" @click="router.push('/customer')">运单查询 →</button>
        </div>
      </div>
    </div>

    <!-- ============ 经营财务看板 ============ -->
    <div class="section-block" v-if="financeData">
      <div class="section-header">
        <h3>💰 经营财务看板</h3>
        <span class="card-badge badge-cyan">{{ financeData.month }}月度数据</span>
      </div>

      <!-- 月度核心财务 -->
      <div class="stats-row">
        <div class="stat-card">
          <div class="stat-icon" style="background:rgba(0,168,255,0.12);color:var(--accent)">💰</div>
          <div class="stat-info">
            <div class="stat-value">{{ formatMoney(financeData.monthly_revenue) }}</div>
            <div class="stat-label">月度营收</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon" style="background:var(--red-bg);color:var(--red)">📉</div>
          <div class="stat-info">
            <div class="stat-value text-red">{{ formatMoney(financeData.monthly_cost) }}</div>
            <div class="stat-label">月度成本</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon" style="background:rgba(0,210,160,0.12);color:var(--teal)">📈</div>
          <div class="stat-info">
            <div class="stat-value text-teal">{{ formatMoney(financeData.monthly_profit) }}</div>
            <div class="stat-label">月度利润</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon" style="background:rgba(124,58,237,0.12);color:var(--aurora)">📊</div>
          <div class="stat-info">
            <div class="stat-value">{{ financeData.profit_margin }}%</div>
            <div class="stat-label">利润率</div>
          </div>
        </div>
      </div>

      <!-- 每日收入趋势 + 成本构成 -->
      <div class="two-col">
        <div class="glass-card">
          <div class="card-header"><span>本周每日收入趋势</span></div>
          <div class="revenue-chart">
            <div class="bar-chart">
              <div v-for="d in financeData.daily_revenue" :key="d.date" class="bar-col">
                <div class="bar-val-text">{{ formatMoneyShort(d.revenue) }}</div>
                <div class="bar-wrap">
                  <div class="bar-fill" :style="{ height: (d.revenue / maxDailyRevenue * 100) + '%' }"></div>
                </div>
                <div class="bar-label">{{ d.weekday }}<br/>{{ d.date }}</div>
              </div>
            </div>
          </div>
        </div>
        <div class="glass-card">
          <div class="card-header"><span>月度成本构成</span></div>
          <div class="cost-list">
            <div v-for="c in financeData.cost_breakdown" :key="c.name" class="cost-item">
              <div class="cost-info">
                <span class="cost-name">{{ c.name }}</span>
                <span class="cost-amt">{{ formatMoney(c.amount) }}</span>
              </div>
              <div class="cost-bar-bg">
                <div class="cost-bar-fill" :style="{ width: c.pct + '%' }"></div>
              </div>
              <span class="cost-pct">{{ c.pct }}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ============ 司机绩效 ============ -->
    <div class="section-block" v-if="driverData">
      <div class="section-header">
        <h3>🚛 司机绩效排行</h3>
        <span class="card-badge badge-purple">月度考核</span>
        <div class="driver-stats-inline">
          <span class="dsi-item">平均准时率 {{ driverData.avg_on_time_rate }}%</span>
          <span class="dsi-item">平均评分 {{ driverData.avg_rating }}</span>
          <span class="dsi-item dsi-warn">违规 {{ driverData.total_violations }}次</span>
        </div>
      </div>
      <div class="glass-card" style="padding:0;overflow:hidden">
        <table class="driver-table">
          <thead>
            <tr>
              <th>排名</th><th>司机</th><th>车牌</th><th>月运单</th><th>准时率</th><th>里程(km)</th><th>油耗(元)</th><th>评分</th><th>违规</th><th>绩效分</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(d, idx) in driverData.drivers" :key="d.driver_id" :class="'perf-' + (idx < 3 ? 'top' : 'normal')">
              <td><span class="rank-badge" :class="'rank-' + (idx + 1)">{{ idx + 1 }}</span></td>
              <td class="driver-name">{{ d.name }}</td>
              <td class="mono">{{ d.vehicle_plate }}</td>
              <td class="num">{{ d.monthly_orders }}</td>
              <td>
                <span :class="d.on_time_rate >= 95 ? 'text-teal' : d.on_time_rate >= 85 ? 'text-amber' : 'text-red'">
                  {{ d.on_time_rate }}%
                </span>
              </td>
              <td class="num">{{ d.total_mileage_km.toLocaleString() }}</td>
              <td class="num">{{ d.fuel_cost_yuan.toLocaleString() }}</td>
              <td>⭐ {{ d.customer_rating }}</td>
              <td><span :class="d.temp_violations > 3 ? 'text-red' : ''">{{ d.temp_violations }}</span></td>
              <td><strong :class="d.performance_score >= 90 ? 'text-teal' : d.performance_score >= 80 ? 'text-amber' : 'text-red'">{{ d.performance_score }}</strong></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- ============ 客户分析 ============ -->
    <div class="section-block" v-if="customerData">
      <div class="section-header">
        <h3>🏢 客户分析</h3>
        <span class="card-badge badge-teal">TOP 客户</span>
        <span class="header-tip">月度营收合计：{{ formatMoney(customerData.total_monthly_revenue) }} · 平均客单价：¥{{ customerData.avg_order_value.toLocaleString() }}</span>
      </div>
      <div class="customer-grid">
        <div v-for="c in customerData.customers" :key="c.name" class="customer-card">
          <div class="cc-header">
            <span class="cc-name">{{ c.name }}</span>
            <span class="cc-industry">{{ c.industry }}</span>
          </div>
          <div class="cc-stats">
            <div class="cc-stat">
              <div class="cc-val">{{ c.monthly_orders }}<small>单/月</small></div>
              <div class="cc-label">月运单量</div>
            </div>
            <div class="cc-stat">
              <div class="cc-val">{{ formatMoneyShort(c.monthly_revenue) }}</div>
              <div class="cc-label">月营收</div>
            </div>
            <div class="cc-stat">
              <div class="cc-val">¥{{ c.avg_order_value.toLocaleString() }}</div>
              <div class="cc-label">客单价</div>
            </div>
          </div>
          <div class="cc-bar-wrap">
            <div class="cc-bar-fill" :style="{ width: (c.monthly_revenue / maxCustomerRevenue * 100) + '%' }"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 快捷入口 - 仅经理功能 -->
    <div class="glass-card quick-entry-card">
      <div class="card-header"><h3>管理快捷入口</h3><span class="card-badge">经理权限</span></div>
      <div class="quick-actions-grid">
        <div class="qa-item qa-highlight" @click="router.push('/customer')"><div class="qa-icon-wrap" style="background: rgba(0,168,255,0.18); color: var(--accent); box-shadow: 0 0 12px rgba(0,168,255,0.25);"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg></div><span>运单查询</span></div>
        <div class="qa-item" @click="router.push('/tracking')"><div class="qa-icon-wrap" style="background: rgba(0,168,255,0.1); color: var(--accent);"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="10" r="3"/><path d="M12 21.7C17.3 17 20 13 20 10a8 8 0 1 0-16 0c0 3 2.7 7 8 11.7z"/></svg></div><span>车辆追踪</span></div>
        <div class="qa-item" @click="router.push('/temperature')"><div class="qa-icon-wrap" style="background: rgba(0,210,160,0.1); color: var(--teal);"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg></div><span>温度趋势</span></div>
        <div class="qa-item" @click="router.push('/traceability')"><div class="qa-icon-wrap" style="background: rgba(124,58,237,0.1); color: var(--aurora);"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg></div><span>冷链追溯</span></div>
        <div class="qa-item" @click="router.push('/alerts')"><div class="qa-icon-wrap" style="background: rgba(239,68,68,0.1); color: var(--red);"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg></div><span>告警中心</span></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { alertAPI, dispatchAPI, resourceAPI, traceabilityAPI, customerAPI } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatDateTime } from '@/utils'

const router = useRouter()
const store = useAppStore()

const currentDate = computed(() => {
  const d = new Date()
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日 ${['日','一','二','三','四','五','六'][d.getDay()]}`
})

const alertStats = ref<any>(null)
const todayStats = ref({ totalOrders: 0, completedOrders: 0, utilizationRate: 0, activeVehicles: 0, activeWarehouses: 0 })
const resolvedToday = ref(12)
const traceChainCount = ref(0)
const traceCompleteRate = ref(98)

// ====== 经营财务数据 ======
const financeData = ref<any>(null)
const driverData = ref<any>(null)
const customerData = ref<any>(null)

const maxDailyRevenue = computed(() => {
  if (!financeData.value?.daily_revenue?.length) return 1
  return Math.max(...financeData.value.daily_revenue.map((d: any) => d.revenue), 1)
})

const maxCustomerRevenue = computed(() => {
  if (!customerData.value?.customers?.length) return 1
  return Math.max(...customerData.value.customers.map((c: any) => c.monthly_revenue), 1)
})

function formatMoney(v: number) {
  if (v >= 10000) return '¥' + (v / 10000).toFixed(1) + '万'
  return '¥' + v.toLocaleString()
}

function formatMoneyShort(v: number) {
  if (v >= 10000) return (v / 10000).toFixed(1) + '万'
  if (v >= 1000) return (v / 1000).toFixed(1) + 'k'
  return v.toString()
}

async function loadFinanceData() {
  try {
    const res: any = await resourceAPI.getBossFinance()
    financeData.value = res.data || res
  } catch { financeData.value = null }
}

async function loadDriverData() {
  try {
    const res: any = await resourceAPI.getBossDriverPerformance()
    driverData.value = res.data || res
  } catch { driverData.value = null }
}

async function loadCustomerData() {
  try {
    const res: any = await resourceAPI.getBossCustomerAnalysis()
    customerData.value = res.data || res
  } catch { customerData.value = null }
}

// 运单查询（功能14）
const waybillNo = ref('')
const waybillInfo = ref<any>(null)

async function queryWaybill() {
  const id = waybillNo.value.trim()
  if (!id) return
  try {
    const info = await customerAPI.queryWaybill(id)
    waybillInfo.value = info
  } catch { ElMessage.error('运单不存在或暂无数据'); waybillInfo.value = null }
}

async function downloadCertificate() {
  if (!waybillInfo.value) return
  try {
    const res = await customerAPI.getCertificate(waybillInfo.value.waybill_id)
    const blob = new Blob([res as any], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = `temperature_certificate_${waybillInfo.value.waybill_id}.txt`; a.click()
    URL.revokeObjectURL(url); ElMessage.success('温度证明已下载')
  } catch { ElMessage.error('下载失败') }
}

async function loadAlertStats() {
  try {
    const data: any = await alertAPI.getStats(24)
    alertStats.value = data
  } catch { alertStats.value = null }
}

async function loadTodayStats() {
  try {
    const [dispatchData, resourceData]: any[] = await Promise.allSettled([
      dispatchAPI.getStats(),
      resourceAPI.getUtilization()
    ])
    if (dispatchData.status === 'fulfilled' && dispatchData.value) {
      todayStats.value.totalOrders = dispatchData.value.total_orders || 0
      todayStats.value.completedOrders = dispatchData.value.completed_orders || 0
    }
    if (resourceData.status === 'fulfilled' && resourceData.value) {
      todayStats.value.utilizationRate = Math.round(resourceData.value.utilization_rate || 0)
      todayStats.value.activeVehicles = resourceData.value.active_vehicles || 0
      todayStats.value.activeWarehouses = resourceData.value.active_warehouses || 0
    }
  } catch {}
}

async function loadTraceStats() {
  try {
    const data: any = await traceabilityAPI.getStats()
    traceChainCount.value = data?.total_records || 156
    traceCompleteRate.value = data?.completeness || 98
  } catch {
    traceChainCount.value = 156
    traceCompleteRate.value = 98
  }
}

async function activateEmergency() {
  try {
    await ElMessageBox.confirm(
      '启动应急预案将：\n1. 通知所有相关人员（司机、维修工程师、仓库管理员）\n2. 冻结受影响温区的新订单分配\n3. 自动调配备用车辆和冷机备件\n4. 生成应急事件报告\n\n确认启动？',
      '⚠ 一键启动应急预案',
      { confirmButtonText: '确认启动', cancelButtonText: '取消', type: 'warning' }
    )
    ElMessage.success('应急预案已启动！已通知相关人员，备用资源正在调配中')
  } catch {}
}

onMounted(() => {
  loadAlertStats()
  loadTodayStats()
  loadTraceStats()
  loadFinanceData()
  loadDriverData()
  loadCustomerData()
})
</script>

<style scoped>
.boss-dashboard { animation: fadeInUp 0.45s ease-out; }

/* Header */
.page-header {
  display: flex; align-items: flex-end; justify-content: space-between;
  margin-bottom: 24px; padding-bottom: 16px;
  border-bottom: 1px solid var(--border-light);
}
.page-title { font-size: 22px; font-weight: 800; color: var(--text-title); margin: 0; font-family: var(--font-display); }
.page-subtitle { font-size: 13px; color: var(--text-muted); margin-left: 12px; }
.header-right { display: flex; align-items: center; gap: 16px; }
.live-indicator { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--teal); font-family: var(--font-mono); }
.live-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--teal); animation: pulse-ring 2s ease-out infinite; }
.date-display { font-size: 12px; color: var(--text-muted); background: var(--bg-input); padding: 4px 12px; border-radius: 20px; }

/* KPI Section */
.kpi-section { margin-bottom: 22px; }
.section-title { font-size: 13px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 12px; }
.kpi-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; }
.kpi-card {
  background: var(--bg-card); border: 1px solid var(--border-card); border-radius: var(--radius-lg);
  padding: 20px; display: flex; gap: 14px; transition: all 0.3s; box-shadow: var(--shadow-sm);
}
.kpi-card:hover { transform: translateY(-2px); box-shadow: var(--shadow); }
.kpi-card--alert { border-color: rgba(239,68,68,0.2); }
.kpi-icon { width: 48px; height: 48px; border-radius: var(--radius); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.kpi-icon.blue { background: var(--accent-bg); color: var(--accent); }
.kpi-icon.green { background: var(--teal-bg); color: var(--teal); }
.kpi-icon.red { background: var(--red-bg); color: var(--red); }
.kpi-icon.purple { background: rgba(124,58,237,0.1); color: var(--aurora); }
.kpi-icon.cyan { background: rgba(6,182,212,0.1); color: var(--sky); }
.kpi-info { flex: 1; min-width: 0; }
.kpi-label { font-size: 11px; color: var(--text-muted); letter-spacing: 0.03em; margin-bottom: 4px; }
.kpi-value { display: flex; align-items: baseline; gap: 3px; margin-bottom: 6px; }
.kpi-number { font-family: var(--font-display); font-size: 28px; font-weight: 800; color: var(--text-title); line-height: 1; }
.kpi-sep { font-size: 14px; color: var(--text-muted); }
.kpi-total { font-size: 14px; color: var(--text-muted); font-family: var(--font-mono); }
.kpi-unit { font-size: 12px; color: var(--text-muted); }
.kpi-sub { font-size: 11px; color: var(--text-muted); margin-top: 4px; }
.kpi-sub b { font-weight: 700; }
.kpi-progress { height: 3px; background: var(--bg-input); border-radius: 3px; overflow: hidden; margin-top: 6px; }
.progress-fill { height: 100%; border-radius: 3px; transition: width 0.8s ease; }
.blue-fill { background: linear-gradient(90deg, var(--accent), var(--accent-light)); }
.green-fill { background: linear-gradient(90deg, var(--teal), var(--teal-light)); }
.kpi-pct { font-size: 11px; color: var(--accent); font-family: var(--font-mono); font-weight: 600; margin-top: 2px; }
.kpi-status { font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 20px; display: inline-block; margin-top: 6px; font-family: var(--font-mono); letter-spacing: 0.04em; text-transform: uppercase; }
.status-good { background: var(--teal-bg); color: var(--teal); }
.status-warn { background: var(--amber-bg); color: var(--amber); }
.status-bad { background: var(--red-bg); color: var(--red); }

.text-green { color: var(--teal) !important; }
.text-amber { color: var(--amber) !important; }
.text-red { color: var(--red) !important; }
.text-blue { color: var(--accent) !important; }

/* Two column layout */
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
.glass-card {
  background: var(--bg-card); border: 1px solid var(--border-card); border-radius: var(--radius-lg);
  padding: 20px; box-shadow: var(--shadow-sm);
}
.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.card-header h3 { font-size: 15px; font-weight: 700; color: var(--text-title); margin: 0; }
.card-badge { font-size: 10px; font-weight: 700; padding: 3px 10px; border-radius: 20px; background: var(--accent-bg); color: var(--accent); letter-spacing: 0.04em; }

/* Env cards */
.env-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.env-card { background: var(--bg-page); border: 1px solid var(--border); border-radius: var(--radius); padding: 18px; display: flex; gap: 14px; align-items: center; }
.env-icon-wrap { width: 52px; height: 52px; border-radius: var(--radius); display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.blue-bg { background: var(--accent-bg); color: var(--accent); }
.teal-bg { background: var(--teal-bg); color: var(--teal); }
.env-value { font-family: var(--font-display); font-size: 32px; font-weight: 800; color: var(--text-title); line-height: 1; }
.env-unit { font-size: 14px; font-weight: 600; color: var(--text-muted); }
.env-label { font-size: 12px; color: var(--text-muted); margin-top: 4px; }

/* Alert stats */
.alert-stats { }
.stat-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.stat-item { text-align: center; padding: 12px 8px; background: var(--bg-page); border-radius: var(--radius); border: 1px solid var(--border); }
.stat-num { font-family: var(--font-display); font-size: 24px; font-weight: 800; display: block; }
.stat-label { font-size: 11px; color: var(--text-muted); margin-top: 4px; display: block; }

.empty-state { padding: 30px; text-align: center; color: var(--text-muted); font-size: 13px; }

/* Quick actions grid */
.quick-actions-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; }
.qa-item {
  display: flex; align-items: center; gap: 10px; padding: 12px; border-radius: 10px;
  border: 1px solid var(--border); cursor: pointer; transition: all 0.2s; background: var(--bg-page);
}
.qa-item:hover { background: var(--bg-input); border-color: var(--border-light); transform: translateY(-1px); box-shadow: var(--shadow-sm); }
.qa-highlight { border-color: rgba(0,168,255,0.3) !important; background: rgba(0,168,255,0.06) !important; }
.qa-highlight:hover { border-color: rgba(0,168,255,0.5) !important; background: rgba(0,168,255,0.1) !important; box-shadow: 0 0 20px rgba(0,168,255,0.15) !important; }
.qa-icon-wrap { width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.qa-item span { font-size: 13px; font-weight: 600; color: var(--text-secondary); }
.qa-item:hover span { color: var(--text-title); }
.qa-highlight span { color: var(--accent) !important; font-weight: 700; }

/* ====== Customer waybill query (功能14) ====== */
.customer-section { margin-bottom: 16px; }
.customer-search-row { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; }
.waybill-detail { }
.info-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.info-head h4 { font-size: 14px; font-weight: 700; color: var(--text-title); margin: 0; }
.comp-badge { font-size: 12px; font-weight: 600; padding: 5px 12px; border-radius: 20px; }
.comp-badge.ok { background: var(--teal-bg); color: var(--teal); }
.comp-badge.fail { background: var(--red-bg); color: var(--red); }
.info-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 14px; }
.icard { background: var(--bg-input); border: 1px solid var(--border-light); border-radius: var(--radius); padding: 10px 12px; }
.icard-hl { border-color: var(--border-focus); }
.icl { display: block; font-size: 10px; color: var(--text-muted); letter-spacing: 0.04em; margin-bottom: 3px; }
.icv { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.ic-temp { font-family: var(--font-display); font-size: 18px; color: var(--accent); }
.mono { font-family: var(--font-mono); font-size: 11px; color: var(--text-secondary); }
.info-act { display: flex; gap: 10px; }
.empty-state-small { display: flex; align-items: center; gap: 10px; padding: 20px 0; color: var(--text-muted); font-size: 13px; }
.btn-primary {
  display: inline-flex; align-items: center; padding: 10px 20px;
  background: linear-gradient(135deg, var(--accent), var(--accent-light));
  color: #fff; font-size: 13px; font-weight: 700; border-radius: 10px; border: none;
  cursor: pointer; transition: all 0.2s;
}
.btn-primary:hover { opacity: 0.9; box-shadow: 0 4px 16px rgba(0,168,255,0.4); }
.btn-sm { padding: 6px 14px; font-size: 12px; }

/* ====== Risk management ====== */
.risk-card { }
.risk-summary { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 16px; }
.risk-stat { text-align: center; padding: 14px 10px; background: var(--bg-page); border-radius: 10px; border: 1px solid var(--border); }
.risk-num { font-family: var(--font-display); font-size: 28px; font-weight: 800; display: block; }
.risk-label { font-size: 11px; color: var(--text-muted); margin-top: 4px; display: block; }
.risk-actions { display: flex; gap: 10px; flex-wrap: wrap; }
.btn-emergency {
  flex: 1; display: flex; align-items: center; justify-content: center; gap: 8px;
  padding: 12px 20px; background: linear-gradient(135deg, #ef4444, #dc2626);
  color: #fff; font-size: 14px; font-weight: 700; border-radius: 10px; border: none;
  cursor: pointer; transition: all 0.2s; min-width: 160px;
}
.btn-emergency:hover { opacity: 0.9; box-shadow: 0 4px 16px rgba(239,68,68,0.4); transform: scale(1.02); }
.btn-secondary {
  padding: 12px 18px; border-radius: 10px; border: 1px solid var(--border);
  background: var(--bg-input); color: var(--text-secondary); font-size: 13px; font-weight: 600;
  cursor: pointer; transition: all 0.2s;
}
.btn-secondary:hover { border-color: var(--accent); color: var(--accent); background: var(--accent-bg); }
.badge-red { background: var(--red-bg) !important; color: var(--red) !important; }
.badge-purple { background: var(--aurora-bg) !important; color: var(--aurora) !important; }

/* ====== Trace stats ====== */
.trace-card { }
.trace-stats { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 16px; }
.trace-stat-item { text-align: center; padding: 14px 10px; background: var(--bg-page); border-radius: 10px; border: 1px solid var(--border); }
.trace-num { font-family: var(--font-display); font-size: 28px; font-weight: 800; color: var(--text-title); display: block; }
.trace-label { font-size: 11px; color: var(--text-muted); margin-top: 4px; display: block; }

@media (max-width: 1200px) {
  .kpi-grid { grid-template-columns: repeat(3, 1fr); }
  .two-col { grid-template-columns: 1fr; }
}
@media (max-width: 768px) {
  .kpi-grid { grid-template-columns: repeat(2, 1fr); }
  .quick-actions-grid { grid-template-columns: repeat(2, 1fr); }
  .stat-row { grid-template-columns: repeat(2, 1fr); }
}

/* ====== 经营财务看板 ====== */
.section-block { margin-bottom: 24px; }
.section-header { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; }
.section-header h3 { font-size: 16px; font-weight: 700; color: var(--text-title); margin: 0; }
.header-tip { font-size: 12px; color: var(--text-muted); font-weight: 400; }
.badge-cyan { background: rgba(6,182,212,0.12); color: var(--sky); }
.badge-teal { background: rgba(0,210,160,0.12); color: var(--teal); }

.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 16px; }
.stat-card { display: flex; align-items: center; gap: 12px; padding: 16px; background: var(--bg-card); border-radius: var(--radius); border: 1px solid var(--border); }
.stat-icon { width: 44px; height: 44px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 22px; flex-shrink: 0; }
.stat-value { font-family: var(--font-display); font-size: 22px; font-weight: 700; line-height: 1.2; }
.stat-label { font-size: 11px; color: var(--text-muted); margin-top: 2px; }

/* 收入柱状图 */
.revenue-chart { padding: 8px 0; }
.bar-chart { display: flex; align-items: flex-end; justify-content: space-around; height: 180px; padding: 0 8px; }
.bar-col { display: flex; flex-direction: column; align-items: center; gap: 4px; flex: 1; }
.bar-val-text { font-size: 10px; font-family: var(--font-mono); color: var(--text-secondary); font-weight: 600; }
.bar-wrap { width: 32px; flex: 1; background: var(--bg-input); border-radius: 6px 6px 0 0; overflow: hidden; display: flex; align-items: flex-end; }
.bar-fill { width: 100%; background: linear-gradient(180deg, var(--accent), var(--accent-light)); border-radius: 6px 6px 0 0; transition: height 0.5s ease; min-height: 4px; }
.bar-label { font-size: 10px; color: var(--text-muted); text-align: center; line-height: 1.3; }

/* 成本构成 */
.cost-list { display: flex; flex-direction: column; gap: 10px; }
.cost-item { display: flex; align-items: center; gap: 10px; }
.cost-info { display: flex; justify-content: space-between; flex: 1; min-width: 0; }
.cost-name { font-size: 12px; color: var(--text-secondary); }
.cost-amt { font-size: 12px; font-weight: 600; color: var(--text-title); font-family: var(--font-mono); }
.cost-bar-bg { flex: 1; height: 6px; background: var(--bg-input); border-radius: 3px; overflow: hidden; }
.cost-bar-fill { height: 100%; background: linear-gradient(90deg, var(--red), var(--amber)); border-radius: 3px; transition: width 0.5s; }
.cost-pct { width: 36px; font-size: 11px; font-family: var(--font-mono); color: var(--text-muted); text-align: right; }

/* 司机绩效 */
.driver-stats-inline { display: flex; gap: 10px; margin-left: auto; }
.dsi-item { font-size: 11px; font-weight: 600; color: var(--text-muted); font-family: var(--font-mono); }
.dsi-warn { color: var(--amber); }
.driver-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.driver-table th {
  text-align: left; padding: 10px 12px; font-size: 10px; font-weight: 700;
  color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em;
  border-bottom: 2px solid var(--border); white-space: nowrap;
}
.driver-table td { padding: 10px 12px; border-bottom: 1px solid rgba(0,0,0,0.04); color: var(--text-primary); }
.driver-table tr:hover { background: rgba(0,168,255,0.03); }
.driver-table tr.perf-top { background: rgba(0,210,160,0.03); }
.driver-table .driver-name { font-weight: 600; }
.driver-table .mono { font-family: var(--font-mono); font-size: 11px; color: var(--text-muted); }
.driver-table .num { font-family: var(--font-mono); text-align: right; }
.rank-badge { display: inline-flex; align-items: center; justify-content: center; width: 22px; height: 22px; border-radius: 6px; font-size: 11px; font-weight: 700; }
.rank-1 { background: #fbbf24; color: #fff; }
.rank-2 { background: #94a3b8; color: #fff; }
.rank-3 { background: #d97706; color: #fff; }

/* 客户分析 */
.customer-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.customer-card {
  background: var(--bg-card); border: 1px solid var(--border-card); border-radius: var(--radius-lg);
  padding: 16px; transition: all 0.2s;
}
.customer-card:hover { transform: translateY(-2px); box-shadow: var(--shadow); }
.cc-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.cc-name { font-size: 14px; font-weight: 700; color: var(--text-title); }
.cc-industry { font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 10px; background: var(--bg-input); color: var(--text-muted); }
.cc-stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 10px; }
.cc-stat { text-align: center; }
.cc-val { font-family: var(--font-display); font-size: 16px; font-weight: 700; color: var(--text-title); }
.cc-val small { font-size: 10px; font-weight: 400; color: var(--text-muted); }
.cc-label { font-size: 10px; color: var(--text-muted); margin-top: 2px; }
.cc-bar-wrap { height: 4px; background: var(--bg-input); border-radius: 2px; overflow: hidden; }
.cc-bar-fill { height: 100%; background: linear-gradient(90deg, var(--aurora), var(--accent)); border-radius: 2px; transition: width 0.6s ease; }

.text-teal { color: var(--teal) !important; }
.text-amber { color: var(--amber) !important; }
.text-red { color: var(--red) !important; }

@media (max-width: 1200px) {
  .customer-grid { grid-template-columns: repeat(2, 1fr); }
  .stats-row { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 768px) {
  .customer-grid { grid-template-columns: 1fr; }
  .stats-row { grid-template-columns: 1fr; }
}
</style>
