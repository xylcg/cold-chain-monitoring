<template>
  <div class="mobile-app">
    <div class="mobile-wrap">
      <!-- 页面头部 -->
      <div class="mb-header">
        <div class="mb-header-title">司机工作台</div>
        <div class="mb-header-sub">接单 · 拍照 · 送达</div>
      </div>

      <!-- ===== 订单 Tab ===== -->
      <div class="mb-page" v-show="activeTab === 'orders'">
        <div class="mb-subtab">
          <div class="mst-item" :class="{ active: orderSubTab === 'my' }" @click="orderSubTab='my';loadDriverOrders()">
            📦 我的任务 <span class="mst-count" v-if="driverOrders.length">{{ driverOrders.length }}</span>
          </div>
          <div class="mst-item" :class="{ active: orderSubTab === 'available' }" @click="orderSubTab='available';loadAvailableOrders()">
            📋 可接订单 <span class="mst-count" v-if="availableOrders.length">{{ availableOrders.length }}</span>
          </div>
        </div>

        <!-- 我的任务 -->
        <div v-if="orderSubTab === 'my'">
          <div v-if="driverOrders.length > 0" class="mb-list">
            <div v-for="o in driverOrders" :key="o.order_id" class="mb-card-item" :class="'card-'+o.status" @click="detailOrder=o">
              <div class="mci-top"><span class="mci-id">{{ o.order_id }}</span><span class="mci-status" :class="o.status">{{ statusMap[o.status]||o.status }}</span></div>
              <div class="mci-route"><span class="mci-dot"></span><span class="mci-city">{{ o.origin }}</span><span class="mci-arrow">→</span><span class="mci-dot end"></span><span class="mci-city">{{ o.destination }}</span></div>
              <div class="mci-meta"><span>{{ o.cargo_name }} · {{ o.quantity }}{{ o.unit }}</span><span class="mci-zone" :class="zoneClass(o.zone_name)">{{ o.zone_name }}</span></div>
              <!-- 拍照预览 -->
              <div class="mci-photos" v-if="o.accept_photo_url || o.deliver_photo_url">
                <img v-if="o.accept_photo_url" :src="o.accept_photo_url" class="mci-thumb" title="接单拍照" />
                <img v-if="o.deliver_photo_url" :src="o.deliver_photo_url" class="mci-thumb" title="送达拍照" />
              </div>
              <!-- 温度追踪条（配送中的订单） -->
              <div v-if="trackingData[o.order_id] && ['accepted','in_transit','delivered'].includes(o.status)" class="mci-temp-bar">
                <div class="mtb-row">
                  <span class="mtb-label">🌡 实时温度</span>
                  <span class="mtb-temp" :class="{ warning: !trackingData[o.order_id].temperature?.is_compliant }">
                    {{ trackingData[o.order_id].temperature?.current?.toFixed(1) }}℃
                  </span>
                  <span class="mtb-loc">📍 {{ trackingData[o.order_id].vehicle?.current_city || '—' }}</span>
                </div>
                <div class="mtb-status" :class="{ warn: !trackingData[o.order_id].temperature?.is_compliant }">
                  {{ trackingData[o.order_id].temperature?.is_compliant ? '✅ 温度正常' : '⚠️ 温度异常！' }}
                </div>
              </div>
              <!-- 操作按钮 -->
              <div class="mci-actions" v-if="o.status==='accepted'">
                <button class="mcia-btn primary" @click.stop="showPhotoUpload(o,'accept')">📸 出发拍照</button>
                <button class="mcia-btn primary" @click.stop="startTransit(o)">🚀 开始配送</button>
                <button class="mcia-btn track" @click.stop="openTracking(o)" v-if="trackingData[o.order_id]">🌡 追踪</button>
              </div>
              <div class="mci-actions" v-if="o.status==='in_transit'">
                <button class="mcia-btn success" @click.stop="showPhotoUpload(o,'deliver')">📸 送达拍照</button>
                <button class="mcia-btn track" @click.stop="openTracking(o)" v-if="trackingData[o.order_id]">🌡 追踪</button>
              </div>
              <div class="mci-actions" v-if="o.status==='delivered'">
                <span class="mci-waiting">⏳ 等待客户确认签收...</span>
                <button class="mcia-btn track" @click.stop="openTracking(o)" v-if="trackingData[o.order_id]">🌡 追踪</button>
              </div>
              <div class="mci-actions" v-if="o.status==='completed'">
                <span class="mci-done">✅ 已完成</span>
                <button class="mcia-btn" @click.stop="deleteDriverOrder(o)">🗑 删除</button>
              </div>
            </div>
          </div>
          <div class="mb-empty" v-else><div class="mbe-icon">📦</div><p>暂无接单任务</p><span>切换到「可接订单」接取新任务</span></div>
        </div>

        <!-- 可接订单 -->
        <div v-if="orderSubTab === 'available'">
          <div v-if="availableOrders.length > 0" class="mb-list">
            <div v-for="o in availableOrders" :key="o.order_id" class="mb-card-item card-pending" @click="detailOrder=o">
              <div class="mci-top"><span class="mci-id">{{ o.order_id }}</span><span class="mci-status pending">待接单</span></div>
              <div class="mci-route"><span class="mci-dot"></span><span class="mci-city">{{ o.origin }}</span><span class="mci-arrow">→</span><span class="mci-dot end"></span><span class="mci-city">{{ o.destination }}</span></div>
              <div class="mci-meta"><span>{{ o.cargo_name }} · {{ o.quantity }}{{ o.unit }}</span><span class="mci-zone" :class="zoneClass(o.zone_name)">{{ o.zone_name }}</span></div>
              <div class="mci-bottom"><span class="mci-price">¥{{ o.price?.toLocaleString() }}</span><span class="mci-time">{{ fmtTime(o.created_at) }}</span></div>
              <div class="mci-actions">
                <button class="mcia-btn primary" @click.stop="acceptAndPhoto(o)">📸 拍照接单</button>
              </div>
            </div>
          </div>
          <div class="mb-empty" v-else><div class="mbe-icon">📋</div><p>暂无可接订单</p><span>等待客户创建新订单</span></div>
        </div>
      </div>

      <!-- ===== 我的 Tab ===== -->
      <div class="mb-page" v-show="activeTab === 'me'">
        <div class="mb-profile">
          <div class="mb-avatar">{{ (driverName||'D')[0] }}</div>
          <div><div class="mb-driver-name">{{ driverName||'司机' }}</div><div class="mb-driver-id">ID: {{ driverId }}</div></div>
        </div>
        <div class="mb-stats">
          <div class="mbs-item"><span class="mbs-num">{{ driverOrders.length }}</span><span class="mbs-label">全部</span></div>
          <div class="mbs-item"><span class="mbs-num active">{{ driverOrders.filter(o=>['accepted','in_transit','delivered'].includes(o.status)).length }}</span><span class="mbs-label">进行中</span></div>
          <div class="mbs-item"><span class="mbs-num done">{{ driverOrders.filter(o=>o.status==='completed').length }}</span><span class="mbs-label">已完成</span></div>
        </div>
        <button class="mb-logout-btn" @click="handleLogout">退出登录</button>
      </div>

      <!-- ===== 订单详情弹窗 ===== -->
      <div class="mb-overlay" v-if="detailOrder" @click.self="detailOrder=null">
        <div class="mb-detail">
          <div class="mbd-header"><span class="mbd-id">{{ detailOrder.order_id }}</span><span class="mbd-close" @click="detailOrder=null">✕</span></div>
          <div class="mbd-body">
            <div class="mbd-row"><span>货物</span><strong>{{ detailOrder.cargo_name }} · {{ detailOrder.cargo_category }}</strong></div>
            <div class="mbd-row"><span>路线</span><strong>{{ detailOrder.origin }} → {{ detailOrder.destination }}</strong></div>
            <div class="mbd-row"><span>数量</span><strong>{{ detailOrder.quantity }}{{ detailOrder.unit }}</strong></div>
            <div class="mbd-row"><span>温区</span><strong>{{ detailOrder.zone_name }} ({{ detailOrder.temperature_requirement }})</strong></div>
            <div class="mbd-row"><span>收件人</span><strong>{{ detailOrder.receiver||'—' }} {{ detailOrder.receiver_phone }}</strong></div>
            <div class="mbd-row"><span>客户</span><strong>{{ detailOrder.customer_name }}</strong></div>
            <div class="mbd-row"><span>运费</span><strong class="text-red">¥{{ detailOrder.price?.toLocaleString() }}</strong></div>
            <div class="mbd-row"><span>时间</span><strong>{{ fmtTime(detailOrder.created_at) }}</strong></div>
            <!-- 拍照记录 -->
            <div class="mbd-row" v-if="detailOrder.accept_photo_url"><span>出发拍照</span><img :src="detailOrder.accept_photo_url" class="mbd-photo" /></div>
            <div class="mbd-row" v-if="detailOrder.deliver_photo_url"><span>送达拍照</span><img :src="detailOrder.deliver_photo_url" class="mbd-photo" /></div>
            <!-- 进度 -->
            <div class="mbd-progress">
              <div class="mbdp-step" :class="{done:detailOrder.status!=='pending'}"><span class="mbdp-dot">1</span>接单</div>
              <div class="mbdp-line" :class="{done:['in_transit','delivered','completed'].includes(detailOrder.status)}"></div>
              <div class="mbdp-step" :class="{done:['in_transit','delivered','completed'].includes(detailOrder.status)}"><span class="mbdp-dot">2</span>配送</div>
              <div class="mbdp-line" :class="{done:['delivered','completed'].includes(detailOrder.status)}"></div>
              <div class="mbdp-step" :class="{done:['delivered','completed'].includes(detailOrder.status)}"><span class="mbdp-dot">3</span>送达</div>
              <div class="mbdp-line" :class="{done:detailOrder.status==='completed'}"></div>
              <div class="mbdp-step" :class="{done:detailOrder.status==='completed'}"><span class="mbdp-dot">4</span>签收</div>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== 温度追踪详情弹窗 ===== -->
      <div class="mb-overlay" v-if="trackingOrder" @click.self="trackingOrder=null">
        <div class="mb-detail">
          <div class="mbd-header">
            <span class="mbd-id">🌡 实时追踪: {{ trackingOrder.order_id }}</span>
            <span class="mbd-close" @click="trackingOrder=null">✕</span>
          </div>
          <div class="mbd-body" v-if="trackingDetail">
            <!-- 车辆信息 -->
            <div class="mtk-grid">
              <div class="mtk-cell"><span>车牌号</span><strong>{{ trackingDetail.vehicle?.plate_number || '—' }}</strong></div>
              <div class="mtk-cell"><span>当前位置</span><strong>{{ trackingDetail.vehicle?.current_city || '—' }}</strong></div>
              <div class="mtk-cell"><span>当前温度</span><strong :class="{ warn: !trackingDetail.temperature?.is_compliant }">{{ trackingDetail.temperature?.current?.toFixed(1) }}℃</strong></div>
              <div class="mtk-cell"><span>目标温度</span><strong>{{ trackingDetail.waybill_info?.temperature_range || '—' }}</strong></div>
              <div class="mtk-cell"><span>湿度</span><strong>{{ trackingDetail.temperature?.humidity?.toFixed(1) }}%</strong></div>
              <div class="mtk-cell"><span>冷机健康</span><strong :class="{ bad: (trackingDetail.cold_car?.health||100) < 70 }">{{ trackingDetail.cold_car?.health || 100 }}%</strong></div>
              <div class="mtk-cell"><span>速度</span><strong>{{ trackingDetail.vehicle?.speed?.toFixed(1) || 0 }} km/h</strong></div>
              <div class="mtk-cell"><span>预计到达</span><strong>{{ trackingDetail.waybill_info?.estimated_arrival || '—' }}</strong></div>
            </div>
            <!-- 温度合规状态 -->
            <div class="mtk-compliance" :class="{ danger: !trackingDetail.temperature?.is_compliant }">
              {{ trackingDetail.temperature?.is_compliant ? '✅ 温度合规 · 全程冷链保障' : '⚠️ 温度异常 · 偏差 ' + (trackingDetail.temperature?.deviation?.toFixed(1)||0) + '℃' }}
            </div>
            <!-- 告警列表 -->
            <div class="mtk-alerts" v-if="trackingDetail.alerts?.items?.length">
              <div class="mtk-alert-title">🚨 温度告警 ({{ trackingDetail.alerts.count }})</div>
              <div v-for="a in trackingDetail.alerts.items.slice(0,5)" :key="a.id" class="mtk-alert-item">
                <span class="mtk-alert-time">{{ fmtTime(a.created_at) }}</span>
                <span class="mtk-alert-msg">{{ a.message }}</span>
              </div>
            </div>
            <button class="mtk-refresh" @click="loadTrackingDetail(trackingOrder)">🔄 刷新数据</button>
          </div>
          <div class="mbd-body" v-else style="text-align:center;padding:20px;color:#999">加载中...</div>
        </div>
      </div>

      <!-- ===== 拍照上传弹窗 ===== -->
      <div class="mb-overlay" v-if="photoMode" @click.self="cancelPhoto">
        <div class="mb-photo-panel">
          <div class="mbd-header">
            <span class="mbd-id">{{ photoMode === 'accept' ? '📸 接单拍照' : '📸 送达拍照' }}</span>
            <span class="mbd-close" @click="cancelPhoto">✕</span>
          </div>
          <div class="mb-photo-body">
            <p class="mb-photo-tip">{{ photoMode === 'accept' ? '请拍摄货物装车照片' : '请拍摄货物送达照片' }}</p>
            <input ref="fileInput" type="file" accept="image/*" class="mb-file-input" @change="onFileSelected" />
            <button class="mb-camera-btn" @click="($refs.fileInput as any).click()" v-if="!photoPreview">
              <span class="mc-icon">📷</span><span class="mc-text">点击拍照</span>
            </button>
            <div class="mb-photo-preview" v-if="photoPreview">
              <img :src="photoPreview" class="mb-preview-img" />
              <div class="mb-photo-actions">
                <button class="mpa-btn cancel" @click="clearPhoto">重拍</button>
                <button class="mpa-btn upload" @click="submitPhotoAndAction" :disabled="uploading">
                  {{ uploading ? '上传中...' : '确认上传并' + (photoMode === 'accept' ? '接单' : '标记送达') }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部导航 -->
      <div class="mb-tabbar">
        <div class="mt-item" :class="{active:activeTab==='orders'}" @click="activeTab='orders'"><span class="mt-icon">📋</span><span class="mt-label">订单</span></div>
        <div class="mt-item" :class="{active:activeTab==='me'}" @click="activeTab='me'"><span class="mt-icon">👤</span><span class="mt-label">我的</span></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { customerAPI, uploadAPI } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'

const activeTab = ref('orders')
const orderSubTab = ref('my')

const driverId = ref(localStorage.getItem('username') || 'driver01')
const driverName = ref(localStorage.getItem('username') || 'driver01')

const driverOrders = ref<any[]>([])
const availableOrders = ref<any[]>([])
const detailOrder = ref<any>(null)

// 拍照相关
const photoMode = ref<'accept' | 'deliver' | null>(null)  // 当前拍照模式
const photoOrder = ref<any>(null)  // 当前操作的订单
const fileInput = ref<any>(null)
const photoPreview = ref('')
const uploading = ref(false)
let photoFile: File | null = null

// ===== 温度追踪 =====
const trackingData = ref<Record<string, any>>({})
const trackingOrder = ref<any>(null)
const trackingDetail = ref<any>(null)

const statusMap: Record<string, string> = {
  pending: '待接单', accepted: '已接单',
  in_transit: '配送中', delivered: '已送达', completed: '已完成',
}

function zoneClass(zoneName: string): string {
  if (zoneName?.includes('冷冻')) return 'z-freeze'
  if (zoneName?.includes('冷藏')) return 'z-chill'
  return 'z-ambient'
}
function fmtTime(t: string) { return t ? dayjs(t).format('MM-DD HH:mm') : '—' }

// ===== 订单加载 =====
async function loadDriverOrders() {
  try {
    const res: any = await customerAPI.getDriverOrders()
    const deleted = loadDeleted()
    driverOrders.value = (res.orders || []).filter((o: any) => !deleted.includes(o.order_id))
    loadTrackingSummary()
  } catch {}
}
async function loadAvailableOrders() {
  try {
    const res: any = await customerAPI.getAvailableOrders()
    const deleted = loadDeleted()
    availableOrders.value = (res.orders || []).filter((o: any) => !deleted.includes(o.order_id))
  } catch {}
}

// ===== 拍照接单流程 =====
function showPhotoUpload(o: any, mode: 'accept' | 'deliver') {
  photoOrder.value = o
  photoMode.value = mode
  clearPhoto()
}

function cancelPhoto() {
  photoMode.value = null
  photoOrder.value = null
  clearPhoto()
}

function onFileSelected(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files && input.files[0]) {
    photoFile = input.files[0]
    const reader = new FileReader()
    reader.onload = (ev: any) => { photoPreview.value = ev.target.result }
    reader.readAsDataURL(photoFile)
  }
}

function clearPhoto() {
  photoPreview.value = ''
  photoFile = null
  if (fileInput.value) fileInput.value.value = ''
}

async function uploadPhoto(): Promise<string> {
  if (!photoFile) return ''
  const fd = new FormData()
  fd.append('file', photoFile)
  fd.append('device_id', driverId.value)
  fd.append('order_id', photoOrder.value?.order_id || '')
  fd.append('photo_type', photoMode.value === 'accept' ? 'accept' : 'deliver')
  fd.append('notes', photoMode.value === 'accept' ? '出发拍照' : '送达拍照')
  try {
    const res: any = await uploadAPI.uploadTempRecord(fd)
    return res.data?.url || ''
  } catch {
    return photoPreview.value  // 降级：返回本地预览URL
  }
}

async function submitPhotoAndAction() {
  if (!photoFile) return
  uploading.value = true
  try {
    const photoUrl = await uploadPhoto()
    if (photoMode.value === 'accept') {
      // 拍照接单
      await customerAPI.acceptOrderWithPhoto(photoOrder.value.order_id, photoUrl)
      ElMessage.success(`已接单并上传出发照片: ${photoOrder.value.order_id}`)
    } else if (photoMode.value === 'deliver') {
      // 拍照送达
      await customerAPI.updateOrderStatus(photoOrder.value.order_id, 'delivered', photoUrl)
      ElMessage.success(`已标记送达并上传照片: ${photoOrder.value.order_id}`)
    }
    cancelPhoto()
    await loadDriverOrders()
    if (photoMode.value === 'accept') {
      await loadAvailableOrders()
      orderSubTab.value = 'my'
    }
  } catch {
    ElMessage.error('操作失败')
  } finally {
    uploading.value = false
  }
}

// ===== 接单（带拍照） =====
async function acceptAndPhoto(o: any) {
  photoOrder.value = o
  photoMode.value = 'accept'
  clearPhoto()
}

// ===== 开始配送 =====
async function startTransit(o: any) {
  try {
    await ElMessageBox.confirm(`确认开始配送 ${o.order_id}？`, '开始配送', { confirmButtonText: '确认出发', cancelButtonText: '取消', type: 'info' })
    await customerAPI.updateOrderStatus(o.order_id, 'in_transit')
    o.status = 'in_transit'
    ElMessage.success('已开始配送')
    await loadDriverOrders()
  } catch {}
}

// ===== 删除（黑名单+后端删除） =====
const DEL_KEY = 'driver_deleted_ids'
function loadDeleted(): string[] { try { const s = localStorage.getItem(DEL_KEY); return s ? JSON.parse(s) : [] } catch { return [] } }
function saveDeleted(id: string) { const ids = loadDeleted(); if (!ids.includes(id)) ids.push(id); localStorage.setItem(DEL_KEY, JSON.stringify(ids)) }
async function deleteDriverOrder(o: any) {
  try {
    await ElMessageBox.confirm(`删除订单 ${o.order_id}？`, '删除确认', { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning' })
    await customerAPI.deleteOrder(o.order_id)
    saveDeleted(o.order_id)
    driverOrders.value = driverOrders.value.filter(x => x.order_id !== o.order_id)
    ElMessage.success('已删除')
  } catch {}
}

// ===== 温度追踪方法 =====
async function loadTrackingSummary() {
  const activeOrders = driverOrders.value.filter(o => ['accepted','in_transit','delivered'].includes(o.status))
  for (const o of activeOrders) {
    try {
      const res: any = await customerAPI.getOrderTracking(o.order_id)
      if (res.status === 'ok' && res.tracking) trackingData.value[o.order_id] = res.tracking
    } catch { /* ignore */ }
  }
}

async function openTracking(o: any) {
  trackingOrder.value = o
  trackingDetail.value = null
  await loadTrackingDetail(o)
}

async function loadTrackingDetail(o: any) {
  try {
    const res: any = await customerAPI.getOrderTracking(o.order_id)
    if (res.status === 'ok' && res.tracking) {
      trackingDetail.value = res.tracking
      trackingData.value[o.order_id] = res.tracking
    }
  } catch { /* ignore */ }
}

function handleLogout() { localStorage.removeItem('token'); localStorage.removeItem('userRole'); window.location.hash = '#/login' }

onMounted(() => { loadDriverOrders() })
</script>

<style scoped>
.mobile-app{display:flex;justify-content:center;min-height:100vh;background:#f0f2f5;padding-bottom:20px}
.mobile-wrap{max-width:420px;width:100%;background:#fff;overflow:hidden;position:relative;padding-bottom:70px;min-height:100vh}

/* Header */
.mb-header{background:linear-gradient(135deg,#00a8ff,#7c3aed);padding:24px 16px 20px;color:#fff}
.mb-header-title{font-size:20px;font-weight:800}
.mb-header-sub{font-size:12px;opacity:.8;margin-top:4px}

/* SubTab */
.mb-subtab{display:flex;margin:12px 12px 0;background:#f5f5f5;border-radius:10px;padding:3px}
.mst-item{flex:1;text-align:center;padding:10px 0;font-size:13px;font-weight:600;color:#999;border-radius:8px;cursor:pointer;transition:all .2s;display:flex;align-items:center;justify-content:center;gap:6px}
.mst-item.active{background:#fff;color:#00a8ff;box-shadow:0 1px 4px rgba(0,0,0,.06)}
.mst-count{font-size:10px;background:#00a8ff;color:#fff;padding:1px 7px;border-radius:10px}

/* Order cards */
.mb-list{padding:10px 12px;display:flex;flex-direction:column;gap:10px}
.mb-card-item{padding:14px;border-radius:12px;background:#fff;border:1px solid #f0f0f0;cursor:pointer;transition:all .2s}
.mb-card-item:active{transform:scale(.98)}
.mb-card-item.card-pending{border-left:4px solid #f59e0b}
.mb-card-item.card-accepted{border-left:4px solid #00a8ff}
.mb-card-item.card-in_transit{border-left:4px solid #7c3aed}
.mb-card-item.card-delivered{border-left:4px solid #f59e0b}
.mb-card-item.card-completed{border-left:4px solid #00d2a0;opacity:.75}

.mci-top{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.mci-id{font-size:12px;font-weight:700;color:#333;font-family:monospace}
.mci-status{font-size:10px;font-weight:700;padding:2px 8px;border-radius:10px}
.mci-status.pending{background:#fef3c7;color:#d97706}
.mci-status.accepted{background:#dbeafe;color:#2563eb}
.mci-status.in_transit{background:#ede9fe;color:#7c3aed}
.mci-status.delivered{background:#fef3c7;color:#d97706}
.mci-status.completed{background:#d1fae5;color:#059669}

.mci-route{display:flex;align-items:center;gap:6px;margin-bottom:8px;font-size:12px}
.mci-dot{width:6px;height:6px;border-radius:50%;background:#00a8ff}
.mci-dot.end{background:#ccc}
.mci-arrow{color:#ccc;font-size:10px}
.mci-city{color:#666}

.mci-meta{display:flex;justify-content:space-between;align-items:center;font-size:11px;color:#999;margin-bottom:6px}
.mci-zone{font-size:10px;font-weight:600;padding:1px 6px;border-radius:4px}
.z-freeze{background:rgba(59,130,246,.1);color:#3b82f6}
.z-chill{background:rgba(16,185,129,.1);color:#10b981}
.z-ambient{background:rgba(245,158,11,.1);color:#f59e0b}

.mci-bottom{display:flex;justify-content:space-between;align-items:center}
.mci-price{font-size:16px;font-weight:800;color:#ef4444}
.mci-time{font-size:10px;color:#ccc}

/* 拍照缩略图 */
.mci-photos{display:flex;gap:6px;margin-top:6px}
.mci-thumb{width:60px;height:60px;border-radius:8px;object-fit:cover;border:1px solid #f0f0f0;background:#fafafa}

/* Actions */
.mci-actions{display:flex;gap:6px;margin-top:8px;align-items:center;flex-wrap:wrap}
.mcia-btn{padding:6px 14px;font-size:12px;font-weight:600;border-radius:8px;border:1px solid #e0e0e0;background:#fff;color:#666;cursor:pointer}
.mcia-btn.primary{background:#00a8ff;color:#fff;border-color:#00a8ff}
.mcia-btn.success{background:#00d2a0;color:#fff;border-color:#00d2a0}
.mci-waiting{font-size:11px;color:#d97706;font-weight:500}
.mci-done{font-size:12px;color:#059669;font-weight:600}

/* Empty */
.mb-empty{text-align:center;padding:60px 20px;color:#ccc}
.mbe-icon{font-size:48px;margin-bottom:10px}
.mb-empty p{font-size:15px;color:#999;margin:4px 0}
.mb-empty span{font-size:12px}

/* Profile */
.mb-profile{display:flex;align-items:center;gap:14px;padding:20px 16px;background:linear-gradient(135deg,#00a8ff,#7c3aed);color:#fff}
.mb-avatar{width:48px;height:48px;border-radius:50%;background:rgba(255,255,255,.25);display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:700}
.mb-driver-name{font-size:16px;font-weight:700}
.mb-driver-id{font-size:12px;opacity:.75;margin-top:2px}

/* Stats */
.mb-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:12px}
.mbs-item{display:flex;flex-direction:column;align-items:center;padding:14px 8px;border-radius:12px;background:#f8f9fa}
.mbs-num{font-size:24px;font-weight:800;color:#333}
.mbs-num.active{color:#00a8ff}
.mbs-num.done{color:#00d2a0}
.mbs-label{font-size:11px;color:#999;margin-top:4px}

/* Logout */
.mb-logout-btn{margin:16px 12px;width:calc(100% - 24px);padding:14px;border-radius:12px;font-size:14px;font-weight:600;background:#fff;border:1px solid #ff4757;color:#ff4757;cursor:pointer}

/* Detail overlay */
.mb-overlay{position:fixed;inset:0;background:rgba(0,0,0,.5);display:flex;align-items:flex-end;justify-content:center;z-index:1000}
.mb-detail{width:100%;max-width:420px;max-height:80vh;overflow-y:auto;background:#fff;border-radius:16px 16px 0 0;padding:20px}
.mbd-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}
.mbd-id{font-size:14px;font-weight:700;font-family:monospace}
.mbd-close{font-size:20px;color:#999;cursor:pointer;padding:4px 8px}
.mbd-body{display:flex;flex-direction:column;gap:8px}
.mbd-row{display:flex;justify-content:space-between;align-items:center;font-size:13px;padding:6px 0;border-bottom:1px solid #f5f5f5}
.mbd-row span{color:#999}
.mbd-row strong{font-weight:600}
.text-red{color:#ef4444}
.mbd-photo{width:80px;height:80px;border-radius:8px;object-fit:cover}

/* Progress */
.mbd-progress{display:flex;align-items:center;gap:0;margin:12px 0;padding:8px 0}
.mbdp-step{display:flex;flex-direction:column;align-items:center;gap:4px;font-size:10px;color:#ccc;flex-shrink:0}
.mbdp-dot{width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:700;background:#f0f0f0;color:#ccc;border:2px solid #e0e0e0}
.mbdp-step.done .mbdp-dot{background:#00a8ff;color:#fff;border-color:#00a8ff}
.mbdp-step.done{color:#00a8ff;font-weight:600}
.mbdp-line{flex:1;height:2px;background:#e0e0e0;min-width:20px}
.mbdp-line.done{background:#00a8ff}

/* Photo upload panel */
.mb-photo-panel{width:100%;max-width:420px;background:#fff;border-radius:16px 16px 0 0;padding:20px}
.mb-photo-body{display:flex;flex-direction:column;align-items:center;gap:16px}
.mb-photo-tip{font-size:14px;color:#666;text-align:center}
.mb-file-input{display:none}
.mb-camera-btn{display:flex;flex-direction:column;align-items:center;gap:6px;width:100%;padding:32px;border:2px dashed #00a8ff;border-radius:14px;background:#e8f4fd;cursor:pointer}
.mc-icon{font-size:36px}
.mc-text{font-size:14px;font-weight:600;color:#00a8ff}
.mb-photo-preview{width:100%}
.mb-preview-img{width:100%;border-radius:10px;max-height:300px;object-fit:contain;background:#f0f0f0}
.mb-photo-actions{display:flex;gap:8px;margin-top:12px}
.mpa-btn{flex:1;padding:12px;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;border:none}
.mpa-btn.cancel{background:#f0f0f0;color:#666}
.mpa-btn.upload{background:#00a8ff;color:#fff}
.mpa-btn:disabled{opacity:.6}

/* 温度追踪条 */
.mci-temp-bar{margin-top:8px;padding:8px 10px;border-radius:8px;background:#f0f9ff;border:1px solid #bae6fd}
.mtb-row{display:flex;align-items:center;gap:8px;font-size:11px}
.mtb-label{color:#0369a1;font-weight:600}
.mtb-temp{font-weight:800;color:#0284c7;font-size:13px}
.mtb-temp.warning{color:#ef4444;animation:pulse 1.5s infinite}
.mtb-loc{color:#666;margin-left:auto;font-size:10px}
.mtb-status{font-size:10px;color:#059669;font-weight:600;margin-top:3px}
.mtb-status.warn{color:#ef4444}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}

/* 追踪按钮 */
.mcia-btn.track{background:#f0f9ff;color:#0369a1;border-color:#bae6fd}

/* 追踪详情网格 */
.mtk-grid{display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:10px}
.mtk-cell{padding:8px 10px;border-radius:8px;background:#f8f9fa;display:flex;flex-direction:column;gap:2px}
.mtk-cell span{font-size:10px;color:#999}
.mtk-cell strong{font-size:13px;color:#333}
.mtk-cell strong.warn{color:#ef4444}
.mtk-cell strong.bad{color:#ef4444}

/* 合规状态 */
.mtk-compliance{padding:10px 12px;border-radius:8px;font-size:12px;font-weight:600;text-align:center;background:#d1fae5;color:#059669}
.mtk-compliance.danger{background:#fef2f2;color:#ef4444}

/* 告警列表 */
.mtk-alerts{margin-top:8px;padding:10px;border-radius:8px;background:#fffbeb;border:1px solid #fde68a}
.mtk-alert-title{font-size:11px;font-weight:700;color:#d97706;margin-bottom:6px}
.mtk-alert-item{display:flex;gap:8px;font-size:10px;padding:3px 0;color:#92400e;border-bottom:1px solid #fef3c7}
.mtk-alert-time{white-space:nowrap;color:#b45309;font-weight:500}
.mtk-alert-msg{flex:1}

/* 刷新按钮 */
.mtk-refresh{width:100%;margin-top:10px;padding:10px;border-radius:8px;background:#f0f9ff;border:1px solid #bae6fd;color:#0369a1;font-size:13px;font-weight:600;cursor:pointer}

/* Tabbar */
.mb-tabbar{position:absolute;bottom:0;left:0;right:0;display:flex;justify-content:space-around;align-items:center;background:#fff;border-top:1px solid #f0f0f0;padding:6px 0 8px;box-shadow:0 -2px 10px rgba(0,0,0,.04)}
.mt-item{display:flex;flex-direction:column;align-items:center;gap:2px;padding:4px 16px;cursor:pointer}
.mt-icon{font-size:20px}
.mt-label{font-size:10px;color:#999}
.mt-item.active .mt-label{color:#00a8ff;font-weight:600}

@media (min-width:768px){.mobile-wrap{border-radius:16px;margin:20px;min-height:auto;box-shadow:0 4px 30px rgba(0,0,0,.08)}}
</style>
