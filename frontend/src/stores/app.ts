import { defineStore } from 'pinia'
import { ref } from 'vue'
import { dashboardAPI, alertAPI } from '@/api'

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
  })

  // 设备列表
  const devices = ref<any[]>([])
  const selectedDevice = ref('')

  // 告警
  const activeAlerts = ref<any[]>([])

  let refreshTimer: number | null = null

  async function fetchKPI() {
    try {
      const data: any = await dashboardAPI.getKPI()
      kpi.value = data
    } catch {}
  }

  async function fetchDevices() {
    try {
      const data: any = await dashboardAPI.getDevices()
      devices.value = data.devices || []
    } catch {}
  }

  async function fetchAlerts() {
    try {
      const data: any = await alertAPI.getActiveAlerts()
      activeAlerts.value = data.devices || []
    } catch {}
  }

  function startAutoRefresh(interval = 10000) {
    stopAutoRefresh()
    fetchKPI()
    fetchDevices()
    fetchAlerts()
    refreshTimer = window.setInterval(() => {
      fetchKPI()
      fetchDevices()
      fetchAlerts()
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
    token.value = ''
    username.value = ''
    userRole.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('userRole')
    localStorage.removeItem('user')
  }

  return {
    token, username, userRole,
    kpi, devices, selectedDevice, activeAlerts,
    fetchKPI, fetchDevices, fetchAlerts,
    startAutoRefresh, stopAutoRefresh,
    setToken, setUserInfo, logout,
  }
})
