<template>
  <div class="mobile-app">
    <div class="mobile-wrap">
      <!-- ===== 页面头部 ===== -->
      <div class="mb-header">
        <div class="mb-header-title">冷链配送</div>
        <div class="mb-header-sub">下单 · 追踪 · 签收</div>
      </div>

      <!-- ===== 我的订单 Tab ===== -->
      <div class="mb-page" v-show="activeTab === 'orders'">
        <!-- 状态过滤栏 -->
        <div class="mb-filter-bar">
          <button v-for="f in statusFilters" :key="f.key"
            class="mfb-btn" :class="{ active: statusFilter === f.key }"
            @click="statusFilter = f.key">
            {{ f.label }}
            <span v-if="f.key === 'all'" class="mfb-count">{{ orders.length }}</span>
            <span v-else class="mfb-count">{{ orders.filter(o => filterFn(o, f.key)).length }}</span>
          </button>
        </div>

        <!-- 订单列表 -->
        <div v-if="filteredOrders.length > 0" class="mb-list">
          <div
            v-for="order in filteredOrders"
            :key="order.order_id"
            class="mb-card-item"
            :class="'card-' + order.status"
            @click="showOrderDetail(order)"
          >
            <div class="mci-top">
              <span class="mci-id">{{ order.order_id }}</span>
              <span class="mci-status" :class="order.status">{{ statusMap[order.status] || order.status }}</span>
            </div>
            <div class="mci-route">
              <span class="mci-dot"></span>
              <span class="mci-city">{{ order.origin }}</span>
              <span class="mci-arrow">→</span>
              <span class="mci-dot end"></span>
              <span class="mci-city">{{ order.destination }}</span>
            </div>
            <div class="mci-meta">
              <span>{{ order.cargo_name }} · {{ order.quantity }}{{ order.unit }}</span>
              <span class="mci-zone" :class="zoneClass(order.zone_name)">{{ order.zone_name }}</span>
            </div>
            <div class="mci-bottom">
              <span class="mci-price">¥{{ order.price?.toLocaleString() }}</span>
              <span class="mci-time">{{ formatTime(order.created_at) }}</span>
            </div>
            <!-- 温度追踪条 -->
            <div v-if="trackingData[order.order_id] && ['accepted','in_transit','delivered'].includes(order.status)" class="mci-temp-bar">
              <div class="mtb-row">
                <span class="mtb-label">🌡 实时温度</span>
                <span class="mtb-temp" :class="{ warning: !trackingData[order.order_id].temperature?.is_compliant }">
                  {{ trackingData[order.order_id].temperature?.current?.toFixed(1) }}℃
                </span>
                <span class="mtb-loc">📍 {{ trackingData[order.order_id].vehicle?.current_city || '—' }}</span>
              </div>
              <div class="mtb-status" :class="{ warn: !trackingData[order.order_id].temperature?.is_compliant }">
                {{ trackingData[order.order_id].temperature?.is_compliant ? '✅ 温度正常' : '⚠️ 温度异常！' }}
              </div>
            </div>
            <!-- 操作按钮 -->
            <div class="mci-actions" v-if="order.status === 'delivered'">
              <button class="mcia-btn success" @click.stop="confirmReceive(order)">📦 确认签收</button>
              <button class="mcia-btn track" @click.stop="openTracking(order)" v-if="trackingData[order.order_id]">🌡 追踪</button>
            </div>
            <div class="mci-actions" v-if="order.status === 'completed'">
              <button class="mcia-btn" @click.stop="deleteCustomerOrder(order)">🗑 删除</button>
              <button class="mcia-btn feedback" @click.stop="openFeedback(order)">⭐ 品质反馈</button>
            </div>
            <div class="mci-actions" v-if="['accepted','in_transit'].includes(order.status)">
              <button class="mcia-btn track" @click.stop="openTracking(order)" v-if="trackingData[order.order_id]">🌡 查看温度</button>
            </div>
            <!-- 司机信息 -->
            <div v-if="order.driver_name" class="mci-driver">🚛 司机: {{ order.driver_name }}</div>
            <!-- 拍照记录 -->
            <div class="mci-photos" v-if="order.accept_photo_url || order.deliver_photo_url">
              <img v-if="order.accept_photo_url" :src="order.accept_photo_url" class="mci-thumb" title="出发拍照" />
              <img v-if="order.deliver_photo_url" :src="order.deliver_photo_url" class="mci-thumb" title="送达拍照" />
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div class="mb-empty" v-else>
          <div class="mbe-icon">📋</div>
          <p>暂无订单</p>
          <span>点击下方「下单」创建冷链配送订单</span>
        </div>
      </div>

      <!-- ===== 下单 Tab ===== -->
      <div class="mb-page" v-show="activeTab === 'create'">
        <div class="mb-form">
          <div class="mb-form-title">新建冷链配送订单</div>

          <div class="mb-field">
            <label>货物名称 <span class="required">*</span></label>
            <input v-model="form.cargo_name" class="mb-input" placeholder="如：冷冻海鲜、进口牛肉" />
          </div>

          <div class="mb-field">
            <label>货物品类</label>
            <select v-model="form.cargo_category" class="mb-input">
              <option v-for="c in cargoCategories" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>

          <div class="mb-row">
            <div class="mb-field">
              <label>发货地 <span class="required">*</span></label>
              <input v-model="form.origin" class="mb-input" placeholder="华北中心冷库" />
            </div>
            <div class="mb-field">
              <label>目的地 <span class="required">*</span></label>
              <input v-model="form.destination" class="mb-input" placeholder="北京市朝阳区" />
            </div>
          </div>

          <div class="mb-row">
            <div class="mb-field">
              <label>数量 <span class="required">*</span></label>
              <input v-model.number="form.quantity" type="number" class="mb-input" placeholder="0" />
            </div>
            <div class="mb-field">
              <label>单位</label>
              <select v-model="form.unit" class="mb-input">
                <option value="kg">公斤 (kg)</option>
                <option value="吨">吨</option>
                <option value="箱">箱</option>
                <option value="件">件</option>
              </select>
            </div>
          </div>

          <div class="mb-row">
            <div class="mb-field">
              <label>温区</label>
              <select v-model="form.zone_name" class="mb-input" @change="onZoneChange">
                <option v-for="z in zones" :key="z.name" :value="z.name">{{ z.label }}</option>
              </select>
            </div>
            <div class="mb-field">
              <label>温度要求</label>
              <input v-model="form.temperature_requirement" class="mb-input" placeholder="-18℃ ~ -15℃" />
            </div>
          </div>

          <div class="mb-row">
            <div class="mb-field">
              <label>收件人</label>
              <input v-model="form.receiver" class="mb-input" placeholder="收件人姓名" />
            </div>
            <div class="mb-field">
              <label>电话</label>
              <input v-model="form.receiver_phone" class="mb-input" placeholder="手机号" />
            </div>
          </div>

          <div class="mb-field">
            <label>备注</label>
            <textarea v-model="form.notes" class="mb-input mb-textarea" placeholder="订单备注（选填）" rows="2"></textarea>
          </div>

          <button class="mb-submit" @click="submitOrder" :disabled="submitting">
            {{ submitting ? '提交中...' : '📤 提交订单' }}
          </button>
        </div>
      </div>

      <!-- ===== 订单详情弹窗 ===== -->
      <div class="mb-overlay" v-if="detailOrder" @click.self="detailOrder = null">
        <div class="mb-detail">
          <div class="mbd-header">
            <span class="mbd-id">{{ detailOrder.order_id }}</span>
            <span class="mbd-close" @click="detailOrder = null">✕</span>
          </div>
          <div class="mbd-body">
            <div class="mbd-row"><span>货物</span><strong>{{ detailOrder.cargo_name }} · {{ detailOrder.cargo_category }}</strong></div>
            <div class="mbd-row"><span>路线</span><strong>{{ detailOrder.origin }} → {{ detailOrder.destination }}</strong></div>
            <div class="mbd-row"><span>数量</span><strong>{{ detailOrder.quantity }}{{ detailOrder.unit }}</strong></div>
            <div class="mbd-row"><span>温区</span><strong>{{ detailOrder.zone_name }} ({{ detailOrder.temperature_requirement }})</strong></div>
            <div class="mbd-row"><span>收件人</span><strong>{{ detailOrder.receiver || '—' }} {{ detailOrder.receiver_phone }}</strong></div>
            <div class="mbd-row" v-if="detailOrder.driver_name"><span>司机</span><strong class="text-blue">{{ detailOrder.driver_name }}</strong></div>
            <div class="mbd-row"><span>运费</span><strong class="text-red">¥{{ detailOrder.price?.toLocaleString() }}</strong></div>
            <div class="mbd-row"><span>时间</span><strong>{{ formatTime(detailOrder.created_at) }}</strong></div>
            <!-- 仓库出库信息 -->
            <div class="mbd-row" v-if="detailOrder.outbound_warehouse">
              <span>出库仓库</span><strong class="text-blue">{{ detailOrder.outbound_warehouse }}</strong>
            </div>
            <div class="mbd-row" v-if="detailOrder.outbound_time">
              <span>出库时间</span><strong>{{ formatTime(detailOrder.outbound_time) }}</strong>
            </div>

            <!-- 进度（5步流程） -->
            <div class="mbd-progress">
              <div class="mbdp-step" :class="{ done: true }"><span class="mbdp-dot">1</span>下单</div>
              <div class="mbdp-line" :class="{ done: detailOrder.status !== 'pending' }"></div>
              <div class="mbdp-step" :class="{ done: detailOrder.status !== 'pending' }"><span class="mbdp-dot">2</span>已接单</div>
              <div class="mbdp-line" :class="{ done: ['in_transit', 'delivered', 'completed'].includes(detailOrder.status) }"></div>
              <div class="mbdp-step" :class="{ done: ['in_transit', 'delivered', 'completed'].includes(detailOrder.status) }"><span class="mbdp-dot">3</span>配送中</div>
              <div class="mbdp-line" :class="{ done: ['delivered', 'completed'].includes(detailOrder.status) }"></div>
              <div class="mbdp-step" :class="{ done: ['delivered', 'completed'].includes(detailOrder.status) }"><span class="mbdp-dot">4</span>已送达</div>
              <div class="mbdp-line" :class="{ done: detailOrder.status === 'completed' }"></div>
              <div class="mbdp-step" :class="{ done: detailOrder.status === 'completed' }"><span class="mbdp-dot">5</span>已签收</div>
            </div>

            <div class="mbd-notes" v-if="detailOrder.notes">{{ detailOrder.notes }}</div>
          </div>
        </div>
      </div>

      <!-- ===== 温度追踪弹窗 ===== -->
      <div class="mb-overlay" v-if="trackingOrder" @click.self="trackingOrder=null">
        <div class="mb-detail">
          <div class="mbd-header">
            <span class="mbd-id">🌡 实时追踪: {{ trackingOrder.order_id }}</span>
            <span class="mbd-close" @click="trackingOrder=null">✕</span>
          </div>
          <div class="mbd-body" v-if="trackingDetail">
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
            <div class="mtk-compliance" :class="{ danger: !trackingDetail.temperature?.is_compliant }">
              {{ trackingDetail.temperature?.is_compliant ? '✅ 温度合规 · 全程冷链保障' : '⚠️ 温度异常 · 偏差 ' + (trackingDetail.temperature?.deviation?.toFixed(1)||0) + '℃' }}
            </div>
            <button class="mtk-refresh" @click="loadTrackingDetail(trackingOrder)">🔄 刷新数据</button>
          </div>
          <div class="mbd-body" v-else style="text-align:center;padding:20px;color:#999">加载中...</div>
        </div>
      </div>

      <!-- ===== 品质反馈弹窗 ===== -->
      <div class="mb-overlay" v-if="feedbackOrder" @click.self="feedbackOrder=null">
        <div class="mb-detail">
          <div class="mbd-header">
            <span class="mbd-id">⭐ 品质反馈: {{ feedbackOrder.order_id }}</span>
            <span class="mbd-close" @click="feedbackOrder=null">✕</span>
          </div>
          <div class="mbd-body">
            <div class="qfb-field">
              <label>货物状态</label>
              <div class="qfb-stars">
                <span v-for="i in 5" :key="i" class="qfb-star" :class="{ active: feedbackForm.cargo_condition >= i }" @click="feedbackForm.cargo_condition = i">{{ feedbackForm.cargo_condition >= i ? '⭐' : '☆' }}</span>
              </div>
            </div>
            <div class="qfb-field">
              <label>温度满意度</label>
              <div class="qfb-stars">
                <span v-for="i in 5" :key="i" class="qfb-star" :class="{ active: feedbackForm.temp_satisfaction >= i }" @click="feedbackForm.temp_satisfaction = i">{{ feedbackForm.temp_satisfaction >= i ? '⭐' : '☆' }}</span>
              </div>
            </div>
            <div class="qfb-field">
              <label>整体评价</label>
              <div class="qfb-stars">
                <span v-for="i in 5" :key="i" class="qfb-star" :class="{ active: feedbackForm.overall_rating >= i }" @click="feedbackForm.overall_rating = i">{{ feedbackForm.overall_rating >= i ? '⭐' : '☆' }}</span>
              </div>
            </div>
            <div class="qfb-field">
              <label>备注</label>
              <textarea v-model="feedbackForm.comment" class="mb-input mb-textarea" placeholder="分享您的收货体验..." rows="3"></textarea>
            </div>
            <button class="mb-submit" @click="submitFeedback" :disabled="feedbackSubmitting">
              {{ feedbackSubmitting ? '提交中...' : '📤 提交反馈' }}
            </button>
          </div>
        </div>
      </div>

      <!-- ===== 底部导航 ===== -->
      <div class="mb-tabbar">
        <div class="mt-item" :class="{ active: activeTab === 'orders' }" @click="activeTab = 'orders'; loadMyOrders()">
          <span class="mt-icon">📋</span>
          <span class="mt-label">我的订单</span>
        </div>
        <div class="mt-item center-btn" :class="{ active: activeTab === 'create' }" @click="activeTab = 'create'">
          <span class="mt-icon-create">＋</span>
          <span class="mt-label">下单</span>
        </div>
        <div class="mt-item" @click="handleLogout">
          <span class="mt-icon">👤</span>
          <span class="mt-label">退出</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { customerAPI } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'

// ===== Tab =====
const activeTab = ref('orders')

// ===== 订单列表 =====
const orders = ref<any[]>([])
const loading = ref(false)
const statusFilter = ref('all')
const detailOrder = ref<any>(null)

// ===== 温度追踪 =====
const trackingData = ref<Record<string, any>>({})
const trackingOrder = ref<any>(null)
const trackingDetail = ref<any>(null)

// ===== 品质反馈 =====
const feedbackOrder = ref<any>(null)
const feedbackSubmitting = ref(false)
const feedbackForm = reactive({ cargo_condition: 5, temp_satisfaction: 5, overall_rating: 5, comment: '' })

const statusFilters = [
  { key: 'all', label: '全部' },
  { key: 'pending', label: '待接单' },
  { key: 'active', label: '配送中' },
  { key: 'completed', label: '已完成' },
]

const statusMap: Record<string, string> = {
  pending: '待接单',
  accepted: '已接单',
  in_transit: '配送中',
  delivered: '已送达',
  completed: '已完成',
}

function filterFn(o: any, key: string): boolean {
  if (key === 'all') return true
  if (key === 'pending') return o.status === 'pending'
  if (key === 'active') return ['accepted', 'in_transit', 'delivered'].includes(o.status)
  if (key === 'completed') return o.status === 'completed'
  return true
}

const filteredOrders = computed(() => orders.value.filter(o => filterFn(o, statusFilter.value)))

function zoneClass(zoneName: string): string {
  if (zoneName?.includes('冷冻')) return 'z-freeze'
  if (zoneName?.includes('冷藏')) return 'z-chill'
  return 'z-ambient'
}

function formatTime(t: string) {
  if (!t) return '—'
  return dayjs(t).format('MM-DD HH:mm')
}

async function loadMyOrders() {
  loading.value = true
  try {
    const res: any = await customerAPI.getMyOrdersNew()
    const deletedIds = loadCustomerDeletedIds()
    orders.value = (res.orders || []).filter((o: any) => !deletedIds.includes(o.order_id))
    loadTrackingSummary()
  } catch { /* ignore */ }
  finally { loading.value = false }
}

function showOrderDetail(order: any) {
  detailOrder.value = order
}

// ===== 下单 =====
const submitting = ref(false)
const cargoCategories = ['冷冻食品', '冷藏生鲜', '疫苗医药', '化工制剂', '其他']
const zones = [
  { name: '冷冻区', label: '❄ 冷冻区 (-22℃~-15℃)' },
  { name: '冷藏区', label: '🧊 冷藏区 (0℃~4℃)' },
  { name: '恒温区', label: '🌡 恒温区 (15℃~20℃)' },
]

const form = reactive({
  cargo_name: '',
  cargo_category: '冷冻食品',
  origin: '',
  destination: '',
  quantity: 100,
  unit: 'kg',
  temperature_requirement: '-22℃ ~ -15℃',
  zone_name: '冷冻区',
  receiver: '',
  receiver_phone: '',
  notes: '',
})

function onZoneChange() {
  const map: Record<string, string> = {
    '冷冻区': '-22℃ ~ -15℃',
    '冷藏区': '0℃ ~ 4℃',
    '恒温区': '15℃ ~ 20℃',
  }
  form.temperature_requirement = map[form.zone_name] || form.temperature_requirement
}

async function submitOrder() {
  if (!form.cargo_name.trim()) { ElMessage.warning('请填写货物名称'); return }
  if (!form.origin.trim()) { ElMessage.warning('请填写发货地'); return }
  if (!form.destination.trim()) { ElMessage.warning('请填写目的地'); return }
  if (!form.quantity || form.quantity <= 0) { ElMessage.warning('请填写有效数量'); return }

  submitting.value = true
  try {
    const res: any = await customerAPI.createOrder({ ...form })
    if (res.status === 'ok') {
      ElMessage.success(`订单 ${res.order.order_id} 创建成功！`)
      form.cargo_name = ''
      form.origin = ''
      form.destination = ''
      form.quantity = 100
      form.receiver = ''
      form.receiver_phone = ''
      form.notes = ''
      activeTab.value = 'orders'
      await loadMyOrders()
    }
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '下单失败')
  } finally {
    submitting.value = false
  }
}

// ===== 签收 =====
async function confirmReceive(order: any) {
  try {
    await ElMessageBox.confirm(`确认签收订单 ${order.order_id}？`, '签收确认', {
      confirmButtonText: '确认签收',
      cancelButtonText: '取消',
      type: 'success',
    })
    const res: any = await customerAPI.confirmReceive(order.order_id)
    // 仅在 API 成功返回后才更新本地状态
    if (res.status === 'ok') {
      order.status = 'completed'
      order.signed_by_customer = true
      ElMessage.success(`订单 ${order.order_id} 已签收！`)
    } else {
      ElMessage.error('签收失败，请重试')
    }
  } catch (err: any) {
    // 用户取消或接口失败
    if (err !== 'cancel' && err?.response?.data?.detail) {
      ElMessage.error(err.response.data.detail)
    }
  }
}

// ===== 删除（后端删除 + 黑名单）=====
const CUST_DELETED_KEY = 'customer_deleted_orders'
function loadCustomerDeletedIds(): string[] {
  try { const s = localStorage.getItem(CUST_DELETED_KEY); return s ? JSON.parse(s) : [] } catch { return [] }
}
function saveCustomerDeletedId(id: string) {
  const ids = loadCustomerDeletedIds()
  if (!ids.includes(id)) ids.push(id)
  localStorage.setItem(CUST_DELETED_KEY, JSON.stringify(ids))
}

async function deleteCustomerOrder(order: any) {
  try {
    await ElMessageBox.confirm(`确认删除订单 ${order.order_id}？`, '删除确认', {
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await customerAPI.deleteOrder(order.order_id)
    saveCustomerDeletedId(order.order_id)
    orders.value = orders.value.filter(o => o.order_id !== order.order_id)
    ElMessage.success('已删除')
  } catch {
    // 用户取消
  }
}

// ===== 温度追踪方法 =====
async function loadTrackingSummary() {
  const activeOrders = orders.value.filter(o => ['accepted','in_transit','delivered'].includes(o.status))
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

// ===== 品质反馈方法 =====
function openFeedback(o: any) {
  feedbackOrder.value = o
  feedbackForm.cargo_condition = 5
  feedbackForm.temp_satisfaction = 5
  feedbackForm.overall_rating = 5
  feedbackForm.comment = ''
}

async function submitFeedback() {
  if (!feedbackOrder.value) return
  feedbackSubmitting.value = true
  try {
    await customerAPI.submitQualityFeedback(feedbackOrder.value.order_id, { ...feedbackForm })
    ElMessage.success('品质反馈提交成功！')
    feedbackOrder.value = null
  } catch { /* ignore */ }
  finally { feedbackSubmitting.value = false }
}

function handleLogout() {
  localStorage.removeItem('token')
  localStorage.removeItem('userRole')
  localStorage.removeItem('username')
  window.location.hash = '#/login'
}

onMounted(() => {
  loadMyOrders()
})
</script>

<style scoped>
.mobile-app {
  display: flex;
  justify-content: center;
  min-height: 100vh;
  background: #f0f2f5;
  padding-bottom: 20px;
}
.mobile-wrap {
  max-width: 420px;
  width: 100%;
  background: #fff;
  border-radius: 0;
  overflow: hidden;
  position: relative;
  padding-bottom: 70px;
  min-height: 100vh;
}

/* Header */
.mb-header {
  background: linear-gradient(135deg, #00a8ff, #7c3aed);
  padding: 24px 16px 20px;
  color: #fff;
}
.mb-header-title { font-size: 20px; font-weight: 800; }
.mb-header-sub { font-size: 12px; opacity: 0.8; margin-top: 4px; }

/* Filter */
.mb-filter-bar {
  display: flex;
  gap: 6px;
  padding: 10px 12px;
  overflow-x: auto;
}
.mfb-btn {
  padding: 6px 14px;
  border-radius: 20px;
  border: 1px solid #e0e0e0;
  background: #fff;
  font-size: 12px;
  color: #666;
  white-space: nowrap;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
}
.mfb-btn.active { background: #00a8ff; color: #fff; border-color: #00a8ff; }
.mfb-count { font-size: 10px; opacity: 0.7; }

/* Order cards */
.mb-list {
  padding: 0 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.mb-card-item {
  padding: 14px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #f0f0f0;
  cursor: pointer;
  transition: all 0.2s;
}
.mb-card-item:active { transform: scale(0.98); }
.mb-card-item.card-pending { border-left: 4px solid #f59e0b; }
.mb-card-item.card-accepted { border-left: 4px solid #00a8ff; }
.mb-card-item.card-in_transit { border-left: 4px solid #7c3aed; }
.mb-card-item.card-delivered { border-left: 4px solid #f59e0b; }
.mb-card-item.card-completed { border-left: 4px solid #00d2a0; opacity: 0.75; }

.mci-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.mci-id { font-size: 12px; font-weight: 700; color: #333; font-family: monospace; }
.mci-status { font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 10px; }
.mci-status.pending { background: #fef3c7; color: #d97706; }
.mci-status.accepted { background: #dbeafe; color: #2563eb; }
.mci-status.in_transit { background: #ede9fe; color: #7c3aed; }
.mci-status.delivered { background: #fef3c7; color: #d97706; }
.mci-status.completed { background: #d1fae5; color: #059669; }

.mci-route { display: flex; align-items: center; gap: 6px; margin-bottom: 8px; font-size: 12px; }
.mci-dot { width: 6px; height: 6px; border-radius: 50%; background: #00a8ff; }
.mci-dot.end { background: #ccc; }
.mci-arrow { color: #ccc; font-size: 10px; }
.mci-city { color: #666; }

.mci-meta { display: flex; justify-content: space-between; align-items: center; font-size: 11px; color: #999; margin-bottom: 6px; }
.mci-zone { font-size: 10px; font-weight: 600; padding: 1px 6px; border-radius: 4px; }
.z-freeze { background: rgba(59,130,246,0.1); color: #3b82f6; }
.z-chill { background: rgba(16,185,129,0.1); color: #10b981; }
.z-ambient { background: rgba(245,158,11,0.1); color: #f59e0b; }

.mci-bottom { display: flex; justify-content: space-between; align-items: center; }
.mci-price { font-size: 16px; font-weight: 800; color: #ef4444; }
.mci-time { font-size: 10px; color: #ccc; }

.mci-review { margin-top: 8px; padding: 6px 10px; border-radius: 6px; font-size: 11px; font-weight: 500; }
/* 操作按钮 */
.mci-actions { display: flex; gap: 6px; margin-top: 8px; }
.mcia-btn {
  padding: 6px 14px; font-size: 12px; font-weight: 600; border-radius: 8px;
  border: 1px solid #e0e0e0; background: #fff; color: #666; cursor: pointer;
}
.mcia-btn.success { background: #00d2a0; color: #fff; border-color: #00d2a0; }

/* 司机信息 */
.mci-driver { margin-top: 6px; font-size: 11px; color: #00a8ff; font-weight: 500; }
/* 拍照缩略图 */
.mci-photos { display: flex; gap: 6px; margin-top: 6px; }
.mci-thumb { width: 50px; height: 50px; border-radius: 6px; object-fit: cover; border: 1px solid #f0f0f0; background: #fafafa; }

.rv-approved { background: rgba(0,210,160,0.08); color: #059669; }
.rv-rejected { background: rgba(239,68,68,0.08); color: #ef4444; }

/* Empty */
.mb-empty { text-align: center; padding: 60px 20px; color: #ccc; }
.mbe-icon { font-size: 48px; margin-bottom: 10px; }
.mb-empty p { font-size: 15px; color: #999; margin: 4px 0; }
.mb-empty span { font-size: 12px; }

/* Form */
.mb-form { padding: 16px 12px; }
.mb-form-title { font-size: 16px; font-weight: 700; color: #333; margin-bottom: 16px; }
.mb-field { display: flex; flex-direction: column; gap: 4px; margin-bottom: 12px; flex: 1; }
.mb-field label { font-size: 11px; font-weight: 600; color: #666; }
.required { color: #ef4444; }
.mb-row { display: flex; gap: 10px; }
.mb-input {
  padding: 10px 12px; border: 1px solid #e0e0e0; border-radius: 8px;
  font-size: 13px; color: #333; background: #fafafa;
  font-family: inherit; transition: border-color 0.2s;
  box-sizing: border-box;
}
.mb-input:focus { outline: none; border-color: #00a8ff; background: #fff; }
.mb-textarea { resize: vertical; min-height: 50px; }
.mb-submit {
  width: 100%; padding: 14px; border: none; border-radius: 12px;
  background: linear-gradient(135deg, #00a8ff, #7c3aed);
  color: #fff; font-size: 15px; font-weight: 700; cursor: pointer;
  margin-top: 8px; transition: opacity 0.2s;
}
.mb-submit:active { opacity: 0.8; }
.mb-submit:disabled { opacity: 0.5; }

/* Detail overlay */
.mb-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.5);
  display: flex; align-items: flex-end; justify-content: center; z-index: 1000;
}
.mb-detail {
  width: 100%; max-width: 420px; max-height: 80vh; overflow-y: auto;
  background: #fff; border-radius: 16px 16px 0 0; padding: 20px;
}
.mbd-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.mbd-id { font-size: 14px; font-weight: 700; font-family: monospace; }
.mbd-close { font-size: 20px; color: #999; cursor: pointer; padding: 4px 8px; }
.mbd-body { display: flex; flex-direction: column; gap: 8px; }
.mbd-row { display: flex; justify-content: space-between; font-size: 13px; padding: 6px 0; border-bottom: 1px solid #f5f5f5; }
.mbd-row span { color: #999; }
.mbd-row strong { font-weight: 600; }
.text-blue { color: #00a8ff; }
.text-red { color: #ef4444; }

/* Progress */
.mbd-progress { display: flex; align-items: center; gap: 0; margin: 12px 0; padding: 8px 0; }
.mbdp-step { display: flex; flex-direction: column; align-items: center; gap: 4px; font-size: 10px; color: #ccc; flex-shrink: 0; }
.mbdp-dot {
  width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-size: 10px; font-weight: 700; background: #f0f0f0; color: #ccc; border: 2px solid #e0e0e0;
}
.mbdp-step.done .mbdp-dot { background: #00a8ff; color: #fff; border-color: #00a8ff; }
.mbdp-step.done { color: #00a8ff; font-weight: 600; }
.mbdp-line { flex: 1; height: 2px; background: #e0e0e0; min-width: 20px; }
.mbdp-line.done { background: #00a8ff; }
.mbd-review { padding: 8px 12px; border-radius: 8px; font-size: 12px; font-weight: 500; }
.mbd-notes { font-size: 11px; color: #999; background: #fafafa; padding: 8px 12px; border-radius: 8px; }

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
.mcia-btn.feedback{background:#fef3c7;color:#d97706;border-color:#fde68a}

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

/* 刷新按钮 */
.mtk-refresh{width:100%;margin-top:10px;padding:10px;border-radius:8px;background:#f0f9ff;border:1px solid #bae6fd;color:#0369a1;font-size:13px;font-weight:600;cursor:pointer}

/* 品质反馈星级 */
.qfb-field{margin-bottom:12px}
.qfb-field label{font-size:12px;font-weight:600;color:#666;display:block;margin-bottom:4px}
.qfb-stars{display:flex;gap:4px}
.qfb-star{font-size:28px;cursor:pointer;transition:transform .15s;user-select:none}
.qfb-star:active{transform:scale(1.2)}

/* Tabbar */
.mb-tabbar {
  position: absolute; bottom: 0; left: 0; right: 0;
  display: flex; justify-content: space-around; align-items: center;
  background: #fff; border-top: 1px solid #f0f0f0;
  padding: 6px 0 8px; box-shadow: 0 -2px 10px rgba(0,0,0,0.04);
}
.mt-item {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  padding: 4px 16px; cursor: pointer;
}
.mt-icon { font-size: 20px; }
.mt-icon-create {
  width: 44px; height: 44px; border-radius: 50%;
  background: linear-gradient(135deg, #00a8ff, #7c3aed);
  color: #fff; display: flex; align-items: center; justify-content: center;
  font-size: 24px; font-weight: 700; margin-top: -16px;
  box-shadow: 0 4px 12px rgba(0,168,255,0.4);
}
.mt-label { font-size: 10px; color: #999; }
.mt-item.active .mt-label { color: #00a8ff; font-weight: 600; }

@media (min-width: 768px) {
  .mobile-wrap { border-radius: 16px; margin: 20px; min-height: auto; box-shadow: 0 4px 30px rgba(0,0,0,0.08); }
}
</style>
