<template>
  <div class="route-page">
    <div class="page-header">
      <h2 class="page-title">冷链路径智能规划</h2>
      <span class="subtitle">多目标优化 · 时效+能耗+成本 · 温敏货物优先级</span>
    </div>

    <div class="plan-layout">
      <!-- 左侧规划面板 -->
      <div class="plan-panel">
        <div class="glass-card">
          <div class="card-header">路线规划</div>
          <div class="form-group">
            <label>出发城市</label>
            <select v-model="origin" class="select-input">
              <option v-for="c in cities" :key="c.name" :value="c.name">{{ c.name }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>目的城市</label>
            <select v-model="destination" class="select-input">
              <option v-for="c in cities" :key="c.name" :value="c.name">{{ c.name }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>货物类型</label>
            <select v-model="cargoType" class="select-input">
              <option v-for="ct in cargoTypes" :key="ct.name" :value="ct.name">
                {{ ct.name }} ({{ ct.range }})
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>优化优先级</label>
            <div class="radio-group">
              <label class="radio"><input type="radio" v-model="priority" value="high" /> 时效优先</label>
              <label class="radio"><input type="radio" v-model="priority" value="normal" /> 综合均衡</label>
              <label class="radio"><input type="radio" v-model="priority" value="economic" /> 经济优先</label>
            </div>
          </div>
          <button class="btn btn-primary btn-block" @click="doPlan" :disabled="planning">
            {{ planning ? '规划中...' : '开始规划' }}
          </button>
        </div>

        <!-- 活跃路线 -->
        <div class="glass-card" style="margin-top:14px">
          <div class="card-header">活跃路线</div>
          <div v-if="activeRoutes.length === 0" class="empty-block">
            <span>暂无活跃路线</span>
          </div>
          <div v-for="r in activeRoutes" :key="r.route_id" class="active-route-item" @click="selectedActive = r">
            <div class="ar-top">
              <span class="ar-name">{{ r.origin }} → {{ r.destination }}</span>
              <span class="tag" :class="r.status === '运输中' ? 'tag-accent' : 'tag-teal'">{{ r.status }}</span>
            </div>
            <div class="ar-meta">
              <span>{{ r.plate_number }}</span>
              <span>{{ r.cargo_type }}</span>
              <span>{{ r.distance_km }}km</span>
            </div>
            <div class="ar-progress"><div class="ar-fill" :style="{width:r.progress_percent+'%'}"></div></div>
          </div>
        </div>
      </div>

      <!-- 右侧地图+结果 -->
      <div class="result-area">
        <!-- 地图 -->
        <div class="map-mini" id="route-map"></div>

        <!-- 方案对比 -->
        <div v-if="planResult" class="routes-compare glass-card" style="margin-top:14px">
          <div class="card-header">
            规划方案对比 — {{ planResult.origin?.name || origin }} → {{ planResult.destination?.name || destination }}
            <span class="pull-right">{{ planResult.direct_distance_km }}km (直线)</span>
          </div>
          <div class="routes-grid">
            <div v-for="(r, i) in planResult.routes" :key="r.route_id" class="route-card" :class="{ recommended: r.recommended }">
              <div class="rc-header">
                <span class="rc-name">{{ r.route_name }}</span>
                <span v-if="r.recommended" class="rc-badge">推荐</span>
              </div>
              <div class="rc-meta">
                <div class="rc-row"><span>距离</span><strong>{{ r.distance_km }} km</strong></div>
                <div class="rc-row"><span>预计耗时</span><strong>{{ r.estimated_duration_h }} h</strong></div>
                <div class="rc-row"><span>总费用</span><strong>¥{{ r.total_cost_yuan }}</strong></div>
                <div class="rc-row"><span>拥堵等级</span><strong>{{ r.congestion_level }}</strong></div>
                <div class="rc-row"><span>碳排放</span><strong>{{ r.carbon_emission_kg }} kg</strong></div>
              </div>
              <div class="rc-scores">
                <div class="score-item"><span>时效</span><div class="score-bar"><div :style="{width:r.scores['时效评分']+'%'}"></div></div><b>{{ r.scores['时效评分'] }}</b></div>
                <div class="score-item"><span>成本</span><div class="score-bar"><div :style="{width:r.scores['成本评分']+'%'}"></div></div><b>{{ r.scores['成本评分'] }}</b></div>
                <div class="score-item"><span>品质</span><div class="score-bar"><div :style="{width:r.scores['品质保障评分']+'%'}"></div></div><b>{{ r.scores['品质保障评分'] }}</b></div>
              </div>
              <div class="rc-composite">综合评分: <strong>{{ r.composite_score }}</strong></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import { routeAPI } from '@/api'
import { ElMessage } from 'element-plus'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const origin = ref('北京')
const destination = ref('上海')
const cargoType = ref('冷藏生鲜')
const priority = ref('normal')
const planning = ref(false)
const planResult = ref<any>(null)
const activeRoutes = ref<any[]>([])
const selectedActive = ref<any>(null)
const cities = ref<any[]>([])
const cargoTypes = ref<any[]>([])

let map: any = null

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

function drawRouteOnMap(routes: any[]) {
  if (!map) return
  // 清除既有图层
  map.eachLayer((layer: any) => { if (layer instanceof L.Polyline || layer instanceof L.Marker) map.removeLayer(layer) })

  const colors = ['#00a8ff', '#7c3aed', '#f59e0b']
  routes.forEach((r: any, i: number) => {
    const coords = [
      [r.origin.lat, r.origin.lng],
      ...(r.waypoints || []).map((w: any) => [w.lat, w.lng]),
      [r.destination.lat, r.destination.lng],
    ]
    L.polyline(coords as any, { color: colors[i % colors.length], weight: r.recommended ? 5 : 3, opacity: r.recommended ? 1 : 0.6, dashArray: r.recommended ? '' : '8 4' }).addTo(map)
    L.circleMarker(coords[0] as any, { radius: 6, color: '#fff', fillColor: '#00a8ff', fillOpacity: 1, weight: 2 }).addTo(map)
    L.circleMarker(coords[coords.length - 1] as any, { radius: 6, color: '#fff', fillColor: '#ef4444', fillOpacity: 1, weight: 2 }).addTo(map)
  })

  // 自适应视图
  const allCoords = routes.flatMap((r: any) => [[r.origin.lat, r.origin.lng], [r.destination.lat, r.destination.lng]])
  if (allCoords.length > 0) {
    map.fitBounds(L.latLngBounds(allCoords as any), { padding: [40, 40] })
  }
}

async function doPlan() {
  planning.value = true
  try {
    const res: any = await routeAPI.quickPlan(origin.value, destination.value, cargoType.value, priority.value)
    planResult.value = res
    await nextTick()
    drawRouteOnMap(res.routes)
  } catch {
    ElMessage.error('路线规划失败')
  } finally {
    planning.value = false
  }
}

async function loadActiveRoutes() {
  try {
    const res: any = await routeAPI.getActive()
    activeRoutes.value = res.routes || []
    if (activeRoutes.value.length > 0) {
      await nextTick()
      drawRouteOnMap(activeRoutes.value)
    }
  } catch {
    ElMessage.warning('加载活跃路线失败，请检查网络')
  }
}

async function loadRefData() {
  try {
    const [citiesRes, cargoRes] = await Promise.all([routeAPI.getCities(), routeAPI.getCargoTypes()])
    cities.value = citiesRes.cities || []
    cargoTypes.value = cargoRes.types || []
  } catch {
    // 使用默认数据作为回退
    cities.value = ['北京', '上海', '广州', '成都', '武汉', '西安', '杭州', '深圳']
    cargoTypes.value = ['冷冻肉类', '冷藏鲜奶', '水果', '蔬菜', '疫苗', '鲜花', '恒温药品']
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
.page-header { margin-bottom: 20px; }
.subtitle { font-size:13px; color:var(--text-muted); margin-left:12px; }
.plan-layout { display:grid; grid-template-columns:320px 1fr; gap:20px; }
.plan-panel { display:flex; flex-direction:column; }
.result-area { min-height:500px; }
.map-mini { width:100%; height:380px; border-radius:var(--radius); overflow:hidden; border:1px solid var(--border); z-index:1; }
.card-header { font-size:14px; font-weight:600; color:var(--text-title); margin-bottom:14px; }
.pull-right { font-size:12px; color:var(--text-muted); float:right; font-weight:400; }

.form-group { margin-bottom:12px; }
.form-group label { display:block; font-size:12px; color:var(--text-muted); margin-bottom:4px; font-weight:500; }
.select-input { width:100%; padding:8px 10px; border:1px solid var(--border); border-radius:6px; background:var(--bg-card); color:var(--text-primary); font-size:13px; appearance:auto; -webkit-appearance:menulist; height:36px; line-height:20px; cursor:pointer; }
.select-input option { background:var(--bg-card); color:var(--text-primary); }
.radio-group { display:flex; flex-direction:column; gap:6px; }
.radio { font-size:13px; cursor:pointer; display:flex; align-items:center; gap:8px; color:var(--text-secondary); }
.radio input[type="radio"] { width:16px; height:16px; accent-color:var(--accent); cursor:pointer; }

.btn { padding:8px 18px; border-radius:6px; font-size:13px; cursor:pointer; border:1px solid var(--border); background:var(--bg-card); color:var(--text-secondary); transition:all .2s; }
.btn-primary { background:linear-gradient(135deg,var(--accent),var(--aurora)); color:#fff; border:none; }
.btn-primary:disabled { opacity:.6; cursor:not-allowed; }
.btn-block { width:100%; padding:10px; font-size:14px; margin-top:8px; }

.empty-block { text-align:center; padding:20px; color:var(--text-muted); font-size:13px; }
.active-route-item { padding:10px; border-radius:8px; margin-bottom:6px; cursor:pointer; transition:background .15s; border:1px solid transparent; }
.active-route-item:hover { background:rgba(0,168,255,0.04); border-color:rgba(0,168,255,0.15); }
.ar-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:4px; }
.ar-name { font-size:13px; font-weight:600; }
.ar-meta { display:flex; gap:12px; font-size:11px; color:var(--text-muted); margin-bottom:6px; }
.ar-progress { height:3px; background:var(--border); border-radius:2px; overflow:hidden; }
.ar-fill { height:100%; background:var(--accent); border-radius:2px; transition:width 1s; }

.tag { display:inline-block; padding:1px 7px; border-radius:4px; font-size:10px; font-weight:600; }
.tag-accent { background:rgba(0,168,255,0.1); color:var(--accent); }
.tag-teal { background:rgba(0,210,160,0.1); color:var(--teal); }

.routes-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; }
.route-card { padding:14px; border-radius:10px; border:1px solid var(--border); background:var(--bg-elevated); }
.route-card.recommended { border-color:var(--accent); box-shadow:0 0 0 1px var(--accent); }
.rc-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }
.rc-name { font-size:14px; font-weight:600; }
.rc-badge { font-size:10px; padding:2px 8px; border-radius:4px; background:linear-gradient(135deg,var(--accent),var(--aurora)); color:#fff; font-weight:600; }
.rc-meta { margin-bottom:10px; }
.rc-row { display:flex; justify-content:space-between; font-size:12px; padding:3px 0; border-bottom:1px solid rgba(0,0,0,0.03); }
.rc-row span { color:var(--text-muted); }
.rc-scores { display:flex; flex-direction:column; gap:6px; margin-bottom:10px; }
.score-item { display:flex; align-items:center; gap:6px; font-size:11px; }
.score-item span { width:28px; color:var(--text-muted); }
.score-item b { width:26px; text-align:right; font-family:var(--font-mono); }
.score-bar { flex:1; height:5px; background:var(--border); border-radius:3px; overflow:hidden; }
.score-bar div { height:100%; background:linear-gradient(90deg,var(--teal),var(--accent)); border-radius:3px; }
.rc-composite { text-align:center; font-size:13px; color:var(--text-muted); }
.rc-composite strong { color:var(--accent); font-family:var(--font-display); font-size:18px; }

@media (max-width:1200px) { .plan-layout { grid-template-columns:1fr; } .routes-grid { grid-template-columns:1fr; } }
</style>
