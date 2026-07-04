<template>
  <div class="tracking-page">
    <!-- 顶部统计栏 -->
    <div class="tracking-header">
      <div class="header-left">
        <h2 class="page-title">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="10" r="3"/><path d="M12 21.7C17.3 17 20 13 20 10a8 8 0 1 0-16 0c0 3 2.7 7 8 11.7z"/></svg>
          车辆实时追踪
        </h2>
        <span class="last-update" v-if="lastUpdate">更新于 {{ lastUpdate }}</span>
      </div>
      <div class="header-stats">
        <div class="stat-item">
          <span class="stat-val online">{{ stats.online }}</span>
          <span class="stat-label">在线</span>
        </div>
        <div class="stat-item">
          <span class="stat-val total">{{ stats.total }}</span>
          <span class="stat-label">总计</span>
        </div>
        <div class="stat-item">
          <span class="stat-val alert" v-if="stats.alerts > 0">{{ stats.alerts }}</span>
          <span class="stat-val normal" v-else>0</span>
          <span class="stat-label">告警</span>
        </div>
      </div>
    </div>

    <div class="tracking-main">
      <!-- 地图区域 -->
      <div class="map-container" ref="mapContainer">
        <div id="vehicle-map"></div>

        <!-- 图例 -->
        <div class="map-legend">
          <div class="legend-item"><span class="legend-dot normal-dot"></span> 正常</div>
          <div class="legend-item"><span class="legend-dot alert-dot"></span> 告警</div>
          <div class="legend-item"><span class="legend-dot offline-dot"></span> 离线</div>
        </div>

        <!-- 刷新按钮 -->
        <button class="map-refresh-btn" @click="refreshPositions" :class="{ spinning: refreshing }">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
        </button>
      </div>

      <!-- 右侧面板 -->
      <div class="side-panel">
        <!-- 搜索 -->
        <div class="panel-search">
          <input
            v-model="searchText"
            type="text"
            placeholder="搜索车牌号/设备号..."
            class="search-input"
            @input="filterVehicles"
          />
        </div>

        <!-- 车辆列表 -->
        <div class="vehicle-list">
          <div
            v-for="v in filteredVehicles"
            :key="v.device_id"
            class="vehicle-card"
            :class="{ selected: selectedVehicle?.device_id === v.device_id, alert: v.has_alert }"
            @click="selectVehicle(v)"
          >
            <div class="v-card-top">
              <span class="v-status-dot" :class="v.online ? 'online' : 'offline'"></span>
              <span class="v-id">{{ v.device_id }}</span>
              <span class="v-speed" v-if="v.online">{{ v.vehicle_speed }}km/h</span>
            </div>
            <div class="v-card-mid">
              <span class="v-plate">{{ v.plate_number }}</span>
              <span class="v-cargo">{{ v.cargo_type }}</span>
            </div>
            <div class="v-card-bottom">
              <span class="v-temp" :class="tempClass(v.temperature)">
                {{ v.temperature }}°C
              </span>
              <span class="v-city">{{ v.current_city }}</span>
              <span class="v-alert-tag" v-if="v.has_alert">⚠</span>
            </div>
          </div>
          <div v-if="filteredVehicles.length === 0" class="no-result">
            暂无匹配车辆
          </div>
        </div>

        <!-- 车辆详情抽屉 -->
        <div class="detail-panel" v-if="selectedVehicle">
          <div class="detail-header">
            <h4>{{ selectedVehicle.device_id }}</h4>
            <button class="detail-close" @click="selectedVehicle = null">×</button>
          </div>
          <div class="detail-body">
            <div class="detail-row">
              <span class="dl">车牌号</span>
              <span class="dv">{{ selectedVehicle.plate_number }}</span>
            </div>
            <div class="detail-row">
              <span class="dl">货物类型</span>
              <span class="dv">{{ selectedVehicle.cargo_type }}</span>
            </div>
            <div class="detail-row">
              <span class="dl">当前温度</span>
              <span class="dv temp" :class="tempClass(selectedVehicle.temperature)">{{ selectedVehicle.temperature }}°C</span>
            </div>
            <div class="detail-row">
              <span class="dl">车速</span>
              <span class="dv">{{ selectedVehicle.vehicle_speed }} km/h</span>
            </div>
            <div class="detail-row">
              <span class="dl">冷机状态</span>
              <span class="dv" :class="selectedVehicle.cold_car_status === 1 ? 'good' : 'bad'">
                {{ selectedVehicle.cold_car_status === 1 ? '正常运行' : '异常' }}
              </span>
            </div>
            <div class="detail-row">
              <span class="dl">当前城市</span>
              <span class="dv">{{ selectedVehicle.current_city }}</span>
            </div>
            <div class="detail-row">
              <span class="dl">坐标</span>
              <span class="dv mono">{{ selectedVehicle.latitude?.toFixed(4) }}, {{ selectedVehicle.longitude?.toFixed(4) }}</span>
            </div>
            <button class="btn-trajectory" @click="loadTrajectory(selectedVehicle.device_id)" :disabled="trajectoryLoading">
              {{ trajectoryLoading ? '加载中...' : '查看历史轨迹' }}
            </button>
            <div class="detail-links">
              <span class="dlink" @click="router.push('/alerts')">🔔 相关告警</span>
              <span class="dlink" @click="router.push('/temperature')">📈 温度趋势</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 轨迹弹窗 -->
    <div class="trajectory-overlay" v-if="showTrajectory" @click.self="showTrajectory = false">
      <div class="trajectory-modal">
        <div class="trajectory-header">
          <h4>历史轨迹 — {{ trajectoryDevice }}</h4>
          <button class="detail-close" @click="showTrajectory = false">×</button>
        </div>
        <div class="trajectory-body" ref="trajectoryContainer">
          <div id="trajectory-map"></div>
        </div>
        <div class="trajectory-info" v-if="trajectoryPoints.length > 0">
          共 {{ trajectoryPoints.length }} 个轨迹点 | 
          起始 {{ formatTime(trajectoryPoints[0]?.time) }} → 
          结束 {{ formatTime(trajectoryPoints[trajectoryPoints.length-1]?.time) }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { vehicleAPI } from '@/api'
import { ElMessage } from 'element-plus'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import dayjs from 'dayjs'

const router = useRouter()

// ===== 数据状态 =====
const mapContainer = ref<HTMLElement | null>(null)
const trajectoryContainer = ref<HTMLElement | null>(null)
let map: L.Map | null = null
let trajectoryMap: L.Map | null = null
let markersLayer: L.LayerGroup | null = null
const refreshTimer = ref<number | null>(null)

const vehicles = ref<any[]>([])
const filteredVehicles = ref<any[]>([])
const searchText = ref('')
const selectedVehicle = ref<any | null>(null)
const refreshing = ref(false)
const lastUpdate = ref('')
const showTrajectory = ref(false)
const trajectoryDevice = ref('')
const trajectoryPoints = ref<any[]>([])
const trajectoryLoading = ref(false)

const stats = reactive({ online: 0, total: 0, alerts: 0 })

// 创建自定义图标
function createVehicleIcon(hasAlert: boolean, isSelected: boolean) {
  const color = hasAlert ? '#ef4444' : '#00a8ff'
  const size = isSelected ? 16 : 12
  const border = isSelected ? '3px solid #fff' : '2px solid #fff'

  return L.divIcon({
    className: 'vehicle-marker',
    html: `<div style="
      width:${size}px;height:${size}px;
      background:${color};
      border:${border};
      border-radius:50%;
      box-shadow:0 0 ${isSelected ? 12 : 6}px ${color};
      ${isSelected ? 'animation: marker-pulse 1.5s ease-in-out infinite;' : ''}
    "></div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  })
}

// ===== 初始化地图 =====
function initMap() {
  if (map) return

  map = L.map('vehicle-map', {
    center: [34.0, 108.0],
    zoom: 5,
    zoomControl: false,
    attributionControl: false,
  })

  // 高德地图瓦片（国内可用）
  L.tileLayer('https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}', {
    subdomains: ['1', '2', '3', '4'],
    maxZoom: 18,
    minZoom: 3,
    attribution: '&copy; 高德地图',
  }).addTo(map)

  // 缩放控件
  L.control.zoom({ position: 'bottomright' }).addTo(map)

  markersLayer = L.layerGroup().addTo(map)
}

// ===== 加载所有车辆位置 =====
async function refreshPositions() {
  refreshing.value = true
  try {
    const res: any = await vehicleAPI.getAllPositions()
    vehicles.value = res.vehicles || []
    stats.online = vehicles.value.filter(v => v.online).length
    stats.total = vehicles.value.length
    stats.alerts = vehicles.value.filter(v => v.has_alert).length
    lastUpdate.value = dayjs().format('HH:mm:ss')

    filterVehicles()
    updateMapMarkers()
  } catch (e) {
    console.error('获取车辆位置失败:', e)
    ElMessage.warning('获取车辆位置失败，请检查网络')
  } finally {
    refreshing.value = false
  }
}

// ===== 更新地图标记 =====
function updateMapMarkers() {
  if (!map || !markersLayer) return
  markersLayer.clearLayers()

  filteredVehicles.value.forEach(v => {
    if (!v.latitude || !v.longitude) return

    const isSelected = selectedVehicle.value?.device_id === v.device_id
    const icon = createVehicleIcon(v.has_alert || false, isSelected)

    const marker = L.marker([v.latitude, v.longitude], { icon })
      .bindTooltip(`
        <div style="font-family:monospace;font-size:11px;text-align:center">
          <b>${v.device_id}</b><br/>
          ${v.plate_number} | ${v.temperature}°C<br/>
          ${v.current_city || ''} ${v.vehicle_speed ? v.vehicle_speed + 'km/h' : ''}
        </div>
      `, { direction: 'top', offset: [0, -10] })

    marker.on('click', () => {
      selectVehicle(v)
    })

    markersLayer!.addLayer(marker)
  })

  // 自动聚焦到选中车辆
  if (selectedVehicle.value?.latitude && selectedVehicle.value?.longitude) {
    map.setView([selectedVehicle.value.latitude, selectedVehicle.value.longitude], 10, { animate: true })
  }
}

// ===== 筛选车辆 =====
function filterVehicles() {
  const s = searchText.value.toLowerCase()
  if (!s) {
    filteredVehicles.value = vehicles.value
  } else {
    filteredVehicles.value = vehicles.value.filter(
      v => v.device_id.toLowerCase().includes(s) || v.plate_number.toLowerCase().includes(s)
    )
  }
  updateMapMarkers()
}

// ===== 选中车辆 =====
async function selectVehicle(vehicle: any) {
  selectedVehicle.value = vehicle
  if (map && vehicle.latitude && vehicle.longitude) {
    map.setView([vehicle.latitude, vehicle.longitude], 10, { animate: true })
  }
  updateMapMarkers()
}

// ===== 加载轨迹 =====
async function loadTrajectory(deviceId: string) {
  trajectoryLoading.value = true
  trajectoryDevice.value = deviceId
  showTrajectory.value = true

  try {
    const res: any = await vehicleAPI.getTrajectory(deviceId, 4)
    trajectoryPoints.value = res.points || []

    await nextTick()
    initTrajectoryMap()
  } catch (e) {
    console.error('加载轨迹失败:', e)
    ElMessage.warning('加载轨迹失败')
  } finally {
    trajectoryLoading.value = false
  }
}

function initTrajectoryMap() {
  if (!trajectoryPoints.value.length) return

  // 销毁旧地图
  const oldContainer = document.getElementById('trajectory-map')
  if (oldContainer) {
    oldContainer.innerHTML = ''
  }

  const pts = trajectoryPoints.value
  const center = pts[Math.floor(pts.length / 2)]

  trajectoryMap = L.map('trajectory-map', {
    center: [center.latitude, center.longitude],
    zoom: 6,
    zoomControl: true,
    attributionControl: false,
  })

  L.tileLayer('https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}', {
    subdomains: ['1', '2', '3', '4'],
    maxZoom: 18,
    attribution: '&copy; 高德地图',
  }).addTo(trajectoryMap)

  // 绘制轨迹线
  const latlngs = pts.map((p: any) => [p.latitude, p.longitude] as [number, number])

  // 按温度颜色分段
  for (let i = 1; i < latlngs.length; i++) {
    const temp = pts[i].temperature
    const color = temp > -15 ? '#ef4444' : temp > -20 ? '#f59e0b' : '#00a8ff'
    L.polyline([latlngs[i - 1], latlngs[i]], {
      color,
      weight: 3,
      opacity: 0.7,
    }).addTo(trajectoryMap)
  }

  // 起点和终点标记
  const startIcon = L.divIcon({
    html: '<div style="width:10px;height:10px;background:#10b981;border:2px solid #fff;border-radius:50%;"></div>',
    iconSize: [10, 10],
    iconAnchor: [5, 5],
  })
  const endIcon = L.divIcon({
    html: '<div style="width:10px;height:10px;background:#ef4444;border:2px solid #fff;border-radius:50%;"></div>',
    iconSize: [10, 10],
    iconAnchor: [5, 5],
  })

  L.marker(latlngs[0], { icon: startIcon })
    .bindTooltip('起点')
    .addTo(trajectoryMap)

  L.marker(latlngs[latlngs.length - 1], { icon: endIcon })
    .bindTooltip('终点')
    .addTo(trajectoryMap)

  trajectoryMap.fitBounds(latlngs, { padding: [30, 30] })
}

// ===== 工具方法 =====
function tempClass(temp: number) {
  if (temp > -15) return 'danger'
  if (temp > -20) return 'warn'
  return 'normal'
}

function formatTime(t: string) {
  return t ? dayjs(t).format('MM-DD HH:mm') : '-'
}

// ===== 生命周期 =====
onMounted(() => {
  initMap()
  refreshPositions()
  // 每15秒刷新
  refreshTimer.value = window.setInterval(refreshPositions, 15000)
})

onUnmounted(() => {
  if (refreshTimer.value) clearInterval(refreshTimer.value)
  if (map) {
    map.remove()
    map = null
  }
  if (trajectoryMap) {
    trajectoryMap.remove()
    trajectoryMap = null
  }
})
</script>

<style scoped>
.tracking-page {
  height: calc(100vh - 56px);
  display: flex;
  flex-direction: column;
  gap: 0;
}

/* ===== 顶部统计 ===== */
.tracking-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 0 12px;
  flex-shrink: 0;
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

.header-stats {
  display: flex;
  gap: 20px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.stat-val {
  font-family: var(--font-display);
  font-size: 22px;
  font-weight: 800;
  line-height: 1;
}
.stat-val.online { color: var(--accent); }
.stat-val.total { color: var(--text-title); }
.stat-val.alert { color: var(--red); }
.stat-val.normal { color: var(--text-muted); }

.stat-label {
  font-size: 10px;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

/* ===== 主区域 ===== */
.tracking-main {
  flex: 1;
  display: flex;
  gap: 0;
  min-height: 0;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 2px 20px rgba(0,0,0,0.04);
  border: 1px solid rgba(0,0,0,0.06);
}

/* ===== 地图 ===== */
.map-container {
  flex: 1;
  position: relative;
  min-width: 0;
  background: #e8ecf1;
}

#vehicle-map {
  width: 100%;
  height: 100%;
}

/* 图例 */
.map-legend {
  position: absolute;
  bottom: 16px;
  left: 16px;
  background: rgba(255,255,255,0.9);
  backdrop-filter: blur(8px);
  border-radius: 10px;
  padding: 8px 12px;
  display: flex;
  gap: 14px;
  font-size: 11px;
  font-weight: 500;
  color: var(--text-secondary);
  box-shadow: 0 2px 12px rgba(0,0,0,0.06);
  border: 1px solid rgba(0,0,0,0.05);
  z-index: 500;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  border: 1.5px solid #fff;
  box-shadow: 0 0 4px currentColor;
}
.normal-dot { background: var(--accent); color: var(--accent); }
.alert-dot { background: var(--red); color: var(--red); }
.offline-dot { background: #94a3b8; color: #94a3b8; }

/* 刷新按钮 */
.map-refresh-btn {
  position: absolute;
  top: 14px;
  right: 14px;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgba(255,255,255,0.9);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(0,0,0,0.06);
  color: var(--accent);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.25s;
  z-index: 500;
  box-shadow: 0 2px 10px rgba(0,0,0,0.04);
}
.map-refresh-btn:hover {
  background: var(--accent-bg);
}
.spinning svg {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes marker-pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.4); opacity: 0.7; }
}

/* ===== 右侧面板 ===== */
.side-panel {
  width: 320px;
  background: #fff;
  display: flex;
  flex-direction: column;
  border-left: 1px solid rgba(0,0,0,0.06);
  overflow: hidden;
}

.panel-search {
  padding: 12px;
  border-bottom: 1px solid rgba(0,0,0,0.05);
  flex-shrink: 0;
}

.search-input {
  width: 100%;
  height: 36px;
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 10px;
  padding: 0 12px;
  font-size: 13px;
  color: var(--text-primary);
  background: var(--bg-input);
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}
.search-input:focus {
  border-color: var(--accent);
}
.search-input::placeholder {
  color: var(--text-muted);
}

/* 车辆列表 */
.vehicle-list {
  flex: 1;
  overflow-y: auto;
  padding: 6px;
}

.vehicle-card {
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 4px;
  border: 1px solid transparent;
}

.vehicle-card:hover {
  background: rgba(0,168,255,0.04);
}

.vehicle-card.selected {
  background: var(--accent-bg);
  border-color: rgba(0,168,255,0.15);
}

.vehicle-card.alert {
  border-left: 3px solid var(--red);
}

.v-card-top {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.v-status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
.v-status-dot.online { background: var(--accent); }
.v-status-dot.offline { background: #94a3b8; }

.v-id {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  color: var(--text-title);
}

.v-speed {
  margin-left: auto;
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--text-muted);
}

.v-card-mid {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  padding-left: 14px;
}

.v-plate {
  font-size: 12px;
  color: var(--text-secondary);
  font-weight: 500;
}

.v-cargo {
  font-size: 10px;
  color: var(--text-muted);
  background: rgba(0,0,0,0.04);
  padding: 1px 6px;
  border-radius: 4px;
}

.v-card-bottom {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-left: 14px;
}

.v-temp {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 700;
}
.v-temp.normal { color: var(--accent); }
.v-temp.warn { color: var(--amber); }
.v-temp.danger { color: var(--red); }

.v-city {
  font-size: 11px;
  color: var(--text-muted);
}

.v-alert-tag {
  margin-left: auto;
  font-size: 13px;
}

.no-result {
  text-align: center;
  padding: 40px 0;
  color: var(--text-muted);
  font-size: 13px;
}

/* ===== 车辆详情面板 ===== */
.detail-panel {
  border-top: 1px solid rgba(0,0,0,0.06);
  background: #fafbfc;
  flex-shrink: 0;
  max-height: 280px;
  overflow-y: auto;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-bottom: 1px solid rgba(0,0,0,0.04);
}

.detail-header h4 {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 700;
  color: var(--text-title);
  margin: 0;
}

.detail-close {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.detail-close:hover {
  background: rgba(0,0,0,0.04);
  color: var(--text-primary);
}

.detail-body {
  padding: 10px 12px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 0;
}

.dl {
  font-size: 11px;
  color: var(--text-muted);
}

.dv {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-title);
}
.dv.temp.normal { color: var(--accent); }
.dv.temp.warn { color: var(--amber); }
.dv.temp.danger { color: var(--red); }
.dv.good { color: var(--teal); }
.dv.bad { color: var(--red); }
.dv.mono { font-family: var(--font-mono); font-size: 10px; }

.btn-trajectory {
  width: 100%;
  margin-top: 10px;
  padding: 8px;
  border-radius: 8px;
  border: 1px solid var(--accent);
  background: var(--accent-bg);
  color: var(--accent);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-trajectory:hover {
  background: var(--accent);
  color: #fff;
}
.btn-trajectory:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.detail-links { display: flex; gap: 8px; margin-top: 6px; }
.dlink { font-size: 11px; color: var(--accent); cursor: pointer; font-weight: 500; padding: 4px 8px; border-radius: 6px; background: var(--accent-bg); transition: all 0.2s; }
.dlink:hover { background: var(--accent); color: #fff; }

/* ===== 轨迹弹窗 ===== */
.trajectory-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  backdrop-filter: blur(4px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.trajectory-modal {
  width: 75vw;
  max-width: 1000px;
  height: 70vh;
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0,0,0,0.2);
}

.trajectory-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid rgba(0,0,0,0.06);
}
.trajectory-header h4 {
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 700;
  color: var(--text-title);
  margin: 0;
}

.trajectory-body {
  flex: 1;
  min-height: 0;
}

#trajectory-map {
  width: 100%;
  height: 100%;
}

.trajectory-info {
  padding: 10px 18px;
  font-size: 11px;
  color: var(--text-muted);
  font-family: var(--font-mono);
  border-top: 1px solid rgba(0,0,0,0.06);
  text-align: center;
}
</style>
