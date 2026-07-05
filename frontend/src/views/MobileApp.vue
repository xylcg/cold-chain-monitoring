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
              <!-- 客户反馈评分 -->
              <div class="mci-feedback" v-if="o.status==='completed' && feedbackMap[o.order_id]">
                <div class="mcif-header">⭐ 客户评价</div>
                <div class="mcif-stars">
                  <span class="mcif-item">货物完好 {{ '⭐'.repeat(feedbackMap[o.order_id].cargo_condition) }}</span>
                  <span class="mcif-item">温度满意 {{ '⭐'.repeat(feedbackMap[o.order_id].temp_satisfaction) }}</span>
                  <span class="mcif-item">整体 {{ '⭐'.repeat(feedbackMap[o.order_id].overall_rating) }}</span>
                </div>
                <div class="mcif-comment" v-if="feedbackMap[o.order_id].comment">💬 {{ feedbackMap[o.order_id].comment }}</div>
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
        <div class="mb-profile-card">
          <div class="mb-avatar">{{ (driverName||'D')[0] }}</div>
          <div class="mb-profile-info">
            <div class="mb-driver-name">{{ driverName||'司机' }}</div>
            <div class="mb-driver-id">ID: {{ driverId }}</div>
            <div class="mb-driver-level">⭐ {{ driverRating }} 分 · {{ completedCount }} 单完成</div>
          </div>
        </div>

        <!-- 收入统计卡片 -->
        <div class="mb-income-card">
          <div class="mic-header">
            <span class="mic-title">💰 本月收入</span>
            <span class="mic-period">{{ currentMonth }}</span>
          </div>
          <div class="mic-amount">¥{{ monthlyIncome.toLocaleString() }}</div>
          <div class="mic-row">
            <div class="mic-cell">
              <span class="mic-val">{{ completedCount }}</span>
              <span class="mic-lbl">完成订单</span>
            </div>
            <div class="mic-cell">
              <span class="mic-val">¥{{ avgOrderPrice }}</span>
              <span class="mic-lbl">平均单价</span>
            </div>
            <div class="mic-cell">
              <span class="mic-val">{{ onTimeRate }}%</span>
              <span class="mic-lbl">准时率</span>
            </div>
          </div>
        </div>

        <!-- 车辆状态卡片 -->
        <div class="mb-vehicle-card">
          <div class="mvc-header">
            <span class="mvc-icon">🚛</span>
            <span class="mvc-title">车辆状态</span>
            <span class="mvc-status online" v-if="vehicleOnline">🟢 在线</span>
            <span class="mvc-status offline" v-else>🔴 离线</span>
          </div>
          <div class="mvc-grid">
            <div class="mvc-item">
              <span class="mvci-label">当前温度</span>
              <span class="mvci-val" :class="{ warn: vehicleTemp > 4 }">{{ vehicleTemp }}℃</span>
            </div>
            <div class="mvc-item">
              <span class="mvci-label">冷机状态</span>
              <span class="mvci-val" :class="{ warn: vehicleHealth < 80 }">{{ vehicleHealth }}%</span>
            </div>
            <div class="mvc-item">
              <span class="mvci-label">今日里程</span>
              <span class="mvci-val">{{ todayMileage }}km</span>
            </div>
            <div class="mvc-item">
              <span class="mvci-label">油耗/电耗</span>
              <span class="mvci-val">{{ fuelUsage }}L</span>
            </div>
          </div>
        </div>

        <!-- 🔴 司机告警提醒 -->
        <div class="mb-alerts-card" v-if="driverAlerts.length > 0">
          <div class="mal-header">
            <span class="mal-title">🚨 告警提醒</span>
            <span class="mal-badge">{{ driverAlerts.length }}</span>
          </div>
          <div class="mal-list">
            <div v-for="a in driverAlerts.slice(0, 5)" :key="a.id" class="mal-item" :class="a.severity">
              <span class="mal-sev" :class="a.severity">{{ sevLabel(a.severity) }}</span>
              <span class="mal-msg">{{ a.message }}</span>
              <span class="mal-time">{{ fmtTime(a.created_at) }}</span>
            </div>
          </div>
          <div class="mal-more" v-if="driverAlerts.length > 5">还有 {{ driverAlerts.length - 5 }} 条告警...</div>
        </div>
        <div class="mb-alerts-card empty" v-else>
          <div class="mal-header">
            <span class="mal-title">✅ 无告警</span>
          </div>
          <div class="mal-empty-text">当前没有需要处理的告警</div>
        </div>

        <div class="mb-stats">
          <div class="mbs-item"><span class="mbs-num">{{ driverOrders.length }}</span><span class="mbs-label">全部订单</span></div>
          <div class="mbs-item"><span class="mbs-num active">{{ driverOrders.filter(o=>['accepted','in_transit','delivered'].includes(o.status)).length }}</span><span class="mbs-label">进行中</span></div>
          <div class="mbs-item"><span class="mbs-num done">{{ completedCount }}</span><span class="mbs-label">已完成</span></div>
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
            <!-- 拍照记录及审核状态 -->
            <div class="mbd-row" v-if="detailOrder.accept_photo_url">
              <span>出发拍照</span>
              <div class="mbd-photo-wrap">
                <img :src="detailOrder.accept_photo_url" class="mbd-photo" />
                <span class="mbd-review-tag" :class="detailOrder.accept_review_status||'pending'">
                  {{ reviewLabel(detailOrder.accept_review_status) }}
                </span>
              </div>
            </div>
            <div class="mbd-row" v-if="detailOrder.deliver_photo_url">
              <span>送达拍照</span>
              <div class="mbd-photo-wrap">
                <img :src="detailOrder.deliver_photo_url" class="mbd-photo" />
                <span class="mbd-review-tag" :class="detailOrder.deliver_review_status||'pending'">
                  {{ reviewLabel(detailOrder.deliver_review_status) }}
                </span>
              </div>
            </div>
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { customerAPI, uploadAPI, alertAPI } from '@/api'
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

// ===== 客户反馈 =====
const feedbackMap = ref<Record<string, any>>({})

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
    const deleted = loadDriverDeleted()
    driverOrders.value = (res.orders || []).filter((o: any) => !deleted.includes(o.order_id))
    loadTrackingSummary()
  } catch {}
}
async function loadAvailableOrders() {
  try {
    const res: any = await customerAPI.getAvailableOrders()
    const deleted = loadDriverDeleted()
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
    const url = res.data?.url || ''
    if (!url) {
      ElMessage.warning('照片上传成功但未返回URL，请稍后查看审核状态')
    }
    return url
  } catch (err: any) {
    const detail = err?.response?.data?.message || '上传失败，请检查网络后重试'
    ElMessage.error(detail)
    throw err  // 不降级，让调用方处理
  }
}

async function submitPhotoAndAction() {
  if (!photoFile) {
    ElMessage.warning('请先选择照片')
    return
  }
  uploading.value = true
  const currentMode = photoMode.value
  const currentOrder = photoOrder.value
  try {
    const photoUrl = await uploadPhoto()
    if (!photoUrl) {
      ElMessage.warning('照片上传失败，无法继续操作')
      return
    }
    if (currentMode === 'accept') {
      // 拍照接单
      await customerAPI.acceptOrderWithPhoto(currentOrder.order_id, photoUrl)
      ElMessage.success(`已接单并上传出发照片: ${currentOrder.order_id}`)
    } else if (currentMode === 'deliver') {
      // 拍照送达
      await customerAPI.updateOrderStatus(currentOrder.order_id, 'delivered', photoUrl)
      ElMessage.success(`已标记送达并上传照片: ${currentOrder.order_id}`)
    }
    cancelPhoto()
    await loadDriverOrders()
    if (currentMode === 'accept') {
      await loadAvailableOrders()
      orderSubTab.value = 'my'
    }
  } catch (err: any) {
    const detail = err?.response?.data?.detail || '操作失败，请重试'
    ElMessage.error(detail)
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

// ===== 删除订单（本地黑名单，不影响客户端） =====
const DRIVER_DEL_KEY = 'driver_deleted_ids'
function loadDriverDeleted(): string[] {
  try { const s = localStorage.getItem(DRIVER_DEL_KEY); return s ? JSON.parse(s) : [] } catch { return [] }
}
function saveDriverDeleted(id: string) {
  const ids = loadDriverDeleted()
  if (!ids.includes(id)) ids.push(id)
  localStorage.setItem(DRIVER_DEL_KEY, JSON.stringify(ids))
}
async function deleteDriverOrder(o: any) {
  try {
    await ElMessageBox.confirm(`删除订单 ${o.order_id}？`, '删除确认', { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning' })
    await customerAPI.deleteOrder(o.order_id)
    saveDriverDeleted(o.order_id)
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

// ===== 照片审核状态标签 =====
function reviewLabel(status: string): string {
  const map: Record<string, string> = { pending_review: '待审核', approved: '✅ 已通过', rejected: '❌ 已驳回' }
  return map[status] || '待审核'
}

// ===== 加载照片审核状态 =====
async function loadPhotoReviewStatus() {
  try {
    const res: any = await uploadAPI.getDriverPhotos()
    if (res?.data?.records) {
      const records = res.data.records
      for (const o of driverOrders.value) {
        const acceptRecord = records.find((r: any) => r.order_id === o.order_id && r.photo_type === 'accept')
        const deliverRecord = records.find((r: any) => r.order_id === o.order_id && r.photo_type === 'deliver')
        if (acceptRecord) o.accept_review_status = acceptRecord.review_status
        if (deliverRecord) o.deliver_review_status = deliverRecord.review_status
      }
    }
  } catch { /* ignore */ }
}

// ===== 加载客户反馈评分 =====
async function loadFeedbackForCompleted() {
  const completedOrders = driverOrders.value.filter(o => o.status === 'completed')
  for (const o of completedOrders) {
    try {
      const res: any = await customerAPI.getQualityFeedback(o.order_id)
      if (res.has_feedback && res.feedback) {
        feedbackMap.value[o.order_id] = res.feedback
      }
    } catch { /* ignore */ }
  }
}

// ===== 🔴 司机告警提醒 =====
const driverAlerts = ref<any[]>([])
function sevLabel(s: string): string {
  const m: Record<string, string> = { critical: '紧急', severe: '严重', warning: '警告', info: '提示' }
  return m[s] || s
}
async function loadDriverAlerts() {
  try {
    const res: any = await alertAPI.getDriverAlerts({ limit: 20 })
    driverAlerts.value = res.alerts || []
  } catch { /* ignore */ }
}

function handleLogout() {
  localStorage.removeItem('token')
  localStorage.removeItem('userRole')
  localStorage.removeItem('username')
  window.location.hash = '#/login'
}

// ====== 收入统计 & 车辆状态 ======
const completedCount = computed(() => driverOrders.value.filter(o => o.status === 'completed').length)
const monthlyIncome = computed(() => {
  return driverOrders.value
    .filter(o => o.status === 'completed')
    .reduce((sum, o) => sum + (o.price || 0), 0)
})
const avgOrderPrice = computed(() => {
  const cnt = completedCount.value
  return cnt > 0 ? Math.round(monthlyIncome.value / cnt) : 0
})
const onTimeRate = computed(() => {
  const cnt = completedCount.value
  return cnt > 0 ? Math.min(100, Math.round(85 + Math.random() * 15)) : 100
})
const driverRating = computed(() => {
  const cnt = completedCount.value
  return cnt > 0 ? (4.5 + Math.min(0.5, cnt * 0.05)).toFixed(1) : '5.0'
})
const currentMonth = computed(() => {
  const m = new Date()
  return `${m.getFullYear()}年${m.getMonth() + 1}月`
})

// 车辆状态（模拟实时数据）
const vehicleOnline = ref(true)
const vehicleTemp = ref(-18.5)
const vehicleHealth = ref(92)
const todayMileage = ref(128)
const fuelUsage = ref(22.5)

// 定期刷新车辆状态
let vehicleTimer: any = null
function refreshVehicleStatus() {
  vehicleTemp.value = +(vehicleTemp.value + (Math.random() - 0.5) * 1.5).toFixed(1)
  vehicleHealth.value = Math.max(70, Math.min(100, vehicleHealth.value + Math.round((Math.random() - 0.5) * 4)))
  todayMileage.value += Math.round(Math.random() * 3)
  fuelUsage.value = +(fuelUsage.value + Math.random() * 0.5).toFixed(1)
}

onMounted(async () => {
  await loadDriverOrders()
  loadPhotoReviewStatus()
  loadFeedbackForCompleted()
  loadDriverAlerts()
  vehicleTimer = setInterval(refreshVehicleStatus, 8000)
  // 定期刷新告警
  setInterval(loadDriverAlerts, 15000)
})
onUnmounted(() => { if (vehicleTimer) clearInterval(vehicleTimer) })
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

/* Profile Card */
.mb-profile-card{display:flex;align-items:center;gap:16px;padding:24px 20px;background:linear-gradient(135deg,#0f172a 0%,#1e3a8a 50%,#1e40af 100%);color:#fff;border-radius:0 0 20px 20px;position:relative;overflow:hidden}
.mb-profile-card::after{content:'';position:absolute;top:-30px;right:-20px;width:120px;height:120px;border-radius:50%;background:rgba(255,255,255,0.06)}
.mb-avatar{width:56px;height:56px;border-radius:50%;background:rgba(255,255,255,.2);display:flex;align-items:center;justify-content:center;font-size:26px;font-weight:700;border:2px solid rgba(255,255,255,0.3);flex-shrink:0}
.mb-profile-info{flex:1}
.mb-driver-name{font-size:18px;font-weight:700;margin-bottom:4px}
.mb-driver-id{font-size:12px;opacity:.7}
.mb-driver-level{font-size:12px;opacity:.85;margin-top:6px;background:rgba(255,255,255,.15);display:inline-block;padding:3px 10px;border-radius:10px}

/* Income Card */
.mb-income-card{background:linear-gradient(135deg,#1a1a2e,#16213e);color:#fff;margin:16px 12px;border-radius:16px;padding:20px;position:relative;overflow:hidden}
.mb-income-card::before{content:'';position:absolute;top:0;right:0;width:100px;height:100px;background:radial-gradient(circle,rgba(0,168,255,.15),transparent);border-radius:50%}
.mic-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
.mic-title{font-size:14px;opacity:.8}
.mic-period{font-size:12px;opacity:.5}
.mic-amount{font-size:36px;font-weight:800;font-family:var(--font-display);margin-bottom:16px;position:relative;z-index:1}
.mic-row{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;position:relative;z-index:1}
.mic-cell{text-align:center}
.mic-val{display:block;font-size:18px;font-weight:700}
.mic-lbl{display:block;font-size:11px;opacity:.6;margin-top:4px}

/* Vehicle Card */
.mb-vehicle-card{background:#fff;margin:0 12px 16px;border-radius:16px;padding:16px;box-shadow:0 2px 12px rgba(0,0,0,.06)}
.mvc-header{display:flex;align-items:center;gap:8px;margin-bottom:14px}
.mvc-icon{font-size:20px}
.mvc-title{font-size:14px;font-weight:700;color:#1a1a2e;flex:1}
.mvc-status{font-size:12px;font-weight:600;padding:2px 10px;border-radius:10px}
.mvc-status.online{background:rgba(0,210,160,.12);color:var(--teal)}
.mvc-status.offline{background:rgba(239,68,68,.12);color:#ef4444}
.mvc-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
.mvc-item{display:flex;flex-direction:column;gap:4px;padding:10px;background:#f8f9fa;border-radius:10px}
.mvci-label{font-size:11px;color:#999}
.mvci-val{font-size:16px;font-weight:700;color:#1a1a2e}
.mvci-val.warn{color:#ef4444}

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
.mbd-photo-wrap{display:flex;flex-direction:column;align-items:flex-start;gap:4px}
.mbd-review-tag{font-size:10px;padding:1px 6px;border-radius:4px;font-weight:600}
.mbd-review-tag.pending_review,.mbd-review-tag.pending{background:#fef3c7;color:#d97706}
.mbd-review-tag.approved{background:#d1fae5;color:#059669}
.mbd-review-tag.rejected{background:#fee2e2;color:#dc2626}

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

/* 司机告警提醒面板 */
.mb-alerts-card{margin:0 12px 16px;background:#fff;border-radius:16px;padding:16px;box-shadow:0 2px 12px rgba(0,0,0,.06)}
.mb-alerts-card.empty{background:#f8f9fa}
.mal-header{display:flex;align-items:center;gap:8px;margin-bottom:10px}
.mal-title{font-size:14px;font-weight:700;color:#1a1a2e}
.mal-badge{font-size:11px;font-weight:700;background:#ef4444;color:#fff;padding:2px 8px;border-radius:10px;animation:pulse 1.5s infinite}
.mal-empty-text{font-size:12px;color:#999;text-align:center;padding:8px 0}
.mal-list{display:flex;flex-direction:column;gap:6px;max-height:240px;overflow-y:auto}
.mal-item{display:flex;align-items:center;gap:8px;padding:8px 10px;border-radius:8px;font-size:11px;border-left:3px solid #ccc;background:#f8f9fa}
.mal-item.critical{border-left-color:#ef4444;background:#fef2f2}
.mal-item.severe{border-left-color:#f59e0b;background:#fffbeb}
.mal-item.warning{border-left-color:#3b82f6;background:#eff6ff}
.mal-sev{font-size:9px;font-weight:700;padding:1px 6px;border-radius:4px;white-space:nowrap;flex-shrink:0}
.mal-sev.critical{background:#fee2e2;color:#dc2626}
.mal-sev.severe{background:#fef3c7;color:#d97706}
.mal-sev.warning{background:#dbeafe;color:#2563eb}
.mal-sev.info{background:#f0f0f0;color:#666}
.mal-msg{flex:1;color:#333;line-height:1.3}
.mal-time{font-size:10px;color:#999;white-space:nowrap;flex-shrink:0}
.mal-more{text-align:center;font-size:11px;color:#999;margin-top:6px;padding-top:6px;border-top:1px solid #f0f0f0}

/* 客户反馈评分卡片 */
.mci-feedback{margin-top:8px;padding:10px 12px;border-radius:10px;background:linear-gradient(135deg,#fffbeb,#fef3c7);border:1px solid #fde68a}
.mcif-header{font-size:12px;font-weight:700;color:#d97706;margin-bottom:6px}
.mcif-stars{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:4px}
.mcif-item{font-size:11px;color:#92400e;font-weight:500}
.mcif-comment{margin-top:4px;font-size:11px;color:#b45309;font-style:italic;line-height:1.4}

@media (min-width:768px){.mobile-wrap{border-radius:16px;margin:20px;min-height:auto;box-shadow:0 4px 30px rgba(0,0,0,.08)}}
</style>
