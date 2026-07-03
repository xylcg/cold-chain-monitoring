<template>
  <div class="resource-page">
    <div class="page-header">
      <h2 class="page-title">冷链资源智能调度</h2>
      <span class="subtitle">冷库库位 · 冷藏车辆 · 蓄冷板/冰排 · 能耗监测</span>
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

    <div class="res-grid">
      <!-- 冷库 -->
      <div class="glass-card">
        <div class="card-header">冷库库位 ({{ warehouses.length }})</div>
        <div v-for="wh in warehouses" :key="wh.warehouse_id" class="wh-card" @click="selectWarehouse(wh.warehouse_id)">
          <div class="wh-name">{{ wh.warehouse_name }}</div>
          <div class="wh-loc">{{ wh.location }}</div>
          <div class="wh-slots">
            <div class="wh-slot">
              <span class="wh-dot" style="background:#4361ee"></span>
              <span>冷冻</span>
              <b>{{ wh.slots.frozen.rate }}%</b>
              <div class="wh-bar"><div :style="{width:wh.slots.frozen.rate+'%',background:'#4361ee'}"></div></div>
            </div>
            <div class="wh-slot">
              <span class="wh-dot" style="background:#00a8ff"></span>
              <span>冷藏</span>
              <b>{{ wh.slots.refrigerated.rate }}%</b>
              <div class="wh-bar"><div :style="{width:wh.slots.refrigerated.rate+'%',background:'#00a8ff'}"></div></div>
            </div>
            <div class="wh-slot">
              <span class="wh-dot" style="background:#f59e0b"></span>
              <span>恒温</span>
              <b>{{ wh.slots.ambient.rate }}%</b>
              <div class="wh-bar"><div :style="{width:wh.slots.ambient.rate+'%',background:'#f59e0b'}"></div></div>
            </div>
          </div>
          <div class="wh-total">总利用率: <b>{{ wh.overall_utilization }}%</b></div>
        </div>
      </div>

      <!-- 车辆 -->
      <div class="glass-card">
        <div class="card-header">冷藏车队 ({{ fleetVehicles.length }})</div>
        <div v-for="v in fleetVehicles" :key="v.id" class="fh-card" :class="'s-'+v.status">
          <div class="fh-top">
            <span class="fh-plate">{{ v.plate }}</span>
            <span class="fh-status" :class="'fhs-'+v.status">{{ statusLabel(v.status) }}</span>
          </div>
          <div class="fh-mid">
            <span>{{ v.type }}</span>
            <span>{{ v.capacity_m3 }}m³</span>
            <span>{{ v.capacity_kg }}kg</span>
          </div>
          <div class="fh-bottom">
            <span>{{ v.fuel_type }}</span>
            <span>{{ v.temp_range }}</span>
            <span>{{ v.location }}</span>
          </div>
        </div>
      </div>

      <!-- 蓄冷板 -->
      <div class="glass-card">
        <div class="card-header">蓄冷板/冰排库存</div>
        <div v-for="cp in coldPlates" :key="cp.id" class="cp-card">
          <div class="cp-top">
            <span class="cp-name">{{ cp.name }}</span>
            <span class="cp-type">{{ cp.type }}</span>
          </div>
          <div class="cp-mid">
            <span>相变温度: {{ cp.phase_change_temp_c }}°C</span>
            <span>持续: {{ cp.duration_h }}h</span>
          </div>
          <div class="cp-bottom">
            <span>库存: <b>{{ cp.stock }}</b></span>
            <span>使用中: <b>{{ cp.in_use }}</b></span>
            <span>可用: <b :style="{color:(cp.stock-cp.in_use)>100?'var(--teal)':'var(--amber)'}">{{ cp.stock - cp.in_use }}</b></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 能耗趋势 -->
    <div class="glass-card" style="margin-top:20px" v-if="utilData?.energy?.trend_24h">
      <div class="card-header">24小时能耗趋势</div>
      <div class="energy-chart">
        <div v-for="e in utilData.energy.trend_24h" :key="e.hour" class="ec-bar-wrap">
          <div class="ec-bar" :style="{height:(e.power_kwh/400*100)+'px',background:e.power_kwh>300?'var(--amber)':'var(--accent)'}"></div>
          <span class="ec-label">{{ e.hour }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { resourceAPI } from '@/api'
import { ElMessage } from 'element-plus'

const warehouses = ref<any[]>([])
const fleetVehicles = ref<any[]>([])
const coldPlates = ref<any[]>([])
const utilData = ref<any>(null)

function statusLabel(s: string) {
  const m: any = { available: '空闲', in_use: '使用中', charging: '充电中', maintenance: '维护中' }
  return m[s] || s
}

async function selectWarehouse(id: string) {
  // 可扩展：点击查看冷库详情
}

async function loadData() {
  try {
    const [whRes, vRes, cpRes, uRes] = await Promise.all([
      resourceAPI.getWarehouses(), resourceAPI.getVehicles(), resourceAPI.getColdPlates(), resourceAPI.getUtilization()
    ])
    warehouses.value = whRes.warehouses || []
    fleetVehicles.value = vRes.vehicles || []
    coldPlates.value = cpRes.items || []
    utilData.value = uRes
  } catch {
    ElMessage.warning('加载资源数据失败，请检查网络或刷新页面重试')
  }
}

onMounted(() => { loadData() })
</script>

<style scoped>
.resource-page { animation: fadeInUp 0.45s ease-out; }
.page-header { margin-bottom: 16px; }
.subtitle { font-size:13px; color:var(--text-muted); margin-left:12px; }
.stats-row { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:20px; }
.stat-card { display:flex; align-items:center; gap:12px; padding:16px; background:var(--bg-card); border-radius:var(--radius); border:1px solid var(--border); }
.stat-icon { width:40px; height:40px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:20px; flex-shrink:0; }
.stat-value { font-family:var(--font-display); font-size:26px; font-weight:700; line-height:1; }
.stat-label { font-size:12px; color:var(--text-muted); margin-top:2px; }
.card-header { font-size:14px; font-weight:600; color:var(--text-title); margin-bottom:14px; }
.res-grid { display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px; }

/* 冷库卡片 */
.wh-card { padding:10px 12px; border-radius:8px; border:1px solid var(--border); margin-bottom:8px; cursor:pointer; transition:background .15s; }
.wh-card:hover { background:rgba(0,168,255,0.03); }
.wh-name { font-size:13px; font-weight:600; margin-bottom:2px; }
.wh-loc { font-size:11px; color:var(--text-muted); margin-bottom:8px; }
.wh-slots { display:flex; flex-direction:column; gap:4px; margin-bottom:6px; }
.wh-slot { display:flex; align-items:center; gap:6px; font-size:11px; }
.wh-dot { width:8px; height:8px; border-radius:50%; flex-shrink:0; }
.wh-slot b { width:32px; text-align:right; font-family:var(--font-mono); font-size:11px; }
.wh-bar { flex:1; height:4px; background:var(--border); border-radius:2px; overflow:hidden; }
.wh-bar div { height:100%; border-radius:2px; }
.wh-total { text-align:right; font-size:11px; color:var(--text-muted); }
.wh-total b { color:var(--accent); }

/* 车辆卡片 */
.fh-card { padding:10px 12px; border-radius:8px; border:1px solid var(--border); margin-bottom:6px; }
.fh-card.s-available { border-left:3px solid var(--teal); }
.fh-card.s-in_use { border-left:3px solid var(--accent); }
.fh-card.s-charging { border-left:3px solid var(--amber); }
.fh-card.s-maintenance { border-left:3px solid var(--red); opacity:.7; }
.fh-top { display:flex; justify-content:space-between; margin-bottom:4px; }
.fh-plate { font-weight:600; font-size:13px; }
.fh-status { font-size:10px; padding:1px 6px; border-radius:3px; }
.fhs-available { background:rgba(0,210,160,0.1); color:var(--teal); }
.fhs-in_use { background:rgba(0,168,255,0.1); color:var(--accent); }
.fhs-charging { background:rgba(245,158,11,0.1); color:var(--amber); }
.fhs-maintenance { background:var(--red-bg); color:var(--red); }
.fh-mid { display:flex; gap:10px; font-size:11px; color:var(--text-muted); margin-bottom:2px; }
.fh-bottom { display:flex; gap:8px; font-size:10px; color:var(--text-muted); }

/* 蓄冷板 */
.cp-card { padding:10px 12px; border-radius:8px; border:1px solid var(--border); margin-bottom:6px; }
.cp-top { display:flex; justify-content:space-between; margin-bottom:4px; }
.cp-name { font-weight:600; font-size:13px; }
.cp-type { font-size:10px; padding:1px 6px; border-radius:3px; background:rgba(124,58,237,0.08); color:var(--aurora); }
.cp-mid { display:flex; gap:12px; font-size:11px; color:var(--text-muted); margin-bottom:4px; }
.cp-bottom { display:flex; gap:12px; font-size:11px; }

/* 能耗图 */
.energy-chart { display:flex; align-items:flex-end; gap:4px; height:180px; padding:0 4px; }
.ec-bar-wrap { flex:1; display:flex; flex-direction:column; align-items:center; justify-content:flex-end; height:100%; }
.ec-bar { width:100%; border-radius:3px 3px 0 0; min-width:8px; transition:height .3s; }
.ec-label { font-size:8px; color:var(--text-muted); margin-top:4px; transform:rotate(-45deg); white-space:nowrap; }

@media (max-width:1200px) { .res-grid { grid-template-columns:1fr; } .stats-row { grid-template-columns:repeat(2,1fr); } }
</style>
