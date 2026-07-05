<template>
  <div class="alert-center">
    <div class="page-header">
      <h2 class="page-title">告警中心</h2>
      <div class="header-stats">
        <span class="stat-badge" :class="store.kpi.active_alerts > 0 ? 'has-alerts' : 'clean'">
          {{ store.kpi.active_alerts > 0 ? `⚠ ${store.kpi.active_alerts} 条活跃告警` : '✓ 全部正常' }}
        </span>
      </div>
    </div>

    <div v-if="store.activeAlerts.length === 0" class="empty-block">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--teal)" stroke-width="1.5" stroke-linecap="round">
        <circle cx="12" cy="12" r="10"/>
        <polyline points="8 12 11 15 16 9"/>
      </svg>
      <p>当前无活跃告警</p>
      <span>所有设备运行正常，温控指标在安全范围内</span>
    </div>

    <div v-else class="alert-grid">
      <div v-for="device in store.activeAlerts" :key="device.device_id" class="alert-card">
        <div class="card-top">
          <div class="top-left">
            <code class="aid">{{ device.device_id }}</code>
            <span class="acount" :class="device.active_alerts > 3 ? 'critical' : 'warning'">
              {{ device.active_alerts }} 条告警
            </span>
          </div>
          <div class="atemp" :class="getTempClass(device.last_temperature)">
            <span class="atemp-num">{{ device.last_temperature }}</span>
            <span class="atemp-u">°C</span>
          </div>
        </div>
        <div class="card-bottom">
          <span class="atime">
            <span class="atime-dot"></span>
            {{ formatTime(device.last_update) }}
          </span>
          <span class="adetail" @click="showDeviceDetail(device)">查看详情 →</span>
        </div>
        <div class="card-actions" v-if="device.device_type === 'vehicle'">
          <span class="alink" @click="router.push('/tracking')">🚛 追踪车辆</span>
        </div>
      </div>
    </div>

    <div v-if="fenceAlerts.length > 0" class="glass-card">
      <h3 class="sec-title">电子围栏告警</h3>
      <div class="fence-alert-list">
        <div v-for="alert in fenceAlerts" :key="alert.event_id" class="fence-alert-item">
          <span class="fence-alert-level" :class="getAlertLevelClass(alert.alert_level)">
            {{ getAlertLevelText(alert.alert_level) }}
          </span>
          <span class="fence-alert-desc">{{ alert.description }}</span>
          <span class="fence-alert-meta">{{ alert.fence_name }} · {{ alert.city_section || alert.plate_number }}</span>
          <span class="fence-alert-time">{{ formatTime(alert.event_time) }}</span>
        </div>
      </div>
    </div>

    <div class="glass-card">
      <h3 class="sec-title">告警级别说明</h3>
      <div class="sev-list">
        <div class="sev-item">
          <span class="sev-badge amber">一般</span>
          <span>推送至配送员终端，需现场确认处置</span>
        </div>
        <div class="sev-item">
          <span class="sev-badge red">严重</span>
          <span>通知区域经理和维修团队立即响应</span>
        </div>
        <div class="sev-item">
          <span class="sev-badge crit">紧急</span>
          <span>启动应急预案，通知客户（如疫苗温度失控）</span>
        </div>
      </div>
    </div>

    <el-dialog v-model="showDetail" :title="selectedDevice?.device_id + ' · 设备详情'" width="480px" class="custom-dialog">
      <div v-if="selectedDevice" class="detail">
        <div class="detail-grid">
          <div class="d-item"><span class="d-lab">类型</span><span class="d-val">{{ selectedDevice.device_type === 'vehicle' ? '冷藏车' : '冷库' }}</span></div>
          <div class="d-item"><span class="d-lab">温度</span><span class="d-val highlight" :class="getTempClass(selectedDevice.temperature)">{{ selectedDevice.temperature }}°C</span></div>
          <div class="d-item"><span class="d-lab">湿度</span><span class="d-val">{{ selectedDevice.humidity }}%</span></div>
          <div class="d-item"><span class="d-lab">车门</span><span class="d-val">{{ selectedDevice.door_status ? '开启' : '关闭' }}</span></div>
          <div class="d-item"><span class="d-lab">振动</span><span class="d-val">{{ selectedDevice.vibration || '—' }}</span></div>
          <div class="d-item"><span class="d-lab">告警</span><span class="d-val danger">{{ selectedDevice.active_alerts || 0 }}</span></div>
          <div class="d-item"><span class="d-lab">车牌号</span><span class="d-val mono">{{ selectedDevice.plate_number || '—' }}</span></div>
          <div class="d-item"><span class="d-lab">车速</span><span class="d-val">{{ selectedDevice.vehicle_speed || 0 }} km/h</span></div>
          <div class="d-item"><span class="d-lab">电量</span><span class="d-val">{{ selectedDevice.battery_level || 0 }}%</span></div>
          <div class="d-item"><span class="d-lab">信号</span><span class="d-val">{{ '★'.repeat(selectedDevice.signal_strength || 0) }}{{ '☆'.repeat(5 - (selectedDevice.signal_strength || 0)) }}</span></div>
          <div class="d-item"><span class="d-lab">货物类型</span><span class="d-val">{{ selectedDevice.cargo_type || '—' }}</span></div>
          <div class="d-item"><span class="d-lab">运单号</span><span class="d-val mono">{{ selectedDevice.waybill_no || '—' }}</span></div>
        </div>
        <div class="d-time"><span class="d-lab">最后更新</span><span class="d-val mono">{{ formatTime(selectedDevice.last_update) }}</span></div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'
import { getTempClass, formatTime } from '@/utils'
import { vehicleAPI, geofenceAPI } from '@/api'
import { ElMessage } from 'element-plus'

const store = useAppStore()
const router = useRouter()
const showDetail = ref(false)
const selectedDevice = ref<any>(null)
const fenceAlerts = ref<any[]>([])
const loadingFenceAlerts = ref(false)

async function showDeviceDetail(device: any) {
  try {
    const detail = await vehicleAPI.getDetail(device.device_id)
    selectedDevice.value = {
      ...detail,
      active_alerts: device.active_alerts,
      temperature: detail.temperature || device.last_temperature,
    }
    showDetail.value = true
  } catch {
    ElMessage.error('获取设备详情失败')
  }
}

async function loadFenceAlerts() {
  loadingFenceAlerts.value = true
  try {
    const res: any = await geofenceAPI.getAlerts()
    fenceAlerts.value = res.alerts || []
  } catch {
    console.error('加载围栏告警失败')
  } finally {
    loadingFenceAlerts.value = false
  }
}

function getAlertLevelClass(level: string) {
  const map: Record<string, string> = {
    severe: 'crit',
    warning: 'red',
    normal: 'amber',
    info: 'normal',
  }
  return map[level] || 'normal'
}

function getAlertLevelText(level: string) {
  const map: Record<string, string> = {
    severe: '严重',
    warning: '警告',
    normal: '一般',
    info: '正常',
  }
  return map[level] || level
}

onMounted(() => {
  loadFenceAlerts()
})
</script>

<style scoped>
.alert-center { animation: fadeInUp 0.45s ease-out; }

.stat-badge {
  font-family: var(--font-mono); font-size: 13px; font-weight: 600;
  padding: 6px 14px; border-radius: 20px;
}
.stat-badge.has-alerts { color: var(--red); background: var(--red-bg); border: 1px solid rgba(239,68,68,0.15); }
.stat-badge.clean { color: var(--teal); background: var(--teal-bg); border: 1px solid rgba(0,210,160,0.12); }

.empty-block {
  text-align: center; padding: 60px 0; color: var(--text-muted);
}
.empty-block p { font-size: 15px; font-weight: 500; margin: 10px 0 4px; color: var(--text-secondary); }
.empty-block span { font-size: 12px; }

.alert-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 14px; margin-bottom: 24px;
}

.alert-card {
  background: var(--bg-card); backdrop-filter: var(--blur-card); -webkit-backdrop-filter: var(--blur-card);
  border: 1px solid rgba(239,68,68,0.18); border-radius: var(--radius-lg);
  padding: 18px; box-shadow: var(--shadow-sm); transition: all 0.3s ease;
}
.alert-card:hover {
  border-color: rgba(239,68,68,0.35); box-shadow: 0 0 20px rgba(239,68,68,0.08); transform: translateY(-2px);
}

.card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.top-left { display: flex; align-items: center; gap: 10px; }
.aid {
  font-family: var(--font-mono); font-size: 12px; color: var(--accent);
  background: var(--accent-bg); padding: 3px 8px; border-radius: 4px; font-weight: 500;
}
.acount { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 4px; font-family: var(--font-mono); }
.acount.warning { color: var(--amber); background: var(--amber-bg); border: 1px solid rgba(245,158,11,0.12); }
.acount.critical { color: #fff; background: var(--red); }

.atemp { display: flex; align-items: baseline; gap: 2px; }
.atemp-num { font-family: var(--font-display); font-size: 30px; font-weight: 800; line-height: 1; }
.atemp-u { font-size: 12px; opacity: 0.7; }
.temp-normal { color: var(--teal); }
.temp-warn { color: var(--amber); }
.temp-danger { color: var(--red); }

.card-bottom { display: flex; justify-content: space-between; align-items: center; padding-top: 12px; border-top: 1px solid var(--border-light); }
.atime { display: flex; align-items: center; gap: 6px; font-size: 11px; color: var(--text-muted); font-family: var(--font-mono); }
.atime-dot { width: 5px; height: 5px; border-radius: 50%; background: var(--red); animation: pulse-ring 1.5s ease-in-out infinite; }
.adetail { font-size: 11px; color: var(--accent); font-family: var(--font-mono); cursor: pointer; }

.card-actions { margin-top: 8px; padding-top: 8px; border-top: 1px solid var(--border-light); text-align: center; }
.alink { font-size: 11px; color: var(--accent); cursor: pointer; font-weight: 600; transition: color 0.2s; }
.alink:hover { color: #0284c7; }

.sec-title { font-size: 15px; font-weight: 700; color: var(--text-title); margin-bottom: 14px; }

.sev-list { display: flex; flex-direction: column; gap: 10px; }
.sev-item {
  display: flex; align-items: center; gap: 14px; padding: 12px 14px;
  background: var(--bg-input); border-radius: var(--radius);
  font-size: 13px; color: var(--text-secondary);
}
.sev-badge {
  font-size: 11px; font-weight: 700; padding: 3px 12px; border-radius: 4px;
  font-family: var(--font-mono); letter-spacing: 0.04em; flex-shrink: 0;
}
.sev-badge.amber { color: var(--amber); background: var(--amber-bg); border: 1px solid rgba(245,158,11,0.15); }
.sev-badge.red { color: var(--red); background: var(--red-bg); border: 1px solid rgba(239,68,68,0.15); }
.sev-badge.crit { color: #fff; background: var(--red); }

.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.d-item { padding: 12px; background: var(--bg-input); border-radius: var(--radius); display: flex; flex-direction: column; gap: 4px; }
.d-lab { font-size: 10px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.04em; }
.d-val { font-size: 15px; font-weight: 600; color: var(--text-primary); font-family: var(--font-mono); }
.d-val.highlight { font-family: var(--font-display); font-size: 18px; }
.d-val.danger { color: var(--red) !important; }
.d-time { margin-top: 10px; padding: 12px; background: var(--bg-input); border-radius: var(--radius); display: flex; justify-content: space-between; align-items: center; }
.mono { font-family: var(--font-mono); color: var(--text-secondary); }

@media (max-width: 768px) { .detail-grid { grid-template-columns: 1fr; } }

.fence-alert-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.fence-alert-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: var(--bg-input);
  border-radius: var(--radius);
  font-size: 12px;
}

.fence-alert-level {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
  font-family: var(--font-mono);
  flex-shrink: 0;
}
.fence-alert-level.crit { color: #fff; background: var(--red); }
.fence-alert-level.red { color: var(--red); background: var(--red-bg); }
.fence-alert-level.amber { color: var(--amber); background: var(--amber-bg); }
.fence-alert-level.normal { color: var(--teal); background: var(--teal-bg); }

.fence-alert-desc {
  flex: 1;
  color: var(--text-primary);
  font-weight: 500;
}

.fence-alert-meta {
  color: var(--text-muted);
  font-size: 11px;
}

.fence-alert-time {
  color: var(--text-muted);
  font-size: 11px;
  font-family: var(--font-mono);
  flex-shrink: 0;
}
</style>
