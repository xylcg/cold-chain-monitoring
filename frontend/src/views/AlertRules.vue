<template>
  <div class="alert-rules">
    <div class="page-header">
      <h2 class="page-title">告警规则配置</h2>
      <button class="btn-primary" @click="showAddDialog = true">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" style="margin-right:4px;vertical-align:-2px"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        添加规则
      </button>
    </div>

    <div class="filter-bar">
      <el-select v-model="categoryFilter" placeholder="全部分类" style="width:160px" @change="fetchRules">
        <el-option label="全部" value="" />
        <el-option label="温控类" value="温控类" />
        <el-option label="设备类" value="设备类" />
        <el-option label="行驶类" value="行驶类" />
        <el-option label="作业类" value="作业类" />
        <el-option label="环境类" value="环境类" />
        <el-option label="高敏专项" value="高敏专项" />
      </el-select>
      <el-select v-model="severityFilter" placeholder="全部级别" style="width:120px" @change="fetchRules">
        <el-option label="全部" value="" />
        <el-option label="一般" value="normal" />
        <el-option label="严重" value="severe" />
        <el-option label="紧急" value="critical" />
      </el-select>
    </div>

    <div class="glass-card">
      <el-table :data="filteredRules" stripe>
        <el-table-column prop="category" label="分类" width="80">
          <template #default="{ row }">
            <span class="category-badge" :class="getCategoryClass(row.category)">{{ row.category || '其他' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="type" label="规则类型" width="180">
          <template #default="{ row }">{{ getRuleTypeLabel(row.type) }}</template>
        </el-table-column>
        <el-table-column prop="field" label="监控字段" width="120">
          <template #default="{ row }">{{ getFieldLabel(row.field) }}</template>
        </el-table-column>
        <el-table-column prop="op" label="条件" width="80">
          <template #default="{ row }">
            <code class="op-code">{{ getOpLabel(row.op) }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="value" label="阈值" width="100">
          <template #default="{ row }">
            <span class="thresh-val">{{ row.value }}<span v-if="getUnit(row.field)" class="thresh-unit">{{ getUnit(row.field) }}</span></span>
          </template>
        </el-table-column>
        <el-table-column prop="severity" label="严重等级" width="100">
          <template #default="{ row }">
            <span class="sev-badge" :class="row.severity">{{ getSeverityLabel(row.severity) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="msg" label="告警描述" min-width="200" />
        <el-table-column label="预警开关" width="110">
          <template #default="{ row }">
            <el-switch v-model="row.enabled" @change="toggleRule(row)" active-text="开启" inactive-text="关闭" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90">
          <template #default="{ row }">
            <el-button type="danger" size="small" text @click="deleteRule(row.type)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="showAddDialog" title="添加告警规则" width="520px">
      <el-form :model="newRule" label-width="100px">
        <el-form-item label="规则名称">
          <el-input v-model="newRule.rule_name" placeholder="如：温度超标告警" />
        </el-form-item>
        <el-form-item label="告警分类">
          <el-select v-model="newRule.category" style="width:100%" @change="updateRuleTypes">
            <el-option label="温控类" value="温控类" />
            <el-option label="设备类" value="设备类" />
            <el-option label="行驶类" value="行驶类" />
            <el-option label="作业类" value="作业类" />
            <el-option label="环境类" value="环境类" />
            <el-option label="高敏专项" value="高敏专项" />
          </el-select>
        </el-form-item>
        <el-form-item label="规则类型">
          <el-select v-model="newRule.rule_type" style="width:100%">
            <el-option v-for="opt in filteredRuleTypes" :key="opt.value" :label="opt.label" :value="opt.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="监控字段">
          <el-select v-model="newRule.condition_field" style="width:100%">
            <el-option label="温度" value="temperature" />
            <el-option label="湿度" value="humidity" />
            <el-option label="振动" value="vibration" />
            <el-option label="车门状态" value="door_status" />
            <el-option label="冷机状态" value="cold_car_status" />
            <el-option label="数据质量" value="data_quality" />
            <el-option label="心跳" value="heartbeat" />
            <el-option label="速度" value="speed" />
            <el-option label="路径偏差" value="path_deviation" />
            <el-option label="外部温度" value="external_temp" />
            <el-option label="疫苗温度" value="vaccine_temp" />
            <el-option label="装载时长" value="loading_duration" />
            <el-option label="卸载时长" value="unloading_duration" />
          </el-select>
        </el-form-item>
        <el-form-item label="条件">
          <el-select v-model="newRule.condition_operator" style="width:100%">
            <el-option label="大于" value=">" />
            <el-option label="小于" value="<" />
            <el-option label="等于" value="==" />
            <el-option label="大于等于" value=">=" />
            <el-option label="小于等于" value="<=" />
            <el-option label="超时" value="timeout" />
            <el-option label="变化率" value="change_rate" />
          </el-select>
        </el-form-item>
        <el-form-item label="阈值">
          <el-input-number v-model="newRule.condition_value" :precision="1" style="width:100%" />
        </el-form-item>
        <el-form-item label="严重等级">
          <el-select v-model="newRule.severity" style="width:100%">
            <el-option label="一般" value="normal" />
            <el-option label="严重" value="severe" />
            <el-option label="紧急" value="critical" />
          </el-select>
        </el-form-item>
        <el-form-item label="预警开关">
          <el-switch v-model="newRule.enabled" active-text="开启" inactive-text="关闭" />
        </el-form-item>
        <el-form-item label="冷却时间(秒)">
          <el-input-number v-model="newRule.cooldown_seconds" :min="30" :max="3600" style="width:100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="addRule">确认添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { alertAPI } from '@/api'
import { ElMessage } from 'element-plus'

const rules = ref<any[]>([])
const showAddDialog = ref(false)
const categoryFilter = ref('')
const severityFilter = ref('')

const newRule = ref({
  rule_name: '', rule_type: '', category: '温控类',
  condition_field: 'temperature', condition_operator: '>',
  condition_value: 8.0, severity: 'severe', cooldown_seconds: 300,
  enabled: true,
})

const allRuleTypes = [
  { label: '温度超标', value: 'temperature_high', category: '温控类' },
  { label: '温度严重超标', value: 'temperature_critical', category: '温控类' },
  { label: '温度偏低', value: 'temperature_low', category: '温控类' },
  { label: '温度骤升', value: 'temperature_spike', category: '温控类' },
  { label: '温度骤变', value: 'temperature_change', category: '温控类' },
  { label: '湿度过高', value: 'humidity_high', category: '温控类' },
  { label: '振动异常', value: 'vibration_high', category: '设备类' },
  { label: '冷机故障', value: 'cold_car_failure', category: '设备类' },
  { label: '数据质量异常', value: 'data_quality_low', category: '设备类' },
  { label: '车门超时开启', value: 'door_open_timeout', category: '设备类' },
  { label: '设备离线', value: 'device_offline', category: '设备类' },
  { label: '路径偏离', value: 'path_deviation', category: '行驶类' },
  { label: '速度异常', value: 'speed_anomaly', category: '行驶类' },
  { label: '电子围栏越界', value: 'zone_breach', category: '行驶类' },
  { label: '装载超时', value: 'loading_timeout', category: '作业类' },
  { label: '卸载超时', value: 'unloading_timeout', category: '作业类' },
  { label: '外部高温', value: 'external_temp_high', category: '环境类' },
  { label: '雨天告警', value: 'rain_alert', category: '环境类' },
  { label: '极端天气', value: 'extreme_weather', category: '环境类' },
  { label: '疫苗温度突破', value: 'vaccine_temp_breach', category: '高敏专项' },
  { label: '血液冷链断裂', value: 'blood_chain_break', category: '高敏专项' },
]

const filteredRuleTypes = computed(() => {
  if (!newRule.value.category) return allRuleTypes
  return allRuleTypes.filter(r => r.category === newRule.value.category)
})

const filteredRules = computed(() => {
  let result = rules.value
  if (categoryFilter.value) {
    result = result.filter(r => r.category === categoryFilter.value)
  }
  if (severityFilter.value) {
    result = result.filter(r => r.severity === severityFilter.value)
  }
  return result
})

function updateRuleTypes() {
  const types = filteredRuleTypes.value
  if (types.length > 0) {
    newRule.value.rule_type = types[0].value
  }
}

function getRuleTypeLabel(type: string) {
  const found = allRuleTypes.find(r => r.value === type)
  return found ? found.label : type
}

function getFieldLabel(field: string) {
  const map: Record<string, string> = {
    temperature: '温度',
    humidity: '湿度',
    vibration: '振动',
    door_status: '车门状态',
    cold_car_status: '冷机状态',
    data_quality: '数据质量',
    heartbeat: '心跳间隔',
    speed: '速度',
    path_deviation: '路径偏差',
    external_temp: '外部温度',
    vaccine_temp: '疫苗温度',
    loading_duration: '装载时长',
    unloading_duration: '卸载时长',
  }
  return map[field] || field
}

function getUnit(field: string) {
  const map: Record<string, string> = {
    temperature: '°C',
    humidity: '%',
    heartbeat: '秒',
    speed: 'km/h',
    external_temp: '°C',
    vaccine_temp: '°C',
    loading_duration: '分钟',
    unloading_duration: '分钟',
  }
  return map[field] || ''
}

function getOpLabel(op: string) {
  const map: Record<string, string> = {
    '>': '大于',
    '<': '小于',
    '==': '等于',
    '>=': '大于等于',
    '<=': '小于等于',
    timeout: '超时',
    change_rate: '变化率',
  }
  return map[op] || op
}

function getSeverityLabel(severity: string) {
  const map: Record<string, string> = { normal: '一般', severe: '严重', critical: '紧急' }
  return map[severity] || severity
}

function getCategoryClass(category: string) {
  const map: Record<string, string> = {
    '温控类': 'temp',
    '设备类': 'device',
    '行驶类': 'drive',
    '作业类': 'work',
    '环境类': 'env',
    '高敏专项': 'high-sens',
  }
  return map[category] || 'other'
}

async function fetchRules() {
  try {
    const data: any = await alertAPI.getRules()
    rules.value = (data.rules || []).map((r: any) => ({ ...r, enabled: r.enabled !== false }))
  } catch {
    ElMessage.warning('加载告警规则失败')
  }
}

async function addRule() {
  try {
    await alertAPI.createRule(newRule.value)
    ElMessage.success('规则添加成功')
    showAddDialog.value = false
    fetchRules()
    newRule.value = {
      rule_name: '', rule_type: '', category: '温控类',
      condition_field: 'temperature', condition_operator: '>',
      condition_value: 8.0, severity: 'severe', cooldown_seconds: 300,
      enabled: true,
    }
    updateRuleTypes()
  } catch {
    ElMessage.error('添加规则失败')
  }
}

async function deleteRule(ruleType: string) {
  try {
    await alertAPI.deleteRule(ruleType)
    ElMessage.success('规则已删除')
    fetchRules()
  } catch {
    ElMessage.error('删除规则失败')
  }
}

async function toggleRule(row: any) {
  try {
    await alertAPI.createRule({
      rule_type: row.type,
      condition_field: row.field,
      condition_operator: row.op,
      condition_value: row.value,
      severity: row.severity,
      cooldown_seconds: row.cooldown_seconds || 300,
      enabled: row.enabled,
      rule_name: row.msg,
      category: row.category,
    })
    ElMessage.success(row.enabled ? '规则已开启' : '规则已关闭')
  } catch {
    ElMessage.error('操作失败')
    row.enabled = !row.enabled
  }
}

onMounted(() => {
  updateRuleTypes()
  fetchRules()
})
</script>

<style scoped>
.alert-rules { animation: fadeInUp 0.45s ease-out; max-width: 1200px; }

.filter-bar {
  display: flex; gap: 12px; margin-bottom: 16px;
}

.category-badge {
  font-size: 10px; font-weight: 700; padding: 2px 8px;
  border-radius: 4px; font-family: var(--font-mono);
}
.category-badge.temp { color: var(--accent); background: var(--accent-bg); }
.category-badge.device { color: var(--amber); background: var(--amber-bg); }
.category-badge.drive { color: var(--teal); background: var(--teal-bg); }
.category-badge.work { color: var(--purple); background: var(--purple-bg); }
.category-badge.env { color: #059669; background: rgba(5,150,105,0.1); }
.category-badge.high-sens { color: var(--red); background: var(--red-bg); }

.op-code {
  font-family: var(--font-mono); font-size: 13px; color: var(--accent);
  background: var(--accent-bg); padding: 2px 8px; border-radius: 4px; font-weight: 600;
}
.thresh-val {
  font-family: var(--font-display); font-weight: 700; font-size: 14px; color: var(--text-title);
}
.thresh-unit { font-family: var(--font-mono); font-size: 12px; color: var(--text-muted); margin-left: 2px; }

.sev-badge {
  font-size: 11px; font-weight: 700; padding: 3px 10px;
  border-radius: 4px; font-family: var(--font-mono); letter-spacing: 0.04em;
}
.sev-badge.normal { color: var(--amber); background: var(--amber-bg); border: 1px solid rgba(245,158,11,0.15); }
.sev-badge.severe { color: var(--red); background: var(--red-bg); border: 1px solid rgba(239,68,68,0.15); }
.sev-badge.critical { color: #fff; background: var(--red); }
</style>