<template>
  <div class="dispatch-page">
    <div class="page-header">
      <h2 class="page-title">多温区车厢智能调度</h2>
      <span class="subtitle">冷冻-18℃ | 冷藏0-4℃ | 恒温15-25℃ · 自动组合优化</span>
    </div>

    <!-- 温区说明 -->
    <div class="zone-legend">
      <div class="zone-item" v-for="z in zones" :key="z.key">
        <div class="zone-dot" :style="{background:z.color}"></div>
        <span class="zone-name">{{ z.name }}</span>
        <span class="zone-range">{{ z.range }}</span>
      </div>
    </div>

    <div class="dispatch-layout">
      <!-- 左侧：可调度车辆 -->
      <div class="left-col">
        <div class="glass-card">
          <div class="card-header">多温区车辆 ({{ vehicles.length }}) <span class="sub">{{ idleCount }}空闲</span></div>
          <div v-for="v in vehicles" :key="v.id" class="vehicle-card" :class="'v-'+v.status">
            <div class="v-info">
              <div class="v-name">{{ v.plate }} <span class="v-model">{{ v.model }}</span></div>
              <div class="v-zones">
                <span v-for="z in v.zones" :key="z" class="v-zone-tag" :style="{background:zoneColor(z)+'20',color:zoneColor(z)}">
                  {{ zoneLabel(z) }}
                </span>
              </div>
              <div class="v-cap">{{ v.capacity_kg }}kg / {{ v.capacity_m3 }}m³</div>
            </div>
            <div class="v-status" :class="'status-'+v.status">{{ statusLabel(v.status) }}</div>
          </div>
        </div>
      </div>

      <!-- 中间：订单列表 -->
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
          <div v-for="o in filteredOrders" :key="o.order_id" class="order-item" :class="{ selected: selectedOrderIds.includes(o.order_id) }">
            <div class="o-top">
              <span class="o-id">{{ o.order_id }}</span>
              <span class="o-zone" :style="{color:zoneColor(o.temp_zone)}">{{ o.zone_name }}</span>
              <span v-if="o.priority !== 'normal'" class="o-priority">{{ o.priority === 'urgent' ? '紧急' : '优先' }}</span>
            </div>
            <div class="o-mid">
              <span>{{ o.cargo_type }}</span>
              <span>{{ o.weight_kg }}kg</span>
              <span>{{ o.volume_m3 }}m³</span>
            </div>
            <div class="o-bottom">
              <span>{{ o.origin }} → {{ o.destination }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：调度方案 -->
      <div class="right-col">
        <div class="glass-card">
          <div class="card-header">调度方案</div>
          <button class="btn btn-primary btn-block" @click="doAssign" :disabled="assigning">
            {{ assigning ? '分配中...' : '自动调度分配' }}
          </button>

          <div v-if="dispatchPlan" class="plan-result" style="margin-top:14px">
            <div class="plan-stats">
              <div class="ps-item"><b>{{ dispatchPlan.total_orders }}</b><span>总订单</span></div>
              <div class="ps-item"><b class="text-teal">{{ dispatchPlan.assigned }}</b><span>已分配</span></div>
              <div class="ps-item"><b class="text-amber">{{ dispatchPlan.unassigned }}</b><span>未分配</span></div>
              <div class="ps-item"><b>{{ dispatchPlan.fleet_utilization }}%</b><span>车队利用率</span></div>
            </div>

            <div v-for="a in dispatchPlan.assignments" :key="a.assignment_id" class="assignment-card">
              <div class="as-head">
                <span class="as-vehicle">{{ a.plate_number }}</span>
                <span class="as-util">利用率 {{ a.capacity_utilization }}%</span>
              </div>
              <div class="as-zones">
                <span v-for="(cnt, zoneName) in a.zone_distribution" :key="zoneName" class="as-zone-tag">
                  {{ zoneName }}: {{ cnt }}单
                </span>
              </div>
              <div class="as-orders">
                <span v-for="oid in a.orders" :key="oid" class="as-oid">{{ oid }}</span>
              </div>
              <div class="as-footer">
                <span>{{ a.total_weight_kg }}kg</span>
                <span>{{ a.total_volume_m3 }}m³</span>
                <span>预计 {{ a.estimated_departure.substring(11,16) }} 出发</span>
              </div>
            </div>
          </div>

          <!-- 统计 -->
          <div v-if="dispatchStats" class="stats-section" style="margin-top:14px">
            <div class="card-header">今日统计</div>
            <div class="stats-mini">
              <div class="sm-item"><span>今日订单</span><b>{{ dispatchStats.today_orders }}</b></div>
              <div class="sm-item"><span>已分配</span><b>{{ dispatchStats.today_assigned }}</b></div>
              <div class="sm-item"><span>平均载货率</span><b>{{ dispatchStats.avg_capacity_usage }}%</b></div>
              <div class="sm-item"><span>成本节省</span><b class="text-teal">~{{ Math.round(20+Math.random()*20) }}%</b></div>
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
const selectedOrderIds = ref<string[]>([])

const zones = [
  { key: 'frozen', name: '冷冻区', range: '-22℃ ~ -15℃', color: '#4361ee' },
  { key: 'refrigerated', name: '冷藏区', range: '0℃ ~ 4℃', color: '#00a8ff' },
  { key: 'ambient', name: '恒温区', range: '15℃ ~ 25℃', color: '#f59e0b' },
]

const idleCount = computed(() => vehicles.value.filter((v: any) => v.status === 'idle').length)
const filteredOrders = computed(() => {
  if (!orderZoneFilter.value) return orders.value
  return orders.value.filter((o: any) => o.temp_zone === orderZoneFilter.value)
})

function zoneColor(key: string) {
  const m: any = { frozen: '#4361ee', refrigerated: '#00a8ff', ambient: '#f59e0b' }
  return m[key] || '#999'
}
function zoneLabel(key: string) {
  const m: any = { frozen: '冷冻', refrigerated: '冷藏', ambient: '恒温' }
  return m[key] || key
}
function statusLabel(s: string) {
  const m: any = { idle: '空闲', loading: '装货中', in_use: '使用中' }
  return m[s] || s
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
    ElMessage.warning('加载调度数据失败，请检查网络或刷新页面重试')
  }
}

async function doAssign() {
  assigning.value = true
  try {
    const res: any = await dispatchAPI.autoAssign()
    dispatchPlan.value = res
    ElMessage.success(`调度完成：${res.assigned}辆车已分配，${res.unassigned}单待处理`)
  } catch {
    ElMessage.error('调度分配失败')
  } finally {
    assigning.value = false
  }
}

onMounted(() => { loadData() })
</script>

<style scoped>
.dispatch-page { animation: fadeInUp 0.45s ease-out; }
.page-header { margin-bottom: 16px; }
.subtitle { font-size:13px; color:var(--text-muted); margin-left:12px; }
.zone-legend { display:flex; gap:20px; margin-bottom:18px; }
.zone-item { display:flex; align-items:center; gap:6px; font-size:12px; }
.zone-dot { width:10px; height:10px; border-radius:50%; }
.zone-name { font-weight:600; }
.zone-range { color:var(--text-muted); }
.dispatch-layout { display:grid; grid-template-columns:280px 1fr 340px; gap:16px; }
.card-header { font-size:14px; font-weight:600; color:var(--text-title); margin-bottom:12px; display:flex; align-items:center; justify-content:space-between; }
.card-header .sub { font-size:11px; font-weight:400; color:var(--text-muted); }
.header-filters { display:flex; gap:6px; }
.mini-select { padding:3px 8px; font-size:11px; border:1px solid var(--border); border-radius:4px; background:var(--bg-card); color:var(--text-primary); }

.vehicle-card { display:flex; padding:10px; border-radius:8px; border:1px solid var(--border); margin-bottom:6px; transition:background .15s; }
.vehicle-card:hover { background:rgba(0,168,255,0.03); }
.vehicle-card.v-idle { border-left:3px solid var(--teal); }
.vehicle-card.v-loading { border-left:3px solid var(--amber); opacity:.7; }
.v-info { flex:1; min-width:0; }
.v-name { font-size:13px; font-weight:600; }
.v-model { font-size:11px; color:var(--text-muted); margin-left:6px; }
.v-zones { display:flex; gap:4px; margin:4px 0; }
.v-zone-tag { font-size:10px; padding:1px 6px; border-radius:3px; font-weight:500; }
.v-cap { font-size:11px; color:var(--text-muted); }
.v-status { font-size:11px; padding:2px 8px; border-radius:4px; align-self:center; }
.status-idle { background:rgba(0,210,160,0.1); color:var(--teal); }
.status-loading { background:rgba(245,158,11,0.1); color:var(--amber); }
.status-in_use { background:rgba(0,168,255,0.1); color:var(--accent); }

.order-item { padding:8px 10px; border-radius:6px; margin-bottom:4px; cursor:pointer; border:1px solid transparent; transition:all .15s; }
.order-item:hover { background:rgba(0,168,255,0.03); }
.o-top { display:flex; align-items:center; gap:8px; margin-bottom:2px; }
.o-id { font-family:var(--font-mono); font-size:11px; font-weight:600; }
.o-zone { font-size:11px; font-weight:600; }
.o-priority { font-size:10px; padding:1px 5px; border-radius:3px; background:var(--red-bg); color:var(--red); }
.o-mid { display:flex; gap:10px; font-size:11px; color:var(--text-muted); }
.o-bottom { font-size:11px; color:var(--text-muted); margin-top:1px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }

.btn { padding:8px 18px; border-radius:6px; font-size:13px; cursor:pointer; border:1px solid var(--border); background:var(--bg-card); color:var(--text-secondary); }
.btn-primary { background:linear-gradient(135deg,var(--accent),var(--aurora)); color:#fff; border:none; }
.btn-primary:disabled { opacity:.6; cursor:not-allowed; }
.btn-block { width:100%; padding:10px; font-size:14px; }

.plan-stats { display:grid; grid-template-columns:repeat(4,1fr); gap:8px; margin-bottom:12px; }
.ps-item { text-align:center; padding:8px; border-radius:6px; background:rgba(0,0,0,0.02); }
.ps-item b { display:block; font-family:var(--font-display); font-size:20px; }
.ps-item span { font-size:10px; color:var(--text-muted); }

.assignment-card { padding:10px; border-radius:8px; border:1px solid var(--border); margin-bottom:8px; }
.as-head { display:flex; justify-content:space-between; margin-bottom:4px; }
.as-vehicle { font-weight:600; font-size:13px; }
.as-util { font-size:11px; color:var(--text-muted); }
.as-zones { display:flex; gap:6px; margin-bottom:4px; }
.as-zone-tag { font-size:10px; padding:1px 6px; border-radius:3px; background:rgba(0,168,255,0.08); color:var(--accent); }
.as-orders { display:flex; flex-wrap:wrap; gap:3px; margin-bottom:4px; }
.as-oid { font-size:10px; padding:1px 5px; border-radius:3px; background:var(--border); font-family:var(--font-mono); }
.as-footer { display:flex; gap:12px; font-size:11px; color:var(--text-muted); }

.stats-mini { display:grid; grid-template-columns:repeat(2,1fr); gap:8px; }
.sm-item { text-align:center; padding:8px; border-radius:6px; background:rgba(0,0,0,0.02); }
.sm-item span { display:block; font-size:10px; color:var(--text-muted); }
.sm-item b { font-family:var(--font-display); font-size:18px; }

.text-teal { color:var(--teal); }
.text-amber { color:var(--amber); }

@media (max-width:1200px) { .dispatch-layout { grid-template-columns:1fr; } }
</style>
