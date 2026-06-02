<template>
  <div class="mobile-app">
    <div class="mobile-wrap">
      <!-- 状态栏 -->
      <div class="mb-status">
        <span>CRYO·TRACK 冷链监控</span>
        <span class="mb-user">司机: {{ username }}</span>
      </div>

      <!-- 当前任务 -->
      <div class="mb-task" v-if="currentTask">
        <div class="mb-task-header">
          <span class="mb-task-id">{{ currentTask.waybill }}</span>
          <span class="mb-tag" :class="taskTempOK ? 'ok' : 'warn'">
            {{ taskTempOK ? '温度正常' : '温度异常' }}
          </span>
        </div>
        <div class="mb-task-route">
          {{ currentTask.origin }} → {{ currentTask.destination }}
        </div>
        <div class="mb-task-prog">
          <div class="mb-prog-bar"><div :style="{width:currentTask.progress+'%'}"></div></div>
          <span>{{ currentTask.progress }}%</span>
        </div>
      </div>

      <!-- 温度面板 -->
      <div class="mb-panel">
        <div class="mb-panel-title">实时温控</div>
        <div class="mb-temp-display" :class="{ danger: tempData.temp > 8 || tempData.temp < -25 }">
          <span class="mb-temp-value">{{ tempData.temp.toFixed(1) }}</span>
          <span class="mb-temp-unit">°C</span>
        </div>
        <div class="mb-temp-meta">
          <div class="mtm-item">
            <span>湿度</span><b>{{ tempData.humidity.toFixed(1) }}%</b>
          </div>
          <div class="mtm-item">
            <span>目标温度</span><b>{{ tempData.target.toFixed(1) }}°C</b>
          </div>
          <div class="mtm-item">
            <span>外部温度</span><b>{{ tempData.external.toFixed(1) }}°C</b>
          </div>
        </div>
      </div>

      <!-- 设备状态 -->
      <div class="mb-status-cards">
        <div class="mb-scard" :class="{ active: doorStatus }" @click="toggleDoor">
          <span class="msc-icon">🚪</span>
          <span class="msc-label">车门</span>
          <span class="msc-value">{{ doorStatus ? '开启' : '关闭' }}</span>
        </div>
        <div class="mb-scard" :class="{ active: coldCarStatus === 1 }">
          <span class="msc-icon">❄</span>
          <span class="msc-label">冷机</span>
          <span class="msc-value">{{ coldCarStatus === 1 ? '运行中' : '故障' }}</span>
        </div>
        <div class="mb-scard" :class="'signal-' + signalLevel">
          <span class="msc-icon">📶</span>
          <span class="msc-label">信号</span>
          <span class="msc-value">{{ signalStrength }} dBm</span>
        </div>
        <div class="mb-scard">
          <span class="msc-icon">🔋</span>
          <span class="msc-label">电量</span>
          <span class="msc-value">{{ batteryLevel }}%</span>
        </div>
      </div>

      <!-- 配送进度 -->
      <div class="mb-panel">
        <div class="mb-panel-title">订单列表</div>
        <div v-for="o in orders" :key="o.id" class="mb-order">
          <div class="mbo-top">
            <span class="mbo-id">#{{ o.id }}</span>
            <span class="mbo-status" :class="o.status">{{ o.statusLabel }}</span>
          </div>
          <div class="mbo-addr">{{ o.address }}</div>
          <div class="mbo-cargo">{{ o.cargo }} · {{ o.weight }}kg</div>
        </div>
      </div>

      <!-- 告警消息 -->
      <div class="mb-panel" v-if="alerts.length > 0">
        <div class="mb-panel-title warn-title">告警通知 ({{ alerts.length }})</div>
        <div v-for="a in alerts" :key="a.id" class="mb-alert" :class="'lvl-'+a.level">
          <div class="mba-msg">{{ a.message }}</div>
          <div class="mba-time">{{ a.time }}</div>
            <div class="mba-actions">
            <button class="mba-btn" @click="ackAlert(a.id)">确认</button>
            <button class="mba-btn primary" @click="reportAlert(a.id)">上报</button>
          </div>
        </div>
      </div>

      <!-- 拍照上传 -->
      <div class="mb-panel">
        <div class="mb-panel-title">温度记录上传</div>
        <div class="mb-upload">
          <button class="mb-upload-btn" @click="mockUpload">
            <span>📸</span>
            <span>拍照记录温度纸</span>
          </button>
          <div v-if="uploadedImages.length > 0" class="mb-upload-imgs">
            <span v-for="(img, i) in uploadedImages" :key="i" class="mb-thumb">📄 温度记录_00{{ i+1 }}</span>
          </div>
        </div>
      </div>

      <!-- 底部操作 -->
      <div class="mb-bottom-bar">
        <button class="mbb-btn" @click="refreshData">🔄 刷新</button>
        <button class="mbb-btn primary" @click="mockScan">📱 扫码签收</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'

const username = ref('李司机')
let refreshTimer: any = null

const currentTask = reactive({
  waybill: 'WB20260602001',
  origin: '华北中心冷库',
  destination: '北京市朝阳区望京SOHO',
  progress: 68,
})

const tempData = reactive({
  temp: 3.8,
  humidity: 78.5,
  target: 3.0,
  external: 31.2,
})

const doorStatus = ref(false)
const coldCarStatus = ref(1)
const signalStrength = ref(-68)
const batteryLevel = ref(85)

const signalLevel = computed(() => {
  if (signalStrength.value > -60) return 'good'
  if (signalStrength.value > -80) return 'ok'
  return 'weak'
})

const taskTempOK = computed(() => tempData.temp >= -25 && tempData.temp <= 8)

const orders = ref([
  { id: '1', status: 'done', statusLabel: '已送达', address: '朝阳区望京街道10号', cargo: '冷冻海鲜', weight: 500 },
  { id: '2', status: 'current', statusLabel: '配送中', address: '海淀区中关村软件园', cargo: '冷藏生鲜', weight: 300 },
  { id: '3', status: 'pending', statusLabel: '待配送', address: '西城区金融街购物中心', cargo: '恒温药品', weight: 200 },
])

const alerts = ref([
  { id: 'a1', level: 'normal', message: '车门开启超过5分钟，请检查', time: '11:05' },
  { id: 'a2', level: 'severe', message: '车厢温度升至5.2°C，接近预警值', time: '10:48' },
])

const uploadedImages = ref<string[]>([])

function toggleDoor() {
  doorStatus.value = !doorStatus.value
}

function ackAlert(id: string) {
  alerts.value = alerts.value.filter(a => a.id !== id)
}

function reportAlert(id: string) {
  ackAlert(id)
}

function mockUpload() {
  uploadedImages.value.push('temp-record')
  if (uploadedImages.value.length > 3) uploadedImages.value.shift()
}

function mockScan() {
  alert('模拟扫码签收：扫描成功！')
}

function simulateData() {
  tempData.temp += (Math.random() - 0.48) * 0.4
  tempData.temp = parseFloat(tempData.temp.toFixed(1))
  tempData.humidity += (Math.random() - 0.5) * 2
  tempData.humidity = parseFloat(Math.max(60, Math.min(95, tempData.humidity)).toFixed(1))
  signalStrength.value = -(Math.floor(Math.random() * 30) + 55)
  batteryLevel.value = Math.max(1, batteryLevel.value - Math.floor(Math.random() * 3))
  if (currentTask.progress < 100) currentTask.progress += Math.floor(Math.random() * 3)
  if (currentTask.progress > 100) currentTask.progress = 100
}

function refreshData() { simulateData() }

onMounted(() => {
  refreshTimer = setInterval(simulateData, 5000)
})
onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
.mobile-app {
  animation: fadeInUp 0.45s ease-out;
  display: flex;
  justify-content: center;
}
.mobile-wrap {
  max-width: 420px;
  width: 100%;
  background: var(--bg-page);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: 0 4px 30px rgba(0,0,0,0.08);
  border: 1px solid var(--border);
}

/* 状态栏 */
.mb-status {
  background: linear-gradient(135deg, var(--accent), var(--aurora));
  color: #fff;
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 600;
}
.mb-user { font-size: 11px; opacity: .85; }

/* 任务卡 */
.mb-task {
  background: var(--bg-card);
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
}
.mb-task-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.mb-task-id { font-family: var(--font-mono); font-size: 14px; font-weight: 700; }
.mb-tag { font-size: 10px; padding: 2px 8px; border-radius: 4px; font-weight: 600; }
.mb-tag.ok { background: rgba(0,210,160,0.12); color: var(--teal); }
.mb-tag.warn { background: var(--red-bg); color: var(--red); }
.mb-task-route { font-size: 12px; color: var(--text-muted); margin-bottom: 8px; }
.mb-task-prog { display: flex; align-items: center; gap: 10px; }
.mb-prog-bar { flex: 1; height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; }
.mb-prog-bar div { height: 100%; background: linear-gradient(90deg, var(--accent), var(--aurora)); border-radius: 3px; transition: width 1s; }
.mb-task-prog span { font-size: 11px; font-weight: 600; color: var(--accent); }

/* 通用面板 */
.mb-panel { padding: 14px 16px; border-bottom: 1px solid var(--border); }
.mb-panel-title { font-size: 12px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: .05em; margin-bottom: 10px; }
.warn-title { color: var(--red) !important; }

/* 温度显示 */
.mb-temp-display { text-align: center; padding: 10px 0; }
.mb-temp-display.danger { color: var(--red); }
.mb-temp-value { font-family: var(--font-display); font-size: 48px; font-weight: 800; line-height: 1; }
.mb-temp-unit { font-size: 18px; margin-left: 4px; }
.mb-temp-meta { display: grid; grid-template-columns: repeat(3,1fr); gap: 8px; margin-top: 8px; }
.mtm-item { text-align: center; padding: 6px; border-radius: 8px; background: rgba(0,0,0,0.03); }
.mtm-item span { display: block; font-size: 10px; color: var(--text-muted); }
.mtm-item b { font-family: var(--font-display); font-size: 15px; }

/* 设备状态 */
.mb-status-cards { display: grid; grid-template-columns: repeat(4,1fr); gap: 8px; padding: 12px 16px; border-bottom: 1px solid var(--border); }
.mb-scard { display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 10px 4px; border-radius: 10px; background: rgba(0,0,0,0.02); cursor: pointer; }
.mb-scard.active { background: rgba(0,210,160,0.08); }
.msc-icon { font-size: 20px; }
.msc-label { font-size: 10px; color: var(--text-muted); }
.msc-value { font-size: 10px; font-weight: 600; }
.signal-good .msc-value { color: var(--teal); }
.signal-weak .msc-value { color: var(--amber); }

/* 订单 */
.mb-order { padding: 10px; border-radius: 8px; background: rgba(0,0,0,0.02); margin-bottom: 6px; }
.mbo-top { display: flex; justify-content: space-between; margin-bottom: 2px; }
.mbo-id { font-size: 12px; font-weight: 600; }
.mbo-status { font-size: 10px; padding: 1px 6px; border-radius: 3px; }
.mbo-status.done { background: rgba(0,210,160,0.1); color: var(--teal); }
.mbo-status.current { background: rgba(0,168,255,0.1); color: var(--accent); }
.mbo-status.pending { background: rgba(0,0,0,0.05); color: var(--text-muted); }
.mbo-addr { font-size: 11px; color: var(--text-secondary); margin-bottom: 2px; }
.mbo-cargo { font-size: 10px; color: var(--text-muted); }

/* 告警 */
.mb-alert { padding: 10px; border-radius: 8px; margin-bottom: 6px; background: var(--bg-card); border: 1px solid var(--border); }
.mb-alert.lvl-severe { border-color: var(--red); background: var(--red-bg); }
.mba-msg { font-size: 12px; font-weight: 500; margin-bottom: 4px; }
.mba-time { font-size: 10px; color: var(--text-muted); margin-bottom: 6px; }
.mba-actions { display: flex; gap: 6px; }
.mba-btn { padding: 3px 12px; font-size: 11px; border: 1px solid var(--border); border-radius: 4px; background: var(--bg-card); cursor: pointer; }
.mba-btn.primary { background: var(--accent); color: #fff; border-color: var(--accent); }

/* 上传 */
.mb-upload { text-align: center; }
.mb-upload-btn { display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 16px; width: 100%; border: 2px dashed var(--border); border-radius: 12px; background: transparent; cursor: pointer; font-size: 12px; color: var(--text-muted); }
.mb-upload-btn span:first-child { font-size: 28px; }
.mb-upload-imgs { display: flex; gap: 6px; margin-top: 8px; flex-wrap: wrap; }
.mb-thumb { font-size: 10px; padding: 3px 8px; border-radius: 4px; background: rgba(0,168,255,0.08); color: var(--accent); }

/* 底部按钮 */
.mb-bottom-bar { display: flex; gap: 10px; padding: 14px 16px; }
.mbb-btn { flex: 1; padding: 12px; border-radius: 10px; font-size: 13px; font-weight: 600; border: 1px solid var(--border); background: var(--bg-card); cursor: pointer; text-align: center; }
.mbb-btn.primary { background: linear-gradient(135deg, var(--accent), var(--aurora)); color: #fff; border: none; }

@media (min-width: 768px) {
  .mobile-wrap { max-width: 420px; }
}
</style>
