import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
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
  // 🔴 P0: 司机专属告警
  getDriverAlerts: (params?: any) => api.get('/alerts/driver', { params }),
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
  // 运单管理
  getWaybills: () => api.get('/traceability/waybills'),
  createWaybill: (data: any) => api.post('/traceability/waybill', data),
  getWaybillDetail: (waybillId: string) => api.get(`/traceability/waybill/${waybillId}`),
}

export const customerAPI = {
  queryWaybill: (waybillId: string) => api.get(`/customer/query/${waybillId}`),
  getTemperatureCurve: (waybillId: string, params?: any) =>
    api.get(`/customer/temperature-curve/${waybillId}`, { params }),
  getCertificate: (waybillId: string) =>
    api.get(`/customer/certificate/${waybillId}`),
  getMyOrders: () => api.get('/customer/my-orders'),
  scanQuery: (code: string) => api.get('/customer/scan', { params: { code } }),
  // 顾客下单
  createOrder: (data: any) => api.post('/customer/create-order', data),
  getMyOrdersNew: () => api.get('/customer/my-orders-new'),
  // 司机接单
  getAvailableOrders: () => api.get('/customer/available-orders'),
  acceptOrder: (orderId: string) => api.post(`/customer/accept-order/${orderId}`),
  acceptOrderWithPhoto: (orderId: string, photoUrl: string) =>
    api.post(`/customer/accept-order-with-photo/${orderId}`, null, { params: { photo_url: photoUrl } }),
  getDriverOrders: () => api.get('/customer/driver-orders'),
  updateOrderStatus: (orderId: string, status: string, photoUrl?: string) =>
    api.post(`/customer/update-order-status/${orderId}`, null, { params: { status, photo_url: photoUrl || '' } }),
  // 客户签收确认
  confirmReceive: (orderId: string) => api.post(`/customer/confirm-receive/${orderId}`),
  // 删除订单
  deleteOrder: (orderId: string) => api.delete(`/customer/order/${orderId}`),
  // P0: 订单实时追踪（温度+车辆位置+告警）
  getOrderTracking: (orderId: string) => api.get(`/customer/order-tracking/${orderId}`),
  // P0: 品质反馈
  submitQualityFeedback: (orderId: string, data: any) => api.post(`/customer/quality-feedback/${orderId}`, data),
  getQualityFeedback: (orderId: string) => api.get(`/customer/quality-feedback/${orderId}`),
  // 管理员/仓库经理：统一订单管理
  getAllOrders: () => api.get('/customer/all-orders'),
  adminAssignDriver: (orderId: string, data: any) => api.post(`/customer/admin-assign-driver/${orderId}`, data),
  // 🔴 P0: 订单-运单关联查询
  getOrderWaybill: (orderId: string) => api.get(`/customer/order-waybill/${orderId}`),
  // 仓库订单审核
  getPendingReviewOrders: () => api.get('/customer/pending-review-orders'),
  getAllReviewOrders: (status?: string) => api.get('/customer/all-review-orders', { params: { status } }),
  reviewOrder: (orderId: string, action: string, notes?: string) =>
    api.post(`/customer/review-order/${orderId}`, { action, notes: notes || '' }),
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
  assessWithImage: (formData: FormData) =>
    api.post('/quality/assess/image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
    }),
  getBatches: (category?: string, grade?: string) =>
    api.get('/quality/batches', { params: { category, grade } }),
  getBatchDetail: (batchId: string) => api.get(`/quality/batch/${batchId}`),
  getStats: () => api.get('/quality/stats'),
  getProducts: () => api.get('/quality/products'),
  getDemo: (productKey: string) => api.get('/quality/demo', { params: { product_key: productKey } }),
}

export const uploadAPI = {
  uploadTempRecord: (formData: FormData) =>
    api.post('/upload/temperature-record', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30000,
    }),
  getTempRecords: (deviceId?: string, waybillId?: string, limit?: number) =>
    api.get('/upload/temperature-records', { params: { device_id: deviceId, waybill_id: waybillId, limit } }),
  // 审核相关
  getPendingReviews: (reviewStatus?: string, limit?: number) =>
    api.get('/upload/pending-reviews', { params: { review_status: reviewStatus || 'pending_review', limit } }),
  reviewPhoto: (recordId: string, action: string, notes?: string) =>
    api.post(`/upload/review/${recordId}`, { action, notes: notes || '' }),
  getReviewStats: () => api.get('/upload/review-stats'),
  // 司机查询自己照片的审核状态
  getDriverPhotos: (orderId?: string) =>
    api.get('/upload/driver-photos', { params: { order_id: orderId || '' } }),
  // 🔴 P0: 批量审核
  batchReview: (recordIds: string[], action: string, notes?: string) =>
    api.post('/upload/review/batch', { record_ids: recordIds, action, notes: notes || '' }),
}

export const resourceAPI = {
  getWarehouses: () => api.get('/resources/warehouses'),
  getWarehouseDetail: (id: string) => api.get(`/resources/warehouses/${id}`),
  getVehicles: (status?: string) => api.get('/resources/vehicles', { params: { status } }),
  getColdPlates: () => api.get('/resources/cold-plates'),
  getUtilization: () => api.get('/resources/utilization'),
  allocate: (resourceType: string, warehouseId?: string) =>
    api.post('/resources/allocate', null, { params: { resource_type: resourceType, warehouse_id: warehouseId } }),
  // 仓库库存管理
  getWarehouseInventory: (params?: any) => api.get('/resources/warehouse-inventory', { params }),
  warehouseInbound: (data: any) => api.post('/resources/warehouse-inbound', data),
  warehouseOutbound: (inventoryId: string, quantityKg: number, notes?: string) =>
    api.post('/resources/warehouse-outbound', null, { params: { inventory_id: inventoryId, quantity_kg: quantityKg, notes: notes || '' } }),
  getWarehouseInventorySummary: () => api.get('/resources/warehouse-inventory-summary'),
  // 老板经营数据
  getBossFinance: () => api.get('/resources/boss-finance'),
  getBossDriverPerformance: () => api.get('/resources/boss-driver-performance'),
  getBossCustomerAnalysis: () => api.get('/resources/boss-customer-analysis'),
}

export default api
