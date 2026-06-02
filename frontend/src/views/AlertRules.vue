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
        <el-table-column prop="type" label="规则类型" width="180" />
        <el-table-column prop="field" label="监控字段" width="110" />
        <el-table-column prop="op" label="条件" width="70">
          <template #default="{ row }">
            <code class="op-code">{{ row.op }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="value" label="阈值" width="90">
          <template #default="{ row }">
            <span class="thresh-val">{{ row.value }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="severity" label="严重等级" width="100">
          <template #default="{ row }">
            <span class="sev-badge" :class="row.severity">{{ getSeverityLabel(row.severity) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="msg" label="告警描述" min-width="200" />
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
          <el-input v-model="newRule.rule_type" placeholder="如：temperature_high" />
        </el-form-item>
        <el-form-item label="监控字段">
          <el-select v-model="newRule.condition_field" style="width:100%">
            <el-option label="温度" value="temperature" />
            <el-option label="湿度" value="humidity" />
            <el-option label="振动" value="vibration" />
            <el-option label="车门状态" value="door_status" />
          </el-select>
        </el-form-item>
        <el-form-item label="条件">
          <el-select v-model="newRule.condition_operator" style="width:100%">
            <el-option label="大于 >" value=">" />
            <el-option label="小于 <" value="<" />
            <el-option label="等于 ==" value="==" />
            <el-option label="大于等于 >=" value=">=" />
            <el-option label="小于等于 <=" value="<=" />
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
})

function getSeverityLabel(severity: string) {
  const map: any = { normal: '一般', severe: '严重', critical: '紧急' }
  return map[severity] || severity
}

async function fetchRules() {
  try { const data: any = await alertAPI.getRules(); rules.value = data.rules || [] } catch {}
}
async function addRule() {
  try {
    await alertAPI.createRule(newRule.value)
    ElMessage.success('规则添加成功')
    showAddDialog.value = false; fetchRules()
    newRule.value = { rule_name: '', rule_type: '', condition_field: 'temperature', condition_operator: '>', condition_value: 8.0, severity: 'severe', cooldown_seconds: 300 }
  } catch {}
}
async function deleteRule(ruleType: string) {
  try { await alertAPI.deleteRule(ruleType); ElMessage.success('规则已删除'); fetchRules() } catch {}
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
