<template>
  <div class="route-page">
    <div class="page-header">
      <div>
        <h2 class="page-title">冷链路径智能规划</h2>
        <p class="page-desc">基于深度学习多目标优化 · 整车直达/零担分拨/多点卸货 · 温敏等级差异化策略</p>
      </div>
    </div>

    <div class="main-content">
      <!-- 左侧规划面板 -->
      <div class="left-panel">
        <div class="glass-card">
          <h3 class="panel-title">规划参数配置</h3>
          
          <div class="form-row">
            <div class="form-group">
              <label>出发城市</label>
              <el-select v-model="form.origin" placeholder="选择城市" style="width:100%">
                <el-option v-for="c in cities" :key="c.name" :value="c.name">{{ c.name }}</el-option>
              </el-select>
            </div>
            <div class="form-group">
              <label>目的城市</label>
              <el-select v-model="form.destination" placeholder="选择城市" style="width:100%">
                <el-option v-for="c in cities" :key="c.name" :value="c.name">{{ c.name }}</el-option>
              </el-select>
            </div>
          </div>

          <div class="form-group">
            <label>运输模式</label>
            <el-select v-model="form.transport_mode" placeholder="选择模式" style="width:100%">
              <el-option v-for="m in transportModes" :key="m.value" :value="m.value">
                {{ m.label }}
              </el-option>
            </el-select>
          </div>

          <div class="form-group">
            <label>货物类型</label>
            <el-select v-model="form.cargo_type" placeholder="选择类型" style="width:100%">
              <el-option v-for="ct in cargoTypes" :key="ct.name" :value="ct.name">
                {{ ct.name }} ({{ ct.temperature_range }})
              </el-option>
            </el-select>
          </div>

          <div class="form-group">
            <label>温敏等级</label>
            <div class="sensitivity-options">
              <label v-for="sl in sensitivityLevels" :key="sl.value" class="sensitivity-radio">
                <input type="radio" v-model="form.temperature_sensitivity" :value="sl.value" />
                <div class="sensitivity-card" :class="sl.value">
                  <div class="sensitivity-label">{{ sl.label }}</div>
                  <div class="sensitivity-desc">{{ sl.description }}</div>
                </div>
              </label>
            </div>
          </div>

          <div class="form-group">
            <label>货物重量 (kg)</label>
            <el-input-number v-model="form.cargo_weight_kg" :min="100" :max="30000" :step="100" style="width:100%" />
          </div>

          <button class="btn-primary" @click="doPlan" :disabled="planning">
            {{ planning ? '规划中...' : '智能规划路线' }}
          </button>
        </div>

        <div class="glass-card">
          <h3 class="panel-title">运输模式说明</h3>
          <div class="mode-explanation">
            <div v-for="m in transportModes" :key="m.value" class="mode-item">
              <div class="mode-header">
                <span class="mode-icon">{{ m.label }}</span>
                <span class="mode-tag">{{ m.suitable_for }}</span>
              </div>
              <p class="mode-desc">{{ m.description }}</p>
              <div class="mode-features">
                <span v-for="(f, idx) in m.features" :key="idx" class="feature-tag">{{ f }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧结果区域 -->
      <div class="right-panel">
        <!-- 地图 -->
        <div class="map-container" id="route-map"></div>

        <!-- 方案对比 -->
        <div v-if="planComparison" class="results-container">
          <div class="results-header">
            <h3>规划方案对比</h3>
            <span class="route-info">{{ form.origin }} → {{ form.destination }}</span>
          </div>

          <div class="plans-grid">
            <div 
              v-for="plan in planComparison.plans" 
              :key="plan.plan_id" 
              class="plan-card" 
              :class="{ recommended: plan.recommended, selected: selectedPlan?.plan_id === plan.plan_id }"
              @click="selectPlan(plan)"
            >
              <div class="plan-header">
                <div class="plan-title">{{ getTransportModeLabel(plan.transport_mode) }}</div>
                <span v-if="plan.recommended" class="recommend-badge">✓ 推荐</span>
              </div>
              
              <div class="plan-summary">
                <div class="summary-item">
                  <span class="summary-label">距离</span>
                  <span class="summary-value">{{ plan.estimated_total_distance_km }} km</span>
                </div>
                <div class="summary-item">
                  <span class="summary-label">耗时</span>
                  <span class="summary-value">{{ plan.estimated_total_duration_h }} h</span>
                </div>
                <div class="summary-item">
                  <span class="summary-label">费用</span>
                  <span class="summary-value">¥{{ plan.estimated_total_cost_yuan }}</span>
                </div>
                <div class="summary-item">
                  <span class="summary-label">风险</span>
                  <span class="summary-value" :class="getRiskClass(plan.overall_risk_score)">{{ plan.overall_risk_score }}</span>
                </div>
              </div>

              <div class="plan-scores">
                <div v-for="(score, key) in plan.scores" :key="key" class="score-row">
                  <span class="score-name">{{ key }}</span>
                  <div class="score-track">
                    <div class="score-fill" :style="{ width: score + '%' }"></div>
                  </div>
                  <span class="score-value">{{ score }}</span>
                </div>
              </div>

              <div class="plan-footer">
                <span class="plan-id">{{ plan.plan_id }}</span>
                <span class="view-detail">查看详情 →</span>
              </div>
            </div>
          </div>

          <!-- 方案详情 -->
          <div v-if="selectedPlan" class="plan-detail glass-card">
            <div class="detail-header">
              <h3>{{ getTransportModeLabel(selectedPlan.transport_mode) }} - 路线详情</h3>
              <button class="close-btn" @click="selectedPlan = null">×</button>
            </div>

            <div class="detail-body">
              <!-- 路线概览 -->
              <div class="overview-section">
                <h4>路线概览</h4>
                <div class="overview-grid">
                  <div class="overview-item">
                    <div class="ov-value">{{ selectedPlan.estimated_total_distance_km }}</div>
                    <div class="ov-label">总距离 (km)</div>
                  </div>
                  <div class="overview-item">
                    <div class="ov-value">{{ selectedPlan.estimated_total_duration_h }}</div>
                    <div class="ov-label">预计耗时 (h)</div>
                  </div>
                  <div class="overview-item">
                    <div class="ov-value">¥{{ selectedPlan.estimated_total_cost_yuan }}</div>
                    <div class="ov-label">总费用</div>
                  </div>
                  <div class="overview-item">
                    <div class="ov-value">{{ selectedPlan.total_carbon_emission_kg }}</div>
                    <div class="ov-label">碳排放 (kg)</div>
                  </div>
                </div>
              </div>

              <!-- 节点链路 -->
              <div class="nodes-section">
                <h4>节点链路</h4>
                <div class="nodes-chain">
                  <div v-for="(node, idx) in selectedPlan.nodes" :key="node.node_id" class="node-item">
                    <div class="node-dot" :class="getNodeClass(node.level)"></div>
                    <div class="node-info">
                      <div class="node-name">{{ node.name }}</div>
                      <div class="node-city">{{ node.city }}</div>
                    </div>
                    <div v-if="idx < selectedPlan.nodes.length - 1" class="node-arrow">→</div>
                  </div>
                </div>
              </div>

              <!-- 分段详情 -->
              <div class="segments-section">
                <h4>分段详情</h4>
                <div class="segments-table">
                  <div class="segments-header">
                    <span>路段</span>
                    <span>距离(km)</span>
                    <span>耗时(h)</span>
                    <span>费用(¥)</span>
                    <span>风险等级</span>
                    <span>拥堵概率</span>
                    <span>高温风险</span>
                  </div>
                  <div v-for="seg in selectedPlan.segments" :key="seg.segment_id" class="segments-row">
                    <span>{{ seg.from_city }} → {{ seg.to_city }}</span>
                    <span>{{ seg.distance_km }}</span>
                    <span>{{ seg.estimated_duration_h }}</span>
                    <span>{{ seg.toll_cost_yuan + seg.fuel_cost_yuan }}</span>
                    <span><span class="risk-badge" :class="seg.risk_level">{{ seg.risk_level }}</span></span>
                    <span>{{ (seg.congestion_probability * 100).toFixed(0) }}%</span>
                    <span>{{ (seg.heat_risk_probability * 100).toFixed(0) }}%</span>
                  </div>
                </div>
              </div>

              <!-- 风险报告 -->
              <div class="risk-section">
                <h4>风险预判报告</h4>
                <div class="risk-grid">
                  <div class="risk-card">
                    <div class="risk-header">
                      <span class="risk-title">整体风险评分</span>
                      <span class="risk-score" :class="getRiskClass(selectedPlan.risk_report.overall_risk_score)">
                        {{ selectedPlan.risk_report.overall_risk_score }}
                      </span>
                    </div>
                    <div class="risk-details">
                      <div class="risk-detail">高风险路段: {{ selectedPlan.risk_report.high_risk_segment_count }} 段</div>
                      <div class="risk-detail">中风险路段: {{ selectedPlan.risk_report.medium_risk_segment_count }} 段</div>
                      <div class="risk-detail">平均拥堵概率: {{ (selectedPlan.risk_report.avg_congestion_probability * 100).toFixed(0) }}%</div>
                      <div class="risk-detail">平均高温风险: {{ (selectedPlan.risk_report.avg_heat_risk_probability * 100).toFixed(0) }}%</div>
                    </div>
                  </div>
                  <div class="risk-alerts">
                    <h5>风险路段提醒</h5>
                    <div v-if="selectedPlan.risk_report.risk_segments.length === 0" class="no-risk">暂无高风险路段</div>
                    <div v-for="(seg, idx) in selectedPlan.risk_report.risk_segments" :key="idx" class="risk-alert-item">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 9v4M12 17h.01M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/></svg>
                      <span>{{ seg }}</span>
                    </div>
                  </div>
                </div>
                <div class="recommended-actions">
                  <h5>建议措施</h5>
                  <div v-for="(action, idx) in selectedPlan.risk_report.recommended_actions.filter((a:any) => a)" :key="idx" class="action-item">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 12l2 2 4-4"/></svg>
                    <span>{{ action }}</span>
                  </div>
                </div>
              </div>

              <!-- 车辆与司机 -->
              <div class="resources-section">
                <h4>资源配置</h4>
                <div class="resources-grid">
                  <div class="resource-card">
                    <h5>车辆配置</h5>
                    <div class="resource-item">车型: {{ selectedPlan.vehicle_allocation.recommended_model }}</div>
                    <div class="resource-item">载重: {{ selectedPlan.vehicle_allocation.capacity_kg }} kg</div>
                    <div class="resource-item">制冷系统: {{ selectedPlan.vehicle_allocation.cooling_system }}</div>
                    <div class="resource-item">温控范围: {{ selectedPlan.vehicle_allocation.temperature_range }}</div>
                  </div>
                  <div class="resource-card">
                    <h5>司机排班</h5>
                    <div class="resource-item">司机人数: {{ selectedPlan.driver_schedule.driver_count }} 人</div>
                    <div class="resource-item">轮班时长: {{ selectedPlan.driver_schedule.shift_hours }} 小时/班</div>
                    <div class="resource-item">驾驶时长: {{ selectedPlan.driver_schedule.total_driving_h }} 小时</div>
                    <div v-if="selectedPlan.driver_schedule.rest_stops.length > 0" class="resource-item">
                      休息站点: {{ selectedPlan.driver_schedule.rest_stops.join(', ') }}
                    </div>
                  </div>
                </div>
              </div>

              <!-- 围栏摘要 -->
              <div class="fence-section">
                <h4>电子围栏配置</h4>
                <div class="fence-info">
                  <span>已创建围栏: {{ selectedPlan.fence_summary.total_fence_count }} 个</span>
                  <span>路段围栏: {{ selectedPlan.fence_summary.segment_fences }} 个</span>
                  <span>节点围栏: {{ selectedPlan.fence_summary.node_fences }} 个</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 活跃路线 -->
        <div class="active-routes glass-card">
          <h3 class="panel-title">活跃路线</h3>
          <div v-if="activeRoutes.length === 0" class="empty-state">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" style="color:var(--text-muted)"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
            <p>暂无活跃路线</p>
          </div>
          <div v-for="route in activeRoutes" :key="route.route_id" class="active-route-item" @click="selectActiveRoute(route)">
            <div class="ar-header">
              <span class="ar-route">{{ route.origin }} → {{ route.destination }}</span>
              <span class="ar-status" :class="route.status">{{ route.status }}</span>
            </div>
            <div class="ar-info">
              <span>{{ route.plate_number }}</span>
              <span>{{ route.cargo_type }}</span>
              <span>{{ getSensitivityLabel(route.temperature_sensitivity) }}</span>
            </div>
            <div class="ar-progress">
              <div class="ar-bar" :style="{ width: route.progress_percent + '%' }"></div>
            </div>
            <div class="ar-metrics">
              <span>{{ route.distance_km }} km</span>
              <span>{{ route.estimated_duration_h }} h</span>
              <span>¥{{ route.total_cost_yuan }}</span>
              <span :class="getRiskClass(route.risk_score)">风险 {{ route.risk_score }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import { routeAPI } from '@/api'
import { ElMessage } from 'element-plus'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const form = reactive({
  origin: '北京',
  destination: '上海',
  transport_mode: 'direct',
  cargo_type: '冷藏生鲜',
  temperature_sensitivity: 'medium',
  cargo_weight_kg: 5000,
})

const planning = ref(false)
const planComparison = ref<any>(null)
const selectedPlan = ref<any>(null)
const activeRoutes = ref<any[]>([])
const cities = ref<any[]>([])
const cargoTypes = ref<any[]>([])
const sensitivityLevels = ref<any[]>([])
const transportModes = ref<any[]>([])

let map: any = null

function selectPlan(plan: any) {
  selectedPlan.value = selectedPlan.value?.plan_id === plan.plan_id ? null : plan
}

function selectActiveRoute(route: any) {
  ElMessage.info(`选择路线: ${route.origin} → ${route.destination}`)
}

function getTransportModeLabel(mode: string) {
  const map: Record<string, string> = {
    direct: '整车直达模式',
    hub_distribution: '零担干支分拨模式',
    multi_drop: '多点沿途卸货模式',
  }
  return map[mode] || mode
}

function getSensitivityLabel(level: string) {
  const map: Record<string, string> = {
    high: '高敏',
    medium: '中敏',
    low: '低敏',
  }
  return map[level] || level
}

function getNodeClass(level: string) {
  const map: Record<string, string> = {
    hub_provincial: 'hub',
    distribution_city: 'distribution',
    end_node: 'end',
  }
  return map[level] || 'end'
}

function getRiskClass(score: number) {
  if (score >= 80) return 'low'
  if (score >= 60) return 'medium'
  return 'high'
}

function initMap() {
  if (map) return
  map = L.map('route-map').setView([35.5, 110], 4)
  L.tileLayer('https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}', {
    subdomains: ['1', '2', '3', '4'],
    maxZoom: 18,
    attribution: '&copy; 高德地图',
  }).addTo(map)
  setTimeout(() => map?.invalidateSize(), 200)
}

function drawRouteOnMap(plans: any[]) {
  if (!map) return
  map.eachLayer((layer: any) => {
    if (layer instanceof L.Polyline || layer instanceof L.Marker) map.removeLayer(layer)
  })

  const colors = ['#00a8ff', '#f59e0b', '#7c3aed']
  plans.forEach((plan: any, i: number) => {
    const coords = plan.nodes.map((n: any) => [n.lat, n.lng])
    L.polyline(coords as any, {
      color: colors[i % colors.length],
      weight: plan.recommended ? 5 : 3,
      opacity: plan.recommended ? 1 : 0.6,
      dashArray: plan.recommended ? '' : '8 4',
    }).addTo(map)
    
    coords.forEach((coord: any, idx: number) => {
      const color = idx === 0 ? '#00a8ff' : idx === coords.length - 1 ? '#ef4444' : '#f59e0b'
      L.circleMarker(coord as any, {
        radius: plan.recommended ? 8 : 6,
        color: '#fff',
        fillColor: color,
        fillOpacity: 1,
        weight: 2,
      }).addTo(map)
    })
  })

  const allCoords = plans.flatMap((plan: any) => plan.nodes.map((n: any) => [n.lat, n.lng]))
  if (allCoords.length > 0) {
    map.fitBounds(L.latLngBounds(allCoords as any), { padding: [40, 40] })
  }
}

async function doPlan() {
  if (!form.origin || !form.destination) {
    ElMessage.warning('请选择出发城市和目的城市')
    return
  }

  planning.value = true
  try {
    const res: any = await routeAPI.plan(form)
    planComparison.value = res.comparison
    await nextTick()
    drawRouteOnMap(res.comparison.plans)
  } catch (e) {
    console.error(e)
    ElMessage.error('路线规划失败')
  } finally {
    planning.value = false
  }
}

async function loadActiveRoutes() {
  try {
    const res: any = await routeAPI.getActive()
    activeRoutes.value = res.routes || []
  } catch {
    ElMessage.warning('加载活跃路线失败')
  }
}

async function loadRefData() {
  try {
    const [citiesRes, cargoRes, sensitivityRes, modesRes] = await Promise.all([
      routeAPI.getCities(),
      routeAPI.getCargoTypes(),
      routeAPI.getSensitivityLevels(),
      routeAPI.getTransportModes(),
    ])
    cities.value = citiesRes.cities || []
    cargoTypes.value = cargoRes.types || []
    sensitivityLevels.value = sensitivityRes.levels || []
    transportModes.value = modesRes.modes || []
  } catch {
    cities.value = ['北京', '上海', '广州', '成都', '武汉', '西安', '杭州', '深圳'].map((name, idx) => ({
      name, lat: 35 + (idx % 3) * 3, lng: 110 + (idx % 4) * 5,
    }))
    cargoTypes.value = ['冷冻食品', '冷藏生鲜', '疫苗医药', '化工制剂', '其他'].map(name => ({
      name, temperature_range: '-20°C ~ 10°C',
    }))
    sensitivityLevels.value = [
      { value: 'high', label: '高敏物资', description: '疫苗、生物制剂' },
      { value: 'medium', label: '中敏物资', description: '鲜肉、海鲜、鲜果' },
      { value: 'low', label: '低敏物资', description: '冷冻肉类、速冻食品' },
    ]
    transportModes.value = [
      { value: 'direct', label: '整车直达模式', suitable_for: '大批量高价值', description: '一单一车、全程不换车', features: ['起止仓围栏', '干线围栏'] },
      { value: 'hub_distribution', label: '零担干支分拨模式', suitable_for: '小批量多批次', description: '多级节点分拨', features: ['枢纽围栏', '换车台账'] },
      { value: 'multi_drop', label: '多点沿途卸货模式', suitable_for: '连锁商超', description: '多站点最优排序', features: ['时效窗口', '折返规避'] },
    ]
  }
}

onMounted(async () => {
  loadRefData()
  loadActiveRoutes()
  await nextTick()
  initMap()
})
</script>

<style scoped>
.route-page { animation: fadeInUp 0.45s ease-out; }
.page-header { margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
.page-title { font-size: 20px; font-weight: 700; color: var(--text-title); }
.page-desc { font-size: 13px; color: var(--text-muted); margin-top: 4px; }

.main-content { display: grid; grid-template-columns: 360px 1fr; gap: 20px; }

.left-panel { display: flex; flex-direction: column; gap: 16px; }
.panel-title { font-size: 14px; font-weight: 600; color: var(--text-title); margin-bottom: 14px; }

.form-row { display: flex; gap: 10px; }
.form-row .form-group { flex: 1; }

.form-group { margin-bottom: 14px; }
.form-group label { display: block; font-size: 12px; color: var(--text-muted); margin-bottom: 6px; font-weight: 500; }

.sensitivity-options { display: flex; flex-direction: column; gap: 8px; }
.sensitivity-radio { display: flex; align-items: stretch; cursor: pointer; }
.sensitivity-radio input { display: none; }
.sensitivity-card { flex: 1; padding: 10px; border-radius: 8px; border: 1px solid var(--border); transition: all 0.2s; }
.sensitivity-radio input:checked + .sensitivity-card { border-color: var(--accent); background: rgba(0,168,255,0.04); }
.sensitivity-card.high { border-left: 3px solid #ef4444; }
.sensitivity-card.medium { border-left: 3px solid #f59e0b; }
.sensitivity-card.low { border-left: 3px solid #10b981; }
.sensitivity-label { font-size: 13px; font-weight: 600; }
.sensitivity-desc { font-size: 11px; color: var(--text-muted); margin-top: 2px; }

.btn-primary { width: 100%; padding: 10px; border-radius: 8px; background: linear-gradient(135deg, var(--accent), var(--aurora)); color: #fff; border: none; font-size: 14px; font-weight: 500; cursor: pointer; transition: opacity 0.2s; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }

.mode-explanation { display: flex; flex-direction: column; gap: 12px; }
.mode-item { padding: 12px; border-radius: 8px; background: var(--bg-elevated); }
.mode-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.mode-icon { font-size: 13px; font-weight: 600; }
.mode-tag { font-size: 10px; padding: 2px 6px; border-radius: 4px; background: rgba(0,168,255,0.1); color: var(--accent); }
.mode-desc { font-size: 12px; color: var(--text-muted); margin-bottom: 6px; }
.mode-features { display: flex; flex-wrap: wrap; gap: 4px; }
.feature-tag { font-size: 10px; padding: 2px 6px; border-radius: 4px; background: rgba(0,0,0,0.04); color: var(--text-secondary); }

.right-panel { display: flex; flex-direction: column; gap: 16px; }
.map-container { height: 350px; border-radius: var(--radius); overflow: hidden; border: 1px solid var(--border); }

.results-container { background: var(--bg-card); border-radius: var(--radius); border: 1px solid var(--border); padding: 16px; }
.results-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.results-header h3 { font-size: 14px; font-weight: 600; }
.route-info { font-size: 12px; color: var(--text-muted); }

.plans-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; margin-bottom: 16px; }
.plan-card { padding: 14px; border-radius: 10px; border: 1px solid var(--border); background: var(--bg-elevated); cursor: pointer; transition: all 0.2s; }
.plan-card:hover { border-color: var(--accent); }
.plan-card.recommended { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent); }
.plan-card.selected { border-color: var(--accent); box-shadow: 0 2px 12px rgba(0,168,255,0.15); }

.plan-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.plan-title { font-size: 13px; font-weight: 600; }
.recommend-badge { font-size: 10px; padding: 2px 8px; border-radius: 4px; background: linear-gradient(135deg, var(--accent), var(--aurora)); color: #fff; font-weight: 600; }

.plan-summary { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-bottom: 12px; }
.summary-item { display: flex; justify-content: space-between; font-size: 12px; }
.summary-label { color: var(--text-muted); }
.summary-value { font-weight: 600; }
.summary-value.low { color: #10b981; }
.summary-value.medium { color: #f59e0b; }
.summary-value.high { color: #ef4444; }

.plan-scores { display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px; }
.score-row { display: flex; align-items: center; gap: 8px; font-size: 11px; }
.score-name { width: 70px; color: var(--text-muted); }
.score-track { flex: 1; height: 4px; background: var(--border); border-radius: 2px; overflow: hidden; }
.score-fill { height: 100%; background: linear-gradient(90deg, var(--teal), var(--accent)); border-radius: 2px; }
.score-value { width: 30px; text-align: right; font-family: var(--font-mono); font-weight: 500; }

.plan-footer { display: flex; justify-content: space-between; align-items: center; padding-top: 8px; border-top: 1px solid var(--border); }
.plan-id { font-size: 10px; color: var(--text-muted); font-family: var(--font-mono); }
.view-detail { font-size: 11px; color: var(--accent); }

.plan-detail { margin-top: 16px; }
.detail-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.detail-header h3 { font-size: 14px; font-weight: 600; }
.close-btn { background: none; border: none; font-size: 20px; color: var(--text-muted); cursor: pointer; }

.detail-body { display: flex; flex-direction: column; gap: 20px; }

.overview-section h4 { font-size: 13px; font-weight: 600; color: var(--text-title); margin-bottom: 12px; }
.overview-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.overview-item { text-align: center; padding: 12px; border-radius: 8px; background: var(--bg-elevated); }
.ov-value { font-size: 18px; font-weight: 700; color: var(--accent); font-family: var(--font-display); }
.ov-label { font-size: 11px; color: var(--text-muted); margin-top: 4px; }

.nodes-section h4 { font-size: 13px; font-weight: 600; color: var(--text-title); margin-bottom: 12px; }
.nodes-chain { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; padding: 12px; background: var(--bg-elevated); border-radius: 8px; }
.node-item { display: flex; align-items: center; gap: 8px; }
.node-dot { width: 10px; height: 10px; border-radius: 50%; }
.node-dot.hub { background: #10b981; }
.node-dot.distribution { background: #f59e0b; }
.node-dot.end { background: var(--accent); }
.node-info { display: flex; flex-direction: column; }
.node-name { font-size: 12px; font-weight: 500; }
.node-city { font-size: 10px; color: var(--text-muted); }
.node-arrow { color: var(--text-muted); font-size: 14px; }

.segments-section h4 { font-size: 13px; font-weight: 600; color: var(--text-title); margin-bottom: 12px; }
.segments-table { border-radius: 8px; overflow: hidden; border: 1px solid var(--border); }
.segments-header { display: grid; grid-template-columns: 180px 80px 80px 80px 80px 90px 90px; padding: 10px 12px; background: var(--bg-elevated); font-size: 11px; font-weight: 600; color: var(--text-muted); }
.segments-row { display: grid; grid-template-columns: 180px 80px 80px 80px 80px 90px 90px; padding: 10px 12px; border-bottom: 1px solid var(--border); font-size: 12px; align-items: center; }
.segments-row:last-child { border-bottom: none; }
.risk-badge { font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: 600; }
.risk-badge.low { background: rgba(16,185,129,0.1); color: #10b981; }
.risk-badge.medium { background: rgba(245,158,11,0.1); color: #f59e0b; }
.risk-badge.high { background: rgba(239,68,68,0.1); color: #ef4444; }

.risk-section h4 { font-size: 13px; font-weight: 600; color: var(--text-title); margin-bottom: 12px; }
.risk-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.risk-card { padding: 14px; border-radius: 8px; background: var(--bg-elevated); }
.risk-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.risk-title { font-size: 12px; font-weight: 600; }
.risk-score { font-size: 24px; font-weight: 700; font-family: var(--font-display); }
.risk-score.low { color: #10b981; }
.risk-score.medium { color: #f59e0b; }
.risk-score.high { color: #ef4444; }
.risk-details { display: flex; flex-direction: column; gap: 4px; font-size: 11px; color: var(--text-muted); }

.risk-alerts { padding: 14px; border-radius: 8px; background: var(--bg-elevated); }
.risk-alerts h5 { font-size: 12px; font-weight: 600; margin-bottom: 8px; }
.no-risk { font-size: 12px; color: #10b981; }
.risk-alert-item { display: flex; align-items: center; gap: 6px; font-size: 11px; color: #ef4444; margin-bottom: 4px; }

.recommended-actions { margin-top: 12px; padding: 12px; border-radius: 8px; background: rgba(0,168,255,0.04); }
.recommended-actions h5 { font-size: 12px; font-weight: 600; margin-bottom: 8px; }
.action-item { display: flex; align-items: center; gap: 6px; font-size: 11px; color: var(--text-secondary); margin-bottom: 4px; }

.resources-section h4 { font-size: 13px; font-weight: 600; color: var(--text-title); margin-bottom: 12px; }
.resources-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.resource-card { padding: 14px; border-radius: 8px; background: var(--bg-elevated); }
.resource-card h5 { font-size: 12px; font-weight: 600; margin-bottom: 8px; }
.resource-item { font-size: 11px; color: var(--text-secondary); margin-bottom: 4px; }

.fence-section h4 { font-size: 13px; font-weight: 600; color: var(--text-title); margin-bottom: 10px; }
.fence-info { display: flex; gap: 16px; font-size: 12px; color: var(--text-secondary); }

.active-routes { padding: 16px; }
.empty-state { text-align: center; padding: 24px; color: var(--text-muted); }
.empty-state p { margin-top: 8px; font-size: 13px; }

.active-route-item { padding: 12px; border-radius: 8px; margin-bottom: 8px; border: 1px solid var(--border); cursor: pointer; transition: all 0.2s; }
.active-route-item:hover { border-color: var(--accent); background: rgba(0,168,255,0.02); }
.ar-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.ar-route { font-size: 13px; font-weight: 600; }
.ar-status { font-size: 10px; padding: 2px 6px; border-radius: 4px; }
.ar-status.运输中 { background: rgba(0,168,255,0.1); color: var(--accent); }
.ar-status.即将到达 { background: rgba(16,185,129,0.1); color: #10b981; }
.ar-status.卸货中 { background: rgba(245,158,11,0.1); color: #f59e0b; }
.ar-info { display: flex; gap: 12px; font-size: 11px; color: var(--text-muted); margin-bottom: 6px; }
.ar-progress { height: 4px; background: var(--border); border-radius: 2px; overflow: hidden; margin-bottom: 6px; }
.ar-bar { height: 100%; background: linear-gradient(90deg, var(--teal), var(--accent)); border-radius: 2px; }
.ar-metrics { display: flex; gap: 12px; font-size: 11px; color: var(--text-muted); }

@media (max-width: 1200px) {
  .main-content { grid-template-columns: 1fr; }
  .plans-grid { grid-template-columns: 1fr; }
  .overview-grid { grid-template-columns: repeat(2, 1fr); }
  .risk-grid { grid-template-columns: 1fr; }
  .resources-grid { grid-template-columns: 1fr; }
  .segments-header, .segments-row { grid-template-columns: 1fr 80px 80px 80px; }
}
</style>
