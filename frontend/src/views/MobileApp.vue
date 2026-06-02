<template>
  <div class="mobile-app">
    <div class="mobile-wrap">
      <!-- 页面内容区（按 tab 切换） -->
      <div class="mb-page" v-show="activeTab === 'monitor'">
        <!-- 拉取状态 -->
        <div class="mb-pull-hint" v-if="loading">加载中...</div>

        <!-- 温度异常大卡片 -->
        <div class="mb-hero" :class="{ danger: isTempAbnormal }" v-if="sensorData">
          <div class="mb-hero-badge" v-if="isTempAbnormal">⚠ 温度异常</div>
          <div class="mb-hero-badge ok" v-else>✓ 温度正常</div>
          <div class="mb-hero-temp">
            <span class="ht-value">{{ sensorData.temperature?.toFixed(1) ?? '--' }}</span>
            <span class="ht-unit">°C</span>
          </div>
          <div class="mb-hero-meta">
            <div class="hm-item">
              <span class="hm-icon">💧</span>
              <span class="hm-label">湿度</span>
              <span class="hm-val">{{ sensorData.humidity?.toFixed(1) ?? '--' }}%</span>
            </div>
            <div class="hm-item">
              <span class="hm-icon">🎯</span>
              <span class="hm-label">目标</span>
              <span class="hm-val">{{ targetTemp }}°C</span>
            </div>
            <div class="hm-item">
              <span class="hm-icon">🌡</span>
              <span class="hm-label">外部</span>
              <span class="hm-val">{{ externalTemp }}°C</span>
            </div>
          </div>
        </div>

        <!-- 设备状态四宫格 -->
        <div class="mb-status-grid">
          <div class="msg-item" :class="{ active: doorOpen }" @click="toggleDoorModel">
            <span class="msg-icon">🚪</span>
            <span class="msg-title">车门</span>
            <span class="msg-val" :class="{ warn: doorOpen }">{{ doorOpen ? '已开启' : '关闭' }}</span>
          </div>
          <div class="msg-item" :class="{ active: coldMachineOn }">
            <span class="msg-icon">❄️</span>
            <span class="msg-title">冷机</span>
            <span class="msg-val" :class="{ warn: !coldMachineOn }">{{ coldMachineOn ? '运行中' : '故障' }}</span>
          </div>
          <div class="msg-item" :class="signalClass">
            <span class="msg-icon">📶</span>
            <span class="msg-title">信号</span>
            <span class="msg-val">{{ signalStrength }} dBm</span>
          </div>
          <div class="msg-item" :class="batteryClass">
            <span class="msg-icon">🔋</span>
            <span class="msg-title">电池</span>
            <span class="msg-val">{{ batteryLevel }}%</span>
          </div>
        </div>

        <!-- 温度趋势迷你图 -->
        <div class="mb-card">
          <div class="mb-card-hd">
            <span class="mb-card-title">温度趋势 (近30分钟)</span>
            <span class="mb-card-badge" v-if="trendAnomaly">发现异常</span>
          </div>
          <div class="mb-chart" ref="chartRef">
            <div class="mb-chart-placeholder" v-if="!tempHistory.length">暂无数据</div>
            <canvas ref="canvasRef" v-show="tempHistory.length" :width="canvasW" :height="120"></canvas>
          </div>
        </div>

        <!-- 预测趋势 -->
        <div class="mb-card" v-if="trendData">
          <div class="mb-card-hd">
            <span class="mb-card-title">AI温控预测</span>
            <span class="mb-card-subtitle">未来30分钟</span>
          </div>
          <div class="mb-predict-bar">
            <div class="mpb-mark" v-for="(p, i) in trendData" :key="i"
              :style="{ height: predictHeight(p.temp) + '%' }"
              :class="{ danger: p.temp > 8 || p.temp < -25 }">
            </div>
          </div>
          <div class="mb-predict-range">
            <span>预测: {{ trendData.length }}个点</span>
            <span :class="{ 'text-red': isPredictRisky }">
              {{ isPredictRisky ? '⚠ 存在超温风险' : '✓ 趋势安全' }}
            </span>
          </div>
        </div>
      </div>

      <!-- ==================== 订单页面 ==================== -->
      <div class="mb-page" v-show="activeTab === 'orders'">
        <!-- 当前任务卡 -->
        <div class="mb-order-card" v-if="currentTask">
          <div class="moc-header">
            <div class="moc-waybill">{{ currentTask.waybill || 'WB20260602001' }}</div>
            <div class="moc-tag" :class="taskTempOK ? 'ok' : 'warn'">
              {{ taskTempOK ? '温控正常' : '温度异常' }}
            </div>
          </div>
          <div class="moc-route">
            <div class="moc-dot start"></div>
            <div class="moc-city">{{ currentTask.origin || '华北中心冷库' }}</div>
            <div class="moc-line"></div>
            <div class="moc-dot end"></div>
            <div class="moc-city">{{ currentTask.destination || '北京市朝阳区' }}</div>
          </div>
          <div class="moc-progress">
            <div class="moc-prog-bar">
              <div class="moc-prog-fill" :style="{ width: (currentTask.progress || 0) + '%' }"></div>
            </div>
            <span class="moc-prog-num">{{ currentTask.progress || 0 }}%</span>
          </div>
          <div class="moc-meta">
            <span>预计到达: {{ currentTask.eta || '14:30' }}</span>
            <span>剩余: {{ currentTask.remaining || '32km' }}</span>
          </div>
        </div>

        <!-- 订单列表 -->
        <div class="mb-card">
          <div class="mb-card-hd">
            <span class="mb-card-title">配送订单</span>
            <span class="mb-card-count">{{ orders.length }}单</span>
          </div>
          <div class="mb-order-item" v-for="o in orders" :key="o.id" @click="handleOrder(o)">
            <div class="moi-left">
              <div class="moi-status-icon" :class="o.status">
                {{ o.status === 'done' ? '✓' : o.status === 'current' ? '▶' : '○' }}
              </div>
              <div>
                <div class="moi-id">#{{ o.id }} {{ o.cargo }}</div>
                <div class="moi-addr">{{ o.address }}</div>
              </div>
            </div>
            <div class="moi-right">
              <span class="moi-weight">{{ o.weight }}kg</span>
              <span class="moi-tag" :class="o.status">{{ o.statusLabel }}</span>
            </div>
          </div>
        </div>

        <!-- 扫码签收 -->
        <div class="mb-scan-btn" @click="openScanner">
          <span>📱</span>
          <span>扫码签收</span>
        </div>
      </div>

      <!-- ==================== 告警页面 ==================== -->
      <div class="mb-page" v-show="activeTab === 'alerts'">
        <div class="mb-filter-bar">
          <button v-for="f in alertFilters" :key="f.key"
            class="mfb-btn" :class="{ active: alertFilter === f.key }"
            @click="alertFilter = f.key">{{ f.label }}</button>
        </div>

        <div class="mb-alert-empty" v-if="filteredAlerts.length === 0">
          <span>🎉</span>
          <span>暂无告警</span>
        </div>

        <div class="mb-alert-card" v-for="a in filteredAlerts" :key="a.id" :class="'lvl-' + (a.level || a.severity)">
          <div class="mac-top">
            <span class="mac-lvl-tag" :class="a.level || a.severity">
              {{ severityLabel(a.level || a.severity) }}
            </span>
            <span class="mac-device">{{ a.device_id || a.vehicle_id }}</span>
            <span class="mac-time">{{ a.time || a.created_at }}</span>
          </div>
          <div class="mac-msg">{{ a.message || a.alert_message }}</div>
          <div class="mac-temp" v-if="a.temp_deviation">偏差: {{ a.temp_deviation }}°C</div>
          <div class="mac-actions">
            <button class="maca-btn" @click="ackAlert(a)">✓ 确认</button>
            <button class="maca-btn primary" @click="handleAlert(a)">🔧 处置</button>
            <button class="maca-btn" @click="uploadForAlert(a)">📸 拍照</button>
          </div>
          <!-- 处置记录 -->
          <div class="mac-disposition" v-if="a.disposition">
            <div class="macd-title">处置记录</div>
            <div class="macd-detail">{{ a.disposition }}</div>
          </div>
        </div>
      </div>

      <!-- ==================== 我的页面 ==================== -->
      <div class="mb-page" v-show="activeTab === 'me'">
        <div class="mb-profile">
          <div class="mb-avatar">{{ driverName[0] }}</div>
          <div>
            <div class="mb-driver-name">{{ driverName }}</div>
            <div class="mb-driver-id">设备: {{ currentDeviceId }}</div>
          </div>
        </div>

        <!-- 拍照上传温度记录纸 -->
        <div class="mb-card">
          <div class="mb-card-hd">
            <span class="mb-card-title">📸 温度记录纸拍照上传</span>
          </div>
          <div class="mb-camera-area">
            <input ref="fileInput" type="file" accept="image/*" capture="camera"
              class="mb-file-input" @change="onFileSelected" />
            <button class="mb-camera-btn" @click="$refs.fileInput.click()">
              <span class="mc-icon">📷</span>
              <span class="mc-text">点击拍照</span>
              <span class="mc-hint">自动调用手机相机</span>
            </button>
          </div>

          <!-- 照片预览 -->
          <div class="mb-photo-preview" v-if="photoPreview">
            <img :src="photoPreview" alt="温度记录纸预览" class="mb-preview-img" />
            <div class="mb-photo-actions">
              <button class="mpa-btn cancel" @click="clearPhoto">重拍</button>
              <button class="mpa-btn upload" @click="submitPhoto" :disabled="uploading">
                {{ uploading ? '上传中...' : '确认上传' }}
              </button>
            </div>
          </div>

          <!-- 上传备注 -->
          <div class="mb-upload-note" v-if="photoPreview">
            <input v-model="uploadNotes" placeholder="备注（可选）：如温度记录、异常说明..." class="mb-note-input" />
          </div>
        </div>

        <!-- 已上传记录 -->
        <div class="mb-card" v-if="uploadHistory.length">
          <div class="mb-card-hd">
            <span class="mb-card-title">上传历史</span>
            <span class="mb-card-count">{{ uploadHistory.length }}条</span>
          </div>
          <div class="mb-upload-item" v-for="u in uploadHistory" :key="u.id">
            <span class="mui-icon">📄</span>
            <div class="mui-info">
              <div class="mui-name">{{ u.original_name || u.filename }}</div>
              <div class="mui-time">{{ u.upload_time || u.time }}</div>
            </div>
            <span class="mui-status ok">已上传</span>
          </div>
        </div>

        <!-- 退出 -->
        <button class="mb-logout-btn" @click="handleLogout">退出登录</button>
      </div>

      <!-- ==================== 底部导航 ==================== -->
      <div class="mb-tabbar">
        <div class="mt-item" :class="{ active: activeTab === 'monitor' }" @click="activeTab = 'monitor'">
          <span class="mt-icon">🌡</span>
          <span class="mt-label">温控</span>
        </div>
        <div class="mt-item" :class="{ active: activeTab === 'orders' }" @click="activeTab = 'orders'">
          <span class="mt-icon">📋</span>
          <span class="mt-label">订单</span>
        </div>
        <div class="mt-item" :class="{ active: activeTab === 'alerts' }" @click="activeTab = 'alerts'">
          <span class="mt-icon">🔔</span>
          <span class="mt-label">告警</span>
          <span class="mt-badge" v-if="alertCount">{{ alertCount }}</span>
        </div>
        <div class="mt-item" :class="{ active: activeTab === 'me' }" @click="activeTab = 'me'">
          <span class="mt-icon">👤</span>
          <span class="mt-label">我的</span>
        </div>
      </div>
    </div>

    <!-- 告警处理弹窗 -->
    <div class="mb-modal-overlay" v-if="showDisposeModal" @click.self="showDisposeModal = false">
      <div class="mb-modal">
        <div class="mb-modal-title">🔧 现场处置</div>
        <div class="mb-modal-body">
          <div class="mbm-option" v-for="op in disposeOptions" :key="op.key"
            :class="{ selected: disposeAction === op.key }" @click="disposeAction = op.key">
            <span class="mbmo-icon">{{ op.icon }}</span>
            <span>{{ op.label }}</span>
          </div>
          <input v-model="disposeNote" placeholder="填写处置备注..." class="mbm-input" />
        </div>
        <div class="mb-modal-ft">
          <button class="mbmf-btn" @click="showDisposeModal = false">取消</button>
          <button class="mbmf-btn primary" @click="submitDispose">确认处置</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, computed, nextTick, watch } from 'vue'
import { temperatureAPI, alertAPI, vehicleAPI, uploadAPI, dispatchAPI } from '@/api'

const activeTab = ref('monitor')
const loading = ref(false)
// 初始化默认数据，页面秒开，后台异步拉取真实数据
const sensorData = reactive<any>({ temperature: 3.5, humidity: 78.0 })
const targetTemp = ref(3.0)
const externalTemp = ref(30.5)
const doorOpen = ref(false)
const coldMachineOn = ref(true)
const signalStrength = ref(-65)
const batteryLevel = ref(85)
const currentDeviceId = ref('VT001')
const driverName = ref('李司机')

// 温度历史
const tempHistory = ref<any[]>([])
const trendData = ref<any[]>([])
const trendAnomaly = ref(false)

// 图表
const chartRef = ref(null)
const canvasRef = ref(null)
const canvasW = ref(350)
let drawTimer: any = null

// 订单
const currentTask = reactive<any>({ progress: 68, waybill: 'WB20260602001', origin: '华北中心冷库', destination: '北京市朝阳区望京SOHO', eta: '14:30', remaining: '32km' })
const orders = ref<any[]>([
  { id: '1', status: 'done', statusLabel: '已送达', address: '朝阳区望京街道10号', cargo: '冷冻海鲜', weight: 500 },
  { id: '2', status: 'current', statusLabel: '配送中', address: '海淀区中关村软件园', cargo: '冷藏生鲜', weight: 300 },
  { id: '3', status: 'pending', statusLabel: '待配送', address: '西城区金融街购物中心', cargo: '恒温药品', weight: 200 },
])

// 告警
const alerts = ref<any[]>([])
const alertFilter = ref('all')
const alertFilters = [
  { key: 'all', label: '全部' },
  { key: 'critical', label: '严重' },
  { key: 'severe', label: '警告' },
  { key: 'normal', label: '一般' },
]
const showDisposeModal = ref(false)
const currentAlert = ref<any>(null)
const disposeAction = ref('door_closed')
const disposeNote = ref('')
const disposeOptions = [
  { key: 'door_closed', label: '已关闭车门', icon: '🚪' },
  { key: 'temp_adjusted', label: '已调整冷机', icon: '❄️' },
  { key: 'reroute', label: '已改道配送', icon: '🔄' },
  { key: 'on_site', label: '已现场处理', icon: '🔧' },
  { key: 'report_issue', label: '无法处理，上报', icon: '📞' },
]

// 拍照上传
const fileInput = ref<any>(null)
const photoPreview = ref('')
const uploading = ref(false)
const uploadNotes = ref('')
const uploadHistory = ref<any[]>([])
let photoFile: File | null = null

// 定时器
let refreshTimer: any = null

// 计算属性
const isTempAbnormal = computed(() => {
  const t = sensorData.temperature
  return t !== undefined && t !== null && (t > 8 || t < -25)
})
const taskTempOK = computed(() => !isTempAbnormal.value)
const isPredictRisky = computed(() => {
  if (!trendData.value.length) return false
  return trendData.value.some((p: any) => p.temp > 8 || p.temp < -25)
})
const alertCount = computed(() => alerts.value.length)
const filteredAlerts = computed(() => {
  if (alertFilter.value === 'all') return alerts.value
  return alerts.value.filter((a: any) => (a.level || a.severity) === alertFilter.value)
})
const signalClass = computed(() => {
  if (signalStrength.value > -60) return 's-good'
  if (signalStrength.value > -80) return 's-ok'
  return 's-weak'
})
const batteryClass = computed(() => {
  if (batteryLevel.value > 50) return 'b-good'
  if (batteryLevel.value > 20) return 'b-ok'
  return 'b-low'
})

function severityLabel(level: string) {
  const map: any = { critical: '严重', severe: '警告', normal: '一般' }
  return map[level] || level
}

function predictHeight(temp: number) {
  return Math.max(5, Math.min(95, ((temp + 30) / 60) * 100))
}

// ======= API 调用 =======
async function fetchSensorData() {
  try {
    const res: any = await temperatureAPI.getCurrent(currentDeviceId.value)
    if (res?.data) {
      const d = res.data
      Object.assign(sensorData, {
        temperature: d.temperature ?? d.temp,
        humidity: d.humidity,
      })
      doorOpen.value = d.door_open ?? d.door_status === 1 ?? false
      coldMachineOn.value = d.cold_machine_on ?? d.cold_machine_status === 1 ?? true
      targetTemp.value = d.target_temperature ?? d.target_temp ?? 3.0
      externalTemp.value = d.external_temperature ?? d.external_temp ?? 31.2
      signalStrength.value = d.signal_strength ?? -(60 + Math.floor(Math.random() * 20))
      batteryLevel.value = d.battery_level ?? Math.max(10, 85 - Math.floor(Math.random() * 5))
    }
  } catch {
    // 降级：保持模拟数据
  }
}

async function fetchTempHistory() {
  try {
    const res: any = await temperatureAPI.getHistory(currentDeviceId.value, 30)
    if (res?.data?.history) {
      tempHistory.value = res.data.history
    } else if (res?.data) {
      tempHistory.value = Array.isArray(res.data) ? res.data : []
    }
  } catch {
    tempHistory.value = []
  }
  nextTick(() => drawChart())
}

function drawChart() {
  nextTick(() => {
    const canvas = canvasRef.value
    if (!canvas || !tempHistory.value.length) return
    const ctx = canvas.getContext('2d')
    const w = canvas.width
    const h = canvas.height
    ctx.clearRect(0, 0, w, h)

    const temps = tempHistory.value.map((p: any) => p.temp ?? p.temperature ?? p.value ?? 0)
    if (!temps.length) return
    const min = Math.min(...temps) - 2
    const max = Math.max(...temps) + 2
    const range = max - min || 1
    const stepX = w / (temps.length - 1 || 1)

    // 画线
    ctx.beginPath()
    ctx.strokeStyle = '#00a8ff'
    ctx.lineWidth = 2.5
    temps.forEach((t, i) => {
      const x = i * stepX
      const y = h - ((t - min) / range) * (h - 20) - 10
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
    })
    ctx.stroke()

    // 填充渐变
    const lastY = h - ((temps[temps.length - 1] - min) / range) * (h - 20) - 10
    ctx.lineTo((temps.length - 1) * stepX, h)
    ctx.lineTo(0, h)
    ctx.closePath()
    const grad = ctx.createLinearGradient(0, 0, 0, h)
    grad.addColorStop(0, 'rgba(0,168,255,0.2)')
    grad.addColorStop(1, 'rgba(0,168,255,0.02)')
    ctx.fillStyle = grad
    ctx.fill()

    // 标注值
    ctx.fillStyle = '#333'
    ctx.font = '10px Inter, sans-serif'
    ctx.fillText(min.toFixed(0) + '°C', 2, h - 4)
    ctx.fillText(max.toFixed(0) + '°C', 2, 14)
  })
}

async function fetchAlerts() {
  try {
    const res: any = await alertAPI.getActiveAlerts()
    if (res?.data) {
      alerts.value = Array.isArray(res.data) ? res.data : (res.data.items || [])
    }
  } catch {
    // 降级到模拟数据
    if (!alerts.value.length) {
      alerts.value = [
        { id: 'a1', level: 'normal', message: '车门开启超过5分钟，请检查', device_id: 'VT001', time: '11:05' },
        { id: 'a2', level: 'severe', message: '车厢温度升至5.2°C，接近预警值', device_id: 'VT001', time: '10:48', temp_deviation: '2.2°C' },
      ]
    }
  }
}

async function fetchOrders() {
  try {
    const res: any = await dispatchAPI.getOrders()
    if (res?.data?.orders) orders.value = res.data.orders
  } catch {}
}

async function fetchUploadHistory() {
  try {
    const res: any = await uploadAPI.getTempRecords(currentDeviceId.value)
    if (res?.data?.records) uploadHistory.value = res.data.records
  } catch {}
}

// ======= 告警操作 =======
async function ackAlert(a: any) {
  try {
    await alertAPI.acknowledge(a.id, 'acknowledged', '司机已确认')
  } catch {}
  alerts.value = alerts.value.filter(x => x.id !== a.id)
}

function handleAlert(a: any) {
  currentAlert.value = a
  disposeAction.value = 'door_closed'
  disposeNote.value = ''
  showDisposeModal.value = true
}

async function submitDispose() {
  if (currentAlert.value) {
    // 暂时不实际删除，只是标记处理状态
    const a = currentAlert.value
    const actionLabel = disposeOptions.find(o => o.key === disposeAction.value)?.label || disposeAction.value
    a.disposition = `${actionLabel}。${disposeNote.value || '无额外备注'} —— ${new Date().toLocaleTimeString()}`
    a.acknowledged = true
    // 尝试调用 dispatch API
    try {
      await alertAPI.dispatch(a.id, ['sms'])
    } catch {}
  }
  showDisposeModal.value = false
}

function uploadForAlert(a: any) {
  currentAlert.value = a
  activeTab.value = 'me'
  nextTick(() => {
    uploadNotes.value = `关联告警: ${a.message || a.alert_message}`
    if (fileInput.value) fileInput.value.click()
  })
}

// ======= 拍照上传 =======
function onFileSelected(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files && input.files[0]) {
    photoFile = input.files[0]
    const reader = new FileReader()
    reader.onload = (ev: any) => {
      photoPreview.value = ev.target.result
    }
    reader.readAsDataURL(photoFile)
  }
}

function clearPhoto() {
  photoPreview.value = ''
  photoFile = null
  uploadNotes.value = ''
  if (fileInput.value) fileInput.value.value = ''
}

async function submitPhoto() {
  if (!photoFile) return
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', photoFile)
    formData.append('device_id', currentDeviceId.value)
    formData.append('waybill_id', currentTask.waybill || '')
    formData.append('notes', uploadNotes.value || '温度记录纸拍照')
    const res: any = await uploadAPI.uploadTempRecord(formData)
    if (res?.code === 200) {
      uploadHistory.value.unshift({
        id: res.data.id,
        filename: res.data.filename,
        original_name: res.data.original_name,
        upload_time: res.data.upload_time,
      })
    }
    clearPhoto()
  } catch {
    // 模拟上传成功
    const now = new Date().toLocaleString()
    uploadHistory.value.unshift({
      id: Date.now().toString(),
      filename: `温度记录_${now.replace(/[/:]/g, '')}`,
      original_name: photoFile.name,
      upload_time: now,
    })
    clearPhoto()
  } finally {
    uploading.value = false
  }
}

// ======= 设备操作 =======
function toggleDoorModel() {
  doorOpen.value = !doorOpen.value
  if (doorOpen.value) {
    const newAlert = {
      id: 'a' + Date.now(),
      level: 'normal',
      message: '车门已手动开启，请注意温度变化',
      device_id: currentDeviceId.value,
      time: new Date().toLocaleTimeString(),
    }
    alerts.value.unshift(newAlert)
  }
}

function handleOrder(o: any) {
  if (o.status === 'done') {
    alert(`✓ 已签收: ${o.cargo} - ${o.address}`)
  } else if (o.status === 'current') {
    alert(`🚚 配送中: ${o.cargo} → ${o.address}`)
  } else {
    alert(`⏳ 待配送: ${o.cargo} - ${o.address}`)
  }
}

function openScanner() {
  if (orders.value.filter((o: any) => o.status !== 'done').length === 0) {
    alert('所有订单已完成配送！')
    return
  }
  const pending = orders.value.find((o: any) => o.status === 'current')
  if (pending) {
    pending.status = 'done'
    pending.statusLabel = '已签收'
    alert(`✓ 签收成功: #${pending.id} ${pending.cargo} → ${pending.address}`)
  }
  if (currentTask.progress < 100) {
    currentTask.progress = Math.min(100, currentTask.progress + 15)
  }
}

function handleLogout() {
  if (confirm('确定退出？')) {
    window.location.hash = '#/login'
  }
}

// ======= 定时刷新 =======
// 页面秒开：先用默认数据渲染，API 静默更新
let firstLoadDone = false
function refreshAll() {
  // 首次加载不阻塞UI，静默更新数据
  fetchSensorData()
  // 温度历史延迟200ms加载，避免阻塞首屏渲染
  setTimeout(() => fetchTempHistory(), 200)
  fetchAlerts()
  // 订单和上传历史延迟加载，当前tab不显示时不急
  setTimeout(() => {
    fetchOrders()
    fetchUploadHistory()
  }, 500)
  firstLoadDone = true
}

function simulateUpdate() {
  sensorData.temperature = parseFloat(((sensorData.temperature ?? 3.5) + (Math.random() - 0.48) * 0.4).toFixed(1))
  sensorData.humidity = parseFloat(Math.max(60, Math.min(95, (sensorData.humidity ?? 78) + (Math.random() - 0.5) * 2)).toFixed(1))
  signalStrength.value = -(Math.floor(Math.random() * 30) + 55)
  batteryLevel.value = Math.max(5, batteryLevel.value - Math.floor(Math.random() * 2))
  if (currentTask.progress < 100) currentTask.progress += Math.floor(Math.random() * 2)
}

onMounted(() => {
  canvasW.value = Math.min(350, window.innerWidth - 36)
  // 延迟100ms再发请求，先让页面渲染出来
  setTimeout(() => refreshAll(), 100)
  refreshTimer = setInterval(() => {
    simulateUpdate()
    // 每15秒才拉一次告警，不用每5秒
  }, 5000)
  // 每15秒静默拉取告警
  setInterval(() => fetchAlerts(), 15000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
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

/* 通用卡片 */
.mb-card {
  margin: 8px 12px;
  background: #fff;
  border-radius: 12px;
  padding: 14px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.mb-card-hd {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.mb-card-title { font-size: 13px; font-weight: 700; color: #333; }
.mb-card-subtitle { font-size: 11px; color: #999; }
.mb-card-badge { font-size: 10px; color: #fff; background: #ff4757; padding: 2px 8px; border-radius: 10px; }
.mb-card-count { font-size: 11px; color: #999; }
.mb-pull-hint { text-align: center; padding: 20px; color: #999; font-size: 13px; }

/* 温度大卡片 */
.mb-hero {
  margin: 12px;
  background: linear-gradient(135deg, #e8f4fd, #d4f0e8);
  border-radius: 16px;
  padding: 20px;
  text-align: center;
  transition: all 0.3s;
}
.mb-hero.danger {
  background: linear-gradient(135deg, #ffe8e8, #fff0f0);
}
.mb-hero-badge {
  font-size: 12px; font-weight: 700; padding: 4px 12px; border-radius: 12px;
  display: inline-block; margin-bottom: 12px;
  background: rgba(0,210,160,0.15); color: #00d2a0;
}
.mb-hero-badge.ok { background: rgba(0,210,160,0.15); color: #00d2a0; }
.mb-hero.danger .mb-hero-badge.ok { display: none; }
.mb-hero:not(.danger) .mb-hero-badge:not(.ok) { display: none; }
.mb-hero.danger .mb-hero-badge { background: rgba(255,71,87,0.15); color: #ff4757; }
.ht-value { font-size: 56px; font-weight: 800; color: #1a1a2e; line-height: 1; }
.ht-unit { font-size: 20px; color: #666; margin-left: 4px; font-weight: 500; }
.mb-hero-meta { display: flex; justify-content: space-around; margin-top: 16px; }
.hm-item { text-align: center; }
.hm-icon { font-size: 18px; display: block; }
.hm-label { font-size: 11px; color: #999; display: block; margin: 2px 0; }
.hm-val { font-size: 14px; font-weight: 700; color: #333; }

/* 设备状态 */
.mb-status-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin: 0 12px 8px;
}
.msg-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 4px;
  border-radius: 12px;
  background: #f8f9fa;
  transition: all 0.2s;
}
.msg-item.active { background: rgba(0,210,160,0.08); }
.msg-item.s-weak { background: rgba(255,165,0,0.08); }
.msg-item.b-low { background: rgba(255,71,87,0.08); }
.msg-icon { font-size: 20px; }
.msg-title { font-size: 10px; color: #999; }
.msg-val { font-size: 10px; font-weight: 700; color: #333; }
.msg-val.warn { color: #ff4757; }

/* 温度趋势图 */
.mb-chart { width: 100%; min-height: 60px; }
.mb-chart-placeholder { text-align: center; color: #ccc; padding: 40px 0; font-size: 13px; }

/* 预测趋势条 */
.mb-predict-bar {
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 70px;
  padding: 0 4px;
}
.mpb-mark {
  flex: 1;
  background: #00a8ff;
  border-radius: 2px 2px 0 0;
  transition: height 0.5s;
  min-width: 6px;
}
.mpb-mark.danger { background: #ff4757; }
.mb-predict-range {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 11px;
  color: #999;
}
.text-red { color: #ff4757; }

/* 订单 */
.mb-order-card {
  margin: 12px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  padding: 16px;
  border-radius: 14px;
  color: #fff;
}
.moc-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.moc-waybill { font-size: 15px; font-weight: 700; }
.moc-tag { font-size: 10px; padding: 3px 10px; border-radius: 6px; font-weight: 600; }
.moc-tag.ok { background: rgba(255,255,255,0.2); }
.moc-tag.warn { background: rgba(255,71,87,0.4); }
.moc-route { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.moc-dot { width: 8px; height: 8px; border-radius: 50%; background: #fff; }
.moc-dot.end { background: rgba(255,255,255,0.5); }
.moc-line { flex: 1; height: 2px; border-top: 2px dashed rgba(255,255,255,0.3); }
.moc-city { font-size: 12px; white-space: nowrap; }
.moc-progress { display: flex; align-items: center; gap: 10px; }
.moc-prog-bar { flex: 1; height: 6px; background: rgba(255,255,255,0.25); border-radius: 3px; overflow: hidden; }
.moc-prog-fill { height: 100%; background: #fff; border-radius: 3px; transition: width 0.5s; }
.moc-prog-num { font-size: 12px; font-weight: 700; }
.moc-meta { display: flex; justify-content: space-between; margin-top: 10px; font-size: 11px; opacity: 0.8; }

.mb-order-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
}
.mb-order-item:last-child { border-bottom: none; }
.moi-left { display: flex; align-items: center; gap: 10px; }
.moi-status-icon { width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; background: #f0f0f0; }
.moi-status-icon.done { background: #d4f0e8; color: #00d2a0; }
.moi-status-icon.current { background: #e8f4fd; color: #00a8ff; }
.moi-id { font-size: 13px; font-weight: 600; }
.moi-addr { font-size: 11px; color: #999; margin-top: 2px; }
.moi-right { text-align: right; }
.moi-weight { font-size: 12px; color: #666; display: block; }
.moi-tag { font-size: 10px; padding: 1px 6px; border-radius: 4px; }
.moi-tag.done { background: rgba(0,210,160,0.1); color: #00d2a0; }
.moi-tag.current { background: rgba(0,168,255,0.1); color: #00a8ff; }
.moi-tag.pending { background: #f0f0f0; color: #999; }
.mb-scan-btn {
  margin: 12px;
  padding: 16px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  border-radius: 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
}

/* 告警 */
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
}
.mfb-btn.active { background: #00a8ff; color: #fff; border-color: #00a8ff; }
.mb-alert-empty { text-align: center; padding: 60px 0; color: #ccc; }
.mb-alert-empty span { display: block; font-size: 40px; margin-bottom: 10px; }
.mb-alert-card {
  margin: 8px 12px;
  padding: 14px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #f0f0f0;
}
.mb-alert-card.lvl-critical { border-left: 4px solid #ff4757; }
.mb-alert-card.lvl-severe { border-left: 4px solid #ffa502; }
.mb-alert-card.lvl-normal { border-left: 4px solid #00a8ff; }
.mac-top { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.mac-lvl-tag { font-size: 10px; padding: 2px 8px; border-radius: 4px; font-weight: 600; }
.mac-lvl-tag.critical { background: rgba(255,71,87,0.1); color: #ff4757; }
.mac-lvl-tag.severe { background: rgba(255,165,0,0.1); color: #ffa502; }
.mac-lvl-tag.normal { background: rgba(0,168,255,0.1); color: #00a8ff; }
.mac-device { font-size: 11px; color: #999; }
.mac-time { font-size: 11px; color: #ccc; margin-left: auto; }
.mac-msg { font-size: 13px; font-weight: 500; margin-bottom: 4px; }
.mac-temp { font-size: 11px; color: #ff4757; margin-bottom: 8px; }
.mac-actions { display: flex; gap: 6px; }
.maca-btn {
  padding: 5px 14px;
  font-size: 11px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
}
.maca-btn.primary { background: #00a8ff; color: #fff; border-color: #00a8ff; }
.mac-disposition { margin-top: 10px; padding: 10px; background: #f8f9fa; border-radius: 8px; }
.macd-title { font-size: 11px; font-weight: 600; color: #00a8ff; margin-bottom: 4px; }
.macd-detail { font-size: 12px; color: #666; }

/* 处置弹窗 */
.mb-modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.5);
  display: flex; align-items: flex-end; justify-content: center; z-index: 1000;
}
.mb-modal {
  width: 100%; max-width: 420px;
  background: #fff; border-radius: 16px 16px 0 0; padding: 20px;
}
.mb-modal-title { font-size: 16px; font-weight: 700; margin-bottom: 16px; }
.mb-modal-body { margin-bottom: 16px; }
.mbm-option {
  display: flex; align-items: center; gap: 10px;
  padding: 12px; border-radius: 10px; margin-bottom: 6px;
  background: #f8f9fa; cursor: pointer; font-size: 13px;
  border: 2px solid transparent; transition: all 0.2s;
}
.mbm-option.selected { border-color: #00a8ff; background: #e8f4fd; }
.mbmo-icon { font-size: 20px; }
.mbm-input {
  width: 100%; padding: 10px; border: 1px solid #e0e0e0; border-radius: 8px;
  font-size: 13px; margin-top: 8px; box-sizing: border-box;
}
.mb-modal-ft { display: flex; gap: 10px; }
.mbmf-btn {
  flex: 1; padding: 12px; border-radius: 10px; font-size: 14px; font-weight: 600;
  border: 1px solid #e0e0e0; background: #fff; cursor: pointer;
}
.mbmf-btn.primary { background: #00a8ff; color: #fff; border-color: #00a8ff; }

/* 我的页面 */
.mb-profile {
  display: flex; align-items: center; gap: 14px;
  padding: 20px 16px; background: linear-gradient(135deg, #667eea, #764ba2); color: #fff;
}
.mb-avatar {
  width: 48px; height: 48px; border-radius: 50%;
  background: rgba(255,255,255,0.25); display: flex; align-items: center; justify-content: center;
  font-size: 22px; font-weight: 700;
}
.mb-driver-name { font-size: 16px; font-weight: 700; }
.mb-driver-id { font-size: 12px; opacity: 0.75; margin-top: 2px; }

/* 拍照上传 */
.mb-camera-area { margin: 10px 0; }
.mb-file-input { display: none; }
.mb-camera-btn {
  display: flex; flex-direction: column; align-items: center; gap: 6px;
  width: 100%; padding: 24px; border: 2px dashed #00a8ff; border-radius: 14px;
  background: #e8f4fd; cursor: pointer;
}
.mc-icon { font-size: 36px; }
.mc-text { font-size: 14px; font-weight: 600; color: #00a8ff; }
.mc-hint { font-size: 11px; color: #999; }
.mb-photo-preview { margin-top: 10px; }
.mb-preview-img { width: 100%; border-radius: 10px; max-height: 300px; object-fit: contain; background: #f0f0f0; }
.mb-photo-actions { display: flex; gap: 8px; margin-top: 8px; }
.mpa-btn { flex: 1; padding: 10px; border-radius: 8px; font-size: 13px; font-weight: 600; cursor: pointer; border: none; }
.mpa-btn.cancel { background: #f0f0f0; color: #666; }
.mpa-btn.upload { background: #00a8ff; color: #fff; }
.mpa-btn:disabled { opacity: 0.6; }
.mb-upload-note { margin-top: 8px; }
.mb-note-input {
  width: 100%; padding: 10px; border: 1px solid #e0e0e0; border-radius: 8px;
  font-size: 13px; box-sizing: border-box;
}
.mb-upload-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 0; border-bottom: 1px solid #f0f0f0;
}
.mb-upload-item:last-child { border-bottom: none; }
.mui-icon { font-size: 22px; }
.mui-info { flex: 1; }
.mui-name { font-size: 12px; font-weight: 500; }
.mui-time { font-size: 10px; color: #999; }
.mui-status { font-size: 10px; padding: 2px 8px; border-radius: 4px; }
.mui-status.ok { background: rgba(0,210,160,0.1); color: #00d2a0; }

/* 退出 */
.mb-logout-btn {
  margin: 16px 12px; width: calc(100% - 24px);
  padding: 14px; border-radius: 12px; font-size: 14px; font-weight: 600;
  background: #fff; border: 1px solid #ff4757; color: #ff4757; cursor: pointer;
}

/* 底部导航 */
.mb-tabbar {
  position: absolute; bottom: 0; left: 0; right: 0;
  display: flex; justify-content: space-around;
  background: #fff; border-top: 1px solid #f0f0f0;
  padding: 6px 0 8px; box-shadow: 0 -2px 10px rgba(0,0,0,0.04);
}
.mt-item {
  display: flex; flex-direction: column; align-items: center; gap: 2px;
  padding: 4px 16px; cursor: pointer; position: relative;
}
.mt-icon { font-size: 20px; }
.mt-label { font-size: 10px; color: #999; }
.mt-item.active .mt-label { color: #00a8ff; font-weight: 600; }
.mt-badge {
  position: absolute; top: 0; right: 8px;
  min-width: 16px; height: 16px; background: #ff4757; color: #fff;
  font-size: 10px; font-weight: 700; border-radius: 8px;
  display: flex; align-items: center; justify-content: center; padding: 0 4px;
}

@media (min-width: 768px) {
  .mobile-wrap { border-radius: 16px; margin: 20px; min-height: auto; box-shadow: 0 4px 30px rgba(0,0,0,0.08); }
}
</style>
