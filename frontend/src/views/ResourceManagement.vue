<template>
  <div class="resource-page">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">冷链资源智能调度</h2>
        <span class="subtitle">冷库库位 · 冷藏车辆 · 蓄冷板/冰排 · 能耗监测</span>
      </div>
      <div class="header-actions">
        <button class="btn-primary" @click="openAllocateModal">
          <span>🔄</span> 一键分配资源
        </button>
        <button class="btn-secondary" @click="loadData">
          <span>🔄</span> 刷新数据
        </button>
      </div>
    </div>

    <!-- 综合利用率 -->
    <div class="stats-row" v-if="utilData">
      <div class="stat-card">
        <div class="stat-icon" style="background:rgba(0,168,255,0.12);color:var(--accent)">🏭</div>
        <div class="stat-info">
          <div class="stat-value">{{ utilData.cold_storage?.avg_utilization || 0 }}%</div>
          <div class="stat-label">冷库平均利用率</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:rgba(124,58,237,0.12);color:var(--aurora)">🚛</div>
        <div class="stat-info">
          <div class="stat-value">{{ utilData.fleet?.utilization || 0 }}%</div>
          <div class="stat-label">车队利用率</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:rgba(0,210,160,0.12);color:var(--teal)">🧊</div>
        <div class="stat-info">
          <div class="stat-value">{{ utilData.cold_plates?.utilization || 0 }}%</div>
          <div class="stat-label">蓄冷板利用率</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background:rgba(245,158,11,0.12);color:var(--amber)">⚡</div>
        <div class="stat-info">
          <div class="stat-value">{{ utilData.energy?.total_kwh_today || 0 }}</div>
          <div class="stat-label">今日能耗 (kWh)</div>
        </div>
      </div>
    </div>

    <!-- 资源选项卡 -->
    <div class="tabs">
      <button 
        v-for="tab in tabs" 
        :key="tab.key"
        :class="['tab-btn', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        <span>{{ tab.icon }}</span> {{ tab.name }}
      </button>
    </div>

    <!-- 冷库库位 -->
    <div v-show="activeTab === 'warehouse'" class="res-content">
      <div class="res-grid">
        <div class="glass-card warehouse-section">
          <div class="card-header">
            <span>🏭 冷库列表</span>
            <span class="count">({{ warehouses.length }}座)</span>
          </div>
          <div v-for="wh in warehouses" :key="wh.warehouse_id" class="wh-card">
            <div class="wh-header">
              <div class="wh-name">{{ wh.warehouse_name }}</div>
              <div class="wh-loc">{{ wh.location }}</div>
            </div>
            <div class="wh-zones">
              <div 
                v-for="(zone, key) in wh.zones" 
                :key="key" 
                class="wh-zone"
                :style="{ borderLeftColor: getZoneColor(key) }"
              >
                <div class="wh-zone-header">
                  <span class="wh-zone-dot" :style="{ background: getZoneColor(key) }"></span>
                  <span class="wh-zone-name">{{ zone.name }}</span>
                  <span class="wh-zone-util">{{ zone.utilization_rate }}%</span>
                </div>
                <div class="wh-zone-bar">
                  <div :style="{ width: zone.utilization_rate + '%', background: zoneColors[key] }"></div>
                </div>
                <div class="wh-zone-detail">
                  <span>容量: {{ zone.used_weight_kg }}/{{ zone.total_weight_kg }}kg</span>
                  <span>体积: {{ zone.used_volume_m3 }}/{{ zone.total_volume_m3 }}m³</span>
                  <span>库位: {{ zone.free_slots }}个空闲</span>
                </div>
              </div>
            </div>
            <div class="wh-footer">
              <span class="wh-total">总利用率: <b :style="{ color: wh.overall_utilization > 80 ? 'var(--amber)' : 'var(--teal)' }">{{ wh.overall_utilization }}%</b></span>
            </div>
          </div>
        </div>

        <div class="glass-card inventory-section">
          <div class="card-header">
            <span>📦 库存概览</span>
            <button class="btn-sm" @click="refreshInventory">刷新</button>
          </div>
          <div v-if="inventorySummary" class="inventory-summary">
            <div class="inv-stat">
              <span class="inv-label">总库存</span>
              <span class="inv-value">{{ inventorySummary.total_kg?.toLocaleString() || 0 }} kg</span>
            </div>
            <div class="inv-stat">
              <span class="inv-label">临期预警</span>
              <span class="inv-value" :style="{ color: 'var(--amber)' }">{{ inventorySummary.total_near_expiry || 0 }} 项</span>
            </div>
            <div class="inv-stat">
              <span class="inv-label">已过期</span>
              <span class="inv-value" :style="{ color: 'var(--red)' }">{{ inventorySummary.total_expired || 0 }} 项</span>
            </div>
          </div>
          <div v-if="inventoryItems.length > 0" class="inventory-list">
            <div v-for="item in inventoryItems.slice(0, 8)" :key="item.id" class="inv-item" :class="{ warning: item.status === 'near_expiry' }">
              <div class="inv-item-name">{{ item.product_name }}</div>
              <div class="inv-item-detail">
                <span>{{ item.quantity_kg }}kg</span>
                <span>{{ item.zone_label }}</span>
                <span :style="{ color: item.status === 'near_expiry' ? 'var(--amber)' : 'var(--text-muted)' }">{{ item.status === 'near_expiry' ? '临期' : '正常' }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 冷藏车辆 -->
    <div v-show="activeTab === 'vehicle'" class="res-content">
      <div class="res-grid">
        <div class="glass-card vehicle-section">
          <div class="card-header">
            <span>🚛 冷藏车辆</span>
            <span class="count">({{ vehicles.length }}辆)</span>
          </div>
          <div class="vehicle-filters">
            <button 
              v-for="filter in vehicleFilters" 
              :key="filter.value"
              :class="['filter-btn', { active: vehicleFilter === filter.value }]"
              @click="vehicleFilter = filter.value"
            >
              {{ filter.label }}
            </button>
          </div>
          <div v-for="v in filteredVehicles" :key="v.id" class="vehicle-card" :class="'status-' + v.status">
            <div class="vehicle-header">
              <div class="vehicle-plate">{{ v.plate }}</div>
              <span class="vehicle-status" :class="getStatusClass(v.status)">{{ v.status_label }}</span>
            </div>
            <div class="vehicle-info">
              <span>{{ v.model }}</span>
              <span>{{ v.capacity_kg }}kg / {{ v.capacity_m3 }}m³</span>
            </div>
            <div class="vehicle-detail">
              <span>{{ v.fuel_type }} · {{ v.fuel_consumption }}L/100km</span>
              <span>📍 {{ v.location }}</span>
            </div>
            <div class="vehicle-zones">
              <span class="vz-label">温区覆盖:</span>
              <span v-for="z in v.zones" :key="z" class="vz-tag" :style="{ background: zoneColors[z] + '20', color: zoneColors[z] }">
                {{ ZONE_MAP[z] }}
              </span>
            </div>
          </div>
        </div>

        <div class="glass-card forecast-section">
          <div class="card-header">
            <span>📊 AI订单预测</span>
            <span class="count">未来{{ forecastHours }}小时</span>
          </div>
          <div v-if="forecastData" class="forecast-content">
            <div class="forecast-summary">
              <div class="fs-item">
                <span class="fs-label">峰值时段</span>
                <span class="fs-value">{{ forecastData.peak_demand_hour }}</span>
              </div>
              <div class="fs-item">
                <span class="fs-label">峰值需求</span>
                <span class="fs-value" style="color:var(--amber)">{{ forecastData.peak_demand_value }}单</span>
              </div>
              <div class="fs-item">
                <span class="fs-label">可用车辆</span>
                <span class="fs-value" style="color:var(--teal)">{{ forecastData.resource_gap_analysis?.vehicle?.available_fleet || 0 }}辆</span>
              </div>
            </div>
            <div class="forecast-chart">
              <div v-for="(f, idx) in displayForecast" :key="f.time" class="fc-bar-wrap">
                <div class="fc-bar-container" :class="{ 'is-peak': f.total_demand === peakDemand }">
                  <div 
                    class="fc-bar" 
                    :class="{ 'fc-bar-peak': f.total_demand === peakDemand }"
                    :style="{ height: getBarHeight(f.total_demand) + '%' }"
                    :title="`${f.hour}:00 · ${f.total_demand}单`"
                  ></div>
                  <span v-if="f.total_demand === peakDemand" class="fc-peak-badge">峰 {{ f.total_demand }}</span>
                </div>
                <span class="fc-label">{{ f.hour }}:00</span>
              </div>
            </div>
            <div class="forecast-recommendations">
              <div v-for="(rec, idx) in forecastData.recommendations" :key="idx" class="rec-item">
                {{ rec }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 蓄冷板 -->
    <div v-show="activeTab === 'coldPlate'" class="res-content">
      <div class="res-grid">
        <div class="glass-card coldplate-section">
          <div class="card-header">
            <span>🧊 蓄冷板/冰排</span>
            <span class="count">({{ coldPlates.length }}种)</span>
          </div>
          <div class="coldplate-summary">
            <div class="cps-item">
              <span class="cps-value">{{ coldPlateSummary.total_stock }}</span>
              <span class="cps-label">总库存</span>
            </div>
            <div class="cps-item">
              <span class="cps-value" style="color:var(--accent)">{{ coldPlateSummary.total_in_use }}</span>
              <span class="cps-label">使用中</span>
            </div>
            <div class="cps-item">
              <span class="cps-value" style="color:var(--teal)">{{ coldPlateSummary.total_precooled }}</span>
              <span class="cps-label">已预冷</span>
            </div>
            <div class="cps-item">
              <span class="cps-value" style="color:var(--red)">{{ coldPlateSummary.total_damaged }}</span>
              <span class="cps-label">损坏</span>
            </div>
          </div>
          <div v-for="cp in coldPlates" :key="cp.id" class="coldplate-card">
            <div class="cp-header">
              <span class="cp-name">{{ cp.name }}</span>
              <span class="cp-type">{{ cp.type }}</span>
            </div>
            <div class="cp-specs">
              <span>❄️ 相变温度: {{ cp.phase_change_temp_c }}°C</span>
              <span>⏱️ 持续时长: {{ cp.duration_h }}h</span>
              <span>📍 存放: {{ cp.storage_location }}</span>
            </div>
            <div class="cp-stock">
              <div class="cp-stock-item">
                <span class="cp-stock-label">库存</span>
                <span class="cp-stock-value">{{ cp.total_stock }}</span>
              </div>
              <div class="cp-stock-item">
                <span class="cp-stock-label">使用中</span>
                <span class="cp-stock-value" style="color:var(--accent)">{{ cp.in_use }}</span>
              </div>
              <div class="cp-stock-item">
                <span class="cp-stock-label">已预冷</span>
                <span class="cp-stock-value" :style="{ color: cp.precooled > 20 ? 'var(--teal)' : 'var(--amber)' }">{{ cp.precooled }}</span>
              </div>
              <div class="cp-stock-item">
                <span class="cp-stock-label">可用</span>
                <span class="cp-stock-value" :style="{ color: (cp.total_stock - cp.in_use - cp.damaged) > 50 ? 'var(--teal)' : 'var(--amber)' }">{{ cp.total_stock - cp.in_use - cp.damaged }}</span>
              </div>
            </div>
            <div class="cp-progress">
              <div class="cp-progress-bar">
                <div class="cp-progress-used" :style="{ width: (cp.in_use / cp.total_stock * 100) + '%' }"></div>
                <div class="cp-progress-precooled" :style="{ width: (cp.precooled / cp.total_stock * 100) + '%' }"></div>
              </div>
              <div class="cp-progress-legend">
                <span><span class="legend-dot used"></span> 使用中</span>
                <span><span class="legend-dot precooled"></span> 已预冷</span>
              </div>
            </div>
          </div>
        </div>

        <div class="glass-card energy-section">
          <div class="card-header">
            <span>⚡ 能耗监测</span>
          </div>
          <div v-if="utilData?.energy" class="energy-content">
            <div class="energy-summary">
              <div class="es-item">
                <span class="es-value">{{ utilData.energy.total_kwh_today }}</span>
                <span class="es-label">今日能耗 (kWh)</span>
              </div>
              <div class="es-item">
                <span class="es-value">{{ utilData.energy.avg_power_kw }}</span>
                <span class="es-label">平均功率 (kW)</span>
              </div>
            </div>
            <div class="energy-chart">
              <div v-for="e in utilData.energy.trend_24h" :key="e.hour" class="ec-bar-wrap">
                <div class="ec-bar" :style="{ height: (e.power_kwh / 400 * 100) + '%', background: e.power_kwh > 300 ? 'var(--amber)' : 'var(--accent)' }"></div>
                <span class="ec-label">{{ e.hour }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 一键分配资源弹窗 -->
    <div v-if="showAllocateModal" class="modal-overlay" @click.self="showAllocateModal = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>🔄 智能资源分配</h3>
          <button class="modal-close" @click="showAllocateModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="form-item">
              <label>订单ID *</label>
              <input v-model="allocateForm.order_id" type="text" placeholder="请输入订单ID" />
            </div>
            <div class="form-item">
              <label>货物名称 *</label>
              <input v-model="allocateForm.cargo_name" type="text" placeholder="如：冷冻牛肉" />
            </div>
            <div class="form-item">
              <label>货物类别 *</label>
              <select v-model="allocateForm.cargo_category">
                <option value="冷冻食品">冷冻食品</option>
                <option value="冷藏生鲜">冷藏生鲜</option>
                <option value="疫苗医药">疫苗医药</option>
                <option value="化工制剂">化工制剂</option>
                <option value="其他">其他</option>
              </select>
            </div>
            <div class="form-item">
              <label>数量 (kg)</label>
              <input v-model.number="allocateForm.quantity" type="number" placeholder="默认1000" />
            </div>
            <div class="form-item">
              <label>发货地</label>
              <input v-model="allocateForm.origin" type="text" placeholder="如：北京" />
            </div>
            <div class="form-item">
              <label>目的地</label>
              <input v-model="allocateForm.destination" type="text" placeholder="如：上海" />
            </div>
            <div class="form-item">
              <label>优先级</label>
              <select v-model="allocateForm.priority">
                <option value="normal">普通</option>
                <option value="high">高</option>
                <option value="urgent">紧急</option>
              </select>
            </div>
            <div class="form-item">
              <label>温度要求</label>
              <input v-model="allocateForm.temperature_requirement" type="text" placeholder="如：2~8℃" />
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showAllocateModal = false">取消</button>
          <button class="btn-primary" @click="doAllocate" :disabled="allocateLoading">
            {{ allocateLoading ? '分配中...' : '确认分配' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 分配结果弹窗 -->
    <div v-if="showResultModal" class="modal-overlay" @click.self="showResultModal = false">
      <div class="modal-content result-modal">
        <div class="modal-header">
          <h3>{{ allocationResult?.all_success ? '✅ 分配成功' : '⚠️ 部分分配' }}</h3>
          <button class="modal-close" @click="showResultModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="result-summary">
            <div class="rs-item">
              <span class="rs-label">分配ID</span>
              <span class="rs-value">{{ allocationResult?.allocation_id }}</span>
            </div>
            <div class="rs-item">
              <span class="rs-label">货物</span>
              <span class="rs-value">{{ allocationResult?.cargo_name }}</span>
            </div>
          </div>
          <div class="result-details">
            <div class="rd-section" :class="{ success: allocationResult?.warehouse?.status === 'success' }">
              <div class="rd-header">
                <span>🏭 库位分配</span>
                <span :class="allocationResult?.warehouse?.status === 'success' ? 'success' : 'failed'">
                  {{ allocationResult?.warehouse?.status === 'success' ? '成功' : '失败' }}
                </span>
              </div>
              <div v-if="allocationResult?.warehouse?.status === 'success'" class="rd-info">
                <span>仓库: {{ allocationResult.warehouse.warehouse_name }}</span>
                <span>温区: {{ allocationResult.warehouse.zone_name }}</span>
                <span>策略: {{ allocationResult.warehouse.allocation_strategy }}</span>
              </div>
            </div>
            <div class="rd-section" :class="{ success: allocationResult?.vehicle?.status === 'success' }">
              <div class="rd-header">
                <span>🚛 车辆分配</span>
                <span :class="allocationResult?.vehicle?.status === 'success' ? 'success' : 'failed'">
                  {{ allocationResult?.vehicle?.status === 'success' ? '成功' : '失败' }}
                </span>
              </div>
              <div v-if="allocationResult?.vehicle?.status === 'success'" class="rd-info">
                <span>车牌: {{ allocationResult.vehicle.plate_number }}</span>
                <span>司机: {{ allocationResult.vehicle.driver }}</span>
                <span>策略: {{ allocationResult.vehicle.allocation_strategy }}</span>
              </div>
            </div>
            <div class="rd-section" :class="{ success: allocationResult?.cold_plate?.status === 'success' }">
              <div class="rd-header">
                <span>🧊 蓄冷板分配</span>
                <span :class="allocationResult?.cold_plate?.status === 'success' ? 'success' : 'failed'">
                  {{ allocationResult?.cold_plate?.status === 'success' ? '成功' : '失败' }}
                </span>
              </div>
              <div v-if="allocationResult?.cold_plate?.status === 'success'" class="rd-info">
                <span>类型: {{ allocationResult.cold_plate.cold_plate_name }}</span>
                <span>数量: {{ allocationResult.cold_plate.quantity_allocated }}个</span>
                <span>目标温度: {{ allocationResult.cold_plate.target_temp_c }}℃</span>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-primary" @click="showResultModal = false">确定</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { resourceAPI } from '@/api'
import { ElMessage } from 'element-plus'

const activeTab = ref('warehouse')
const tabs = [
  { key: 'warehouse', name: '冷库库位', icon: '🏭' },
  { key: 'vehicle', name: '冷藏车辆', icon: '🚛' },
  { key: 'coldPlate', name: '蓄冷板', icon: '🧊' },
]

const getZoneColor = (key: string): string => {
  const colors: Record<string, string> = {
    frozen: '#4361ee',
    refrigerated: '#00a8ff',
    ambient: '#f59e0b',
  }
  return colors[key] || '#9ca3af'
}

const ZONE_MAP: Record<string, string> = {
  frozen: '冷冻',
  refrigerated: '冷藏',
  ambient: '恒温',
}

const zoneColors: Record<string, string> = {
  frozen: '#4361ee',
  refrigerated: '#00a8ff',
  ambient: '#f59e0b',
}

const warehouses = ref<any[]>([])
const vehicles = ref<any[]>([])
const coldPlates = ref<any[]>([])
const utilData = ref<any>(null)
const inventorySummary = ref<any>(null)
const inventoryItems = ref<any[]>([])
const forecastData = ref<any>(null)
const forecastHours = ref(48)

// 图表相关计算
const displayForecast = computed(() => {
  return forecastData.value?.forecast_data?.slice(0, 12) || []
})

const peakDemand = computed(() => {
  if (!forecastData.value?.forecast_data) return 0
  return Math.max(...forecastData.value.forecast_data.map((f: any) => f.total_demand))
})

const maxDemand = computed(() => {
  if (!forecastData.value?.forecast_data) return 1
  // 用绝对最大值作为基准（不乘1.1），让最高的柱子接近100%
  const vals = forecastData.value.forecast_data.map((f: any) => f.total_demand)
  return Math.max(...vals, 1)
})

function getBarHeight(value: number): number {
  const maxVal = maxDemand.value || 1
  // 确保最小4%，最大95%+，拉大视觉差距
  return Math.max(4, (value / maxVal) * 95)
}

const vehicleFilter = ref('all')
const vehicleFilters = [
  { label: '全部', value: 'all' },
  { label: '空闲', value: 'idle' },
  { label: '运输中', value: 'in_transit' },
  { label: '维护中', value: 'maintenance' },
]

const showAllocateModal = ref(false)
const showResultModal = ref(false)
const allocateLoading = ref(false)
const allocationResult = ref<any>(null)

const allocateForm = ref({
  order_id: '',
  cargo_name: '',
  cargo_category: '冷藏生鲜',
  quantity: 1000,
  origin: '',
  destination: '',
  priority: 'normal',
  temperature_requirement: '',
})

// 待分配的推荐订单（从系统获取或使用默认示例）
const pendingOrders = ref<any[]>([])

function openAllocateModal() {
  // 自动填充默认值
  const now = new Date()
  const dateStr = now.toISOString().slice(0,10).replace(/-/g,'')
  const timeStr = String(now.getHours()).padStart(2,'0') + String(now.getMinutes()).padStart(2,'0')
  allocateForm.value = {
    order_id: `ORD${dateStr}${timeStr}`,
    cargo_name: '冷冻牛肉',
    cargo_category: '冷冻食品',
    quantity: 2000,
    origin: '北京',
    destination: '上海',
    priority: 'normal',
    temperature_requirement: '-18℃~-15℃',
  }
  showAllocateModal.value = true
}

const filteredVehicles = computed(() => {
  if (vehicleFilter.value === 'all') return vehicles.value
  return vehicles.value.filter(v => v.status === vehicleFilter.value)
})

const coldPlateSummary = computed(() => {
  const summary = {
    total_stock: 0,
    total_in_use: 0,
    total_precooled: 0,
    total_damaged: 0,
  }
  coldPlates.value.forEach(cp => {
    summary.total_stock += cp.total_stock
    summary.total_in_use += cp.in_use
    summary.total_precooled += cp.precooled
    summary.total_damaged += cp.damaged
  })
  return summary
})

function getStatusClass(status: string) {
  const classes: Record<string, string> = {
    idle: 'status-idle',
    loading: 'status-loading',
    in_transit: 'status-transit',
    charging: 'status-charging',
    maintenance: 'status-maintenance',
    offline: 'status-offline',
  }
  return classes[status] || 'status-idle'
}

async function loadData() {
  try {
    // 并行加载核心数据（每个 API 独立容错）
    const [whRes, vRes, cpRes, uRes] = await Promise.allSettled([
      resourceAPI.getWarehouses(),
      resourceAPI.getVehicles(),
      resourceAPI.getColdPlates(),
      resourceAPI.getUtilization(),
    ])
    
    warehouses.value = whRes.status === 'fulfilled' ? (whRes.value?.warehouses || []) : []
    vehicles.value = vRes.status === 'fulfilled' ? (vRes.value?.vehicles || []) : []
    coldPlates.value = cpRes.status === 'fulfilled' ? (cpRes.value?.items || []) : []
    utilData.value = uRes.status === 'fulfilled' ? uRes.value : null
    
    // 子数据异步加载失败不影响主页面
    loadInventory()
    loadForecast()
  } catch (e) {
    console.error('loadData error:', e)
    ElMessage.warning('加载资源数据失败，请检查网络或刷新页面重试')
  }
}

async function loadInventory() {
  try {
    const res = await resourceAPI.getWarehouseInventorySummary()
    inventorySummary.value = res?.data || null
    const itemsRes = await resourceAPI.getWarehouseInventory()
    inventoryItems.value = itemsRes?.data?.items || []
  } catch (e) {
    console.log('加载库存失败', e)
  }
}

async function refreshInventory() {
  try {
    // 调用后端刷新接口，重新生成库存数据
    const refreshRes = await fetch('/api/v1/resources/refresh-inventory', { method: 'POST' })
    const data = await refreshRes.json()
    if (data.code === 200) {
      inventorySummary.value = data.data || null
      // 重新加载明细
      const itemsRes = await resourceAPI.getWarehouseInventory()
      inventoryItems.value = itemsRes?.data?.items || []
      ElMessage.success('库存数据已刷新')
    }
  } catch (e) {
    console.log('刷新库存失败', e)
    // 降级：至少重新加载现有数据
    await loadInventory()
  }
}

async function loadForecast() {
  try {
    const res = await resourceAPI.getForecast(forecastHours.value)
    forecastData.value = res
  } catch {
    console.log('加载预测失败')
  }
}

async function doAllocate() {
  if (!allocateForm.value.order_id || !allocateForm.value.cargo_name) {
    ElMessage.warning('请填写订单ID和货物名称')
    return
  }
  allocateLoading.value = true
  try {
    const res = await resourceAPI.allocateAll(allocateForm.value)
    allocationResult.value = res
    showAllocateModal.value = false
    showResultModal.value = true
    loadData()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '分配失败')
  } finally {
    allocateLoading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.resource-page { animation: fadeInUp 0.45s ease-out; padding: 16px; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.header-left { display: flex; align-items: center; gap: 12px; }
.subtitle { font-size: 13px; color: var(--text-muted); }
.header-actions { display: flex; gap: 8px; }

.btn-primary { 
  padding: 8px 16px; background: var(--accent); color: white; 
  border: none; border-radius: 6px; cursor: pointer; display: flex; align-items: center; gap: 6px;
}
.btn-secondary { 
  padding: 8px 16px; background: var(--bg-card); color: var(--text-title); 
  border: 1px solid var(--border); border-radius: 6px; cursor: pointer; display: flex; align-items: center; gap: 6px;
}
.btn-sm { padding: 4px 12px; font-size: 12px; }

.stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 20px; }
.stat-card { display: flex; align-items: center; gap: 12px; padding: 16px; background: var(--bg-card); border-radius: var(--radius); border: 1px solid var(--border); }
.stat-icon { width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0; }
.stat-value { font-family: var(--font-display); font-size: 26px; font-weight: 700; line-height: 1; }
.stat-label { font-size: 12px; color: var(--text-muted); margin-top: 2px; }

.tabs { display: flex; gap: 4px; margin-bottom: 16px; border-bottom: 1px solid var(--border); }
.tab-btn { 
  padding: 10px 20px; border: none; background: none; 
  border-bottom: 2px solid transparent; cursor: pointer; font-size: 14px;
  display: flex; align-items: center; gap: 6px; transition: all 0.2s;
}
.tab-btn.active { border-bottom-color: var(--accent); color: var(--accent); font-weight: 600; }

.res-content { animation: fadeIn 0.3s ease; }
.res-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 16px; }
.glass-card { padding: 16px; background: var(--bg-card); border-radius: var(--radius); border: 1px solid var(--border); }
.card-header { display: flex; justify-content: space-between; align-items: center; font-size: 14px; font-weight: 600; color: var(--text-title); margin-bottom: 14px; }
.count { font-size: 12px; color: var(--text-muted); font-weight: normal; }

/* 冷库卡片 */
.wh-card { padding: 14px; border-radius: 10px; border: 1px solid var(--border); margin-bottom: 10px; }
.wh-header { margin-bottom: 12px; }
.wh-name { font-size: 14px; font-weight: 600; }
.wh-loc { font-size: 12px; color: var(--text-muted); }
.wh-zones { display: flex; flex-direction: column; gap: 8px; }
.wh-zone { padding: 8px 10px; background: var(--bg-page); border-radius: 6px; border-left: 3px solid; }
.wh-zone-header { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.wh-zone-dot { width: 8px; height: 8px; border-radius: 50%; }
.wh-zone-name { font-size: 12px; font-weight: 500; }
.wh-zone-util { margin-left: auto; font-size: 12px; font-weight: 600; font-family: var(--font-mono); }
.wh-zone-bar { height: 6px; background: var(--border); border-radius: 3px; overflow: hidden; margin-bottom: 6px; }
.wh-zone-bar div { height: 100%; border-radius: 3px; transition: width 0.3s; }
.wh-zone-detail { display: flex; gap: 12px; font-size: 10px; color: var(--text-muted); }
.wh-footer { margin-top: 10px; text-align: right; }
.wh-total { font-size: 12px; color: var(--text-muted); }

/* 库存概览 */
.inventory-summary { display: flex; gap: 16px; margin-bottom: 16px; padding: 12px; background: var(--bg-page); border-radius: 8px; }
.inv-stat { text-align: center; flex: 1; }
.inv-label { display: block; font-size: 11px; color: var(--text-muted); }
.inv-value { display: block; font-size: 20px; font-weight: 700; }
.inventory-list { max-height: 300px; overflow-y: auto; }
.inv-item { display: flex; justify-content: space-between; padding: 8px; border-bottom: 1px solid var(--border); }
.inv-item-name { font-size: 12px; font-weight: 500; }
.inv-item-detail { display: flex; gap: 12px; font-size: 11px; color: var(--text-muted); }
.inv-item.warning { background: rgba(245,158,11,0.05); }

/* 车辆卡片 */
.vehicle-filters { display: flex; gap: 4px; margin-bottom: 12px; }
.filter-btn { padding: 4px 12px; font-size: 12px; border: 1px solid var(--border); border-radius: 4px; background: none; cursor: pointer; }
.filter-btn.active { background: var(--accent); color: white; border-color: var(--accent); }
.vehicle-card { padding: 12px; border-radius: 8px; border: 1px solid var(--border); margin-bottom: 8px; }
.vehicle-card.status-idle { border-left: 3px solid var(--teal); }
.vehicle-card.status-in_transit { border-left: 3px solid var(--accent); }
.vehicle-card.status-charging { border-left: 3px solid var(--amber); }
.vehicle-card.status-maintenance { border-left: 3px solid var(--red); opacity: 0.7; }
.vehicle-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.vehicle-plate { font-size: 13px; font-weight: 600; }
.vehicle-status { font-size: 10px; padding: 2px 8px; border-radius: 4px; }
.status-idle { background: rgba(0,210,160,0.1); color: var(--teal); }
.status-transit { background: rgba(0,168,255,0.1); color: var(--accent); }
.status-charging { background: rgba(245,158,11,0.1); color: var(--amber); }
.status-maintenance { background: var(--red-bg); color: var(--red); }
.vehicle-info { display: flex; gap: 12px; font-size: 11px; color: var(--text-muted); margin-bottom: 4px; }
.vehicle-detail { display: flex; justify-content: space-between; font-size: 11px; color: var(--text-muted); }
.vehicle-zones { display: flex; align-items: center; gap: 6px; margin-top: 8px; }
.vz-label { font-size: 10px; color: var(--text-muted); }
.vz-tag { font-size: 10px; padding: 2px 6px; border-radius: 3px; }

/* 预测区域 */
.forecast-summary { display: flex; gap: 16px; margin-bottom: 16px; padding: 12px; background: var(--bg-page); border-radius: 8px; }
.fs-item { flex: 1; }
.fs-label { display: block; font-size: 11px; color: var(--text-muted); }
.fs-value { display: block; font-size: 16px; font-weight: 600; }
.forecast-chart { display: flex; align-items: flex-end; gap: 6px; height: 160px; padding: 10px 10px 28px 10px; margin-bottom: 12px; background: rgba(0,168,255,0.03); border-radius: 10px; }
.fc-bar-wrap { flex: 1; display: flex; flex-direction: column; align-items: center; position: relative; height: 100%; justify-content: flex-end; }
.fc-bar-container { width: 100%; display: flex; justify-content: center; align-items: flex-end; position: relative; height: 130px; }
.fc-bar { width: 70%; border-radius: 4px 4px 0 0; min-height: 4px; transition: all 0.35s ease; cursor: pointer; background: linear-gradient(180deg, #00c6ff 0%, #0072ff 100%); opacity: 0.85; box-shadow: 0 0 6px rgba(0,114,255,0.15); }
.fc-bar:hover { opacity: 1; transform: scaleX(1.15); box-shadow: 0 2px 12px rgba(0,114,255,0.3); }
.fc-bar-peak { background: linear-gradient(180deg, #ff7b54 0%, #ff3366 100%) !important; opacity: 1 !important; box-shadow: 0 0 14px rgba(255,51,102,0.4) !important; }
.fc-label { font-size: 10px; color: var(--text-muted); margin-top: 5px; white-space: nowrap; font-weight: 500; }
.fc-peak-badge { position: absolute; top: -22px; left: 50%; transform: translateX(-50%); font-size: 10px; color: #fff; font-weight: 700; background: linear-gradient(135deg, #ff3366, #ff7b54); padding: 2px 8px; border-radius: 8px; white-space: nowrap; box-shadow: 0 2px 8px rgba(255,51,102,0.3); }
.forecast-recommendations { background: rgba(0,168,255,0.05); border-radius: 6px; padding: 10px; }
.rec-item { font-size: 12px; color: var(--text-muted); margin-bottom: 4px; }
.rec-item:last-child { margin-bottom: 0; }

/* 蓄冷板 */
.coldplate-summary { display: flex; gap: 12px; margin-bottom: 16px; padding: 12px; background: var(--bg-page); border-radius: 8px; }
.cps-item { flex: 1; text-align: center; }
.cps-value { display: block; font-size: 22px; font-weight: 700; }
.cps-label { display: block; font-size: 11px; color: var(--text-muted); }
.coldplate-card { padding: 12px; border-radius: 8px; border: 1px solid var(--border); margin-bottom: 8px; }
.cp-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.cp-name { font-size: 13px; font-weight: 600; }
.cp-type { font-size: 10px; padding: 2px 8px; border-radius: 4px; background: rgba(124,58,237,0.08); color: var(--aurora); }
.cp-specs { display: flex; gap: 12px; font-size: 11px; color: var(--text-muted); margin-bottom: 10px; flex-wrap: wrap; }
.cp-stock { display: flex; gap: 16px; margin-bottom: 10px; }
.cp-stock-item { text-align: center; }
.cp-stock-label { display: block; font-size: 10px; color: var(--text-muted); }
.cp-stock-value { display: block; font-size: 14px; font-weight: 600; }
.cp-progress { margin-top: 8px; }
.cp-progress-bar { height: 8px; background: var(--border); border-radius: 4px; overflow: hidden; position: relative; }
.cp-progress-used { position: absolute; left: 0; top: 0; height: 100%; background: var(--accent); }
.cp-progress-precooled { position: absolute; left: 0; top: 0; height: 100%; background: var(--teal); }
.cp-progress-legend { display: flex; gap: 12px; margin-top: 4px; font-size: 10px; color: var(--text-muted); }
.legend-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 4px; }
.legend-dot.used { background: var(--accent); }
.legend-dot.precooled { background: var(--teal); }

/* 能耗 */
.energy-summary { display: flex; gap: 16px; margin-bottom: 16px; padding: 12px; background: var(--bg-page); border-radius: 8px; }
.es-item { flex: 1; }
.es-value { display: block; font-size: 24px; font-weight: 700; }
.es-label { display: block; font-size: 11px; color: var(--text-muted); }
.energy-chart { display: flex; align-items: flex-end; gap: 4px; height: 180px; padding: 0 4px; }
.ec-bar-wrap { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 100%; }
.ec-bar { width: 100%; border-radius: 3px 3px 0 0; min-width: 8px; transition: height 0.3s; }
.ec-label { font-size: 8px; color: var(--text-muted); margin-top: 4px; transform: rotate(-45deg); white-space: nowrap; }

/* 弹窗 */
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-content { background: white; border-radius: 12px; width: 90%; max-width: 600px; max-height: 90vh; overflow-y: auto; }
.result-modal { max-width: 700px; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid var(--border); }
.modal-header h3 { margin: 0; font-size: 16px; }
.modal-close { font-size: 24px; border: none; background: none; cursor: pointer; color: var(--text-muted); }
.modal-body { padding: 20px; }
.modal-footer { display: flex; justify-content: flex-end; gap: 10px; padding: 16px 20px; border-top: 1px solid var(--border); }

.form-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; }
.form-item label { display: block; font-size: 12px; color: var(--text-muted); margin-bottom: 4px; }
.form-item input, .form-item select { 
  width: 100%; padding: 8px 10px; border: 1px solid var(--border); 
  border-radius: 6px; font-size: 13px; background: var(--bg-page); 
}

.result-summary { display: flex; gap: 20px; margin-bottom: 20px; padding: 12px; background: var(--bg-page); border-radius: 8px; }
.rs-item { flex: 1; }
.rs-label { display: block; font-size: 11px; color: var(--text-muted); }
.rs-value { display: block; font-size: 14px; font-weight: 600; }
.result-details { display: flex; flex-direction: column; gap: 12px; }
.rd-section { padding: 12px; border-radius: 8px; border: 1px solid var(--border); }
.rd-section.success { border-color: var(--teal); background: rgba(0,210,160,0.05); }
.rd-header { display: flex; justify-content: space-between; margin-bottom: 8px; }
.rd-header span:first-child { font-size: 13px; font-weight: 600; }
.rd-header span.success { color: var(--teal); font-size: 12px; }
.rd-header span.failed { color: var(--red); font-size: 12px; }
.rd-info { display: flex; gap: 16px; font-size: 12px; color: var(--text-title); flex-wrap: wrap; }

@media (max-width: 1024px) {
  .res-grid { grid-template-columns: 1fr; }
  .stats-row { grid-template-columns: repeat(2, 1fr); }
  .form-grid { grid-template-columns: 1fr; }
}
</style>