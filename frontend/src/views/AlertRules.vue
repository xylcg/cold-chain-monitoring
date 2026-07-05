<template>
  <div class="alert-rules">
    <div class="page-header">
      <h2 class="page-title">告警规则配置</h2>
      <button class="btn-primary" @click="showAddDialog = true">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" style="margin-right:4px;vertical-align:-2px"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        添加规则
      </button>
    </div>

    <div class="glass-card">
      <el-table :data="rules" stripe>
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
            <span class="thresh-val">{{ row.value }}<span v-if="row.field === 'heartbeat'" class="thresh-unit">秒</span></span>
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

    <el-dialog v-model="showAddDialog" title="添加告警规则" width="480px">
      <el-form :model="newRule" label-width="100px">
        <el-form-item label="规则名称">
          <el-input v-model="newRule.rule_name" placeholder="如：温度超标告警" />
        </el-form-item>
        <el-form-item label="规则类型">
          <el-select v-model="newRule.rule_type" style="width:100%">
            <el-option label="温度超标" value="temperature_high" />
            <el-option label="温度严重超标" value="temperature_critical" />
            <el-option label="温度偏低" value="temperature_low" />
            <el-option label="温度骤升" value="temperature_spike" />
            <el-option label="温度骤变" value="temperature_change" />
            <el-option label="湿度过高" value="humidity_high" />
            <el-option label="振动异常" value="vibration_high" />
            <el-option label="冷机故障" value="cold_car_failure" />
            <el-option label="数据质量异常" value="data_quality_low" />
            <el-option label="车门超时开启" value="door_open_timeout" />
            <el-option label="设备离线" value="device_offline" />
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
import { ref, onMounted } from 'vue'
import { alertAPI } from '@/api'
import { ElMessage } from 'element-plus'

const rules = ref<any[]>([])
const showAddDialog = ref(false)
const newRule = ref({
  rule_name: '', rule_type: '',
  condition_field: 'temperature', condition_operator: '>',
  condition_value: 8.0, severity: 'severe', cooldown_seconds: 300,
  enabled: true,
})

function getRuleTypeLabel(type: string) {
  const map: Record<string, string> = {
    temperature_high: '温度超标',
    temperature_critical: '温度严重超标',
    temperature_low: '温度偏低',
    temperature_spike: '温度骤升',
    temperature_change: '温度骤变',
    humidity_high: '湿度过高',
    vibration_high: '振动异常',
    cold_car_failure: '冷机故障',
    data_quality_low: '数据质量异常',
    door_open_timeout: '车门超时开启',
    device_offline: '设备离线',
  }
  return map[type] || type
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
  }
  return map[field] || field
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
      rule_name: '', rule_type: '',
      condition_field: 'temperature', condition_operator: '>',
      condition_value: 8.0, severity: 'severe', cooldown_seconds: 300,
      enabled: true,
    }
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
    })
    ElMessage.success(row.enabled ? '规则已开启' : '规则已关闭')
  } catch {
    ElMessage.error('操作失败')
    row.enabled = !row.enabled
  }
}

onMounted(() => { fetchRules() })
</script>

<style scoped>
.alert-rules { animation: fadeInUp 0.45s ease-out; max-width: 1200px; }

.op-code {
  font-family: var(--font-mono); font-size: 13px; color: var(--accent);
  background: var(--accent-bg); padding: 2px 8px; border-radius: 4px; font-weight: 600;
}
.thresh-val {
  font-family: var(--font-display); font-weight: 700; font-size: 14px; color: var(--text-title);
}
.sev-badge {
  font-size: 11px; font-weight: 700; padding: 3px 10px;
  border-radius: 4px; font-family: var(--font-mono); letter-spacing: 0.04em;
}
.sev-badge.normal { color: var(--amber); background: var(--amber-bg); border: 1px solid rgba(245,158,11,0.15); }
.sev-badge.severe { color: var(--red); background: var(--red-bg); border: 1px solid rgba(239,68,68,0.15); }
.sev-badge.critical { color: #fff; background: var(--red); }
</style>