import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
})

// 请求拦截器
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.detail || '请求失败'
    ElMessage.error(message)
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.hash = '#/login'
    }
    return Promise.reject(error)
  }
)

// API 方法
export const authAPI = {
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }),
  me: () => api.get('/auth/me'),
}

export const dashboardAPI = {
  getKPI: () => api.get('/dashboard/kpi'),
  getDevices: () => api.get('/dashboard/devices'),
  getOverview: () => api.get('/dashboard/overview'),
  getAlertsSummary: () => api.get('/dashboard/alerts/summary'),
}

export const sensorAPI = {
  getLatest: (deviceId: string) => api.get(`/sensors/latest/${deviceId}`),
  getHistory: (deviceId: string, start: string, end: string, limit?: number) =>
    api.get(`/sensors/history/${deviceId}`, { params: { start, end, limit } }),
}

export const temperatureAPI = {
  getCurrent: (deviceId: string) => api.get(`/temperature/current/${deviceId}`),
  getTrend: (deviceId: string, horizon?: number) =>
    api.get(`/temperature/trend/${deviceId}`, { params: { horizon } }),
  getHistory: (deviceId: string, minutes?: number) =>
    api.get(`/temperature/history/${deviceId}`, { params: { minutes } }),
  checkAnomaly: (deviceId: string) => api.get(`/temperature/anomaly/${deviceId}`),
}

export const alertAPI = {
  getAlerts: (params?: any) => api.get('/alerts', { params }),
  getActiveAlerts: () => api.get('/alerts/active'),
  acknowledge: (alertId: string, action?: string, notes?: string) =>
    api.post(`/alerts/acknowledge/${alertId}`, null, { params: { action, notes } }),
  dispatch: (alertId: string, channels?: string[]) =>
    api.post(`/alerts/dispatch/${alertId}`, { notify_channels: channels || ['sms', 'email'] }),
  getNotifications: (params?: any) => api.get('/alerts/notifications', { params }),
  getStats: (hours?: number) => api.get('/alerts/stats', { params: { hours } }),
  getRules: () => api.get('/alerts/rules'),
  createRule: (rule: any) => api.post('/alerts/rules', rule),
  deleteRule: (ruleType: string) => api.delete(`/alerts/rules/${ruleType}`),
}

export const geofenceAPI = {
  getList: (type?: string) => api.get('/geofence', { params: { type } }),
  getDetail: (id: string) => api.get(`/geofence/${id}`),
  create: (data: any) => api.post('/geofence', null, { params: data }),
  update: (id: string, data: any) => api.put(`/geofence/${id}`, null, { params: data }),
  delete: (id: string) => api.delete(`/geofence/${id}`),
  getEvents: (params?: any) => api.get('/geofence/events', { params }),
  getDeviceStatus: (deviceId: string) => api.get(`/geofence/device/${deviceId}/status`),
}

export const traceabilityAPI = {
  getRecords: (waybillId: string) => api.get(`/traceability/records/${waybillId}`),
  getReport: (waybillId: string, format?: string) =>
    api.get(`/traceability/report/${waybillId}`, { params: { format } }),
  search: (keyword: string, params?: any) =>
    api.get('/traceability/search', { params: { keyword, ...params } }),
  getStats: () => api.get('/traceability/stats'),
  verifyBlockchain: (waybillId: string) => api.get(`/traceability/blockchain/verify/${waybillId}`),
  getLedger: (limit?: number) => api.get('/traceability/blockchain/ledger', { params: { limit } }),
}

export const customerAPI = {
  queryWaybill: (waybillId: string) => api.get(`/customer/query/${waybillId}`),
  getTemperatureCurve: (waybillId: string, params?: any) =>
    api.get(`/customer/temperature-curve/${waybillId}`, { params }),
  getCertificate: (waybillId: string) =>
    api.get(`/customer/certificate/${waybillId}`),
  getMyOrders: () => api.get('/customer/my-orders'),
  scanQuery: (code: string) => api.get('/customer/scan', { params: { code } }),
}

export const vehicleAPI = {
  getList: (params?: any) => api.get('/vehicles/list', { params }),
  getDetail: (deviceId: string) => api.get(`/vehicles/${deviceId}/detail`),
  getTrajectory: (deviceId: string, hours?: number) =>
    api.get(`/vehicles/${deviceId}/trajectory`, { params: { hours } }),
  getAllPositions: () => api.get('/vehicles/all/positions'),
}

export const maintenanceAPI = {
  predictAll: (status?: string) => api.get('/maintenance/predict', { params: { status } }),
  predictDevice: (deviceId: string) => api.get(`/maintenance/predict/${deviceId}`),
  getStatus: () => api.get('/maintenance/status'),
  getHistory: (deviceId: string) => api.get(`/maintenance/history/${deviceId}`),
}

export const routeAPI = {
  plan: (data: any) => api.post('/routes/plan', data),
  quickPlan: (origin: string, destination: string, cargoType?: string, priority?: string) =>
    api.get('/routes/plan', { params: { origin, destination, cargo_type: cargoType, priority } }),
  getActive: () => api.get('/routes/active'),
  getCities: () => api.get('/routes/cities'),
  getCargoTypes: () => api.get('/routes/cargo-types'),
}

export const dispatchAPI = {
  getOrders: (tempZone?: string) => api.get('/dispatch/orders', { params: { temp_zone: tempZone } }),
  getVehicles: () => api.get('/dispatch/vehicles'),
  autoAssign: () => api.post('/dispatch/assign'),
  getPlan: () => api.get('/dispatch/plan'),
  getStats: () => api.get('/dispatch/stats'),
}

export const qualityAPI = {
  assess: (productType: string, storageDays: number) =>
    api.post('/quality/assess', { product_type: productType, storage_days: storageDays }),
  getBatches: (category?: string, grade?: string) =>
    api.get('/quality/batches', { params: { category, grade } }),
  getBatchDetail: (batchId: string) => api.get(`/quality/batch/${batchId}`),
  getStats: () => api.get('/quality/stats'),
  getProducts: () => api.get('/quality/products'),
}

export const uploadAPI = {
  uploadTempRecord: (formData: FormData) =>
    api.post('/upload/temperature-record', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30000,
    }),
  getTempRecords: (deviceId?: string, waybillId?: string, limit?: number) =>
    api.get('/upload/temperature-records', { params: { device_id: deviceId, waybill_id: waybillId, limit } }),
}

export const resourceAPI = {
  getWarehouses: () => api.get('/resources/warehouses'),
  getWarehouseDetail: (id: string) => api.get(`/resources/warehouses/${id}`),
  getVehicles: (status?: string) => api.get('/resources/vehicles', { params: { status } }),
  getColdPlates: () => api.get('/resources/cold-plates'),
  getUtilization: () => api.get('/resources/utilization'),
  allocate: (resourceType: string, warehouseId?: string) =>
    api.post('/resources/allocate', null, { params: { resource_type: resourceType, warehouse_id: warehouseId } }),
}

export default api
