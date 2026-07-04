<template>
  <div class="driver-tracking">
    <div class="tracking-header">
      <div class="header-left">
        <h2 class="page-title">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="10" r="3"/><path d="M12 21.7C17.3 17 20 13 20 10a8 8 0 1 0-16 0c0 3 2.7 7 8 11.7z"/></svg>
          我的车辆追踪
        </h2>
        <span class="last-update" v-if="lastUpdate">更新于 {{ lastUpdate }}</span>
      </div>
      <div class="header-info">
        <div class="info-card">
          <span class="ic-label">车牌号</span>
          <span class="ic-val">{{ vehicle.plate }}</span>
        </div>
        <div class="info-card">
          <span class="ic-label">车型</span>
          <span class="ic-val">{{ vehicle.model }}</span>
        </div>
        <div class="info-card">
          <span class="ic-label">当前位置</span>
          <span class="ic-val">{{ vehicle.location }}</span>
        </div>
        <div class="info-card" :class="vehicle.online ? 'online' : 'offline'">
          <span class="ic-label">状态</span>
          <span class="ic-val">{{ vehicle.online ? '在线' : '离线' }}</span>
        </div>
      </div>
    </div>

    <div class="tracking-main">
      <!-- 地图 -->
      <div class="map-container">
        <div id="driver-vehicle-map"></div>
        <div class="map-overlay">
          <div class="mo-item">
            <span class="mo-label">当前温度</span>
            <span class="mo-val" :class="tempClass(vehicle.temp)">{{ vehicle.temp }}°C</span>
          </div>
          <div class="mo-item">
            <span class="mo-label">车速</span>
            <span class="mo-val">{{ vehicle.speed }} km/h</span>
          </div>
          <div class="mo-item">
            <span class="mo-label">冷机状态</span>
            <span class="mo-val" :class="vehicle.coldChain ? 'good' : 'bad'">{{ vehicle.coldChain ? '正常运行' : '异常' }}</span>
          </div>
        </div>
      </div>

      <!-- 右侧面板 -->
      <div class="side-panel">
        <!-- 实时数据 -->
        <div class="panel-section">
          <h4 class="ps-title">实时数据</h4>
          <div class="data-grid">
            <div class="data-item">
              <span class="data-label">设备编号</span>
              <span class="data-val mono">{{ vehicle.deviceId }}</span>
            </div>
            <div class="data-item">
              <span class="data-label">温度</span>
              <span class="data-val" :class="tempClass(vehicle.temp)">{{ vehicle.temp }}°C</span>
            </div>
            <div class="data-item">
              <span class="data-label">湿度</span>
              <span class="data-val">{{ vehicle.humidity }}%</span>
            </div>
            <div class="data-item">
              <span class="data-label">车速</span>
              <span class="data-val">{{ vehicle.speed }} km/h</span>
            </div>
            <div class="data-item">
              <span class="data-label">车门</span>
              <span class="data-val" :class="vehicle.doorClosed ? 'good' : 'bad'">{{ vehicle.doorClosed ? '已关闭' : '已开启' }}</span>
            </div>
            <div class="data-item">
              <span class="data-label">电量</span>
              <span class="data-val">{{ vehicle.battery }}%</span>
            </div>
            <div class="data-item">
              <span class="data-label">信号</span>
              <span class="data-val">{{ '★'.repeat(vehicle.signal) }}{{ '☆'.repeat(5 - vehicle.signal) }}</span>
            </div>
            <div class="data-item">
              <span class="data-label">坐标</span>
              <span class="data-val mono coords">{{ vehicle.lat.toFixed(4) }}, {{ vehicle.lng.toFixed(4) }}</span>
            </div>
          </div>
        </div>

        <!-- 温度趋势 -->
        <div class="panel-section">
          <h4 class="ps-title">温度趋势 (近1小时)</h4>
          <div class="temp-chart" ref="tempChart"></div>
        </div>

        <!-- 轨迹回放 -->
        <div class="panel-section">
          <h4 class="ps-title">轨迹记录</h4>
          <div class="trajectory-list" v-if="trajectoryPts.length > 0">
            <div v-for="(pt, i) in trajectoryPts.slice(-8).reverse()" :key="i" class="traj-item">
              <span class="traj-time">{{ formatTime(pt.time) }}</span>
              <span class="traj-temp" :class="tempClass(pt.temp)">{{ pt.temp }}°C</span>
              <span class="traj-speed">{{ pt.speed }}km/h</span>
            </div>
          </div>
          <div v-else class="no-data">暂无轨迹数据</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import dayjs from 'dayjs'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import * as echarts from 'echarts'

// 司机车辆信息（只有自己的车）
const vehicle = reactive({
  plate: '冷A-8801',
  model: '解放J6F冷藏车',
  deviceId: 'DEV-VEH-8801',
  location: '北京市朝阳区望京',
  online: true,
  temp: -3.2,
  humidity: 62,
  speed: 58,
  battery: 85,
  doorClosed: true,
  coldChain: true,
  signal: 4,
  lat: 39.9942,
  lng: 116.4774,
})

const lastUpdate = ref('')
const trajectoryPts = ref<any[]>([])
const tempChart = ref<HTMLElement | null>(null)
let chartInstance: echarts.ECharts | null = null

// 地图
let map: L.Map | null = null
let vehicleMarker: L.Marker | null = null
let routeLine: L.Polyline | null = null

// 历史温度数据（模拟）
const tempHistory = ref<{ time: string; temp: number }[]>([])

function tempClass(temp: number) {
  if (temp > 4) return 'danger'
  if (temp > 0) return 'warn'
  if (temp < -22) return 'warn'
  return 'normal'
}

function formatTime(t: string) {
  return t ? dayjs(t).format('HH:mm:ss') : '-'
}

function initMap() {
  if (map) return

  map = L.map('driver-vehicle-map', {
    center: [vehicle.lat, vehicle.lng],
    zoom: 13,
    zoomControl: false,
    attributionControl: false,
  })

  L.tileLayer('https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}', {
    subdomains: ['1', '2', '3', '4'],
    maxZoom: 18,
    minZoom: 3,
  }).addTo(map)

  L.control.zoom({ position: 'bottomright' }).addTo(map)

  // 创建车辆标记
  const truckIcon = L.divIcon({
    className: 'truck-marker',
    html: `<div class="truck-icon-wrap">
      <svg width="32" height="32" viewBox="0 0 24 24" fill="#00a8ff" stroke="#fff" stroke-width="1.5">
        <rect x="1" y="3" width="15" height="13" rx="1"/>
        <polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/>
        <circle cx="5.5" cy="18.5" r="2.5" fill="#fff"/>
        <circle cx="18.5" cy="18.5" r="2.5" fill="#fff"/>
      </svg>
      <div class="truck-pulse"></div>
    </div>`,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
  })

  vehicleMarker = L.marker([vehicle.lat, vehicle.lng], { icon: truckIcon })
    .bindPopup(`
      <div style="font-family:monospace;font-size:12px;text-align:center;line-height:1.6">
        <b>${vehicle.plate}</b><br/>
        ${vehicle.deviceId}<br/>
        温度: ${vehicle.temp}°C | 速度: ${vehicle.speed}km/h
      </div>
    `)
    .addTo(map)

  // 初始路线
  updateRouteLine()
}

function updateRouteLine() {
  if (!map) return
  if (routeLine) map.removeLayer(routeLine)

  // 模拟从起点到当前位置的路线
  const startLat = vehicle.lat - 0.05
  const startLng = vehicle.lng - 0.06
  const pts: [number, number][] = [
    [startLat, startLng],
    [startLat + 0.02, startLng + 0.03],
    [startLat + 0.03, startLng + 0.04],
    [vehicle.lat, vehicle.lng],
  ]

  routeLine = L.polyline(pts, {
    color: '#00a8ff',
    weight: 3,
    opacity: 0.6,
    dashArray: '8 4',
  }).addTo(map)
}

function initTempChart() {
  if (!tempChart.value) return

  chartInstance = echarts.init(tempChart.value)
  const option: echarts.EChartsOption = {
    grid: { top: 8, right: 12, bottom: 20, left: 36 },
    xAxis: {
      type: 'category',
      data: tempHistory.value.map(t => t.time),
      axisLabel: { fontSize: 9, color: '#94a3b8' },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      min: -25,
      max: 10,
      axisLabel: { fontSize: 9, color: '#94a3b8' },
      splitLine: { lineStyle: { color: '#f1f5f9' } },
    },
    series: [{
      type: 'line',
      data: tempHistory.value.map(t => t.temp),
      smooth: true,
      symbol: 'none',
      lineStyle: { color: '#00a8ff', width: 2 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(0,168,255,0.15)' },
          { offset: 1, color: 'rgba(0,168,255,0)' },
        ]),
      },
      markLine: {
        silent: true,
        symbol: 'none',
        data: [
          { yAxis: -18, lineStyle: { color: '#f59e0b', type: 'dashed' }, label: { formatter: '下限-18°C', fontSize: 9, color: '#f59e0b' } },
          { yAxis: 4, lineStyle: { color: '#ef4444', type: 'dashed' }, label: { formatter: '上限4°C', fontSize: 9, color: '#ef4444' } },
        ],
      },
    }],
  }
  chartInstance.setOption(option)
}

function updateTempChart() {
  if (!chartInstance) return
  chartInstance.setOption({
    xAxis: { data: tempHistory.value.map(t => t.time) },
    series: [{ data: tempHistory.value.map(t => t.temp) }],
  })
}

// 定时更新
let timer: number | null = null

onMounted(() => {
  initMap()
  lastUpdate.value = dayjs().format('HH:mm:ss')

  // 初始温度历史数据
  for (let i = 30; i >= 0; i--) {
    tempHistory.value.push({
      time: dayjs().subtract(i, 'minute').format('HH:mm'),
      temp: +(vehicle.temp + (Math.random() - 0.5) * 3).toFixed(1),
    })
  }

  nextTick(() => initTempChart())

  // 生成初始轨迹
  for (let i = 5; i >= 0; i--) {
    trajectoryPts.value.push({
      time: dayjs().subtract(i * 5, 'minute').format('HH:mm:ss'),
      temp: +(vehicle.temp + (Math.random() - 0.5) * 2).toFixed(1),
      speed: Math.max(20, vehicle.speed + (Math.random() - 0.5) * 20 | 0),
    })
  }

  timer = window.setInterval(() => {
    // 更新车辆位置（模拟移动）
    vehicle.lat += (Math.random() - 0.5) * 0.005
    vehicle.lng += (Math.random() - 0.5) * 0.005
    vehicle.temp = +(vehicle.temp + (Math.random() - 0.5) * 0.4).toFixed(1)
    vehicle.speed = Math.max(0, Math.min(100, vehicle.speed + (Math.random() - 0.5) * 15 | 0))
    vehicle.battery = Math.max(5, vehicle.battery - (Math.random() * 0.15))
    vehicle.humidity = Math.max(30, Math.min(90, vehicle.humidity + (Math.random() - 0.5) * 3 | 0))
    vehicle.signal = Math.max(1, Math.min(5, Math.random() > 0.9 ? vehicle.signal - 1 : vehicle.signal + (Math.random() > 0.5 ? 1 : 0)))
    lastUpdate.value = dayjs().format('HH:mm:ss')

    // 更新地图
    if (vehicleMarker && map) {
      vehicleMarker.setLatLng([vehicle.lat, vehicle.lng])
      vehicleMarker.setPopupContent(`
        <div style="font-family:monospace;font-size:12px;text-align:center;line-height:1.6">
          <b>${vehicle.plate}</b><br/>
          ${vehicle.deviceId}<br/>
          温度: ${vehicle.temp}°C | 速度: ${vehicle.speed}km/h
        </div>
      `)
      map.panTo([vehicle.lat, vehicle.lng], { animate: true, duration: 0.5 })
      updateRouteLine()
    }

    // 更新温度历史
    tempHistory.value.push({
      time: dayjs().format('HH:mm'),
      temp: +(vehicle.temp + (Math.random() - 0.5) * 1.5).toFixed(1),
    })
    if (tempHistory.value.length > 30) {
      tempHistory.value.shift()
    }
    updateTempChart()

    // 更新轨迹
    trajectoryPts.value.push({
      time: dayjs().format('HH:mm:ss'),
      temp: vehicle.temp,
      speed: vehicle.speed,
    })
    if (trajectoryPts.value.length > 50) {
      trajectoryPts.value.shift()
    }

    // 随机事件
    if (Math.random() > 0.9) {
      vehicle.doorClosed = !vehicle.doorClosed
    }
    if (Math.random() > 0.95) {
      vehicle.coldChain = !vehicle.coldChain
    }
  }, 5000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  if (chartInstance) chartInstance.dispose()
  if (map) {
    map.remove()
    map = null
  }
})
</script>

<style scoped>
.driver-tracking {
  animation: fadeInUp 0.4s ease-out;
}

/* Header */
.tracking-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
  flex-wrap: wrap;
  gap: 12px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.page-title {
  font-family: var(--font-display);
  font-size: 18px;
  font-weight: 700;
  color: var(--text-title);
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
}
.page-title svg { color: var(--accent); }

.last-update {
  font-size: 11px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.header-info {
  display: flex;
  gap: 8px;
}
.info-card {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: 8px;
  padding: 6px 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}
.info-card.online { border-color: rgba(0,168,255,0.2); }
.info-card.offline { border-color: rgba(148,163,184,0.2); }
.ic-label { font-size: 10px; color: var(--text-muted); }
.ic-val {
  font-size: 13px; font-weight: 700; color: var(--text-title);
  font-family: var(--font-display);
}

/* Main */
.tracking-main {
  display: flex;
  gap: 16px;
  height: calc(100vh - 160px);
  min-height: 500px;
}

/* Map */
.map-container {
  flex: 1;
  position: relative;
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid var(--border-card);
  background: #e8ecf1;
}

#driver-vehicle-map {
  width: 100%;
  height: 100%;
}

.map-overlay {
  position: absolute;
  bottom: 16px;
  left: 16px;
  right: 16px;
  display: flex;
  gap: 8px;
  z-index: 500;
}
.mo-item {
  background: rgba(255,255,255,0.92);
  backdrop-filter: blur(8px);
  border-radius: 10px;
  padding: 8px 14px;
  border: 1px solid rgba(0,0,0,0.06);
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}
.mo-label { font-size: 10px; color: var(--text-muted); }
.mo-val {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 700;
  color: var(--text-title);
}
.mo-val.normal { color: var(--accent); }
.mo-val.warn { color: var(--amber); }
.mo-val.danger { color: var(--red); }
.mo-val.good { color: var(--teal); }
.mo-val.bad { color: var(--red); }

/* Truck marker */
:global(.truck-icon-wrap) {
  position: relative;
}
:global(.truck-pulse) {
  position: absolute;
  top: 0; left: 0;
  width: 32px; height: 32px;
  border-radius: 50%;
  background: rgba(0,168,255,0.2);
  animation: truck-pulse 2s ease-in-out infinite;
}
@keyframes truck-pulse {
  0%, 100% { transform: scale(1); opacity: 0.6; }
  50% { transform: scale(1.8); opacity: 0; }
}

/* Side Panel */
.side-panel {
  width: 340px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow-y: auto;
  flex-shrink: 0;
}

.panel-section {
  background: var(--bg-card);
  border: 1px solid var(--border-card);
  border-radius: 12px;
  padding: 16px;
  box-shadow: var(--shadow-sm);
}

.ps-title {
  font-size: 13px;
  font-weight: 700;
  color: var(--text-title);
  margin: 0 0 12px;
}

/* Data grid */
.data-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}
.data-item {
  padding: 8px 10px;
  background: var(--bg-input);
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.data-label { font-size: 9px; color: var(--text-muted); text-transform: uppercase; }
.data-val {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-title);
  font-family: var(--font-mono);
}
.data-val.normal { color: var(--accent); }
.data-val.warn { color: var(--amber); }
.data-val.danger { color: var(--red); }
.data-val.good { color: var(--teal); }
.data-val.bad { color: var(--red); }
.data-val.coords { font-size: 10px; }
.mono { font-family: var(--font-mono); }

/* Temp chart */
.temp-chart {
  height: 120px;
}

/* Trajectory */
.trajectory-list { display: flex; flex-direction: column; gap: 3px; }
.traj-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 5px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-family: var(--font-mono);
}
.traj-item:hover { background: var(--bg-input); }
.traj-time { color: var(--text-muted); min-width: 55px; }
.traj-temp { font-weight: 600; min-width: 42px; }
.traj-temp.normal { color: var(--accent); }
.traj-temp.warn { color: var(--amber); }
.traj-temp.danger { color: var(--red); }
.traj-speed { color: var(--text-secondary); margin-left: auto; }
.no-data {
  text-align: center; padding: 20px 0; color: var(--text-muted); font-size: 12px;
}

@media (max-width: 900px) {
  .tracking-main { flex-direction: column; height: auto; }
  .side-panel { width: 100%; }
  .header-info { width: 100%; justify-content: flex-start; }
}
</style>
