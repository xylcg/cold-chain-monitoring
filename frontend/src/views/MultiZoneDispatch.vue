<template>
  <div class="dispatch-page">
    <div class="page-header">
      <h2 class="page-title">多温区车厢智能调度</h2>
      <span class="subtitle">多目标优化算法 · 冷冻-18℃ | 冷藏0-4℃ | 恒温15-25℃</span>
    </div>

    <!-- 温区说明 -->
    <div class="zone-legend">
      <div class="zone-item" v-for="z in zones" :key="z.key">
        <div class="zone-dot" :style="{background:z.color}"></div>
        <span class="zone-name">{{ z.name }}</span>
        <span class="zone-range">{{ z.range }}</span>
        <span class="zone-target">目标 {{ z.target }}℃</span>
      </div>
      <div class="zone-item high-sens">
        <div class="zone-dot" style="background:#ef4444"></div>
        <span class="zone-name">高敏货物</span>
        <span class="zone-range">强制隔离</span>
      </div>
    </div>

    <!-- 算法说明条 -->
    <div class="algo-bar">
      <div class="algo-step"><span class="step-num">1</span>温区合规校验</div>
      <div class="algo-arrow">→</div>
      <div class="algo-step"><span class="step-num">2</span>货量比例适配</div>
      <div class="algo-arrow">→</div>
      <div class="algo-step"><span class="step-num">3</span>订单聚合优化</div>
      <div class="algo-arrow">→</div>
      <div class="algo-step"><span class="step-num">4</span>成本最优匹配</div>
    </div>

    <!-- 顶部统计卡片 -->
    <div class="stats-row" v-if="dispatchStats">
      <div class="stat-card">
        <div class="stat-val">{{ dispatchStats.today_orders }}</div>
        <div class="stat-label">待调度订单</div>
      </div>
      <div class="stat-card">
        <div class="stat-val text-teal">{{ dispatchStats.today_assigned }}</div>
        <div class="stat-label">已分配</div>
      </div>
      <div class="stat-card">
        <div class="stat-val text-amber">{{ dispatchStats.today_unassigned }}</div>
        <div class="stat-label">未分配</div>
      </div>
      <div class="stat-card">
        <div class="stat-val">{{ dispatchStats.fleet_utilization }}%</div>
        <div class="stat-label">车队利用率</div>
      </div>
      <div class="stat-card">
        <div class="stat-val">{{ dispatchStats.avg_capacity_usage }}%</div>
        <div class="stat-label">平均装载率</div>
      </div>
      <div class="stat-card">
        <div class="stat-val text-teal">{{ dispatchStats.cost_saved_percent }}%</div>
        <div class="stat-label">成本节省</div>
      </div>
      <div class="stat-card">
        <div class="stat-val text-red">{{ dispatchStats.high_sensitivity_count }}</div>
        <div class="stat-label">高敏订单</div>
      </div>
    </div>

    <div class="dispatch-layout">
      <!-- 左侧：多温区车辆 -->
      <div class="left-col">
        <div class="glass-card">
          <div class="card-header">
            多温区车辆 ({{ vehicles.length }})
            <span class="sub">{{ idleCount }}空闲</span>
          </div>
          <div v-for="v in vehicles" :key="v.id" class="vehicle-card" :class="'v-'+v.status">
            <div class="v-top">
              <div class="v-name">{{ v.plate }} <span class="v-model">{{ v.model }}</span></div>
              <div class="v-status" :class="'status-'+v.status">{{ statusLabel(v.status) }}</div>
            </div>
            <div class="v-zones">
              <span v-for="z in v.zones" :key="z" class="v-zone-tag"
                    :style="{background:zoneColor(z)+'20',color:zoneColor(z)}">
                {{ zoneLabel(z) }} {{ v.compartments[z].capacity_kg }}kg
              </span>
            </div>
            <div class="v-meta">
              <span>{{ v.total_capacity_kg }}kg / {{ v.total_capacity_m3 }}m³</span>
              <span>{{ v.fuel_type === 'diesel' ? '柴油' : '电动' }} · {{ v.fuel_consumption }}L/100km</span>
            </div>
            <div class="v-driver">
              <span>{{ v.driver }}</span>
              <span class="v-city">{{ v.current_city }}</span>
            </div>
          </div>
        </div>

        <!-- 温区车辆覆盖 -->
        <div class="glass-card" v-if="vehicles.length">
          <div class="card-header">温区车辆覆盖</div>
          <div v-for="zc in zoneCoverageList" :key="zc.zone" class="zone-cov-item">
            <span class="zc-dot" :style="{background: zc.color}"></span>
            <span class="zc-name">{{ zc.zone }}</span>
            <span class="zc-range">{{ zc.range }}</span>
            <span class="zc-count">{{ zc.vehicle_count }}辆</span>
          </div>
        </div>
      </div>

      <!-- 中间：待调度订单 -->
      <div class="mid-col">
        <div class="glass-card">
          <div class="card-header">
            待调度订单 ({{ filteredOrders.length }})
            <div class="header-filters">
              <select v-model="orderZoneFilter" class="mini-select">
                <option value="">全部温区</option>
                <option value="frozen">冷冻区</option>
                <option value="refrigerated">冷藏区</option>
                <option value="ambient">恒温区</option>
              </select>
            </div>
          </div>
          <div class="orders-scroll">
            <div v-for="o in filteredOrders" :key="o.order_id" class="order-item"
                 :class="{ 'high-sens': o.is_high_sensitivity }">
              <div class="o-top">
                <span class="o-id">{{ o.order_id }}</span>
                <span class="o-zone" :style="{color:zoneColor(o.temp_zone)}">{{ o.zone_name }}</span>
                <span v-if="o.is_high_sensitivity" class="o-high-sens">高敏</span>
                <span v-else-if="o.priority !== 'normal'" class="o-priority">{{ o.priority === 'urgent' ? '紧急' : '优先' }}</span>
              </div>
              <div class="o-mid">
                <span class="o-cargo">{{ o.cargo_type }}</span>
                <span>{{ o.weight_kg }}kg</span>
                <span>{{ o.volume_m3 }}m³</span>
                <span class="o-temp">目标{{ o.target_temp_c }}℃</span>
              </div>
              <div class="o-bottom">
                <span class="o-route">{{ o.origin }} → {{ o.destination }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：调度方案 -->
      <div class="right-col">
        <div class="glass-card">
          <div class="card-header">智能调度方案</div>
          <button class="btn btn-primary btn-block" @click="doAssign" :disabled="assigning">
            {{ assigning ? '多目标优化计算中...' : '执行多目标优化调度' }}
          </button>

          <div v-if="dispatchPlan" class="plan-result">
            <!-- 调度概览 -->
            <div class="plan-stats">
              <div class="ps-item"><b>{{ dispatchPlan.total_orders }}</b><span>总订单</span></div>
              <div class="ps-item"><b class="text-teal">{{ dispatchPlan.assigned }}</b><span>已分配</span></div>
              <div class="ps-item"><b class="text-amber">{{ dispatchPlan.unassigned }}</b><span>未分配</span></div>
              <div class="ps-item"><b>{{ dispatchPlan.vehicles_used }}</b><span>用车数</span></div>
            </div>

            <!-- 约束检查 -->
            <div class="constraint-bar">
              <div class="cb-item" :class="{ok: dispatchPlan.constraint_check.high_sensitivity_isolated}">
                <span class="cb-icon">{{ dispatchPlan.constraint_check.high_sensitivity_isolated ? '✓' : '—' }}</span>
                高敏隔离
              </div>
              <div class="cb-item ok"><span class="cb-icon">✓</span>容积拦截</div>
              <div class="cb-item ok"><span class="cb-icon">✓</span>时效过滤</div>
              <div class="cb-item ok"><span class="cb-icon">✓</span>温区合规</div>
            </div>

            <!-- 成本分析 -->
            <div class="cost-analysis">
              <div class="ca-row">
                <span>专车配送成本</span>
                <span class="ca-val">¥{{ dispatchPlan.cost_analysis.traditional_cost_yuan }}</span>
              </div>
              <div class="ca-row">
                <span>优化后成本</span>
                <span class="ca-val text-teal">¥{{ dispatchPlan.cost_analysis.optimized_cost_yuan }}</span>
              </div>
              <div class="ca-row ca-saved">
                <span>成本节省</span>
                <span class="ca-val text-teal">{{ dispatchPlan.cost_analysis.cost_saved_percent }}%</span>
              </div>
            </div>

            <!-- 调度方案列表 -->
            <div class="assignments-title">调度方案明细 ({{ dispatchPlan.assignments.length }})</div>
            <div v-for="a in dispatchPlan.assignments" :key="a.assignment_id" class="assignment-card"
                 :class="{ 'has-hs': a.has_high_sensitivity, 'dispatched': a.status === 'dispatched' }">
              <div class="as-head">
                <div>
                  <span class="as-vehicle">{{ a.plate_number }}</span>
                  <span class="as-driver">{{ a.driver }}</span>
                </div>
                <span class="as-util" :class="utilClass(a.capacity_utilization)">载率 {{ a.capacity_utilization }}%</span>
              </div>
              <div class="as-zones">
                <span v-for="(cnt, zoneName) in a.zone_distribution" :key="zoneName" class="as-zone-tag"
                      :style="{background: zoneColorByName(zoneName)+'20', color: zoneColorByName(zoneName)}">
                  {{ zoneName }}: {{ cnt }}单
                </span>
                <span v-if="a.has_high_sensitivity" class="as-hs-tag">含高敏</span>
              </div>

              <!-- 舱位详情 -->
              <div class="compartment-grid">
                <div v-for="(comp, zoneName) in a.compartment_details" :key="zoneName" class="comp-item">
                  <div class="comp-head">
                    <span class="comp-dot" :style="{background: zoneColorByName(zoneName)}"></span>
                    <span class="comp-name">{{ zoneName }}</span>
                    <span class="comp-temp">{{ comp.temp_range }}</span>
                  </div>
                  <div class="comp-bar">
                    <div class="comp-bar-fill" :style="{width: comp.weight_utilization + '%', background: zoneColorByName(zoneName)}"></div>
                  </div>
                  <div class="comp-meta">
                    {{ comp.used_weight_kg }}/{{ comp.capacity_kg }}kg · {{ comp.weight_utilization }}%
                  </div>
                </div>
              </div>

              <!-- 订单清单 -->
              <div class="as-orders">
                <span v-for="o in a.orders" :key="o.order_id" class="as-oid"
                      :style="{borderColor: zoneColor(o.temp_zone)}">
                  {{ o.cargo_type }} ({{ o.weight_kg }}kg)
                </span>
              </div>

              <!-- 路线与成本 -->
              <div class="as-footer">
                <span class="as-route">{{ a.origins.join(',')}} → {{ a.destinations.join(',') }}</span>
                <span>{{ a.estimated_distance_km }}km</span>
                <span>{{ a.fuel_type }} {{ a.fuel_consumption }}L</span>
                <span class="as-cost">¥{{ a.estimated_cost_yuan }}</span>
              </div>

              <!-- 操作按钮 -->
              <div class="as-actions">
                <button v-if="a.status === 'scheduled'" class="btn btn-sm btn-primary" @click="confirmDispatch(a.assignment_id)">
                  确认派单发车
                </button>
                <button v-if="a.status === 'dispatched'" class="btn btn-sm btn-info" @click="openMonitor(a.assignment_id)">
                  在途监控
                </button>
              </div>
            </div>

            <!-- 未分配订单 -->
            <div v-if="dispatchPlan.unassigned_orders && dispatchPlan.unassigned_orders.length" class="unassigned-section">
              <div class="card-header">未分配订单 ({{ dispatchPlan.unassigned_orders.length }})</div>
              <div v-for="u in dispatchPlan.unassigned_orders" :key="u.order_id" class="unassigned-item">
                <span class="o-id">{{ u.order_id }}</span>
                <span>{{ u.cargo_type }}</span>
                <span class="text-amber">{{ u.reason }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 在途监控弹窗 -->
    <div v-if="monitorVisible" class="monitor-modal" @click.self="monitorVisible = false">
      <div class="monitor-content">
        <div class="monitor-head">
          <h3>在途监控 - {{ monitorData.plate_number }}</h3>
          <button class="btn-close" @click="monitorVisible = false">×</button>
        </div>
        <div class="monitor-body" v-if="monitorData">
          <div class="mon-progress">
            <div class="mon-progress-bar">
              <div class="mon-progress-fill" :style="{width: monitorData.current_progress + '%'}"></div>
            </div>
            <span>{{ monitorData.current_progress }}%</span>
          </div>
          <div class="mon-info">
            <div class="mon-row"><span>车辆</span><span>{{ monitorData.vehicle_id }}</span></div>
            <div class="mon-row"><span>当前位置</span><span>{{ monitorData.current_city }}</span></div>
            <div class="mon-row"><span>状态</span><span :class="monitorData.all_compliant ? 'text-teal' : 'text-red'">{{ monitorData.all_compliant ? '温控正常' : '温度异常' }}</span></div>
          </div>
          <div class="mon-zones">
            <div class="card-header">各温区实时温度</div>
            <div v-for="(temp, zoneKey) in monitorData.zone_temperatures" :key="zoneKey" class="mon-zone">
              <span class="mz-name">{{ zoneLabel(zoneKey) }}</span>
              <span class="mz-temp" :class="tempCompliantClass(zoneKey, temp)">{{ temp }}℃</span>
              <span class="mz-status">{{ tempCompliantClass(zoneKey, temp) === 'text-teal' ? '达标' : '异常' }}</span>
            </div>
          </div>
          <div class="mon-modules">
            <div class="card-header">模块联动</div>
            <div class="mm-item"><span class="mm-icon">🌡️</span> 传感器：{{ monitorData.sensor_bound ? '已绑定各温区温湿度传感器' : '未绑定' }}</div>
            <div class="mm-item"><span class="mm-icon">🗺️</span> 路径规划：{{ monitorData.route_planned ? '已规划多温区差异化路径' : '未规划' }}</div>
            <div class="mm-item"><span class="mm-icon">🚧</span> 电子围栏：{{ monitorData.geofence_bound ? '已绑定仓库/站点围栏' : '未绑定' }}</div>
          </div>
          <div class="mon-events">
            <div class="card-header">运输事件</div>
            <div v-for="(ev, idx) in monitorData.events" :key="idx" class="mon-event">
              <span class="ev-time">{{ ev.time.substring(11, 19) }}</span>
              <span>{{ ev.event }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { dispatchAPI } from '@/api'
import { ElMessage } from 'element-plus'

const orders = ref<any[]>([])
const vehicles = ref<any[]>([])
const dispatchPlan = ref<any>(null)
const dispatchStats = ref<any>(null)
const assigning = ref(false)
const orderZoneFilter = ref('')
const monitorVisible = ref(false)
const monitorData = ref<any>(null)

const zones = [
  { key: 'frozen', name: '冷冻区', range: '-22℃ ~ -15℃', target: -18, color: '#4361ee' },
  { key: 'refrigerated', name: '冷藏区', range: '0℃ ~ 4℃', target: 2, color: '#00a8ff' },
  { key: 'ambient', name: '恒温区', range: '15℃ ~ 25℃', target: 20, color: '#f59e0b' },
]

const idleCount = computed(() => vehicles.value.filter((v: any) => v.status === 'idle').length)
const filteredOrders = computed(() => {
  if (!orderZoneFilter.value) return orders.value
  return orders.value.filter((o: any) => o.temp_zone === orderZoneFilter.value)
})

const zoneCoverageList = computed(() => {
  if (!dispatchStats.value) return []
  return dispatchStats.value.zone_coverage.map((zc: any) => {
    const key = zc.zone === '冷冻区' ? 'frozen' : zc.zone === '冷藏区' ? 'refrigerated' : 'ambient'
    return { ...zc, color: zoneColor(key) }
  })
})

function zoneColor(key: string) {
  const m: any = { frozen: '#4361ee', refrigerated: '#00a8ff', ambient: '#f59e0b' }
  return m[key] || '#999'
}
function zoneColorByName(name: string) {
  const m: any = { '冷冻区': '#4361ee', '冷藏区': '#00a8ff', '恒温区': '#f59e0b' }
  return m[name] || '#999'
}
function zoneLabel(key: string) {
  const m: any = { frozen: '冷冻', refrigerated: '冷藏', ambient: '恒温' }
  return m[key] || key
}
function statusLabel(s: string) {
  const m: any = { idle: '空闲', loading: '装货中', in_use: '使用中' }
  return m[s] || s
}
function utilClass(util: number) {
  if (util >= 80) return 'text-teal'
  if (util >= 50) return ''
  return 'text-amber'
}
function tempCompliantClass(zoneKey: string, temp: number) {
  const m: any = { frozen: { min: -22, max: -15 }, refrigerated: { min: 0, max: 4 }, ambient: { min: 15, max: 25 } }
  const r = m[zoneKey]
  if (!r) return ''
  return r.min <= temp <= r.max ? 'text-teal' : 'text-red'
}

async function loadData() {
  try {
    const [oRes, vRes, sRes] = await Promise.all([
      dispatchAPI.getOrders(), dispatchAPI.getVehicles(), dispatchAPI.getStats()
    ])
    orders.value = oRes.orders || []
    vehicles.value = vRes.vehicles || []
    dispatchStats.value = sRes
  } catch {
    ElMessage.warning('加载调度数据失败')
  }
}

async function doAssign() {
  assigning.value = true
  try {
    const res: any = await dispatchAPI.autoAssign()
    dispatchPlan.value = res
    ElMessage.success(`多目标优化完成：${res.assigned}单已分配，使用${res.vehicles_used}辆车，节省成本${res.cost_analysis.cost_saved_percent}%`)
    // 刷新统计
    const sRes: any = await dispatchAPI.getStats()
    dispatchStats.value = sRes
  } catch {
    ElMessage.error('调度分配失败')
  } finally {
    assigning.value = false
  }
}

async function confirmDispatch(assignmentId: string) {
  try {
    await dispatchAPI.confirmDispatch(assignmentId)
    ElMessage.success('派单成功，车辆已发车')
    // 更新方案状态
    if (dispatchPlan.value) {
      const a = dispatchPlan.value.assignments.find((x: any) => x.assignment_id === assignmentId)
      if (a) a.status = 'dispatched'
    }
  } catch {
    ElMessage.error('派单失败')
  }
}

async function openMonitor(assignmentId: string) {
  try {
    const res: any = await dispatchAPI.monitor(assignmentId)
    monitorData.value = res
    monitorVisible.value = true
  } catch {
    ElMessage.error('获取监控数据失败')
  }
}

onMounted(() => { loadData() })
</script>

<style scoped>
.dispatch-page { animation: fadeInUp 0.45s ease-out; }
.page-header { margin-bottom: 16px; }
.subtitle { font-size:13px; color:var(--text-muted); margin-left:12px; }
.zone-legend { display:flex; gap:20px; margin-bottom:14px; flex-wrap:wrap; }
.zone-item { display:flex; align-items:center; gap:6px; font-size:12px; }
.zone-dot { width:10px; height:10px; border-radius:50%; }
.zone-name { font-weight:600; }
.zone-range { color:var(--text-muted); }
.zone-target { color:var(--accent); font-size:11px; }
.high-sens .zone-name { color:var(--red); }

.algo-bar { display:flex; align-items:center; gap:8px; margin-bottom:16px; padding:10px 14px; background:rgba(0,168,255,0.05); border-radius:8px; border:1px solid rgba(0,168,255,0.15); }
.algo-step { display:flex; align-items:center; gap:6px; font-size:12px; color:var(--text-secondary); }
.step-num { display:inline-flex; align-items:center; justify-content:center; width:20px; height:20px; border-radius:50%; background:var(--accent); color:#fff; font-size:11px; font-weight:600; }
.algo-arrow { color:var(--text-muted); font-size:14px; }

.stats-row { display:grid; grid-template-columns:repeat(7,1fr); gap:10px; margin-bottom:16px; }
.stat-card { text-align:center; padding:12px 8px; border-radius:8px; background:var(--bg-card); border:1px solid var(--border); }
.stat-val { font-family:var(--font-display); font-size:22px; font-weight:700; }
.stat-label { font-size:11px; color:var(--text-muted); margin-top:2px; }

.dispatch-layout { display:grid; grid-template-columns:300px 1fr 380px; gap:16px; }
.card-header { font-size:14px; font-weight:600; color:var(--text-title); margin-bottom:12px; display:flex; align-items:center; justify-content:space-between; }
.card-header .sub { font-size:11px; font-weight:400; color:var(--text-muted); }
.header-filters { display:flex; gap:6px; }
.mini-select { padding:3px 8px; font-size:11px; border:1px solid var(--border); border-radius:4px; background:var(--bg-card); color:var(--text-primary); }

.vehicle-card { padding:10px; border-radius:8px; border:1px solid var(--border); margin-bottom:6px; transition:background .15s; }
.vehicle-card:hover { background:rgba(0,168,255,0.03); }
.vehicle-card.v-idle { border-left:3px solid var(--teal); }
.vehicle-card.v-loading { border-left:3px solid var(--amber); opacity:.7; }
.v-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:4px; }
.v-name { font-size:13px; font-weight:600; }
.v-model { font-size:11px; color:var(--text-muted); margin-left:6px; }
.v-zones { display:flex; gap:4px; margin:4px 0; flex-wrap:wrap; }
.v-zone-tag { font-size:10px; padding:1px 6px; border-radius:3px; font-weight:500; }
.v-meta { display:flex; justify-content:space-between; font-size:11px; color:var(--text-muted); margin-bottom:2px; }
.v-driver { display:flex; justify-content:space-between; font-size:11px; }
.v-city { color:var(--accent); }
.v-status { font-size:11px; padding:2px 8px; border-radius:4px; }
.status-idle { background:rgba(0,210,160,0.1); color:var(--teal); }
.status-loading { background:rgba(245,158,11,0.1); color:var(--amber); }
.status-in_use { background:rgba(0,168,255,0.1); color:var(--accent); }

.zone-cov-item { display:flex; align-items:center; gap:6px; padding:6px 0; border-bottom:1px solid var(--border); font-size:12px; }
.zc-dot { width:8px; height:8px; border-radius:50%; }
.zc-name { font-weight:600; min-width:50px; }
.zc-range { color:var(--text-muted); flex:1; }
.zc-count { color:var(--accent); font-weight:600; }

.orders-scroll { max-height:600px; overflow-y:auto; }
.order-item { padding:8px 10px; border-radius:6px; margin-bottom:4px; border:1px solid var(--border); transition:all .15s; }
.order-item:hover { background:rgba(0,168,255,0.03); }
.order-item.high-sens { border-left:3px solid var(--red); background:rgba(239,68,68,0.03); }
.o-top { display:flex; align-items:center; gap:8px; margin-bottom:2px; }
.o-id { font-family:var(--font-mono); font-size:11px; font-weight:600; }
.o-zone { font-size:11px; font-weight:600; }
.o-priority { font-size:10px; padding:1px 5px; border-radius:3px; background:var(--red-bg); color:var(--red); }
.o-high-sens { font-size:10px; padding:1px 5px; border-radius:3px; background:var(--red); color:#fff; }
.o-mid { display:flex; gap:10px; font-size:11px; color:var(--text-muted); }
.o-cargo { color:var(--text-primary); font-weight:500; }
.o-temp { color:var(--accent); }
.o-bottom { display:flex; justify-content:space-between; font-size:11px; color:var(--text-muted); margin-top:1px; }
.o-source { font-size:10px; padding:0 4px; border-radius:2px; }
.src-customer { background:rgba(0,210,160,0.1); color:var(--teal); }
.src-demo { background:var(--border); color:var(--text-muted); }

.btn { padding:8px 18px; border-radius:6px; font-size:13px; cursor:pointer; border:1px solid var(--border); background:var(--bg-card); color:var(--text-secondary); }
.btn-primary { background:linear-gradient(135deg,var(--accent),var(--aurora)); color:#fff; border:none; }
.btn-primary:disabled { opacity:.6; cursor:not-allowed; }
.btn-block { width:100%; padding:10px; font-size:14px; }
.btn-sm { padding:5px 12px; font-size:11px; }
.btn-info { background:rgba(0,168,255,0.1); color:var(--accent); border:1px solid var(--accent); }

.plan-result { margin-top:14px; }
.plan-stats { display:grid; grid-template-columns:repeat(4,1fr); gap:8px; margin-bottom:12px; }
.ps-item { text-align:center; padding:8px; border-radius:6px; background:rgba(0,0,0,0.02); }
.ps-item b { display:block; font-family:var(--font-display); font-size:20px; }
.ps-item span { font-size:10px; color:var(--text-muted); }

.constraint-bar { display:flex; gap:6px; margin-bottom:12px; flex-wrap:wrap; }
.cb-item { display:flex; align-items:center; gap:4px; font-size:11px; padding:3px 8px; border-radius:4px; background:rgba(0,0,0,0.03); color:var(--text-muted); }
.cb-item.ok { background:rgba(0,210,160,0.1); color:var(--teal); }
.cb-icon { font-weight:700; }

.cost-analysis { padding:10px; border-radius:6px; background:rgba(0,0,0,0.02); margin-bottom:12px; }
.ca-row { display:flex; justify-content:space-between; font-size:12px; padding:3px 0; }
.ca-val { font-weight:600; }
.ca-saved { border-top:1px solid var(--border); margin-top:4px; padding-top:6px; font-weight:600; }

.assignments-title { font-size:13px; font-weight:600; margin-bottom:8px; }
.assignment-card { padding:12px; border-radius:8px; border:1px solid var(--border); margin-bottom:10px; }
.assignment-card.has-hs { border-left:3px solid var(--red); }
.assignment-card.dispatched { border-color:var(--teal); background:rgba(0,210,160,0.02); }
.as-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; }
.as-vehicle { font-weight:600; font-size:13px; }
.as-driver { font-size:11px; color:var(--text-muted); margin-left:6px; }
.as-util { font-size:11px; font-weight:600; }
.as-zones { display:flex; gap:6px; margin-bottom:8px; flex-wrap:wrap; }
.as-zone-tag { font-size:10px; padding:2px 6px; border-radius:3px; font-weight:500; }
.as-hs-tag { font-size:10px; padding:2px 6px; border-radius:3px; background:var(--red); color:#fff; }

.compartment-grid { display:grid; grid-template-columns:1fr 1fr; gap:6px; margin-bottom:8px; }
.comp-item { padding:6px; border-radius:4px; background:rgba(0,0,0,0.02); }
.comp-head { display:flex; align-items:center; gap:4px; margin-bottom:3px; }
.comp-dot { width:6px; height:6px; border-radius:50%; }
.comp-name { font-size:11px; font-weight:600; }
.comp-temp { font-size:9px; color:var(--text-muted); margin-left:auto; }
.comp-bar { height:4px; background:rgba(0,0,0,0.1); border-radius:2px; overflow:hidden; margin-bottom:2px; }
.comp-bar-fill { height:100%; transition:width .3s; }
.comp-meta { font-size:10px; color:var(--text-muted); }

.as-orders { display:flex; flex-wrap:wrap; gap:3px; margin-bottom:6px; }
.as-oid { font-size:10px; padding:2px 6px; border-radius:3px; background:rgba(0,0,0,0.03); border-left:2px solid; }
.as-footer { display:flex; gap:8px; font-size:11px; color:var(--text-muted); padding-top:6px; border-top:1px solid var(--border); flex-wrap:wrap; }
.as-route { flex:1; min-width:120px; }
.as-cost { color:var(--amber); font-weight:600; }
.as-actions { margin-top:8px; display:flex; gap:6px; }

.unassigned-section { margin-top:14px; padding-top:10px; border-top:1px solid var(--border); }
.unassigned-item { display:flex; gap:8px; padding:4px 0; font-size:11px; }

.text-teal { color:var(--teal); }
.text-amber { color:var(--amber); }
.text-red { color:var(--red); }

.monitor-modal { position:fixed; top:0; left:0; right:0; bottom:0; background:rgba(0,0,0,0.5); display:flex; align-items:center; justify-content:center; z-index:2000; }
.monitor-content { background:var(--bg-card); border-radius:12px; padding:20px; width:560px; max-height:80vh; overflow-y:auto; }
.monitor-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:14px; }
.monitor-head h3 { font-size:16px; margin:0; }
.btn-close { background:none; border:none; font-size:24px; cursor:pointer; color:var(--text-muted); }
.monitor-body { font-size:12px; }
.mon-progress { display:flex; align-items:center; gap:10px; margin-bottom:14px; }
.mon-progress-bar { flex:1; height:8px; background:rgba(0,0,0,0.1); border-radius:4px; overflow:hidden; }
.mon-progress-fill { height:100%; background:linear-gradient(90deg,var(--accent),var(--aurora)); }
.mon-info { margin-bottom:14px; }
.mon-row { display:flex; justify-content:space-between; padding:4px 0; border-bottom:1px solid var(--border); }
.mon-zones { margin-bottom:14px; }
.mon-zone { display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid var(--border); }
.mz-name { font-weight:600; }
.mz-temp { font-weight:600; }
.mz-status { font-size:11px; }
.mon-modules { margin-bottom:14px; }
.mm-item { display:flex; align-items:center; gap:6px; padding:4px 0; font-size:12px; }
.mon-events { }
.mon-event { display:flex; gap:8px; padding:3px 0; font-size:11px; }
.ev-time { font-family:var(--font-mono); color:var(--text-muted); }

@media (max-width:1200px) {
  .dispatch-layout { grid-template-columns:1fr; }
  .stats-row { grid-template-columns:repeat(4,1fr); }
}
</style>
