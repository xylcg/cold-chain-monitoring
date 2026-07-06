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

    <div class="alert-tabs">
      <button class="tab-btn" :class="{ active: activeTab === 'all' }" @click="activeTab = 'all'">全部告警</button>
      <button class="tab-btn" :class="{ active: activeTab === 'critical' }" @click="activeTab = 'critical'">
        <span class="tab-badge crit">紧急</span> {{ criticalCount }}
      </button>
      <button class="tab-btn" :class="{ active: activeTab === 'severe' }" @click="activeTab = 'severe'">
        <span class="tab-badge red">严重</span> {{ severeCount }}
      </button>
      <button class="tab-btn" :class="{ active: activeTab === 'normal' }" @click="activeTab = 'normal'">
        <span class="tab-badge amber">一般</span> {{ normalCount }}
      </button>
    </div>

    <div v-if="filteredAlerts.length === 0" class="empty-block">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--teal)" stroke-width="1.5" stroke-linecap="round">
        <circle cx="12" cy="12" r="10"/>
        <polyline points="8 12 11 15 16 9"/>
      </svg>
      <p>当前无{{ activeTab === 'all' ? '' : alertLevelText[activeTab] }}告警</p>
      <span>所有设备运行正常，温控指标在安全范围内</span>
    </div>

    <div v-else class="alert-grid">
      <div v-for="alert in filteredAlerts" :key="alert.alert_id" class="alert-card" :class="alert.severity">
        <div class="card-header">
          <div class="header-left">
            <span class="severity-badge" :class="alert.severity">
              {{ alertLevelText[alert.severity] }}
            </span>
            <span class="category-tag">{{ alert.category }}</span>
          </div>
          <span class="alert-time">{{ formatTime(alert.timestamp) }}</span>
        </div>
        <div class="card-body">
          <code class="device-id">{{ alert.device_id }}</code>
          <p class="alert-message">{{ alert.message }}</p>
          <div class="alert-values" v-if="alert.sensor_value !== undefined">
            <span class="value-item">当前值: <strong>{{ alert.sensor_value }}</strong></span>
            <span class="value-item">阈值: {{ alert.threshold_value }}</span>
          </div>
        </div>
        <div class="card-footer">
          <div class="alert-status" :class="alert.status || 'active'">
            {{ alert.status === 'resolved' ? '已解决' : alert.status === 'acknowledged' ? '已确认' : '待处理' }}
          </div>
          <div class="card-actions">
            <button v-if="alert.status !== 'resolved'" class="action-btn" @click="handleAcknowledge(alert)">确认</button>
            <button v-if="alert.status !== 'resolved'" class="action-btn primary" @click="handleResolve(alert)">解决</button>
            <button v-if="alert.severity === 'critical' && !alert.emergency_plan" class="action-btn danger" @click="handleTriggerPlan(alert)">启动预案</button>
          </div>
        </div>
        <div v-if="alert.emergency_plan" class="emergency-plan-summary">
          <div class="plan-header">
            <span class="plan-icon">🚨</span>
            <span class="plan-name">{{ alert.emergency_plan.plan_name }}</span>
            <span class="plan-status" :class="alert.emergency_plan.status">
              {{ alert.emergency_plan.status === 'completed' ? '已完成' : alert.emergency_plan.status === 'in_progress' ? '执行中' : '待启动' }}
            </span>
          </div>
          <div class="plan-progress">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: planProgress(alert.emergency_plan) + '%' }"></div>
            </div>
            <span class="progress-text">{{ alert.emergency_plan.steps.filter(s => s.status === 'completed').length }}/{{ alert.emergency_plan.steps.length }} 步骤</span>
          </div>
          <button class="view-plan-btn" @click="viewEmergencyPlan(alert.emergency_plan)">查看预案详情</button>
        </div>
      </div>
    </div>

    <div class="stats-row">
      <div class="stat-card">
        <span class="stat-icon normal">✓</span>
        <div class="stat-info">
          <span class="stat-value">{{ normalCount }}</span>
          <span class="stat-label">一般预警</span>
        </div>
        <span class="stat-desc">司机自主处理</span>
      </div>
      <div class="stat-card">
        <span class="stat-icon severe">⚠</span>
        <div class="stat-info">
          <span class="stat-value">{{ severeCount }}</span>
          <span class="stat-label">严重预警</span>
        </div>
        <span class="stat-desc">需人工介入</span>
      </div>
      <div class="stat-card">
        <span class="stat-icon critical">🚨</span>
        <div class="stat-info">
          <span class="stat-value">{{ criticalCount }}</span>
          <span class="stat-label">紧急预警</span>
        </div>
        <span class="stat-desc">启动应急预案</span>
      </div>
    </div>

    <div class="glass-card">
      <h3 class="sec-title">三级预警体系说明</h3>
      <div class="sev-list">
        <div class="sev-item">
          <span class="sev-badge amber">一般</span>
          <div class="sev-content">
            <span class="sev-title">轻微风险</span>
            <span class="sev-desc">温度轻微波动、设备低电量提醒等，推送至司机终端自主处理</span>
          </div>
        </div>
        <div class="sev-item">
          <span class="sev-badge red">严重</span>
          <div class="sev-content">
            <span class="sev-title">需人工介入</span>
            <span class="sev-desc">温度超标、设备异常等，通知区域经理和维修团队立即响应</span>
          </div>
        </div>
        <div class="sev-item">
          <span class="sev-badge crit">紧急</span>
          <div class="sev-content">
            <span class="sev-title">启动应急预案</span>
            <span class="sev-desc">温度失控、冷机故障、高敏货物异常等，立即启动应急预案并通知客户</span>
          </div>
        </div>
      </div>
    </div>

    <el-dialog v-model="showPlan" :title="selectedPlan?.plan_name || '应急预案'" width="600px" class="custom-dialog">
      <div v-if="selectedPlan" class="plan-detail">
        <div class="plan-info">
          <div class="info-row">
            <span class="info-label">预案ID</span>
            <code class="info-value">{{ selectedPlan.plan_id }}</code>
          </div>
          <div class="info-row">
            <span class="info-label">优先级</span>
            <span class="info-value priority" :class="selectedPlan.priority">{{ selectedPlan.priority }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">状态</span>
            <span class="info-value status" :class="selectedPlan.status">{{ selectedPlan.status === 'completed' ? '已完成' : selectedPlan.status === 'in_progress' ? '执行中' : '待启动' }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">触发时间</span>
            <span class="info-value">{{ formatTime(selectedPlan.trigger_time) }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">关联设备</span>
            <code class="info-value">{{ selectedPlan.device_id }}</code>
          </div>
        </div>
        <div class="plan-steps">
          <h4 class="steps-title">应急处置步骤</h4>
          <div v-for="step in selectedPlan.steps" :key="step.step" class="step-item" :class="step.status">
            <div class="step-header">
              <span class="step-number">{{ step.step }}</span>
              <span class="step-title">{{ step.title }}</span>
              <span class="step-status" :class="step.status">
                {{ step.status === 'completed' ? '✓ 已完成' : step.status === 'in_progress' ? '● 进行中' : '○ 待处理' }}
              </span>
            </div>
            <p class="step-desc">{{ step.description }}</p>
            <div v-if="step.updated_at" class="step-meta">
              <span>更新时间: {{ formatTime(step.updated_at) }}</span>
              <span v-if="step.updated_by">更新人: {{ step.updated_by }}</span>
            </div>
            <div v-if="step.status !== 'completed'" class="step-actions">
              <button class="step-btn" @click="updateStep(step.step, 'in_progress')">开始执行</button>
              <button class="step-btn primary" @click="updateStep(step.step, 'completed')">标记完成</button>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>

    <el-dialog v-model="showResolve" :title="`解决告警 - ${resolvingAlert?.alert_id}`" width="500px" class="custom-dialog">
      <div v-if="resolvingAlert" class="resolve-form">
        <p class="resolve-message">{{ resolvingAlert.message }}</p>
        <el-form :model="resolveForm" label-width="80px">
          <el-form-item label="解决方式">
            <el-input v-model="resolveForm.resolution" placeholder="请输入解决方式" />
          </el-form-item>
          <el-form-item label="备注">
            <el-textarea v-model="resolveForm.notes" placeholder="请输入备注信息" :rows="3" />
          </el-form-item>
        </el-form>
        <div class="resolve-actions">
          <el-button @click="showResolve = false">取消</el-button>
          <el-button type="primary" @click="confirmResolve">确认解决</el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAppStore } from '@/stores/app'
import { formatTime } from '@/utils'
import { alertAPI } from '@/api'
import { ElMessage } from 'element-plus'

const store = useAppStore()
const activeTab = ref('all')
const alerts = ref<any[]>([])
const showPlan = ref(false)
const selectedPlan = ref<any>(null)
const showResolve = ref(false)
const resolvingAlert = ref<any>(null)
const resolveForm = ref({ resolution: '', notes: '' })

const alertLevelText: Record<string, string> = {
  normal: '一般',
  severe: '严重',
  critical: '紧急',
}

const filteredAlerts = computed(() => {
  if (activeTab.value === 'all') return alerts.value
  return alerts.value.filter(a => a.severity === activeTab.value)
})

const normalCount = computed(() => alerts.value.filter(a => a.severity === 'normal').length)
const severeCount = computed(() => alerts.value.filter(a => a.severity === 'severe').length)
const criticalCount = computed(() => alerts.value.filter(a => a.severity === 'critical').length)

async function loadAlerts() {
  try {
    const res: any = await alertAPI.getActiveAlerts()
    alerts.value = res.devices?.flatMap((d: any) => d.alerts) || []
    if (alerts.value.length === 0) {
      const historyRes: any = await alertAPI.getAlerts({ limit: 50 })
      alerts.value = historyRes.alerts || []
    }
  } catch (e) {
    console.error('加载告警失败', e)
  }
}

function handleAcknowledge(alert: any) {
  alertAPI.acknowledge(alert.alert_id, 'acknowledged').then(() => {
    alert.status = 'acknowledged'
    ElMessage.success('告警已确认')
    loadAlerts()
  }).catch(() => {
    ElMessage.error('确认失败')
  })
}

function handleResolve(alert: any) {
  resolvingAlert.value = alert
  resolveForm.value = { resolution: '', notes: '' }
  showResolve.value = true
}

function confirmResolve() {
  if (!resolvingAlert.value) return
  alertAPI.resolve(resolvingAlert.value.alert_id, resolveForm.value.resolution, resolveForm.value.notes).then(() => {
    ElMessage.success('告警已解决')
    showResolve.value = false
    loadAlerts()
  }).catch(() => {
    ElMessage.error('解决失败')
  })
}

function handleTriggerPlan(alert: any) {
  alertAPI.triggerEmergencyPlan(alert.alert_id).then((res: any) => {
    alert.emergency_plan = res.plan
    ElMessage.success('应急预案已触发')
  }).catch((e: any) => {
    ElMessage.error(e.response?.data?.detail || '触发失败')
  })
}

function viewEmergencyPlan(plan: any) {
  selectedPlan.value = plan
  showPlan.value = true
}

function updateStep(stepNum: number, status: string) {
  if (!selectedPlan.value) return
  alertAPI.updateEmergencyStep(selectedPlan.value.plan_id, stepNum, status).then((res: any) => {
    selectedPlan.value = res.plan
    ElMessage.success('步骤状态已更新')
  }).catch(() => {
    ElMessage.error('更新失败')
  })
}

function planProgress(plan: any) {
  if (!plan.steps || plan.steps.length === 0) return 0
  const completed = plan.steps.filter((s: any) => s.status === 'completed').length
  return Math.round((completed / plan.steps.length) * 100)
}

onMounted(() => {
  loadAlerts()
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

.alert-tabs {
  display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap;
}

.tab-btn {
  padding: 8px 16px; border-radius: var(--radius); border: 1px solid var(--border-light);
  background: var(--bg-card); color: var(--text-secondary); font-size: 13px;
  cursor: pointer; transition: all 0.2s; display: flex; align-items: center; gap: 6px;
}

.tab-btn:hover { border-color: var(--accent); color: var(--accent); }
.tab-btn.active { border-color: var(--accent); background: var(--accent-bg); color: var(--accent); }

.tab-badge {
  font-size: 10px; font-weight: 700; padding: 1px 6px; border-radius: 4px; font-family: var(--font-mono);
}
.tab-badge.crit { color: #fff; background: var(--red); }
.tab-badge.red { color: var(--red); background: var(--red-bg); }
.tab-badge.amber { color: var(--amber); background: var(--amber-bg); }

.empty-block {
  text-align: center; padding: 60px 0; color: var(--text-muted);
}
.empty-block p { font-size: 15px; font-weight: 500; margin: 10px 0 4px; color: var(--text-secondary); }
.empty-block span { font-size: 12px; }

.alert-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
  gap: 16px; margin-bottom: 24px;
}

.alert-card {
  background: var(--bg-card); backdrop-filter: var(--blur-card); -webkit-backdrop-filter: var(--blur-card);
  border: 1px solid var(--border-light); border-radius: var(--radius-lg);
  padding: 20px; box-shadow: var(--shadow-sm); transition: all 0.3s ease;
}

.alert-card:hover { transform: translateY(-2px); }
.alert-card.normal { border-left: 3px solid var(--amber); }
.alert-card.severe { border-left: 3px solid var(--red); }
.alert-card.critical { border-left: 3px solid var(--red); background: linear-gradient(135deg, var(--red-bg) 0%, var(--bg-card) 100%); }

.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }

.header-left { display: flex; align-items: center; gap: 8px; }

.severity-badge {
  font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 4px; font-family: var(--font-mono);
}
.severity-badge.normal { color: var(--amber); background: var(--amber-bg); border: 1px solid rgba(245,158,11,0.2); }
.severity-badge.severe { color: var(--red); background: var(--red-bg); border: 1px solid rgba(239,68,68,0.2); }
.severity-badge.critical { color: #fff; background: var(--red); }

.category-tag {
  font-size: 10px; padding: 2px 8px; border-radius: 4px; background: var(--bg-input); color: var(--text-muted);
}

.alert-time { font-size: 11px; color: var(--text-muted); font-family: var(--font-mono); }

.card-body { margin-bottom: 14px; }

.device-id {
  font-family: var(--font-mono); font-size: 12px; color: var(--accent);
  background: var(--accent-bg); padding: 3px 8px; border-radius: 4px; margin-bottom: 8px; display: inline-block;
}

.alert-message {
  font-size: 14px; font-weight: 500; color: var(--text-primary); margin: 0; line-height: 1.5;
}

.alert-values {
  display: flex; gap: 16px; margin-top: 8px; font-size: 12px; color: var(--text-secondary);
}

.value-item strong { color: var(--text-primary); }

.card-footer {
  display: flex; justify-content: space-between; align-items: center; padding-top: 12px;
  border-top: 1px solid var(--border-light);
}

.alert-status {
  font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 4px; font-family: var(--font-mono);
}
.alert-status.active { color: var(--amber); background: var(--amber-bg); }
.alert-status.acknowledged { color: var(--accent); background: var(--accent-bg); }
.alert-status.resolved { color: var(--teal); background: var(--teal-bg); }

.card-actions { display: flex; gap: 6px; }

.action-btn {
  padding: 5px 12px; font-size: 11px; border-radius: 4px; border: 1px solid var(--border-light);
  background: transparent; color: var(--text-secondary); cursor: pointer; transition: all 0.2s;
}

.action-btn:hover { border-color: var(--accent); color: var(--accent); }
.action-btn.primary { background: var(--accent); color: #fff; border-color: var(--accent); }
.action-btn.primary:hover { background: #0284c7; }
.action-btn.danger { background: var(--red); color: #fff; border-color: var(--red); }
.action-btn.danger:hover { background: #dc2626; }

.emergency-plan-summary {
  margin-top: 14px; padding-top: 14px; border-top: 1px solid var(--border-light);
}

.plan-header {
  display: flex; align-items: center; gap: 8px; margin-bottom: 10px;
}

.plan-icon { font-size: 16px; }
.plan-name { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.plan-status {
  font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 4px; font-family: var(--font-mono);
  margin-left: auto;
}
.plan-status.completed { color: var(--teal); background: var(--teal-bg); }
.plan-status.in_progress { color: var(--amber); background: var(--amber-bg); }
.plan-status.pending { color: var(--text-muted); background: var(--bg-input); }

.plan-progress {
  display: flex; align-items: center; gap: 10px; margin-bottom: 10px;
}

.progress-bar {
  flex: 1; height: 6px; background: var(--bg-input); border-radius: 3px; overflow: hidden;
}

.progress-fill {
  height: 100%; background: linear-gradient(90deg, var(--accent), var(--teal)); border-radius: 3px;
  transition: width 0.3s ease;
}

.progress-text { font-size: 11px; color: var(--text-muted); font-family: var(--font-mono); }

.view-plan-btn {
  width: 100%; padding: 8px; font-size: 12px; border-radius: 4px;
  border: 1px solid var(--accent); background: transparent; color: var(--accent);
  cursor: pointer; transition: all 0.2s;
}
.view-plan-btn:hover { background: var(--accent-bg); }

.stats-row {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px;
}

.stat-card {
  background: var(--bg-card); border-radius: var(--radius-lg); padding: 20px;
  display: flex; flex-direction: column; gap: 8px;
}

.stat-icon {
  width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center;
  justify-content: center; font-size: 18px; font-weight: 700;
}
.stat-icon.normal { background: var(--amber-bg); color: var(--amber); }
.stat-icon.severe { background: var(--red-bg); color: var(--red); }
.stat-icon.critical { background: var(--red); color: #fff; }

.stat-info { display: flex; align-items: baseline; gap: 4px; }
.stat-value { font-family: var(--font-display); font-size: 28px; font-weight: 800; color: var(--text-primary); }
.stat-label { font-size: 13px; color: var(--text-secondary); }
.stat-desc { font-size: 11px; color: var(--text-muted); }

.sec-title { font-size: 15px; font-weight: 700; color: var(--text-title); margin-bottom: 14px; }

.sev-list { display: flex; flex-direction: column; gap: 12px; }

.sev-item {
  display: flex; align-items: flex-start; gap: 14px; padding: 14px;
  background: var(--bg-input); border-radius: var(--radius);
}

.sev-badge {
  font-size: 11px; font-weight: 700; padding: 3px 12px; border-radius: 4px;
  font-family: var(--font-mono); letter-spacing: 0.04em; flex-shrink: 0;
}
.sev-badge.amber { color: var(--amber); background: var(--amber-bg); border: 1px solid rgba(245,158,11,0.15); }
.sev-badge.red { color: var(--red); background: var(--red-bg); border: 1px solid rgba(239,68,68,0.15); }
.sev-badge.crit { color: #fff; background: var(--red); }

.sev-content { display: flex; flex-direction: column; gap: 4px; flex: 1; }
.sev-title { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.sev-desc { font-size: 12px; color: var(--text-secondary); }

.plan-detail { display: flex; flex-direction: column; gap: 20px; }

.plan-info {
  background: var(--bg-input); border-radius: var(--radius); padding: 16px;
}

.info-row {
  display: flex; justify-content: space-between; align-items: center; padding: 8px 0;
  border-bottom: 1px solid var(--border-light);
}
.info-row:last-child { border-bottom: none; }

.info-label { font-size: 12px; color: var(--text-muted); }
.info-value { font-size: 13px; font-weight: 500; color: var(--text-primary); font-family: var(--font-mono); }
.info-value.priority {
  padding: 2px 8px; border-radius: 4px; font-size: 11px;
}
.info-value.priority.high { color: var(--red); background: var(--red-bg); }
.info-value.priority.medium { color: var(--amber); background: var(--amber-bg); }
.info-value.status.completed { color: var(--teal); }
.info-value.status.in_progress { color: var(--amber); }

.plan-steps { display: flex; flex-direction: column; gap: 12px; }

.steps-title { font-size: 14px; font-weight: 600; color: var(--text-primary); margin: 0; }

.step-item {
  padding: 14px; border-radius: var(--radius); border: 1px solid var(--border-light);
  transition: all 0.2s;
}
.step-item.completed { background: var(--teal-bg); border-color: rgba(0,210,160,0.2); }
.step-item.in_progress { background: var(--amber-bg); border-color: rgba(245,158,11,0.2); }

.step-header {
  display: flex; align-items: center; gap: 10px; margin-bottom: 8px;
}

.step-number {
  width: 24px; height: 24px; border-radius: 50%; background: var(--bg-card);
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700; color: var(--text-secondary); font-family: var(--font-mono);
}

.step-title { font-size: 13px; font-weight: 600; color: var(--text-primary); flex: 1; }

.step-status {
  font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 4px; font-family: var(--font-mono);
}
.step-status.completed { color: var(--teal); background: var(--bg-card); }
.step-status.in_progress { color: var(--amber); background: var(--bg-card); }
.step-status.pending { color: var(--text-muted); background: var(--bg-card); }

.step-desc {
  font-size: 12px; color: var(--text-secondary); margin: 0; line-height: 1.5;
}

.step-meta {
  display: flex; gap: 12px; margin-top: 8px; font-size: 11px; color: var(--text-muted);
}

.step-actions {
  display: flex; gap: 6px; margin-top: 10px;
}

.step-btn {
  padding: 5px 12px; font-size: 11px; border-radius: 4px; border: 1px solid var(--border-light);
  background: transparent; color: var(--text-secondary); cursor: pointer; transition: all 0.2s;
}
.step-btn:hover { border-color: var(--accent); color: var(--accent); }
.step-btn.primary { background: var(--accent); color: #fff; border-color: var(--accent); }

.resolve-form { display: flex; flex-direction: column; gap: 16px; }

.resolve-message {
  font-size: 14px; color: var(--text-primary); margin: 0; padding: 12px;
  background: var(--bg-input); border-radius: var(--radius);
}

.resolve-actions {
  display: flex; justify-content: flex-end; gap: 10px; margin-top: 8px;
}

@media (max-width: 768px) {
  .alert-grid { grid-template-columns: 1fr; }
  .stats-row { grid-template-columns: 1fr; }
}
</style>