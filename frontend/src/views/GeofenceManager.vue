<template>
  <div class="geofence-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">冷链电子围栏管理</h2>
        <p class="page-desc">管理圆形点围栏、带状线路围栏、多边形围栏、行政城市围栏</p>
      </div>
      <button class="btn-primary" @click="showAddDialog = true; editingFence = null">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" style="margin-right:4px;vertical-align:-2px"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        添加围栏
      </button>
    </div>

    <div class="stats-row">
      <div class="stat-card">
        <div class="stat-num">{{ stats.total_fences || 0 }}</div>
        <div class="stat-label">围栏总数</div>
      </div>
      <div class="stat-card">
        <div class="stat-num">{{ stats.active_fences || 0 }}</div>
        <div class="stat-label">活跃围栏</div>
      </div>
      <div class="stat-card">
        <div class="stat-num">{{ stats.total_events || 0 }}</div>
        <div class="stat-label">事件总数</div>
      </div>
      <div class="stat-card">
        <div class="stat-num">{{ stats.active_events || 0 }}</div>
        <div class="stat-label">未处理告警</div>
      </div>
    </div>

    <div class="main-content">
      <div class="left-panel">
        <div class="panel-header">
          <h3>围栏列表 <span class="list-count">({{ filteredFences.length }}/{{ fences.length }})</span></h3>
          <div class="filter-row">
            <el-select v-model="filterType" placeholder="类型" size="small" style="width:120px">
              <el-option label="全部类型" value="" />
              <el-option label="圆形点围栏" value="circle" />
              <el-option label="带状线路围栏" value="line_buffer" />
              <el-option label="多边形围栏" value="polygon" />
              <el-option label="行政城市围栏" value="city" />
            </el-select>
            <el-select v-model="filterCategory" placeholder="分类" size="small" style="width:120px">
              <el-option label="全部分类" value="" />
              <el-option label="仓库" value="warehouse" />
              <el-option label="枢纽" value="hub" />
              <el-option label="干线" value="route_segment" />
              <el-option label="服务区" value="service_area" />
              <el-option label="禁行区" value="forbidden" />
              <el-option label="高温区" value="high_temp" />
              <el-option label="城市" value="city_zone" />
            </el-select>
            <el-select v-model="filterStatus" placeholder="状态" size="small" style="width:100px">
              <el-option label="全部" value="" />
              <el-option label="启用中" value="active" />
              <el-option label="已禁用" value="inactive" />
            </el-select>
          </div>
        </div>

        <div class="fence-list">
          <div v-for="fence in filteredFences" :key="fence.fence_id" 
               class="fence-item" :class="{ active: selectedFence?.fence_id === fence.fence_id }"
               @click="selectFence(fence)">
            <div class="fence-icon" :class="fence.fence_type">
              <svg v-if="fence.fence_type === 'circle'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg>
              <svg v-else-if="fence.fence_type === 'line_buffer'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="5" y1="12" x2="19" y2="12"/></svg>
              <svg v-else-if="fence.fence_type === 'polygon'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10"/></svg>
              <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 21l1.65-3.8a9 9 0 1 1 3.4 2.9L3 21"/><path d="M12 7v5l4 2"/></svg>
            </div>
            <div class="fence-info">
              <div class="fence-name">{{ fence.name }}</div>
              <div class="fence-meta">{{ fenceTypeName(fence.fence_type) }} · {{ fenceCategoryName(fence.category) }}</div>
            </div>
            <div class="fence-alert" :class="fence.alert_level">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 9v4M12 17h.01M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/></svg>
            </div>
          </div>
        </div>
      </div>

      <div class="right-panel">
        <div v-if="selectedFence" class="detail-panel">
          <div class="detail-header">
            <h3>{{ selectedFence.name }}</h3>
            <div class="detail-actions">
              <el-button size="small" @click="editFence(selectedFence)">编辑</el-button>
              <el-button size="small" type="danger" @click="deleteFence(selectedFence.fence_id)">删除</el-button>
            </div>
          </div>
          <div class="detail-body">
            <div class="detail-row">
              <span class="detail-label">围栏ID</span>
              <span class="detail-value mono">{{ selectedFence.fence_id }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">围栏类型</span>
              <span class="detail-value">{{ fenceTypeName(selectedFence.fence_type) }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">分类</span>
              <span class="detail-value">{{ fenceCategoryName(selectedFence.category) }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">告警等级</span>
              <span class="detail-value alert-badge" :class="selectedFence.alert_level">{{ alertLevelName(selectedFence.alert_level) }}</span>
            </div>
            <div class="detail-row">
              <span class="detail-label">状态</span>
              <span class="detail-value" :class="selectedFence.active ? 'active-text' : 'inactive-text'">{{ selectedFence.active ? '启用' : '禁用' }}</span>
            </div>
            <div v-if="selectedFence.data" class="detail-row">
              <span class="detail-label">地理数据</span>
              <div class="geo-data">
                <div v-if="selectedFence.fence_type === 'circle'">
                  <div>中心点: {{ selectedFence.data.center?.lat?.toFixed(4) }}, {{ selectedFence.data.center?.lng?.toFixed(4) }}</div>
                  <div>半径: {{ selectedFence.data.radius_meters }}米</div>
                </div>
                <div v-else-if="selectedFence.fence_type === 'line_buffer'">
                  <div>起点: {{ selectedFence.data.start_city }} - 终点: {{ selectedFence.data.end_city }}</div>
                  <div>缓冲宽度: {{ selectedFence.data.buffer_meters }}米</div>
                  <div>途经点数: {{ selectedFence.data.points?.length || 0 }}</div>
                </div>
                <div v-else-if="selectedFence.fence_type === 'polygon'">
                  <div>顶点数: {{ selectedFence.data.coordinates?.[0]?.length || 0 }}</div>
                </div>
                <div v-else-if="selectedFence.fence_type === 'city'">
                  <div>城市: {{ selectedFence.data.city_name }}</div>
                  <div>省份: {{ selectedFence.data.province }}</div>
                  <div>范围: {{ selectedFence.data.radius_meters / 1000 }}公里</div>
                </div>
              </div>
            </div>
            <div v-if="selectedFence.allowed_stay_minutes" class="detail-row">
              <span class="detail-label">允许停留</span>
              <span class="detail-value">{{ selectedFence.allowed_stay_minutes }}分钟</span>
            </div>
            <div v-if="selectedFence.description" class="detail-row">
              <span class="detail-label">描述</span>
              <span class="detail-value">{{ selectedFence.description }}</span>
            </div>
            <div v-if="selectedFence.tags?.length" class="detail-row">
              <span class="detail-label">标签</span>
              <div class="tags">
                <span v-for="tag in selectedFence.tags" :key="tag" class="tag">{{ tag }}</span>
              </div>
            </div>
          </div>

          <div class="events-section">
            <h4>最近事件</h4>
            <div v-if="fenceEvents.length" class="event-list">
              <div v-for="event in fenceEvents" :key="event.event_id" class="event-item">
                <div class="event-icon" :class="event.alert_level">
                  <svg v-if="event.event_type === 'enter'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12l7-7 7 7"/></svg>
                  <svg v-else-if="event.event_type === 'exit'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 19V5M19 12l-7 7-7-7"/></svg>
                  <svg v-else-if="event.event_type === 'deviation'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M5 12h14M12 2l7 7M12 2l-7 7M12 22l7-7M12 22l-7-7"/></svg>
                  <svg v-else-if="event.event_type === 'stay'" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                  <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 9v4M12 17h.01"/></svg>
                </div>
                <div class="event-content">
                  <div class="event-type">{{ eventTypeName(event.event_type) }}</div>
                  <div class="event-desc">{{ event.description }}</div>
                </div>
                <div class="event-time">{{ formatDateTime(event.event_time) }}</div>
              </div>
            </div>
            <div v-else class="empty-text">暂无事件记录</div>
          </div>
        </div>

        <div v-else class="empty-panel">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" style="color:var(--text-muted)"><circle cx="12" cy="10" r="3"/><path d="M12 21.7C17.3 17 20 13 20 10a8 8 0 1 0-16 0c0 3 2.7 7 8 11.7z"/></svg>
          <p>选择一个围栏查看详情</p>
        </div>
      </div>
    </div>

    <el-dialog v-model="showAddDialog" :title="editingFence ? '编辑电子围栏' : '添加电子围栏'" width="600px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="围栏名称" required>
          <el-input v-model="form.name" placeholder="如：华北中心冷库围栏" />
        </el-form-item>
        <el-form-item label="围栏类型" required>
          <el-select v-model="form.fence_type" style="width:100%" @change="onFenceTypeChange">
            <el-option label="圆形点围栏" value="circle" />
            <el-option label="带状线路围栏" value="line_buffer" />
            <el-option label="多边形围栏" value="polygon" />
            <el-option label="行政城市围栏" value="city" />
          </el-select>
        </el-form-item>
        <el-form-item label="分类" required>
          <el-select v-model="form.category" style="width:100%">
            <el-option label="仓库" value="warehouse" />
            <el-option label="枢纽" value="hub" />
            <el-option label="干线" value="route_segment" />
            <el-option label="服务区" value="service_area" />
            <el-option label="禁行区" value="forbidden" />
            <el-option label="高温区" value="high_temp" />
            <el-option label="检查站" value="checkpoint" />
            <el-option label="城市" value="city_zone" />
          </el-select>
        </el-form-item>

        <template v-if="form.fence_type === 'circle'">
          <el-form-item label="中心纬度"><el-input-number v-model="form.lat" :precision="6" :step="0.01" style="width:100%" /></el-form-item>
          <el-form-item label="中心经度"><el-input-number v-model="form.lng" :precision="6" :step="0.01" style="width:100%" /></el-form-item>
          <el-form-item label="半径(米)"><el-input-number v-model="form.radius" :min="50" :max="5000" :step="50" style="width:100%" /></el-form-item>
        </template>

        <template v-else-if="form.fence_type === 'line_buffer'">
          <el-form-item label="起点城市"><el-input v-model="form.start_city" placeholder="如：北京" /></el-form-item>
          <el-form-item label="终点城市"><el-input v-model="form.end_city" placeholder="如：上海" /></el-form-item>
          <el-form-item label="缓冲宽度(米)"><el-input-number v-model="form.buffer_meters" :min="50" :max="500" :step="10" style="width:100%" /></el-form-item>
        </template>

        <template v-else-if="form.fence_type === 'polygon'">
          <el-form-item label="顶点坐标">
            <el-input v-model="form.coordinates" type="textarea" :rows="4" placeholder="格式：lng1,lat1;lng2,lat2;lng3,lat3" />
          </el-form-item>
        </template>

        <template v-else-if="form.fence_type === 'city'">
          <el-form-item label="城市名称"><el-input v-model="form.city_name" placeholder="如：北京" /></el-form-item>
          <el-form-item label="省份"><el-input v-model="form.province" placeholder="如：北京" /></el-form-item>
          <el-form-item label="范围(公里)"><el-input-number v-model="form.city_radius" :min="10" :max="100" :step="5" style="width:100%" /></el-form-item>
        </template>

        <el-form-item label="告警等级">
          <el-select v-model="form.alert_level" style="width:100%">
            <el-option label="严重" value="severe" />
            <el-option label="警告" value="warning" />
            <el-option label="一般" value="normal" />
            <el-option label="信息" value="info" />
          </el-select>
        </el-form-item>
        <el-form-item label="允许停留(分钟)">
          <el-input-number v-model="form.allowed_stay_minutes" :min="0" :max="1440" :step="10" style="width:100%" />
        </el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="标签"><el-input v-model="form.tags" placeholder="多个标签用逗号分隔" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="saveFence">{{ editingFence ? '保存' : '添加' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { geofenceAPI } from '@/api'
import { formatDateTime } from '@/utils'

const fences = ref<any[]>([])
const stats = ref<any>({})
const selectedFence = ref<any>(null)
const fenceEvents = ref<any[]>([])
const showAddDialog = ref(false)
const editingFence = ref<any>(null)

const filterType = ref('')
const filterCategory = ref('')
const filterStatus = ref('')

const form = ref({
  name: '',
  fence_type: 'circle',
  category: 'warehouse',
  alert_level: 'normal',
  lat: 39.9042,
  lng: 116.4074,
  radius: 500,
  start_city: '',
  end_city: '',
  buffer_meters: 100,
  coordinates: '',
  city_name: '',
  province: '',
  city_radius: 50,
  allowed_stay_minutes: 60,
  description: '',
  tags: '',
})

const filteredFences = computed(() => {
  return fences.value.filter(f => {
    if (filterType.value && f.fence_type !== filterType.value) return false
    if (filterCategory.value && f.category !== filterCategory.value) return false
    if (filterStatus.value === 'active' && !f.active) return false
    if (filterStatus.value === 'inactive' && f.active) return false
    return true
  })
})

function fenceTypeName(type: string) {
  const map: Record<string, string> = {
    circle: '圆形点围栏',
    line_buffer: '带状线路围栏',
    polygon: '多边形围栏',
    city: '行政城市围栏',
  }
  return map[type] || type
}

function fenceCategoryName(category: string) {
  const map: Record<string, string> = {
    warehouse: '仓库',
    hub: '枢纽',
    route_segment: '干线',
    service_area: '服务区',
    forbidden: '禁行区',
    high_temp: '高温区',
    checkpoint: '检查站',
    city_zone: '城市',
    restricted: '限制区',
    store: '门店',
    maintenance: '维修站',
  }
  return map[category] || category
}

function alertLevelName(level: string) {
  const map: Record<string, string> = {
    severe: '严重',
    warning: '警告',
    normal: '一般',
    info: '信息',
  }
  return map[level] || level
}

function eventTypeName(type: string) {
  const map: Record<string, string> = {
    enter: '进入围栏',
    exit: '离开围栏',
    depart: '离开节点',
    stay: '异常停留',
    stay_severe: '严重停留',
    deviation: '路线偏离',
    forbidden_entry: '禁区闯入',
    offline: '设备离线',
    timeout: '节点超时',
  }
  return map[type] || type
}

function onFenceTypeChange() {
  form.value.lat = 39.9042
  form.value.lng = 116.4074
  form.value.radius = 500
  form.value.start_city = ''
  form.value.end_city = ''
  form.value.buffer_meters = 100
  form.value.coordinates = ''
  form.value.city_name = ''
  form.value.province = ''
  form.value.city_radius = 50
}

function selectFence(fence: any) {
  selectedFence.value = fence
  loadFenceEvents(fence.fence_id)
}

function editFence(fence: any) {
  editingFence.value = fence
  form.value = {
    name: fence.name,
    fence_type: fence.fence_type,
    category: fence.category,
    alert_level: fence.alert_level,
    lat: fence.data?.center?.lat || 39.9042,
    lng: fence.data?.center?.lng || 116.4074,
    radius: fence.data?.radius_meters || 500,
    start_city: fence.data?.start_city || '',
    end_city: fence.data?.end_city || '',
    buffer_meters: fence.data?.buffer_meters || 100,
    coordinates: fence.data?.coordinates?.[0]?.map((p: any) => `${p.lng},${p.lat}`).join(';') || '',
    city_name: fence.data?.city_name || '',
    province: fence.data?.province || '',
    city_radius: (fence.data?.radius_meters || 50000) / 1000,
    allowed_stay_minutes: fence.allowed_stay_minutes || 60,
    description: fence.description || '',
    tags: (fence.tags || []).join(', '),
  }
  showAddDialog.value = true
}

async function saveFence() {
  try {
    let data: any = {
      name: form.value.name,
      fence_type: form.value.fence_type,
      category: form.value.category,
      alert_level: form.value.alert_level,
      active: true,
      description: form.value.description || undefined,
      allowed_stay_minutes: form.value.allowed_stay_minutes || undefined,
      tags: form.value.tags ? form.value.tags.split(',').map((t: string) => t.trim()) : undefined,
    }

    if (form.value.fence_type === 'circle') {
      data.data = {
        center: { lat: form.value.lat, lng: form.value.lng },
        radius_meters: form.value.radius,
      }
    } else if (form.value.fence_type === 'line_buffer') {
      data.data = {
        points: [],
        buffer_meters: form.value.buffer_meters,
        start_city: form.value.start_city,
        end_city: form.value.end_city,
      }
    } else if (form.value.fence_type === 'polygon') {
      const coords = form.value.coordinates.split(';').map((c: string) => {
        const [lng, lat] = c.split(',').map(Number)
        return { lng, lat }
      })
      data.data = { coordinates: [coords] }
    } else if (form.value.fence_type === 'city') {
      data.data = {
        city_name: form.value.city_name,
        province: form.value.province,
        center: { lat: 0, lng: 0 },
        radius_meters: form.value.city_radius * 1000,
      }
    }

    if (editingFence.value) {
      await geofenceAPI.update(editingFence.value.fence_id, data)
      ElMessage.success('围栏已更新')
    } else {
      await geofenceAPI.create(data)
      ElMessage.success('围栏已创建')
    }
    showAddDialog.value = false
    editingFence.value = null
    await loadData()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '操作失败')
  }
}

async function deleteFence(id: string) {
  try {
    await ElMessageBox.confirm('确定要删除此电子围栏吗？', '确认删除', { type: 'warning' })
    await geofenceAPI.delete(id)
    ElMessage.success('围栏已删除')
    selectedFence.value = null
    await loadData()
  } catch {}
}

async function loadFenceEvents(fenceId: string) {
  try {
    const res = await geofenceAPI.getEvents({ fence_id: fenceId, hours: 24 })
    fenceEvents.value = res.events || res.slice(0, 10)
  } catch {
    fenceEvents.value = []
  }
}

async function loadData() {
  try {
    const [fenceRes, statsRes] = await Promise.all([
      geofenceAPI.getList(),
      geofenceAPI.getStats(),
    ])
    fences.value = fenceRes.fences || fenceRes
    stats.value = statsRes
  } catch {
    ElMessage.error('获取围栏数据失败')
  }
}

onMounted(loadData)
</script>

<style scoped>
.geofence-page { animation: fadeInUp 0.45s ease-out; }

.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 20px; }
.stat-card {
  background: var(--bg-card); border: 1px solid var(--border-card); border-radius: var(--radius-lg);
  padding: 16px; text-align: center;
}
.stat-num { font-size: 28px; font-weight: 700; color: var(--text-title); }
.stat-label { font-size: 13px; color: var(--text-muted); margin-top: 4px; }

.main-content { display: flex; gap: 20px; }
.left-panel { width: 360px; flex-shrink: 0; }
.right-panel { flex: 1; }

.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.panel-header h3 { font-size: 15px; font-weight: 700; color: var(--text-title); }
.list-count { font-weight: 400; font-size: 12px; color: var(--text-muted); margin-left: 4px; }
.filter-row { display: flex; gap: 8px; }

.fence-list {
  background: var(--bg-card); border: 1px solid var(--border-card); border-radius: var(--radius-lg);
  max-height: 500px; overflow-y: auto;
}
.fence-item {
  display: flex; align-items: center; gap: 12px; padding: 12px 14px;
  border-bottom: 1px solid var(--border-light); cursor: pointer;
  transition: background 0.2s;
}
.fence-item:last-child { border-bottom: none; }
.fence-item:hover { background: var(--bg-hover); }
.fence-item.active { background: var(--accent-bg); }

.fence-icon { width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; }
.fence-icon.circle { background: #dbeafe; color: #3b82f6; }
.fence-icon.line_buffer { background: #dcfce7; color: #22c55e; }
.fence-icon.polygon { background: #fee2e2; color: #ef4444; }
.fence-icon.city { background: #f5f3ff; color: #8b5cf6; }

.fence-info { flex: 1; min-width: 0; }
.fence-name { font-size: 13px; font-weight: 600; color: var(--text-title); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.fence-meta { font-size: 11px; color: var(--text-muted); }

.fence-alert { width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; }
.fence-alert.severe { color: var(--red); }
.fence-alert.warning { color: var(--amber); }
.fence-alert.normal { color: var(--text-muted); }
.fence-alert.info { color: var(--accent); }

.detail-panel {
  background: var(--bg-card); border: 1px solid var(--border-card); border-radius: var(--radius-lg);
  padding: 20px;
}
.detail-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.detail-header h3 { font-size: 16px; font-weight: 700; color: var(--text-title); }
.detail-actions { display: flex; gap: 8px; }

.detail-body { display: grid; gap: 12px; margin-bottom: 24px; }
.detail-row { display: flex; gap: 16px; }
.detail-label { width: 100px; flex-shrink: 0; font-size: 13px; color: var(--text-muted); }
.detail-value { flex: 1; font-size: 13px; color: var(--text-secondary); word-break: break-all; }
.detail-value.mono { font-family: var(--font-mono); background: var(--bg-input); padding: 2px 6px; border-radius: 3px; }
.detail-value.active-text { color: var(--teal); font-weight: 600; }
.detail-value.inactive-text { color: var(--text-muted); }

.alert-badge {
  display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600;
}
.alert-badge.severe { background: var(--red-bg); color: var(--red); }
.alert-badge.warning { background: var(--amber-bg); color: var(--amber); }
.alert-badge.normal { background: var(--accent-bg); color: var(--accent); }
.alert-badge.info { background: var(--bg-input); color: var(--text-muted); }

.geo-data { flex: 1; font-size: 12px; color: var(--text-secondary); display: flex; flex-direction: column; gap: 4px; }

.tags { display: flex; flex-wrap: wrap; gap: 6px; }
.tag { padding: 2px 8px; background: var(--bg-input); border-radius: 4px; font-size: 11px; color: var(--text-secondary); }

.events-section { padding-top: 16px; border-top: 1px solid var(--border-light); }
.events-section h4 { font-size: 14px; font-weight: 600; color: var(--text-title); margin-bottom: 12px; }

.event-list { display: flex; flex-direction: column; gap: 10px; }
.event-item { display: flex; align-items: flex-start; gap: 12px; padding: 10px 12px; background: var(--bg-hover); border-radius: 8px; }
.event-icon { width: 24px; height: 24px; border-radius: 6px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.event-icon.severe { background: var(--red-bg); color: var(--red); }
.event-icon.warning { background: var(--amber-bg); color: var(--amber); }
.event-icon.normal, .event-icon.info { background: var(--bg-input); color: var(--accent); }

.event-content { flex: 1; min-width: 0; }
.event-type { font-size: 13px; font-weight: 600; color: var(--text-title); }
.event-desc { font-size: 12px; color: var(--text-muted); margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.event-time { font-size: 11px; color: var(--text-muted); flex-shrink: 0; }

.empty-panel { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 400px; color: var(--text-muted); }
.empty-panel p { margin-top: 12px; font-size: 14px; }
.empty-text { text-align: center; color: var(--text-muted); padding: 20px; }

.page-desc { font-size: 13px; color: var(--text-muted); margin-top: 4px; }
</style>
