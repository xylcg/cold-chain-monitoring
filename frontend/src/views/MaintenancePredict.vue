<template>
  <div class="maintenance-page">
    <div class="page-header">
      <h2 class="page-title">冷机故障预测性维护</h2>
      <span class="subtitle">梯度提升树/XGBoost 模型 · 提前72小时故障预警</span>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-icon" style="background:var(--red-bg);color:var(--red)">⚠</div>
        <div class="stat-info">
          <div class="stat-value text-red">{{ stats.critical + stats.high }}</div>
          <div class="stat-label">高风险设备</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:rgba(245,158,11,0.12);color:var(--amber)">●</div>
        <div class="stat-info">
          <div class="stat-value text-amber">{{ stats.medium }}</div>
          <div class="stat-label">中风险设备</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:rgba(0,210,160,0.12);color:var(--teal)">✓</div>
        <div class="stat-info">
          <div class="stat-value text-teal">{{ stats.low }}</div>
          <div class="stat-label">正常运行</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:rgba(0,168,255,0.12);color:var(--accent)">📊</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">监测设备总数</div>
        </div>
      </div>
    </div>

    <!-- 工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <button class="btn btn-sm" :class="{ active: filterRisk === '' }" @click="filterRisk = ''">全部</button>
        <button class="btn btn-sm" :class="{ active: filterRisk === 'critical' }" @click="filterRisk = 'critical'" style="color:var(--red)">紧急</button>
        <button class="btn btn-sm" :class="{ active: filterRisk === 'high' }" @click="filterRisk = 'high'" style="color:var(--red)">高风险</button>
        <button class="btn btn-sm" :class="{ active: filterRisk === 'medium' }" @click="filterRisk = 'medium'" style="color:var(--amber)">中风险</button>
        <button class="btn btn-sm" :class="{ active: filterRisk === 'low' }" @click="filterRisk = 'low'" style="color:var(--teal)">低风险</button>
      </div>
      <button class="btn btn-primary btn-sm" @click="refreshAll" :disabled="loading">
        {{ loading ? '预测中...' : '刷新预测' }}
      </button>
    </div>

    <!-- 设备预测列表 -->
    <div class="glass-card">
      <div class="card-header">设备故障预测列表</div>
      <div v-if="loading" class="loading-block">
        <div class="spinner"></div>
        <span>正在执行XGBoost模型推理...</span>
      </div>
      <div v-else class="device-table">
        <div class="table-header">
          <span class="col-id">设备ID</span>
          <span class="col-model">冷机型号</span>
          <span class="col-life">剩余寿命</span>
          <span class="col-prob">故障概率</span>
          <span class="col-risk">风险等级</span>
          <span class="col-type">预测故障</span>
          <span class="col-action">操作</span>
        </div>
        <div v-for="item in filteredDevices" :key="item.device_id" class="table-row" :class="'row-' + item.risk_level" @click="selectDevice(item)">
          <span class="col-id">{{ item.device_id }}</span>
          <span class="col-model">{{ item.unit_brand }} {{ item.unit_model }}</span>
          <span class="col-life">{{ item.remaining_life_days }}天</span>
          <span class="col-prob">
            <div class="prob-bar">
              <div class="prob-fill" :style="{ width: (item.failure_probability * 100) + '%', background: probColor(item.failure_probability) }"></div>
            </div>
            <span>{{ (item.failure_probability * 100).toFixed(1) }}%</span>
          </span>
          <span class="col-risk">
            <span class="tag" :class="'tag-' + item.risk_level">{{ item.risk_label }}</span>
          </span>
          <span class="col-type">{{ item.predicted_failure_type || '—' }}</span>
          <span class="col-action">
            <button class="btn-text" @click.stop="selectDevice(item)">详情</button>
          </span>
        </div>
      </div>
    </div>

    <!-- 详情面板 -->
    <div class="glass-card" v-if="selectedDevice" style="margin-top:20px;">
      <div class="card-header">设备详情 — {{ selectedDevice.device_id }}</div>
      <div class="detail-grid">
        <div class="dg-col">
          <h4>基本信息</h4>
          <div class="info-row"><span>设备ID</span><strong>{{ selectedDevice.device_id }}</strong></div>
          <div class="info-row"><span>冷机型号</span><strong>{{ selectedDevice.unit_brand }} {{ selectedDevice.unit_model }}</strong></div>
          <div class="info-row"><span>额定功率</span><strong>{{ selectedDevice.unit_power_kw }} kW</strong></div>
          <div class="info-row"><span>总寿命</span><strong>{{ selectedDevice.total_life_hours }}小时</strong></div>
          <div class="info-row"><span>已运行</span><strong>{{ selectedDevice.current_run_hours }}小时</strong></div>
          <div class="info-row"><span>剩余寿命</span><strong :class="lifeClass(selectedDevice.remaining_life_days)">{{ selectedDevice.remaining_life_days }}天</strong></div>
        </div>
        <div class="dg-col">
          <h4>实时运行参数</h4>
          <div class="info-row" v-for="(val, key) in selectedDevice.real_time_params" :key="key">
            <span>{{ key.replace(/_/g, ' ') }}</span>
            <strong>{{ val }}</strong>
          </div>
        </div>
        <div class="dg-col">
          <h4>预测结果</h4>
          <div class="info-row"><span>故障概率</span><strong :style="{color:probColor(selectedDevice.failure_probability)}">{{ (selectedDevice.failure_probability * 100).toFixed(1) }}%</strong></div>
          <div class="info-row"><span>风险等级</span><strong>{{ selectedDevice.risk_label }}</strong></div>
          <div class="info-row"><span>预测故障类型</span><strong>{{ selectedDevice.predicted_failure_type || '暂无预测' }}</strong></div>
          <div class="info-row"><span>建议维护时间</span><strong>{{ selectedDevice.next_maintenance_label }} ({{ selectedDevice.next_maintenance_hours }}小时内)</strong></div>
          <hr>
          <h4>特征重要性分析</h4>
          <div class="info-row" v-for="(pct, name) in selectedDevice.feature_importance" :key="name">
            <span>{{ name }}</span>
            <strong>{{ pct }}%</strong>
          </div>
        </div>
      </div>

      <!-- 维护历史 -->
      <div v-if="selectedDevice.maintenance_history" style="margin-top:16px">
        <h4>维护历史</h4>
        <div class="history-table">
          <div class="table-header s">
            <span>日期</span><span>事件</span><span>说明</span><span>技师</span><span>费用</span>
          </div>
          <div v-for="h in selectedDevice.maintenance_history" :key="h.event_id" class="table-row s">
            <span>{{ formatDate(h.event_date) }}</span>
            <span>{{ h.event_type }}</span>
            <span>{{ h.notes }}</span>
            <span>{{ h.technician }}</span>
            <span>¥{{ h.cost_yuan }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { maintenanceAPI } from '@/api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const filterRisk = ref('')
const predictions = ref<any[]>([])
const selectedDevice = ref<any>(null)
const stats = reactive({ total: 0, critical: 0, high: 0, medium: 0, low: 0 })

import { reactive } from 'vue'

const filteredDevices = computed(() => {
  if (!filterRisk.value) return predictions.value
  return predictions.value.filter((p: any) => p.risk_level === filterRisk.value)
})

function probColor(p: number) {
  if (p > 0.65) return 'var(--red)'
  if (p > 0.4) return 'var(--amber)'
  if (p > 0.15) return 'var(--accent)'
  return 'var(--teal)'
}

function lifeClass(days: number) {
  if (days < 30) return 'text-red'
  if (days < 90) return 'text-amber'
  return 'text-teal'
}

function formatDate(iso: string) {
  if (!iso) return ''
  return iso.substring(0, 16).replace('T', ' ')
}

async function refreshAll() {
  loading.value = true
  try {
    const res: any = await maintenanceAPI.predictAll(filterRisk.value || undefined)
    predictions.value = res.predictions || []
    stats.total = res.total_devices || 0
    stats.critical = res.summary.critical_high || 0
    stats.high = res.summary.critical_high || 0
    stats.medium = res.summary.medium || 0
    stats.low = res.summary.low || 0
  } catch {
    ElMessage.error('获取预测数据失败')
  } finally {
    loading.value = false
  }
}

async function selectDevice(item: any) {
  try {
    const res: any = await maintenanceAPI.predictDevice(item.device_id)
    selectedDevice.value = res
  } catch {
    ElMessage.error('获取设备详情失败')
  }
}

onMounted(() => { refreshAll() })
</script>

<style scoped>
.maintenance-page { animation: fadeInUp 0.45s ease-out; }
.page-header { margin-bottom: 20px; }
.page-header .subtitle { font-size:13px; color:var(--text-muted); margin-left:12px; }
.stats-row { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:20px; }
.stat-card { display:flex; align-items:center; gap:12px; padding:16px; background:var(--bg-card); border-radius:var(--radius); border:1px solid var(--border); }
.stat-icon { width:40px; height:40px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:18px; flex-shrink:0; }
.stat-value { font-family:var(--font-display); font-size:26px; font-weight:700; line-height:1; }
.stat-label { font-size:12px; color:var(--text-muted); margin-top:2px; }
.toolbar { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }
.toolbar-left { display:flex; gap:6px; }
.btn { border:1px solid var(--border); background:var(--bg-card); color:var(--text-secondary); padding:6px 14px; border-radius:6px; cursor:pointer; font-size:13px; transition:all .2s; }
.btn:hover { border-color:var(--accent); color:var(--accent); }
.btn.active { background:rgba(0,168,255,0.1); border-color:var(--accent); color:var(--accent); font-weight:600; }
.btn-primary { background:linear-gradient(135deg,var(--accent),var(--aurora)); color:#fff; border:none; }
.btn-sm { padding:5px 12px; font-size:12px; }
.btn-text { color:var(--accent); border:none; background:none; cursor:pointer; font-size:13px; }
.btn-text:hover { text-decoration:underline; }

.card-header { font-size:14px; font-weight:600; color:var(--text-title); margin-bottom:14px; }

.loading-block { display:flex; flex-direction:column; align-items:center; gap:12px; padding:40px; color:var(--text-muted); }
.spinner { width:32px; height:32px; border:3px solid var(--border); border-top-color:var(--accent); border-radius:50%; animation:spin .8s linear infinite; }
@keyframes spin { to { transform:rotate(360deg); } }

.table-header { display:flex; padding:10px 14px; font-size:11px; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:.05em; border-bottom:2px solid var(--border); }
.table-header.s { font-size:11px; padding:8px 14px; }
.table-row { display:flex; align-items:center; padding:10px 14px; border-bottom:1px solid rgba(0,0,0,0.04); cursor:pointer; transition:background .15s; font-size:13px; }
.table-row.s { font-size:12px; cursor:default; }
.table-row:hover { background:rgba(0,168,255,0.03); }
.table-row.row-critical { background:rgba(239,68,68,0.04); }
.table-row.row-high { background:rgba(245,158,11,0.03); }
.col-id { width:100px; font-family:var(--font-mono); font-size:12px; }
.col-model { flex:1; }
.col-life { width:80px; }
.col-prob { width:160px; display:flex; align-items:center; gap:8px; }
.col-risk { width:80px; }
.col-type { width:120px; color:var(--text-muted); }
.col-action { width:60px; }
.prob-bar { width:80px; height:6px; background:var(--border); border-radius:3px; overflow:hidden; }
.prob-fill { height:100%; border-radius:3px; transition:width .5s; }

.tag { display:inline-block; padding:2px 8px; border-radius:4px; font-size:11px; font-weight:600; }
.tag-critical { background:var(--red-bg); color:var(--red); }
.tag-high { background:rgba(245,158,11,0.15); color:var(--amber); }
.tag-medium { background:rgba(0,168,255,0.1); color:var(--accent); }
.tag-low { background:rgba(0,210,160,0.1); color:var(--teal); }

.detail-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:20px; }
.dg-col h4 { font-size:13px; margin-bottom:10px; color:var(--text-title); }
.info-row { display:flex; justify-content:space-between; padding:5px 0; font-size:12px; border-bottom:1px solid rgba(0,0,0,0.03); }
.info-row span { color:var(--text-muted); }
.info-row strong { font-weight:600; }
hr { border:none; border-top:1px solid var(--border); margin:12px 0; }

.history-table { margin-top:8px; }
.history-table .table-row { cursor:default; }
.history-table .table-row:hover { background:transparent; }
.history-table .table-header span, .history-table .table-row span { flex:1; }

.text-red { color:var(--red); }
.text-amber { color:var(--amber); }
.text-teal { color:var(--teal); }

@media (max-width:1200px) { .stats-row { grid-template-columns:repeat(2,1fr); } .detail-grid { grid-template-columns:1fr; } }
</style>
