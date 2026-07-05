import { defineStore } from 'pinia'
import { ref } from 'vue'
import { dashboardAPI, alertAPI, customerAPI, uploadAPI } from '@/api'

export const useAppStore = defineStore('app', () => {
  // 用户（持久化到 localStorage）
  const token = ref(localStorage.getItem('token') || '')
  const username = ref(localStorage.getItem('username') || '')
  const userRole = ref(localStorage.getItem('userRole') || '')

  // KPI 数据
  const kpi = ref({
    total_devices: 110,
    online_devices: 0,
    online_rate: 0,
    temperature_compliance_rate: 0,
    active_alerts: 0,
    critical_alerts: 0,
    avg_temperature: 0,
    avg_humidity: 0,
    // 扩展字段
    warehouse_utilization: 0,
    fleet_online_rate: 0,
    total_waybills: 0,
    quality_batches: 0,
    total_online_devices: 0,
    device_compliant_count: 0,
    device_anomaly_count: 0,
    alerts_by_severity: { critical: 0, severe: 0, normal: 0 },
    zone_stats: { freeze: 0, refrigerated: 0, ambient: 0 },
    warehouse_distribution: [] as any[],
    timestamp: '',
    data_source: '',
  })

  // 设备列表
  const devices = ref<any[]>([])
  const selectedDevice = ref('')

  // 告警
  const activeAlerts = ref<any[]>([])

  // ====== 订单流转数据（Admin/Warehouse 与 司机/客户 联动） ======
  const orderFlow = ref({
    pending: 0,      // 待接单
    accepted: 0,     // 已接单
    in_transit: 0,   // 配送中
    delivered: 0,    // 已送达
    completed: 0,    // 已完成
    total: 0,
    all_orders: [] as any[],
  })

  // ====== 照片审核摘要（仓库审核与司机拍照联动） ======
  const photoReview = ref({
    pending_count: 0,
    approved_today: 0,
    rejected_today: 0,
    pending_items: [] as any[],
  })

  // ====== 业务事件时间线（全局） ======
  const recentEvents = ref<any[]>([])

  let refreshTimer: number | null = null

  async function fetchKPI() {
    try {
      const data: any = await dashboardAPI.getKPI()
      kpi.value = data
    } catch (e: any) {
      console.error('[Store] fetchKPI 失败:', e?.message || e)
    }
  }

  async function fetchDevices() {
    try {
      const data: any = await dashboardAPI.getDevices()
      devices.value = data.devices || []
    } catch (e: any) {
      console.error('[Store] fetchDevices 失败:', e?.message || e)
    }
  }

  async function fetchAlerts() {
    try {
      const data: any = await alertAPI.getActiveAlerts()
      activeAlerts.value = data.devices || []
    } catch (e: any) {
      console.error('[Store] fetchAlerts 失败:', e?.message || e)
    }
  }

  async function fetchOrderFlow() {
    try {
      const res: any = await customerAPI.getAllOrders()
      const orders = res?.orders || []
      const stats = { pending: 0, accepted: 0, in_transit: 0, delivered: 0, completed: 0 }
      for (const o of orders) {
        const s = o.status
        if (stats.hasOwnProperty(s)) (stats as any)[s]++
      }
      orderFlow.value = {
        ...stats,
        total: orders.length,
        all_orders: orders,
      }
      buildEventTimeline(orders)
    } catch (e: any) {
      console.error('[Store] fetchOrderFlow 失败:', e?.message || e)
    }
  }

  async function fetchPhotoReviewSummary() {
    try {
      const res: any = await uploadAPI.getPendingReviews('pending_review', 20)
      const items = res?.records || res?.data || []
      photoReview.value.pending_count = items.length
      photoReview.value.pending_items = items.slice(0, 5)
    } catch { /* ignore */ }
  }

  function buildEventTimeline(orders: any[]) {
    const events: any[] = []
    const sorted = [...orders].sort((a, b) =>
      (b.updated_at || b.created_at || '').localeCompare(a.updated_at || a.created_at || '')
    )
    for (const o of sorted.slice(0, 10)) {
      const statusLabels: Record<string, string> = {
        pending: '客户下单', accepted: '司机接单', in_transit: '开始配送',
        delivered: '司机送达', completed: '客户签收',
      }
      const iconMap: Record<string, string> = {
        pending: '📝', accepted: '📸', in_transit: '🚀', delivered: '📦', completed: '✅',
      }
      events.push({
        id: o.order_id,
        time: o.updated_at || o.created_at,
        status: o.status,
        label: statusLabels[o.status] || o.status,
        icon: iconMap[o.status] || '📋',
        desc: `${o.origin || '?'} → ${o.destination || '?'} · ${o.cargo_name || '冷链'}`,
        driver: o.driver_name || o.driver_id || '—',
        customer: o.customer_name || '—',
      })
    }
    recentEvents.value = events
  }

  function startAutoRefresh(interval = 5000) {
    stopAutoRefresh()
    fetchKPI()
    fetchDevices()
    fetchAlerts()
    fetchOrderFlow()
    fetchPhotoReviewSummary()
    refreshTimer = window.setInterval(() => {
      fetchKPI()
      fetchDevices()
      fetchAlerts()
      fetchOrderFlow()
      fetchPhotoReviewSummary()
    }, interval)
  }

  function stopAutoRefresh() {
    if (refreshTimer) {
      clearInterval(refreshTimer)
      refreshTimer = null
    }
  }

  function setToken(t: string) {
    token.value = t
    localStorage.setItem('token', t)
  }

  function setUserInfo(name: string, role: string) {
    username.value = name
    userRole.value = role
    localStorage.setItem('username', name)
    localStorage.setItem('userRole', role)
  }

  function logout() {
    stopAutoRefresh()
    token.value = ''
    username.value = ''
    userRole.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('userRole')
  }

  return {
    token, username, userRole,
    kpi, devices, selectedDevice, activeAlerts,
    orderFlow, photoReview, recentEvents,
    fetchKPI, fetchDevices, fetchAlerts,
    fetchOrderFlow, fetchPhotoReviewSummary,
    startAutoRefresh, stopAutoRefresh,
    setToken, setUserInfo, logout,
  }
})
