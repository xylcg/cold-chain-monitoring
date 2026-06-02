<template>
  <div class="geofence-page">
    <div class="page-header">
      <h2 class="page-title">冷链电子围栏管理</h2>
      <button class="btn-primary" @click="showAddDialog = true; editingFence = null">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" style="margin-right:4px;vertical-align:-2px"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        添加围栏
      </button>
    </div>

    <div class="fence-grid">
      <div v-for="fence in fences" :key="fence.id" class="fence-card">
        <div class="fence-head">
          <div class="fence-name">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="12" cy="10" r="3"/><path d="M12 21.7C17.3 17 20 13 20 10a8 8 0 1 0-16 0c0 3 2.7 7 8 11.7z"/></svg>
            {{ fence.name }}
          </div>
          <span class="fence-type" :class="fence.type">{{ fenceTypeLabel(fence.type) }}</span>
        </div>

        <div class="fence-body">
          <div class="f-row">
            <span class="fl">位置</span>
            <code class="fv mono">{{ fence.center.lat.toFixed(4) }}, {{ fence.center.lng.toFixed(4) }}</code>
          </div>
          <div class="f-row"><span class="fl">半径</span><span class="fv">{{ fence.radius }}m</span></div>
          <div class="f-row"><span class="fl">地址</span><span class="fv">{{ fence.address }}</span></div>
          <div class="f-row">
            <span class="fl">温度要求</span>
            <span class="fv temp-range">{{ fence.temp_range.min }}°C ~ {{ fence.temp_range.max }}°C</span>
          </div>
          <div class="f-row"><span class="fl">联系人</span><span class="fv">{{ fence.contact }} · {{ fence.phone }}</span></div>
        </div>

        <div class="fence-foot">
          <el-button size="small" @click="editFence(fence)">编辑</el-button>
          <el-button size="small" type="danger" @click="deleteFence(fence.id)">删除</el-button>
          <el-button size="small" type="primary" @click="viewEvents(fence.id)">进出记录</el-button>
        </div>
      </div>
    </div>

    <div v-if="showEvents" class="glass-card" style="margin-top:20px;">
      <div class="card-head-between">
        <h3>围栏进出事件记录</h3>
        <el-button size="small" text @click="showEvents = false">关闭</el-button>
      </div>
      <el-table :data="events" stripe size="small" max-height="400">
        <el-table-column prop="geofence_name" label="围栏" width="140" />
        <el-table-column prop="device_id" label="设备" width="120" />
        <el-table-column prop="event_type" label="状态" width="90">
          <template #default="{ row }">
            <span class="geo-status" :class="{ inside: row.is_inside }">{{ row.is_inside ? '围栏内' : '围栏外' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="distance_meters" label="距离(m)" width="90" />
        <el-table-column prop="temperature" label="温度" width="80">
          <template #default="{ row }">
            <span class="temp-warn" v-if="!row.temp_in_range && row.is_inside">{{ row.temperature }}°C</span>
            <span v-else>{{ row.temperature }}°C</span>
          </template>
        </el-table-column>
        <el-table-column prop="warning" label="告警" min-width="200">
          <template #default="{ row }">
            <span v-if="row.warning" class="warning-text">{{ row.warning }}</span>
            <span v-else class="normal-text">正常</span>
          </template>
        </el-table-column>
        <el-table-column prop="timestamp" label="时间" width="170">
          <template #default="{ row }">{{ formatDateTime(row.timestamp) }}</template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="showAddDialog" :title="editingFence ? '编辑电子围栏' : '添加电子围栏'" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="围栏名称"><el-input v-model="form.name" placeholder="如：华北中心冷库" /></el-form-item>
        <el-form-item label="围栏类型">
          <el-select v-model="form.type" style="width:100%">
            <el-option label="冷库" value="cold_storage" />
            <el-option label="配送中心" value="distribution_center" />
            <el-option label="前置仓" value="front_warehouse" />
          </el-select>
        </el-form-item>
        <el-form-item label="中心纬度"><el-input-number v-model="form.lat" :precision="6" :step="0.01" style="width:100%" /></el-form-item>
        <el-form-item label="中心经度"><el-input-number v-model="form.lng" :precision="6" :step="0.01" style="width:100%" /></el-form-item>
        <el-form-item label="半径(米)"><el-input-number v-model="form.radius" :min="100" :max="5000" :step="100" style="width:100%" /></el-form-item>
        <el-form-item label="地址"><el-input v-model="form.address" /></el-form-item>
        <el-form-item label="联系人"><el-input v-model="form.contact" /></el-form-item>
        <el-form-item label="联系电话"><el-input v-model="form.phone" /></el-form-item>
        <el-form-item label="温度下限"><el-input-number v-model="form.temp_min" :step="1" style="width:100%" /></el-form-item>
        <el-form-item label="温度上限"><el-input-number v-model="form.temp_max" :step="1" style="width:100%" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="saveFence">{{ editingFence ? '保存' : '添加' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { geofenceAPI } from '@/api'
import { formatDateTime } from '@/utils'

const fences = ref<any[]>([])
const events = ref<any[]>([])
const showEvents = ref(false)
const showAddDialog = ref(false)
const editingFence = ref<any>(null)

const form = ref({
  name: '', type: 'cold_storage', lat: 39.9, lng: 116.4,
  radius: 500, address: '', contact: '', phone: '',
  temp_min: -25, temp_max: -15,
})

function fenceTypeLabel(type: string) {
  return type === 'cold_storage' ? '冷库' : type === 'distribution_center' ? '配送中心' : '前置仓'
}
function editFence(fence: any) {
  editingFence.value = fence
  form.value = {
    name: fence.name, type: fence.type,
    lat: fence.center.lat, lng: fence.center.lng,
    radius: fence.radius, address: fence.address || '',
    contact: fence.contact || '', phone: fence.phone || '',
    temp_min: fence.temp_range?.min ?? -25, temp_max: fence.temp_range?.max ?? -15,
  }
  showAddDialog.value = true
}
async function saveFence() {
  try {
    const data = { ...form.value }
    if (editingFence.value) { await geofenceAPI.update(editingFence.value.id, data); ElMessage.success('围栏已更新') }
    else { await geofenceAPI.create(data); ElMessage.success('围栏已创建') }
    showAddDialog.value = false; editingFence.value = null; await loadFences()
  } catch (e: any) { ElMessage.error(e?.response?.data?.detail || '操作失败') }
}
async function deleteFence(id: string) {
  try {
    await ElMessageBox.confirm('确定要删除此电子围栏吗？', '确认删除', { type: 'warning' })
    await geofenceAPI.delete(id); ElMessage.success('围栏已删除'); await loadFences()
  } catch {}
}
async function viewEvents(geofenceId: string) {
  try { const res = await geofenceAPI.getEvents({ geofence_id: geofenceId, limit: 50 }); events.value = res.events || []; showEvents.value = true }
  catch { ElMessage.error('获取事件记录失败') }
}
async function loadFences() {
  try { const res = await geofenceAPI.getList(); fences.value = res.geofences || [] }
  catch { ElMessage.error('获取围栏列表失败') }
}

onMounted(loadFences)
</script>

<style scoped>
.geofence-page { animation: fadeInUp 0.45s ease-out; }

.fence-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 14px; }
.fence-card {
  background: var(--bg-card); backdrop-filter: var(--blur-card); -webkit-backdrop-filter: var(--blur-card);
  border: 1px solid var(--border-card); border-radius: var(--radius-lg);
  padding: 20px; box-shadow: var(--shadow-sm); transition: all 0.3s ease;
}
.fence-card:hover { box-shadow: var(--shadow); transform: translateY(-2px); border-color: var(--border-focus); }

.fence-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.fence-name { display: flex; align-items: center; gap: 8px; font-size: 15px; font-weight: 700; color: var(--text-title); }
.fence-type {
  font-size: 10px; padding: 3px 8px; border-radius: 20px; font-weight: 600; letter-spacing: 0.04em;
}
.fence-type.cold_storage { background: var(--accent-bg); color: var(--accent); }
.fence-type.distribution_center { background: var(--amber-bg); color: var(--amber); }
.fence-type.front_warehouse { background: var(--teal-bg); color: var(--teal); }

.fence-body { margin-bottom: 14px; display: flex; flex-direction: column; gap: 6px; }
.f-row { display: flex; justify-content: space-between; align-items: center; font-size: 12px; }
.fl { color: var(--text-muted); min-width: 56px; }
.fv { color: var(--text-secondary); }
.mono { font-family: var(--font-mono); color: var(--text-secondary); background: var(--bg-input); padding: 1px 6px; border-radius: 3px; font-size: 11px; }
.temp-range { color: var(--accent); font-weight: 600; font-family: var(--font-mono); font-size: 13px; }

.fence-foot { display: flex; gap: 8px; padding-top: 12px; border-top: 1px solid var(--border-light); }

.card-head-between { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.card-head-between h3 { font-size: 15px; font-weight: 700; color: var(--text-title); }

.geo-status { font-size: 11px; padding: 2px 8px; border-radius: 4px; font-weight: 500; background: var(--bg-input); color: var(--text-secondary); }
.geo-status.inside { background: var(--teal-bg); color: var(--teal); }
.warning-text { color: var(--amber); font-size: 12px; }
.normal-text { color: var(--teal); font-size: 12px; font-weight: 600; }
.temp-warn { color: var(--red); font-weight: 600; }
</style>
