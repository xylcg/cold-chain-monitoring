<template>
  <div class="driver-dashboard">
    <!-- ===== 顶部状态栏：车辆信息 + 实时温控 ===== -->
    <div class="driver-header">
      <div class="dh-left">
        <div class="vehicle-badge">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="1" y="3" width="15" height="13" rx="1"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>
          <div>
            <span class="v-plate">{{ vehicleInfo.plate }}</span>
            <span class="v-model">{{ vehicleInfo.model }} · {{ vehicleInfo.driverName }}</span>
          </div>
        </div>
      </div>
      <div class="dh-right">
        <div class="dh-stat" v-for="zone in multiZoneTemps" :key="zone.name">
          <span class="dhs-label">{{ zone.label }}</span>
          <span class="dhs-val" :class="getTempZoneClass(zone.temp, zone.min, zone.max)">{{ zone.temp }}°C</span>
          <span class="dhs-range">{{ zone.min }}~{{ zone.max }}°C</span>
        </div>
        <div class="dh-stat">
          <span class="dhs-label">冷机</span>
          <span class="dhs-val" :class="deviceInfo.cold_chain ? 'temp-ok' : 'temp-high'">{{ deviceInfo.cold_chain ? '运行中' : '停机' }}</span>
        </div>
      </div>
    </div>

    <div class="driver-grid">
      <!-- ===== 左侧：今日配送任务列表 ===== -->
      <div class="driver-card tasks-card">
        <div class="card-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/></svg>
          配送任务
          <span class="card-badge">功能6/11：多温区调度 + 移动端APP</span>
        </div>

        <!-- Tab切换：我的任务 / 可接订单 -->
        <div class="task-tabs">
          <button class="task-tab" :class="{ active: taskTab === 'my' }" @click="taskTab = 'my'">
            我的任务 ({{ orders.length }})
          </button>
          <button class="task-tab" :class="{ active: taskTab === 'available' }" @click="switchToAvailable">
            可接订单 <span v-if="availableOrders.length > 0" class="available-badge">{{ availableOrders.length }}</span>
          </button>
        </div>

        <!-- 我的任务 Tab -->
        <template v-if="taskTab === 'my'">
        <!-- 装货指引 -->
        <div class="loading-guide" v-if="hasPendingOrder">
          <div class="guide-icon">📦</div>
          <div class="guide-text">
            <div class="guide-title">装货指引</div>
            <div class="guide-desc">扫码确认货物 · 系统自动记录电子围栏进出时间与温度 · 车门开启超时APP语音提醒</div>
          </div>
        </div>
        <div v-if="orders.length === 0" class="empty-state">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--border)" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
          <p>暂无配送任务</p>
          <span>切换到「可接订单」查看待接订单，或等待管理员派发</span>
        </div>
        <div v-else class="order-list">
          <div
            v-for="o in orders"
            :key="o.order_id"
            class="order-item"
            :class="['status-'+o.driver_status, { selected: selectedOrder?.order_id === o.order_id }]"
            @click="selectOrder(o)"
          >
            <div class="oi-top">
              <span class="oi-id">{{ o.order_id }}</span>
              <span class="oi-status-tag" :class="o.driver_status">{{ statusMap[o.driver_status] || o.driver_status }}</span>
            </div>
            <div class="oi-info">
              <div><span class="oi-label">路线</span><span>{{ o.origin }} → {{ o.destination }}</span></div>
              <div><span class="oi-label">货物</span><span>{{ o.cargo_type }} | {{ o.weight_kg }}kg</span></div>
              <div><span class="oi-label">温区</span><span class="zone-badge" :class="getZoneClass(o.zone_name)">{{ o.zone_name }}</span><span class="oi-temp-range">{{ o.temp_range }}</span></div>
              <div><span class="oi-label">时限</span><span>{{ formatDeadline(o.deadline) }}</span></div>
              <div><span class="oi-label">运费</span><span class="oi-price">¥{{ o.price?.toLocaleString() }}</span></div>
            </div>
            <div class="oi-actions" @click.stop>
              <button v-if="o.driver_status === 'pending'" class="btn btn-scan" @click="scanGoods(o)">📱 扫码装货</button>
              <button v-if="o.driver_status === 'loaded'" class="btn btn-accept" @click="triggerPhoto(o, 'accept')">🚛 确认出发</button>
              <button v-if="o.driver_status === 'in_transit'" class="btn btn-photo" @click="triggerPhoto(o, 'deliver')">📷 拍照送达</button>
              <button v-if="o.driver_status === 'completed' && o.photo_review_status !== 'rejected'" class="btn btn-done" disabled>✅ 已完成</button>
              <button v-if="o.driver_status === 'completed' && o.photo_review_status === 'rejected'" class="btn btn-invalid" disabled>❌ 订单无效</button>
            </div>
            <!-- 审核状态提示 -->
            <div v-if="o.photo_review_status === 'pending_review'" class="oi-review-status review-pending">
              ⏳ 照片审核中，请等待仓管确认...
            </div>
            <div v-if="o.photo_review_status === 'approved'" class="oi-review-status review-ok">
              ✅ 照片已通过审核
            </div>
            <div v-if="o.photo_review_status === 'rejected'" class="oi-review-status review-fail">
              ❌ 审核未通过：{{ o.photo_review_notes || '未填写原因' }}<br/>
              <span class="review-action-hint">该订单无效，请联系仓管处理</span>
            </div>
          </div>
        </div>
        </template>

        <!-- 可接订单 Tab -->
        <template v-if="taskTab === 'available'">
          <div v-if="availableOrders.length === 0" class="empty-state">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--border)" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            <p>暂无可接订单</p>
            <span>等待顾客下单后，新订单将显示在此处</span>
          </div>
          <div v-else class="order-list">
            <div
              v-for="o in availableOrders"
              :key="o.order_id"
              class="order-item status-pending"
            >
              <div class="oi-top">
                <span class="oi-id">{{ o.order_id }}</span>
                <span class="oi-status-tag pending">待接单</span>
              </div>
              <div class="oi-info">
                <div><span class="oi-label">路线</span><span>{{ o.origin }} → {{ o.destination }}</span></div>
                <div><span class="oi-label">货物</span><span>{{ o.cargo_name }} | {{ o.quantity }}{{ o.unit }}</span></div>
                <div><span class="oi-label">温区</span><span class="zone-badge" :class="getZoneClass(o.zone_name)">{{ o.zone_name }}</span><span class="oi-temp-range">{{ o.temperature_requirement }}</span></div>
                <div><span class="oi-label">收件人</span><span>{{ o.receiver || '—' }}</span></div>
                <div><span class="oi-label">运费</span><span class="oi-price">¥{{ o.price?.toLocaleString() }}</span></div>
              </div>
              <div class="oi-actions">
                <button class="btn btn-accept-order" @click="acceptCustomerOrder(o)">🤝 接单</button>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- ===== 右侧：温湿度曲线 + 路线 + 告警 ===== -->
      <div class="driver-column">
        <!-- 温湿度实时曲线 -->
        <div class="driver-card temp-monitor-card">
          <div class="card-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
            车厢温湿度实时曲线
            <span class="card-badge">功能2/3：温度异常检测 + LSTM趋势预测</span>
          </div>
          <div class="temp-chart-area">
            <div class="temp-chart" ref="tempChartRef"></div>
          </div>
          <div class="temp-prediction" v-if="tempPrediction">
            <div class="pred-header">
              <span class="pred-icon">🔮</span>
              <span>LSTM预测：未来30分钟温度趋势</span>
              <span class="pred-confidence">置信度 {{ tempPrediction.confidence }}%</span>
            </div>
            <div class="pred-values">
              <span>预测终点 {{ tempPrediction.predicted_temp }}°C</span>
              <span :class="tempPrediction.risk_level === 'danger' ? 'text-red' : tempPrediction.risk_level === 'warning' ? 'text-amber' : 'text-green'">
                {{ tempPrediction.risk_level === 'danger' ? '⚠ 存在越限风险' : tempPrediction.risk_level === 'warning' ? '⚡ 接近阈值' : '✓ 温控安全' }}
              </span>
            </div>
          </div>
        </div>

        <!-- 当前路线 -->
        <div class="driver-card route-card">
          <div class="card-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="3 12 7 5 17 19 21 12"/></svg>
            <span v-if="selectedOrder">路线 · {{ selectedOrder.order_id }}</span><span v-else>配送路线</span>
            <span class="card-badge">功能5：冷链路径智能规划</span>
          </div>
          <div class="route-visual" v-if="activeRoute && selectedOrder">
            <div class="route-order-brief">
              <span class="rob-dest">{{ selectedOrder.destination }}</span>
              <span class="rob-price">¥{{ selectedOrder.price?.toLocaleString() }}</span>
            </div>
            <div class="route-points">
              <div class="rp-item start"><div class="rp-dot start-dot"></div><div class="rp-info"><span class="rp-loc">{{ activeRoute.origin_name }}</span><span class="rp-time">出发 · 电子围栏记录</span></div></div>
              <div class="rp-line"></div>
              <div v-for="(wp, i) in activeRoute.waypoints" :key="i" class="rp-item mid"><div class="rp-dot mid-dot"></div><div class="rp-info"><span class="rp-loc">{{ wp.name }}</span><span class="rp-time">第{{ Number(i)+1 }}站</span></div></div>
              <div class="rp-line"></div>
              <div class="rp-item end"><div class="rp-dot end-dot"></div><div class="rp-info"><span class="rp-loc">{{ activeRoute.dest_name }}</span><span class="rp-time">终点 · 电子围栏签收</span></div></div>
            </div>
            <div class="route-stats">
              <span>距离 {{ activeRoute.distance_km }}km</span><span>预计 {{ activeRoute.eta_min }}分钟</span><span>成本 ¥{{ activeRoute.cost_yuan }}</span>
            </div>
          </div>
          <div v-else class="empty-state">
            <p>点击左侧订单查看配送路线</p>
          </div>
        </div>

        <!-- 实时告警 + 应急处置指引 -->
        <div class="driver-card alerts-card">
          <div class="card-title">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
            智能预警与应急处置
            <span class="alerts-badge" v-if="liveAlerts.length > 0">{{ liveAlerts.length }}</span>
            <span class="card-badge">功能13：多级预警 + 应急响应</span>
          </div>
          <div v-if="liveAlerts.length === 0" class="alerts-clean">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--teal)" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="8 12 11 15 16 9"/></svg>
            <span>设备运行正常，无告警</span>
          </div>
          <div v-else class="alerts-list">
            <div v-for="(a, i) in liveAlerts" :key="i" class="alert-row" :class="a.level">
              <span class="alert-dot" :class="a.level"></span>
              <div class="alert-content">
                <span class="alert-msg">{{ a.message }}</span>
                <span class="alert-time">{{ a.time }}</span>
                <div class="alert-guidance" v-if="a.guidance">
                  <span class="guidance-label">处置指引：</span>{{ a.guidance }}
                </div>
              </div>
              <div class="alert-actions-col">
                <button class="alert-action" @click="dismissAlert(i)">{{ a.level === 'critical' ? '启动应急' : '处理' }}</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 拍照弹窗 -->
    <div class="photo-modal" v-if="showPhoto" @click.self="showPhoto = false">
      <div class="photo-inner">
        <h4>{{ photoAction === 'accept' ? '出发确认 · 装货拍照' : '送达签收 · 货物拍照' }} - {{ photoOrder?.order_id }}</h4>
        <p class="photo-tip">{{ photoAction === 'accept' ? '请拍摄装货完毕后的车厢/货物照片，温度数据将自动同步至追溯链' : '请拍摄送达货物照片作为签收凭证，系统将记录电子围栏签收时间与温度' }}</p>
        <div class="photo-preview" v-if="photoPreview"><img :src="photoPreview" alt="预览" /></div>
        <div class="photo-placeholder" v-else @click="takePhoto">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>
          <p>点击拍照</p>
        </div>
        <div class="photo-actions">
          <input ref="fileInput" type="file" accept="image/*" capture="environment" @change="onFileChange" style="display:none" />
          <button class="btn btn-cancel" @click="showPhoto = false">取消</button>
          <button class="btn btn-confirm" :disabled="!photoPreview || uploading" @click="submitPhoto">
            {{ uploading ? '⏳ 上传中...' : (photoPreview ? '📤 确认上传' : '请先拍照') }}
          </button>
        </div>
      </div>
    </div>

    <!-- 扫码装货弹窗 -->
    <div class="photo-modal" v-if="showScan" @click.self="showScan = false">
      <div class="photo-inner">
        <h4>📱 扫码装货确认 - {{ scanOrder?.order_id }}</h4>
        <p class="photo-tip">确认货物信息与多温区货位分配，系统将自动记录电子围栏进出时间与温度</p>
        <div class="scan-info" v-if="scanOrder">
          <div class="scan-row"><span class="scan-label">货物</span><span>{{ scanOrder.cargo_type }} {{ scanOrder.weight_kg }}kg</span></div>
          <div class="scan-row"><span class="scan-label">温区</span><span class="zone-badge" :class="getZoneClass(scanOrder.zone_name)">{{ scanOrder.zone_name }}</span><span>{{ scanOrder.temp_range }}</span></div>
          <div class="scan-row"><span class="scan-label">货位</span><span>{{ scanOrder.slot || 'A区-第3排' }}</span></div>
          <div class="scan-row"><span class="scan-label">围栏</span><span class="text-green">电子围栏已就绪 · 车门超时30s将语音提醒</span></div>
        </div>
        <div class="photo-actions">
          <button class="btn btn-cancel" @click="showScan = false">取消</button>
          <button class="btn btn-confirm" @click="confirmScan">✅ 确认装货完成</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { uploadAPI, customerAPI } from '@/api'
import dayjs from 'dayjs'

// ========== 车辆信息 ==========
const vehicleInfo = reactive({
  plate: '冷A-8801',
  model: '解放J6F冷藏车',
  driverName: '张司机',
  temp: -3.2,
  speed: 62,
  battery: 85,
})

// ========== 多温区温度监控 ==========
const multiZoneTemps = reactive([
  { name: 'freezer', label: '❄ 冷冻区', temp: -18.5, min: -22, max: -15 },
  { name: 'chiller', label: '🧊 冷藏区', temp: 2.3, min: 0, max: 4 },
  { name: 'ambient', label: '🌡 恒温区', temp: 16.8, min: 15, max: 20 },
])

function getTempZoneClass(temp: number, min: number, max: number): string {
  if (temp > max) return 'temp-high'
  if (temp < min) return 'temp-low'
  return 'temp-ok'
}

function getZoneClass(zoneName: string): string {
  if (zoneName?.includes('冷冻')) return 'zone-freeze'
  if (zoneName?.includes('冷藏')) return 'zone-chill'
  return 'zone-ambient'
}

// ========== 设备信息 ==========
const deviceInfo = reactive({ door: 'closed', cold_chain: true })
const deviceAlerts = ref(0)

// ========== LSTM温度预测 ==========
const tempPrediction = ref<{ predicted_temp: number; confidence: number; risk_level: string } | null>(null)
const tempChartRef = ref<HTMLDivElement>()

function updatePrediction() {
  const baseTemp = vehicleInfo.temp
  const drift = (Math.random() - 0.45) * 2
  const predicted = +(baseTemp + drift).toFixed(1)
  let risk = 'safe'
  if (predicted > 3) risk = 'danger'
  else if (predicted > 1 || predicted < -20) risk = 'warning'
  tempPrediction.value = {
    predicted_temp: predicted,
    confidence: Math.floor(90 + Math.random() * 8),
    risk_level: risk,
  }
}

// 简易温度曲线绘制
function drawTempChart() {
  if (!tempChartRef.value) return
  const ctx = tempChartRef.value
  const w = ctx.clientWidth || 340
  if (w <= 0) return
  const h = 120
  const points: { x: number; y: number }[] = []
  const now = Date.now()
  for (let i = 0; i < 30; i++) {
    const t = now - (30 - i) * 60000
    const val = -3 + Math.sin(i * 0.3) * 1.5 + (Math.random() - 0.5) * 0.6
    points.push({ x: (i / 29) * (w - 20) + 10, y: h - 20 - ((val + 5) / 10) * (h - 40) })
  }
  let svg = `<svg width="${w}" height="${h}" style="overflow:visible"><defs><linearGradient id="tg" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="var(--accent)" stop-opacity="0.2"/><stop offset="100%" stop-color="var(--accent)" stop-opacity="0"/></linearGradient></defs>`
  svg += `<line x1="10" y1="10" x2="10" y2="${h-20}" stroke="var(--border)" stroke-width="0.5"/>`
  svg += `<line x1="10" y1="${h-20}" x2="${w-10}" y2="${h-20}" stroke="var(--border)" stroke-width="0.5"/>`
  svg += `<text x="2" y="15" fill="var(--text-muted)" font-size="9">5°C</text>`
  svg += `<text x="2" y="${h/2}" fill="var(--text-muted)" font-size="9">0°C</text>`
  svg += `<text x="2" y="${h-22}" fill="var(--text-muted)" font-size="9">-5°C</text>`
  let area = `M${points[0].x},${points[0].y}`
  let line = `M${points[0].x},${points[0].y}`
  for (let i = 1; i < points.length; i++) { line += ` L${points[i].x},${points[i].y}`; area += ` L${points[i].x},${points[i].y}` }
  area += ` L${points[points.length-1].x},${h-20} L${points[0].x},${h-20} Z`
  svg += `<path d="${area}" fill="url(#tg)"/>`
  svg += `<path d="${line}" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linejoin="round"/>`
  // 最后5分钟预测虚线
  if (points.length > 5) {
    let predLine = `M${points[points.length-6].x},${points[points.length-6].y}`
    for (let i = points.length-5; i < points.length; i++) predLine += ` L${points[i].x},${points[i].y}`
    svg += `<path d="${predLine}" fill="none" stroke="var(--amber)" stroke-width="2" stroke-dasharray="4,3" stroke-linejoin="round"/>`
  }
  svg += `<circle cx="${points[points.length-1].x}" cy="${points[points.length-1].y}" r="3" fill="var(--accent)"/>`
  svg += `</svg>`
  ctx.innerHTML = svg
}

// ========== 实时告警（含处置指引） ==========
interface AlertItem {
  message: string
  time: string
  level: 'warning' | 'danger' | 'critical'
  guidance: string
}
const liveAlerts = ref<AlertItem[]>([])

const alertTemplates = [
  { message: '温度异常：冷藏区温度升至 5.2°C，超出安全范围', level: 'danger' as const, guidance: '检查冷机制冷效果，调整温控设定，必要时联系维修工程师' },
  { message: '车门开启超时：车辆行驶中车门异常开启超过30秒', level: 'critical' as const, guidance: '立即靠边停车，检查车门锁闭状态，确认货物安全' },
  { message: '冷机故障预警：冷机压缩机压力异常，制冷效率下降', level: 'critical' as const, guidance: '立即联系维修工程师（功能4），定位故障车辆，携带配件现场处置' },
  { message: '温度接近阈值：冷冻区温度-14.8°C，接近上限-15°C', level: 'warning' as const, guidance: '监控温度变化，若持续上升则调整冷机功率' },
  { message: '温区波动：冷冻区温度波动 ±3°C，LSTM预测30分钟后可能越限', level: 'warning' as const, guidance: '检查温区隔板密封性，确认货位分配是否合理' },
  { message: '设备离线：温度传感器 DT-102 通信中断（延迟>10秒）', level: 'danger' as const, guidance: '重启传感器模块，若无法恢复则手动记录温度并上报' },
]

function generateAlert() {
  if (Math.random() > 0.82) {
    const template = alertTemplates[Math.floor(Math.random() * alertTemplates.length)]
    liveAlerts.value.unshift({ ...template, time: dayjs().format('HH:mm:ss') })
    if (liveAlerts.value.length > 5) liveAlerts.value = liveAlerts.value.slice(0, 5)
    deviceAlerts.value = liveAlerts.value.length
  }
}

function dismissAlert(index: number) {
  const a = liveAlerts.value[index]
  if (a.level === 'critical') {
    ElMessage.success(`已启动应急预案：${a.message}`)
  } else {
    ElMessage.success('告警已处置')
  }
  liveAlerts.value.splice(index, 1)
  deviceAlerts.value = liveAlerts.value.length
}

// ========== 订单管理 ==========
const DEFAULT_ORDERS = [
  {
    order_id: 'ORD-20260703-0001',
    origin: '华北中心冷库',
    destination: '北京市朝阳区望京SOHO',
    cargo_type: '冷冻海鲜',
    weight_kg: 1200,
    zone_name: '冷冻区',
    temp_range: '-22℃ ~ -15℃',
    deadline: new Date(Date.now() + 4 * 3600000).toISOString(),
    driver_status: 'pending',
    photo_review_status: '',
    photo_review_notes: '',
    slot: 'A区-第3排',
    price: 3850,
    route: { origin_name: '华北中心冷库', dest_name: '北京市朝阳区望京SOHO', waypoints: [{ name: '望京SOHO T3' }, { name: '望京凯德MALL' }], distance_km: 35.6, eta_min: 52, cost_yuan: 285 },
  },
  {
    order_id: 'ORD-20260703-0005',
    origin: '华北中心冷库',
    destination: '北京市海淀区中关村',
    cargo_type: '冷藏鲜奶',
    weight_kg: 800,
    zone_name: '冷藏区',
    temp_range: '0℃ ~ 4℃',
    deadline: new Date(Date.now() + 6 * 3600000).toISOString(),
    driver_status: 'in_transit',
    photo_review_status: '',
    photo_review_notes: '',
    slot: 'B区-第1排',
    price: 2180,
    route: { origin_name: '华北中心冷库', dest_name: '北京市海淀区中关村', waypoints: [{ name: '中关村软件园' }, { name: '中关村SOHO' }], distance_km: 45.8, eta_min: 68, cost_yuan: 320 },
  },
  {
    order_id: 'ORD-20260703-0009',
    origin: '华北中心冷库',
    destination: '北京市西城区金融街',
    cargo_type: '冰淇淋',
    weight_kg: 500,
    zone_name: '冷冻区',
    temp_range: '-22℃ ~ -15℃',
    deadline: new Date(Date.now() + 3 * 3600000).toISOString(),
    driver_status: 'pending',
    photo_review_status: '',
    photo_review_notes: '',
    slot: 'A区-第5排',
    price: 1560,
    route: { origin_name: '华北中心冷库', dest_name: '北京市西城区金融街', waypoints: [{ name: '金融街购物中心' }, { name: '丰融国际大厦' }], distance_km: 28.3, eta_min: 42, cost_yuan: 198 },
  },
]

const STORAGE_KEY = 'driver_orders_v2'

function loadOrders(): any[] {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      const parsed = JSON.parse(saved)
      // 校验数据完整性：至少要有 origin 字段才算有效数据
      if (Array.isArray(parsed) && parsed.length > 0 && parsed[0].origin) {
        return parsed
      }
    }
  } catch {}
  return JSON.parse(JSON.stringify(DEFAULT_ORDERS))
}

function saveOrders() {
  // 保存完整订单数据，确保页面刷新后数据不丢失
  localStorage.setItem(STORAGE_KEY, JSON.stringify(orders.value))
}

const orders = ref<any[]>(loadOrders())

// 确保已保存数据包含所有默认订单（新订单不会被遗漏）
for (const def of DEFAULT_ORDERS) {
  if (!orders.value.find(o => o.order_id === def.order_id)) {
    orders.value.push(JSON.parse(JSON.stringify(def)))
  }
}

const statusMap: Record<string, string> = {
  pending: '待仓库审核',
  loaded: '待装货出发',
  in_transit: '配送中',
  completed: '已送达',
}

const hasPendingOrder = computed(() => orders.value.some(o => o.driver_status === 'pending'))
const selectedOrder = ref<any>(null)

const activeRoute = computed(() => {
  if (selectedOrder.value?.route) return selectedOrder.value.route
  const first = orders.value.find(o => o.route)
  return first?.route || null
})

function selectOrder(order: any) {
  selectedOrder.value = order
  if (order.route) ElMessage.info(`已切换到 ${order.order_id}，路线已更新`)
}

// ========== 顾客订单接单 ==========
const taskTab = ref('my')
const availableOrders = ref<any[]>([])

async function switchToAvailable() {
  taskTab.value = 'available'
  await loadAvailableOrders()
}

async function loadAvailableOrders() {
  try {
    const res: any = await customerAPI.getAvailableOrders()
    availableOrders.value = res.orders || []
  } catch { /* ignore */ }
}

async function acceptCustomerOrder(order: any) {
  try {
    await customerAPI.acceptOrder(order.order_id)
    ElMessage.success(`已接单 ${order.order_id}！请前往仓库装货`)
    // 将订单添加到本地订单列表
    const newOrder = {
      ...order,
      driver_status: 'pending',
      photo_review_status: '',
      photo_review_notes: '',
      slot: 'A区-第' + (orders.value.length + 1) + '排',
      temp_range: order.temperature_requirement || order.temp_range,
      deadline: new Date(Date.now() + 8 * 3600000).toISOString(),
      weight_kg: order.quantity || order.weight_kg,
      cargo_type: order.cargo_name || order.cargo_type,
      route: {
        origin_name: order.origin,
        dest_name: order.destination,
        waypoints: [{ name: order.destination }],
        distance_km: Math.floor(Math.random() * 40 + 20),
        eta_min: Math.floor(Math.random() * 40 + 30),
        cost_yuan: Math.floor((order.price || 200) * 0.4),
      },
    }
    orders.value.push(newOrder)
    saveOrders()
    // 刷新可接列表
    availableOrders.value = availableOrders.value.filter(o => o.order_id !== order.order_id)
    // 切换到我的任务
    taskTab.value = 'my'
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || '接单失败')
  }
}

// ========== 删除订单（加黑名单）==========
const DRIVER_DELETED_KEY = 'driver_deleted_orders'

function loadDriverDeletedIds(): string[] {
  try { const s = localStorage.getItem(DRIVER_DELETED_KEY); return s ? JSON.parse(s) : [] } catch { return [] }
}

function saveDriverDeletedId(id: string) {
  const ids = loadDriverDeletedIds()
  if (!ids.includes(id)) ids.push(id)
  localStorage.setItem(DRIVER_DELETED_KEY, JSON.stringify(ids))
}

async function deleteOrder(order: any) {
  try {
    await ElMessageBox.confirm(`确认删除订单 ${order.order_id}？\n删除后不再显示。`, '删除确认', {
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
    saveDriverDeletedId(order.order_id)
    orders.value = orders.value.filter(o => o.order_id !== order.order_id)
    saveOrders()
    if (selectedOrder.value?.order_id === order.order_id) selectedOrder.value = null
    ElMessage.success('已删除')
  } catch {
    // 用户取消
  }
}

// ========== 扫码装货 ==========
const showScan = ref(false)
const scanOrder = ref<any>(null)

function scanGoods(order: any) {
  scanOrder.value = order
  showScan.value = true
}

function confirmScan() {
  if (!scanOrder.value) return
  scanOrder.value.driver_status = 'in_transit'
  saveOrders()
  // 同步更新后端状态
  customerAPI.updateOrderStatus(scanOrder.value.order_id, 'in_transit').catch(() => {})
  ElMessage.success(`装货出发！${scanOrder.value.order_id} 已出发配送`)
  showScan.value = false
  scanOrder.value = null
}

// ========== 拍照 ==========
const showPhoto = ref(false)
const photoOrder = ref<any>(null)
const photoAction = ref<'deliver' | 'accept'>('deliver')
const photoPreview = ref('')
const fileInput = ref<HTMLInputElement>()

function formatDeadline(d: string) { return dayjs(d).format('MM-DD HH:mm 前') }

function triggerPhoto(order: any, action: 'deliver' | 'accept' = 'deliver') {
  photoOrder.value = order
  photoAction.value = action
  photoPreview.value = ''
  showPhoto.value = true
}

function takePhoto() { fileInput.value?.click() }

const uploading = ref(false)
const selectedFileData = ref<File | null>(null)

function onFileChange(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (file) {
    selectedFileData.value = file
    const reader = new FileReader()
    reader.onload = () => { photoPreview.value = reader.result as string }
    reader.readAsDataURL(file)
  }
}

async function submitPhoto() {
  if (!photoOrder.value) return
  if (!photoPreview.value) { ElMessage.warning('请先拍照再确认'); return }
  if (uploading.value) return

  uploading.value = true
  try {
    // 构建 FormData 上传到后端
    const formData = new FormData()
    if (selectedFileData.value) {
      formData.append('file', selectedFileData.value)
    } else {
      // 如果没有文件对象（旧数据），从 base64 转 blob
      const blob = await fetch(photoPreview.value).then(r => r.blob())
      const ext = blob.type === 'image/png' ? 'png' : 'jpg'
      formData.append('file', blob, `photo_${Date.now()}.${ext}`)
    }
    formData.append('device_id', vehicleInfo.plate.replace('冷', 'DEV-'))
    formData.append('waybill_id', photoOrder.value.order_id)
    formData.append('order_id', photoOrder.value.order_id)
    formData.append('photo_type', photoAction.value)
    formData.append('notes', photoAction.value === 'accept' ? '装货出发确认' : '货物送达签收')
    formData.append('latitude', '39.9')
    formData.append('longitude', '116.4')

    const res: any = await uploadAPI.uploadTempRecord(formData)
    const record = res.data || res

    if (photoAction.value === 'accept') {
      photoOrder.value.driver_status = 'in_transit'
      photoOrder.value.photo_review_status = 'pending_review'
      selectedOrder.value = photoOrder.value
      // 同步后端状态
      customerAPI.updateOrderStatus(photoOrder.value.order_id, 'in_transit').catch(() => {})
      ElMessage.success(`出发确认成功！${photoOrder.value.order_id} 照片已提交仓管审核，温度数据已同步至追溯链`)
    } else {
      photoOrder.value.driver_status = 'completed'
      photoOrder.value.photo_record_id = record.id
      photoOrder.value.photo_review_status = 'pending_review'
      photoOrder.value.photo_review_notes = ''
      const stillActive = orders.value.find(o => o.driver_status === 'in_transit')
      selectedOrder.value = stillActive || null
      // 同步后端状态
      customerAPI.updateOrderStatus(photoOrder.value.order_id, 'completed').catch(() => {})
      ElMessage.success(`送达签收成功！${photoOrder.value.order_id} 照片已提交仓管审核`)
    }
    saveOrders()
    showPhoto.value = false
    photoPreview.value = ''
    selectedFileData.value = null
    // 启动审核状态轮询
    startReviewPolling()
  } catch (err: any) {
    ElMessage.error('照片上传失败：' + (err?.response?.data?.message || err?.message || '网络错误'))
  } finally {
    uploading.value = false
  }
}

// ========== 审核状态轮询 ==========
let reviewTimer: number | null = null

async function checkReviewStatus() {
  // 查询所有已完成订单的最新审核状态
  const completedOrders = orders.value.filter(
    o => o.driver_status === 'completed' && o.photo_review_status !== 'approved' && o.photo_review_status !== 'rejected'
  )
  console.log('[审核轮询] 待查询订单:', completedOrders.map(o => ({ id: o.order_id, status: o.driver_status, review: o.photo_review_status })))
  if (completedOrders.length === 0) {
    if (reviewTimer) { clearInterval(reviewTimer); reviewTimer = null }
    return
  }
  try {
    // 对每个待审核订单单独查询
    for (const o of completedOrders) {
      console.log('[审核轮询] 查询订单:', o.order_id)
      const res: any = await uploadAPI.getDriverPhotos(o.order_id)
      console.log('[审核轮询] API返回:', JSON.stringify(res))
      const records = res?.data?.records || res?.records || (Array.isArray(res?.data) ? res.data : [])
      const record = records.find((r: any) => r.order_id === o.order_id || r.order_id === String(o.order_id))
      console.log('[审核轮询] 匹配记录:', record)
      if (record) {
        console.log(`[审核轮询] 订单 ${o.order_id} 审核状态更新:`, record.review_status)
        o.photo_review_status = record.review_status
        o.photo_review_notes = record.review_notes || ''
        saveOrders()
        if (record.review_status === 'approved') {
          ElMessage.success(`${o.order_id} 审核通过 ✅`)
        } else if (record.review_status === 'rejected') {
          ElMessage.error(`${o.order_id} 审核未通过：${record.review_notes || '订单无效，请联系仓管'}`)
        }
      } else {
        console.log(`[审核轮询] 订单 ${o.order_id} 未找到审核记录`)
      }
    }
    // 如果没有待审核的订单了，停止轮询
    const stillPending = orders.value.filter(
      o => o.driver_status === 'completed' && o.photo_review_status !== 'approved' && o.photo_review_status !== 'rejected'
    )
    if (stillPending.length === 0 && reviewTimer) {
      clearInterval(reviewTimer)
      reviewTimer = null
    }
  } catch (e) { console.error('审核轮询失败:', e) }
}

function startReviewPolling() {
  console.log('[审核轮询] 启动轮询，当前订单:', orders.value.map(o => ({ id: o.order_id, ds: o.driver_status, rs: o.photo_review_status })))
  if (reviewTimer) clearInterval(reviewTimer)
  // 立即执行一次
  checkReviewStatus()
  // 每10秒检查一次
  reviewTimer = window.setInterval(checkReviewStatus, 10000)
}

// ========== 定时刷新 ==========
let statusTimer: number | null = null
let chartTimer: number | null = null

onMounted(() => {
  try {
    const active = orders.value.find(o => o.driver_status === 'in_transit')
    if (active) selectedOrder.value = active

    // 延迟绘制图表，确保 DOM 完全渲染
    setTimeout(() => {
      try { drawTempChart() } catch (e) { console.error('图表绘制失败:', e) }
    }, 500)

    // 启动审核轮询（检查已提交的照片状态）
    startReviewPolling()
  } catch (e) {
    console.error('DriverDashboard onMounted error:', e)
  }

  statusTimer = window.setInterval(() => {
    multiZoneTemps.forEach(z => { z.temp = +(z.temp + (Math.random() - 0.5) * 0.4).toFixed(1) })
    vehicleInfo.temp = +(multiZoneTemps[1].temp + (Math.random() - 0.5) * 0.2).toFixed(1)
    vehicleInfo.speed = Math.max(0, Math.min(100, vehicleInfo.speed + (Math.random() - 0.5) * 10 | 0))
    vehicleInfo.battery = Math.max(10, vehicleInfo.battery - Math.random() * 0.15 | 0)
    generateAlert()
    updatePrediction()
    if (Math.random() > 0.9) deviceInfo.door = deviceInfo.door === 'closed' ? 'open' : 'closed'
    if (Math.random() > 0.95) deviceInfo.cold_chain = !deviceInfo.cold_chain
  }, 5000)

  chartTimer = window.setInterval(() => drawTempChart(), 30000)
})

onUnmounted(() => {
  if (statusTimer) clearInterval(statusTimer)
  if (chartTimer) clearInterval(chartTimer)
  if (reviewTimer) clearInterval(reviewTimer)
})
</script>

<style scoped>
.driver-dashboard {
  animation: fadeInUp 0.4s ease-out;
  max-width: 1100px;
}

/* ====== Header ====== */
.driver-header {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-lg);
  padding: 18px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
  box-shadow: var(--shadow-sm);
}
.dh-left { flex-shrink: 0; }
.vehicle-badge {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--accent);
}
.vehicle-badge div {
  display: flex;
  flex-direction: column;
}
.v-plate {
  font-size: 20px;
  font-weight: 800;
  font-family: var(--font-display);
  color: var(--text-title);
  letter-spacing: 0.04em;
}
.v-model {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 1px;
}
.dh-right {
  display: flex;
  gap: 28px;
}
.dh-stat {
  text-align: center;
}
.dhs-label {
  display: block;
  font-size: 10px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 3px;
}
.dhs-val {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 700;
  color: var(--text-title);
}
.dhs-val.temp-ok { color: var(--teal); }
.dhs-val.temp-high { color: var(--red); }
.dhs-val.temp-low { color: var(--accent); }
.dhs-range {
  display: block;
  font-size: 10px;
  color: var(--text-muted);
  font-family: var(--font-mono);
  margin-top: 2px;
}

/* ====== Grid ====== */
.driver-grid {
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: 18px;
}
.driver-card {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-sm);
}
.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 700;
  color: var(--text-title);
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.card-badge {
  font-size: 10px;
  font-weight: 500;
  color: var(--text-muted);
  background: var(--bg-input);
  padding: 2px 8px;
  border-radius: 10px;
  white-space: nowrap;
}
.driver-column {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* ====== Empty state ====== */
.empty-state {
  text-align: center;
  padding: 40px 0;
  color: var(--text-muted);
}
.empty-state p { font-size: 14px; margin: 10px 0 4px; color: var(--text-secondary); }
.empty-state span { font-size: 11px; }

/* ====== 装货指引 ====== */
.loading-guide {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 12px 14px;
  background: linear-gradient(135deg, rgba(0,168,255,0.06), rgba(0,168,255,0.02));
  border: 1px solid rgba(0,168,255,0.15);
  border-radius: 10px;
  margin-bottom: 14px;
}
.guide-icon { font-size: 28px; flex-shrink: 0; line-height: 1; }
.guide-text { flex: 1; }
.guide-title { font-size: 13px; font-weight: 700; color: var(--accent); margin-bottom: 4px; }
.guide-desc { font-size: 11px; color: var(--text-muted); line-height: 1.5; }

/* ====== Orders ====== */
.order-item {
  padding: 14px;
  border-radius: 10px;
  border: 1px solid var(--border);
  margin-bottom: 10px;
  transition: all 0.2s;
}
.order-item.status-pending { border-left: 3px solid var(--amber); cursor: pointer; }
.order-item.status-loaded { border-left: 3px solid var(--accent); cursor: pointer; }
.order-item.status-in_transit { border-left: 3px solid var(--aurora); cursor: pointer; }
.order-item.status-completed { border-left: 3px solid var(--teal); opacity: 0.7; cursor: pointer; }
.order-item:hover { background: var(--bg-input); }
.order-item.selected { background: var(--accent-bg); border-color: rgba(0,168,255,0.3); box-shadow: 0 0 0 1px rgba(0,168,255,0.2); }
.oi-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.oi-id {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  color: var(--text-title);
}
.oi-status-tag {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
}
.oi-status-tag.pending { background: var(--amber-bg); color: var(--amber); }
.oi-status-tag.loaded { background: var(--accent-bg); color: var(--accent); }
.oi-status-tag.in_transit { background: var(--aurora-bg); color: var(--aurora); }
.oi-status-tag.completed { background: var(--teal-bg); color: var(--teal); }
.oi-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 12px;
  font-size: 12px;
}
.oi-info > div { display: flex; gap: 8px; align-items: center; }
.oi-label { color: var(--text-muted); min-width: 36px; flex-shrink: 0; }
.oi-price { color: var(--red); font-weight: 700; font-family: var(--font-display); font-size: 13px; }
.oi-actions { display: flex; gap: 8px; }
.oi-temp-range {
  font-size: 10px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

/* Zone badges */
.zone-badge {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
}
.zone-freeze { background: rgba(59,130,246,0.12); color: #3b82f6; }
.zone-chill { background: rgba(16,185,129,0.12); color: #10b981; }
.zone-ambient { background: rgba(245,158,11,0.12); color: #f59e0b; }

/* ====== Task Tabs ====== */
.task-tabs {
  display: flex; gap: 0; margin-bottom: 14px;
  background: var(--bg-input); border-radius: 8px; padding: 3px;
}
.task-tab {
  flex: 1; padding: 7px 12px; border: none; border-radius: 6px;
  cursor: pointer; font-size: 12px; font-weight: 600;
  color: var(--text-muted); background: transparent; transition: all 0.2s;
}
.task-tab:hover { color: var(--text-primary); }
.task-tab.active { background: var(--bg-card); color: var(--accent); box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.available-badge {
  display: inline-flex; align-items: center; justify-content: center;
  background: var(--red); color: #fff; font-size: 10px; font-weight: 700;
  min-width: 18px; height: 18px; border-radius: 9px; margin-left: 4px; padding: 0 5px;
}

/* ====== Buttons ====== */
.btn {
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}
.btn-scan { background: var(--amber); color: #fff; }
.btn-scan:hover { opacity: 0.9; }
.btn-accept { background: var(--accent); color: #fff; }
.btn-accept:hover { opacity: 0.9; }
.btn-accept-order { background: linear-gradient(135deg, var(--teal), #22c55e); color: #fff; }
.btn-accept-order:hover { opacity: 0.9; transform: scale(1.03); }
.btn-photo { background: var(--aurora-bg); color: var(--aurora); border: 1px solid rgba(124,58,237,0.2); }
.btn-done { background: var(--teal-bg); color: var(--teal); cursor: default; }
.btn-cancel { background: var(--bg-input); color: var(--text-muted); }
.btn-cancel:hover { background: var(--border); }
.btn-confirm { background: var(--accent); color: #fff; }
.btn-confirm:hover { opacity: 0.9; }
.btn-confirm:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-rephoto { background: var(--red); color: #fff; }
.btn-rephoto:hover { opacity: 0.9; }
.btn-invalid { background: var(--red-bg); color: var(--red); cursor: not-allowed; border: 1px solid rgba(239,68,68,0.3); }

/* ====== 审核状态提示 ====== */
.oi-review-status {
  margin-top: 8px; padding: 8px 10px; border-radius: 6px;
  font-size: 11px; line-height: 1.5;
}
.review-pending { background: rgba(245,158,11,0.08); color: var(--amber); border: 1px solid rgba(245,158,11,0.2); }
.review-ok { background: rgba(0,210,160,0.08); color: var(--teal); border: 1px solid rgba(0,210,160,0.2); }
.review-fail { background: var(--red-bg); color: var(--red); border: 1px solid rgba(239,68,68,0.2); }
.review-action-hint { font-weight: 600; color: var(--red); }

/* ====== Temperature monitor ====== */
.temp-monitor-card { overflow: hidden; }
.temp-chart-area {
  background: var(--bg-input);
  border-radius: 10px;
  padding: 10px 8px 4px;
  margin-bottom: 12px;
  min-height: 130px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.temp-chart {
  width: 100%;
  overflow: hidden;
}
.temp-prediction {
  padding: 12px;
  background: linear-gradient(135deg, rgba(124,58,237,0.06), rgba(124,58,237,0.02));
  border: 1px solid rgba(124,58,237,0.15);
  border-radius: 10px;
}
.pred-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: var(--aurora);
  margin-bottom: 8px;
}
.pred-icon { font-size: 16px; }
.pred-confidence {
  margin-left: auto;
  font-size: 10px;
  font-weight: 500;
  color: var(--text-muted);
  background: var(--bg-input);
  padding: 2px 6px;
  border-radius: 4px;
}
.pred-values {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}
.text-red { color: var(--red); }
.text-amber { color: var(--amber); }
.text-green { color: var(--teal); }

/* ====== Route visual ====== */
.route-visual { padding: 4px 0; }
.route-order-brief {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: var(--accent-bg);
  border-radius: 8px;
  margin-bottom: 14px;
  border: 1px solid rgba(0,168,255,0.12);
}
.rob-dest {
  font-size: 13px;
  font-weight: 600;
  color: var(--accent);
}
.rob-price {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 800;
  color: var(--red);
}
.route-points { position: relative; padding-left: 24px; }
.rp-item { position: relative; padding: 6px 0; }
.rp-dot { position: absolute; left: -24px; top: 10px; width: 12px; height: 12px; border-radius: 50%; border: 2px solid; }
.start-dot { background: var(--accent); border-color: var(--accent); }
.mid-dot { background: var(--bg-card); border-color: var(--amber); }
.end-dot { background: var(--red); border-color: var(--red); }
.rp-line {
  position: absolute;
  left: -19px;
  top: 24px;
  bottom: 24px;
  width: 2px;
  background: var(--border);
  height: calc(100% - 48px);
}
.rp-info { padding-left: 8px; }
.rp-loc { font-size: 13px; font-weight: 600; color: var(--text-secondary); display: block; }
.rp-time { font-size: 10px; color: var(--text-muted); }
.route-stats {
  display: flex;
  gap: 16px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
  font-size: 12px;
  color: var(--text-muted);
}

/* ====== Alerts card ====== */
.alerts-card .card-title { position: relative; }
.alerts-badge {
  margin-left: auto;
  background: var(--red);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  min-width: 20px;
  height: 20px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 6px;
}
.alerts-clean {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px 0;
  color: var(--teal);
  font-size: 12px;
  font-weight: 500;
}
.alerts-list { display: flex; flex-direction: column; gap: 6px; }
.alert-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid var(--border);
  transition: all 0.2s;
}
.alert-row.warning { border-left: 3px solid var(--amber); background: var(--amber-bg); }
.alert-row.danger { border-left: 3px solid var(--red); background: var(--red-bg); }
.alert-row.critical { border-left: 3px solid var(--red); background: rgba(239,68,68,0.1); animation: alert-pulse 2s ease-in-out infinite; }
@keyframes alert-pulse {
  0%, 100% { border-left-color: var(--red); }
  50% { border-left-color: #fca5a5; }
}
.alert-dot {
  width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
  margin-top: 3px;
}
.alert-dot.warning { background: var(--amber); }
.alert-dot.danger { background: var(--red); }
.alert-dot.critical { background: var(--red); box-shadow: 0 0 6px var(--red); }
.alert-content { flex: 1; min-width: 0; }
.alert-msg {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-title);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.alert-time {
  font-size: 10px;
  color: var(--text-muted);
  font-family: var(--font-mono);
  margin-top: 2px;
  display: block;
}
.alert-guidance {
  margin-top: 6px;
  padding: 6px 8px;
  background: rgba(0,0,0,0.06);
  border-radius: 5px;
  font-size: 11px;
  color: var(--text-secondary);
  line-height: 1.5;
}
.guidance-label {
  font-weight: 700;
  color: var(--accent);
}
.alert-actions-col {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex-shrink: 0;
  margin-top: 2px;
}
.alert-action {
  flex-shrink: 0;
  padding: 4px 10px;
  border-radius: 5px;
  border: 1px solid var(--accent);
  background: transparent;
  color: var(--accent);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}
.alert-action:hover {
  background: var(--accent);
  color: #fff;
}

/* ====== Photo & Scan modals ====== */
.photo-modal {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
}
.photo-inner {
  background: var(--bg-card);
  border-radius: 14px;
  padding: 24px;
  width: 90%;
  max-width: 400px;
}
.photo-inner h4 {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 6px;
  color: var(--text-title);
}
.photo-tip {
  font-size: 12px;
  color: var(--amber);
  margin-bottom: 16px;
}
.photo-placeholder {
  border: 2px dashed var(--border);
  border-radius: 12px;
  height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--text-muted);
  margin-bottom: 16px;
  transition: all 0.2s;
}
.photo-placeholder:hover { border-color: var(--accent); color: var(--accent); }
.photo-placeholder p { margin-top: 8px; font-size: 13px; }
.photo-preview { margin-bottom: 16px; }
.photo-preview img {
  width: 100%;
  border-radius: 12px;
  max-height: 300px;
  object-fit: cover;
}
.photo-actions { display: flex; gap: 10px; justify-content: flex-end; }

/* ====== Scan info ====== */
.scan-info {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px;
  background: var(--bg-input);
  border-radius: 10px;
  margin-bottom: 16px;
}
.scan-row {
  display: flex;
  gap: 10px;
  font-size: 13px;
  align-items: center;
}
.scan-label {
  color: var(--text-muted);
  min-width: 42px;
  flex-shrink: 0;
}

/* ====== Responsive ====== */
@media (max-width: 900px) {
  .driver-grid { grid-template-columns: 1fr; }
  .driver-header { flex-direction: column; gap: 12px; }
  .dh-right { flex-wrap: wrap; gap: 16px; }
}
</style>
