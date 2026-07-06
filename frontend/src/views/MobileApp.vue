<template>
  <div class="mobile-app">
    <div class="mobile-wrap">
      <!-- 页面头部 -->
      <div class="mb-header">
        <div class="mb-header-title">{{ headerTitle }}</div>
        <div class="mb-header-sub">{{ headerSub }}</div>
      </div>

      <!-- ===== 实时监控 Tab ===== -->
      <div class="mb-page" v-show="activeTab === 'monitor'">
        <div v-if="dashboardData.has_vehicle">
          <div class="mb-card temp-card">
            <div class="mbc-header">
              <span class="mbc-icon">🌡</span>
              <span class="mbc-title">车厢温度</span>
              <span class="mbc-status" :class="{ ok: dashboardData.temperature.is_compliant, warn: !dashboardData.temperature.is_compliant }">
                {{ dashboardData.temperature.is_compliant ? '正常' : '异常' }}
              </span>
            </div>
            <div class="temp-main">
              <span class="temp-current">{{ dashboardData.temperature.current }}℃</span>
              <span class="temp-target">目标: {{ dashboardData.temperature.target }}℃</span>
            </div>
            <div class="temp-range">
              <div class="temp-bar">
                <div class="temp-fill" :style="{ width: tempProgress + '%' }" :class="{ warn: !dashboardData.temperature.is_compliant }"></div>
              </div>
              <div class="temp-labels">
                <span>{{ dashboardData.temperature.target - 5 }}℃</span>
                <span>{{ dashboardData.temperature.target }}℃</span>
                <span>{{ dashboardData.temperature.target + 5 }}℃</span>
              </div>
            </div>
          </div>

          <div class="mb-card humidity-card">
            <div class="mbc-header">
              <span class="mbc-icon">💧</span>
              <span class="mbc-title">湿度</span>
            </div>
            <div class="humidity-main">
              <span class="humidity-value">{{ dashboardData.humidity.current }}%</span>
              <span class="humidity-status" :class="{ ok: dashboardData.humidity.is_compliant, warn: !dashboardData.humidity.is_compliant }">
                {{ dashboardData.humidity.is_compliant ? '合规' : '超标' }}
              </span>
            </div>
          </div>

          <div class="mb-card cold-machine-card">
            <div class="mbc-header">
              <span class="mbc-icon">❄</span>
              <span class="mbc-title">冷机状态</span>
              <span class="cmc-status" :class="dashboardData.cold_machine.status">
                {{ dashboardData.cold_machine.status === 'running' ? '运行中' : '已停止' }}
              </span>
            </div>
            <div class="cmc-body">
              <div class="cmc-health">
                <span class="cmch-label">健康度</span>
                <span class="cmch-value" :class="{ warn: dashboardData.cold_machine.health < 80 }">{{ dashboardData.cold_machine.health }}%</span>
              </div>
              <div class="cmc-info">
                <span>{{ dashboardData.cold_machine.brand || '冷机' }} · {{ dashboardData.cold_machine.model || '型号' }}</span>
              </div>
            </div>
          </div>

          <div class="mb-card door-card" :class="{ warning: dashboardData.door_status.is_open }">
            <div class="mbc-header">
              <span class="mbc-icon">🚪</span>
              <span class="mbc-title">车门状态</span>
              <span class="dc-status" :class="{ open: dashboardData.door_status.is_open, closed: !dashboardData.door_status.is_open }">
                {{ dashboardData.door_status.is_open ? '开启' : '关闭' }}
              </span>
            </div>
            <div v-if="dashboardData.door_status.is_open" class="dc-open-info">
              <div class="dco-row">
                <span>开启时长</span>
                <span class="dco-val" :class="{ timeout: dashboardData.door_status.is_timeout }">{{ dashboardData.door_status.duration_minutes }}分钟</span>
              </div>
              <div v-if="dashboardData.door_status.is_timeout" class="dco-warning">⚠️ 车门开启时间过长，请及时关闭！</div>
            </div>
          </div>

          <div v-if="dashboardData.multi_zone.length > 0" class="mb-card zones-card">
            <div class="mbc-header">
              <span class="mbc-icon">📦</span>
              <span class="mbc-title">多温区监控</span>
            </div>
            <div class="zones-list">
              <div v-for="zone in dashboardData.multi_zone" :key="zone.zone_key" class="zone-item">
                <div class="zone-header">
                  <span class="zone-name">{{ zone.name }}</span>
                  <span class="zone-status" :class="{ ok: zone.is_compliant, warn: !zone.is_compliant }">
                    {{ zone.is_compliant ? '正常' : '异常' }}
                  </span>
                </div>
                <div class="zone-temp">
                  <span class="zt-current" :style="{ color: zone.color }">{{ zone.temperature }}℃</span>
                  <span class="zt-target">目标: {{ zone.target_temperature }}℃</span>
                </div>
                <div class="zone-humidity">湿度: {{ zone.humidity }}%</div>
              </div>
            </div>
          </div>

          <div class="mb-card location-card">
            <div class="mbc-header">
              <span class="mbc-icon">📍</span>
              <span class="mbc-title">位置信息</span>
            </div>
            <div class="loc-info">
              <div class="loc-row">
                <span>当前城市</span>
                <span class="loc-val">{{ dashboardData.location.city || '未知' }}</span>
              </div>
              <div class="loc-row">
                <span>行驶速度</span>
                <span class="loc-val">{{ dashboardData.location.speed }} km/h</span>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="mb-empty">
          <div class="mbe-icon">🚛</div>
          <p>暂未绑定车辆</p>
          <span>请联系管理员绑定车辆</span>
        </div>
      </div>

      <!-- ===== 配送进度 Tab ===== -->
      <div class="mb-page" v-show="activeTab === 'progress'">
        <div v-if="progressData.success">
          <div class="mb-card progress-card">
            <div class="mbc-header">
              <span class="mbc-icon">🚛</span>
              <span class="mbc-title">车辆信息</span>
            </div>
            <div class="progress-vehicle">
              <div class="pv-row">
                <span>车牌号</span>
                <span class="pv-val">{{ progressData.vehicle.plate_number }}</span>
              </div>
              <div class="pv-row">
                <span>当前位置</span>
                <span class="pv-val">{{ progressData.vehicle.current_city || '行驶中' }}</span>
              </div>
              <div class="pv-row">
                <span>当前速度</span>
                <span class="pv-val">{{ progressData.vehicle.speed }} km/h</span>
              </div>
            </div>
          </div>

          <div class="mb-card route-card">
            <div class="mbc-header">
              <span class="mbc-icon">🗺</span>
              <span class="mbc-title">配送路线</span>
              <span class="mbc-badge">{{ progressData.route.total_stations }}站</span>
            </div>
            <div v-if="progressData.route.full_route.length > 0" class="route-info">
              <div class="route-progress">
                <div class="rp-bar">
                  <div class="rp-fill" :style="{ width: progressData.route.progress_percent + '%' }"></div>
                </div>
                <span class="rp-text">已完成 {{ progressData.route.progress_percent }}%</span>
              </div>
              <div class="route-segments">
                <div v-for="(city, idx) in progressData.route.full_route" :key="idx" class="route-segment" :class="{ current: idx === getCurrentSegmentIdx() }">
                  <span class="rs-num">{{ idx + 1 }}</span>
                  <span class="rs-city">{{ city }}</span>
                  <span v-if="idx < progressData.route.full_route.length - 1" class="rs-arrow">→</span>
                </div>
              </div>
            </div>
            <div v-else class="route-empty">暂无规划路线</div>
          </div>

          <div class="mb-card timing-card">
            <div class="mbc-header">
              <span class="mbc-icon">⏱</span>
              <span class="mbc-title">时效信息</span>
              <span class="timing-status" :class="{ ok: progressData.timing.is_on_time, warn: !progressData.timing.is_on_time }">
                {{ progressData.timing.is_on_time ? '准时' : '延误' }}
              </span>
            </div>
            <div class="timing-info">
              <div class="timing-row">
                <span>预计到达</span>
                <span class="timing-val">{{ fmtTime(progressData.timing.estimated_arrival) }}</span>
              </div>
              <div class="timing-row">
                <span>剩余时间</span>
                <span class="timing-val">{{ progressData.timing.remaining_hours }}小时</span>
              </div>
              <div class="timing-row">
                <span>出发时间</span>
                <span class="timing-val">{{ fmtTime(progressData.timing.departure_time) }}</span>
              </div>
            </div>
          </div>

          <div v-if="progressData.current_waybill" class="mb-card current-waybill-card">
            <div class="mbc-header">
              <span class="mbc-icon">📋</span>
              <span class="mbc-title">当前运单</span>
            </div>
            <div class="cwb-info">
              <div class="cwb-id">{{ progressData.current_waybill.waybill_id }}</div>
              <div class="cwb-cargo">{{ progressData.current_waybill.cargo_name }} · {{ progressData.current_waybill.quantity }}{{ progressData.current_waybill.unit }}</div>
              <div class="cwb-route">{{ progressData.current_waybill.origin }} → {{ progressData.current_waybill.destination }}</div>
              <div class="cwb-temp">温控: {{ progressData.current_waybill.temperature_requirement }}</div>
              <div class="cwb-status" :class="progressData.current_waybill.is_compliant ? 'ok' : 'warn'">
                {{ progressData.current_waybill.is_compliant ? '✅ 温控合规' : '⚠️ 温控异常' }}
              </div>
            </div>
          </div>
        </div>

        <div v-else class="mb-empty">
          <div class="mbe-icon">🗺</div>
          <p>暂无配送进度</p>
          <span>{{ progressData.error || '请先绑定车辆' }}</span>
        </div>
      </div>

      <!-- ===== 异常预警 Tab ===== -->
      <div class="mb-page" v-show="activeTab === 'alerts'">
        <div v-if="alertsData.success && alertsData.alerts.length > 0">
          <div class="mb-alerts-filter">
            <div class="maf-item" :class="{ active: alertFilter === 'all' }" @click="alertFilter = 'all'; loadAlerts()">全部</div>
            <div class="maf-item" :class="{ active: alertFilter === 'critical' }" @click="alertFilter = 'critical'; loadAlerts()">紧急</div>
            <div class="maf-item" :class="{ active: alertFilter === 'severe' }" @click="alertFilter = 'severe'; loadAlerts()">严重</div>
            <div class="maf-item" :class="{ active: alertFilter === 'warning' }" @click="alertFilter = 'warning'; loadAlerts()">警告</div>
          </div>

          <div class="mb-list">
            <div v-for="alert in alertsData.alerts" :key="alert.id" class="mb-card-item alert-item" :class="alert.severity">
              <div class="ai-header">
                <span class="ai-sev" :class="alert.severity">{{ sevLabel(alert.severity) }}</span>
                <span class="ai-time">{{ fmtTime(alert.timestamp) }}</span>
              </div>
              <div class="ai-message">{{ alert.message }}</div>
              <div v-if="alert.location" class="ai-location">📍 {{ alert.location }}</div>
              <div v-if="alert.temperature" class="ai-temp">🌡 {{ alert.temperature }}℃</div>
              <div v-if="alert.suggestions && alert.suggestions.length > 0" class="ai-suggestions">
                <div class="ais-title">处置建议:</div>
                <div class="ais-list">
                  <span v-for="(s, idx) in alert.suggestions" :key="idx" class="ais-item">{{ s }}</span>
                </div>
              </div>
              <div class="ai-actions" v-if="alert.status === 'active'">
                <button class="aia-btn" @click="handleAlert(alert)">处理</button>
              </div>
              <div class="ai-resolved" v-else>✅ 已处理</div>
            </div>
          </div>
        </div>

        <div v-else class="mb-empty">
          <div class="mbe-icon">✅</div>
          <p>暂无异常预警</p>
          <span>当前冷链状态正常</span>
        </div>
      </div>

      <!-- ===== 凭证上传 Tab ===== -->
      <div class="mb-page" v-show="activeTab === 'upload'">
        <div class="mb-upload-header">
          <div class="muh-title">📸 拍照上传</div>
          <div class="muh-sub">支持温度记录表、设备巡检单、现场照片等</div>
        </div>

        <div class="mb-card upload-card">
          <div class="upload-form">
            <div class="uf-item">
              <label>运单号</label>
              <input v-model="uploadForm.waybill_id" type="text" placeholder="请输入运单号" class="uf-input" />
            </div>
            <div class="uf-item">
              <label>记录类型</label>
              <select v-model="uploadForm.record_type" class="uf-select">
                <option value="temperature_record">温度记录表</option>
                <option value="inspection_report">设备巡检单</option>
                <option value="temperature_log">温控台账</option>
                <option value="equipment_photo">设备状态照片</option>
                <option value="other">其他</option>
              </select>
            </div>
            <div class="uf-item">
              <label>备注说明</label>
              <textarea v-model="uploadForm.notes" placeholder="请输入备注信息" class="uf-textarea"></textarea>
            </div>
            <div class="uf-item">
              <label>照片上传</label>
              <input ref="uploadFileInput" type="file" accept="image/*" class="mb-file-input" @change="onUploadFileSelected" />
              <button class="mb-camera-btn" @click="triggerFileInput" v-if="!uploadPhotoPreview">
                <span class="mc-icon">📷</span><span class="mc-text">点击拍照</span>
              </button>
              <div class="mb-photo-preview" v-else>
                <img :src="uploadPhotoPreview" class="mb-preview-img" />
                <button class="mpa-btn cancel" @click="clearUploadPhoto">重拍</button>
              </div>
            </div>
            <button class="uf-submit-btn" @click="submitUpload" :disabled="!uploadForm.waybill_id || !uploadPhotoFile || uploading">
              {{ uploading ? '上传中...' : '确认上传' }}
            </button>
          </div>
        </div>

        <div class="mb-card upload-history-card">
          <div class="mbc-header">
            <span class="mbc-icon">📁</span>
            <span class="mbc-title">上传记录</span>
            <span class="mbc-badge">{{ uploadHistory.count }}</span>
          </div>
          <div v-if="uploadHistory.count > 0" class="uh-list">
            <div v-for="record in uploadHistory.records" :key="record.id" class="uh-item">
              <div class="uhi-header">
                <span class="uhi-id">{{ record.record_id }}</span>
                <span class="uhi-status" :class="record.review_status">{{ reviewLabel(record.review_status) }}</span>
              </div>
              <div class="uhi-info">
                <span>运单号: {{ record.waybill_id }}</span>
                <span>类型: {{ recordTypeLabel(record.record_type) }}</span>
              </div>
              <div class="uhi-time">{{ fmtTime(record.created_at) }}</div>
            </div>
          </div>
          <div v-else class="uh-empty">暂无上传记录</div>
        </div>
      </div>

      <!-- ===== 运单管理 Tab ===== -->
      <div class="mb-page" v-show="activeTab === 'waybills'">
        <div class="mb-subtab">
          <div class="mst-item" :class="{ active: waybillSubTab === 'all' }" @click="waybillSubTab = 'all'; loadWaybills()">全部</div>
          <div class="mst-item" :class="{ active: waybillSubTab === 'in_transit' }" @click="waybillSubTab = 'in_transit'; loadWaybills('in_transit')">配送中</div>
          <div class="mst-item" :class="{ active: waybillSubTab === 'delivered' }" @click="waybillSubTab = 'delivered'; loadWaybills('delivered')">已送达</div>
          <div class="mst-item" :class="{ active: waybillSubTab === 'completed' }" @click="waybillSubTab = 'completed'; loadWaybills('completed')">已完成</div>
        </div>

        <div v-if="waybillsData.count > 0" class="mb-list">
          <div v-for="wb in waybillsData.waybills" :key="wb.waybill_id" class="mb-card-item" :class="'card-'+wb.status" @click="viewWaybillDetail(wb)">
            <div class="mci-top">
              <span class="mci-id">{{ wb.waybill_id }}</span>
              <span class="mci-status" :class="wb.status">{{ waybillStatusLabel(wb.status) }}</span>
            </div>
            <div class="mci-route">
              <span class="mci-dot"></span>
              <span class="mci-city">{{ wb.origin }}</span>
              <span class="mci-arrow">→</span>
              <span class="mci-dot end"></span>
              <span class="mci-city">{{ wb.destination }}</span>
            </div>
            <div class="mci-meta">
              <span>{{ wb.cargo_name }} · {{ wb.quantity }}{{ wb.unit }}</span>
            </div>
            <div class="mci-temp-info">
              <span>🌡 {{ wb.current_temperature }}℃</span>
              <span>{{ wb.temperature_requirement }}</span>
            </div>
            <div class="mci-compliance" :class="{ ok: wb.is_compliant, warn: !wb.is_compliant }">
              {{ wb.is_compliant ? '✅ 合规' : `⚠️ ${wb.violations_count}次异常` }}
            </div>
          </div>
        </div>

        <div v-else class="mb-empty">
          <div class="mbe-icon">📦</div>
          <p>暂无运单</p>
          <span>{{ waybillsData.error || '没有找到相关运单' }}</span>
        </div>
      </div>

      <!-- ===== 运单详情弹窗 ===== -->
      <div class="mb-overlay" v-if="waybillDetail" @click.self="waybillDetail = null">
        <div class="mb-detail">
          <div class="mbd-header">
            <span class="mbd-id">{{ waybillDetail.waybill_id }}</span>
            <span class="mbd-close" @click="waybillDetail = null">✕</span>
          </div>
          <div class="mbd-body">
            <div class="mbd-row">
              <span>货物名称</span>
              <strong>{{ waybillDetail.cargo_name }}</strong>
            </div>
            <div class="mbd-row">
              <span>货物类别</span>
              <strong>{{ waybillDetail.cargo_category }}</strong>
            </div>
            <div class="mbd-row">
              <span>路线</span>
              <strong>{{ waybillDetail.origin }} → {{ waybillDetail.destination }}</strong>
            </div>
            <div class="mbd-row">
              <span>数量</span>
              <strong>{{ waybillDetail.quantity }}{{ waybillDetail.unit }}</strong>
            </div>
            <div class="mbd-row">
              <span>温控要求</span>
              <strong>{{ waybillDetail.temperature_requirement }}</strong>
            </div>
            <div class="mbd-row">
              <span>当前温度</span>
              <strong :class="{ warn: !waybillDetail.is_compliant }">{{ waybillDetail.current_temperature }}℃</strong>
            </div>
            <div class="mbd-row">
              <span>当前湿度</span>
              <strong>{{ waybillDetail.current_humidity }}%</strong>
            </div>
            <div class="mbd-row">
              <span>合规状态</span>
              <strong :class="waybillDetail.is_compliant ? 'text-green' : 'text-red'">
                {{ waybillDetail.is_compliant ? '✅ 合规' : '⚠️ 异常' }}
              </strong>
            </div>
            <div class="mbd-row">
              <span>异常次数</span>
              <strong :class="{ warn: waybillDetail.violations_count > 0 }">{{ waybillDetail.violations_count }}次</strong>
            </div>
            <div class="mbd-row">
              <span>记录总数</span>
              <strong>{{ waybillDetail.total_records }}</strong>
            </div>
            <div class="mbd-section">
              <div class="mbds-title">🚛 配送进度</div>
              <div class="mbds-stages">
                <div v-for="stage in waybillDetail.stages" :key="stage.key" class="mbds-stage" :class="{ done: stage.completed }">
                  <span class="mbds-icon">{{ stage.completed ? '✅' : '○' }}</span>
                  <span class="mbds-name">{{ stage.name }}</span>
                  <span v-if="stage.completed" class="mbds-range">{{ stage.temp_range }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== 预警处理弹窗 ===== -->
      <div class="mb-overlay" v-if="handlingAlert" @click.self="handlingAlert = null">
        <div class="mb-detail">
          <div class="mbd-header">
            <span class="mbd-id">🚨 处理预警</span>
            <span class="mbd-close" @click="handlingAlert = null">✕</span>
          </div>
          <div class="mbd-body">
            <div class="ha-info">
              <div class="hai-sev" :class="handlingAlert.severity">{{ sevLabel(handlingAlert.severity) }}</div>
              <div class="hai-message">{{ handlingAlert.message }}</div>
            </div>
            <div class="ha-actions">
              <div class="haa-title">选择处置方式</div>
              <div class="haa-options">
                <button v-for="action in handleActions" :key="action.value" class="haa-btn" @click="confirmHandleAlert(action.value)">
                  {{ action.label }}
                </button>
              </div>
            </div>
            <div class="ha-notes">
              <label>备注说明</label>
              <textarea v-model="handleNotes" placeholder="请输入处置备注..." class="uf-textarea"></textarea>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部导航 -->
      <div class="mb-tabbar">
        <div class="mt-item" :class="{ active: activeTab === 'monitor' }" @click="activeTab = 'monitor'; loadDashboard()">
          <span class="mt-icon">📊</span>
          <span class="mt-label">监控</span>
        </div>
        <div class="mt-item" :class="{ active: activeTab === 'progress' }" @click="activeTab = 'progress'; loadProgress()">
          <span class="mt-icon">🗺</span>
          <span class="mt-label">进度</span>
        </div>
        <div class="mt-item" :class="{ active: activeTab === 'alerts' }" @click="activeTab = 'alerts'; loadAlerts()">
          <span class="mt-icon">🚨</span>
          <span class="mt-label">预警</span>
          <span v-if="alertCount > 0" class="mt-badge">{{ alertCount }}</span>
        </div>
        <div class="mt-item" :class="{ active: activeTab === 'upload' }" @click="activeTab = 'upload'; loadUploadHistory()">
          <span class="mt-icon">📸</span>
          <span class="mt-label">凭证</span>
        </div>
        <div class="mt-item" :class="{ active: activeTab === 'waybills' }" @click="activeTab = 'waybills'; loadWaybills()">
          <span class="mt-icon">📋</span>
          <span class="mt-label">运单</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { driverAPI } from '@/api'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'

const activeTab = ref('monitor')
const alertFilter = ref('all')
const waybillSubTab = ref('all')

const dashboardData = ref<any>({ has_vehicle: false })
const progressData = ref<any>({ success: false })
const alertsData = ref<any>({ success: false, alerts: [], alert_count: 0 })
const uploadHistory = ref<any>({ count: 0, records: [] })
const waybillsData = ref<any>({ count: 0, waybills: [] })
const waybillDetail = ref<any>(null)

const uploadForm = ref({
  waybill_id: '',
  record_type: 'temperature_record',
  notes: '',
})
const uploadFileInput = ref<any>(null)
const uploadPhotoPreview = ref('')
const uploading = ref(false)
let uploadPhotoFile: File | null = null

const handlingAlert = ref<any>(null)
const handleNotes = ref('')

const handleActions = [
  { value: 'check', label: '检查设备' },
  { value: 'adjust_temp', label: '调整温度' },
  { value: 'close_door', label: '关闭车门' },
  { value: 'stop_check', label: '停靠检查' },
  { value: 'contact', label: '联系调度' },
]

const headerTitle = computed(() => {
  const titles: Record<string, string> = {
    monitor: '实时监控',
    progress: '配送进度',
    alerts: '异常预警',
    upload: '凭证上传',
    waybills: '运单管理',
  }
  return titles[activeTab.value] || '冷链监控'
})

const headerSub = computed(() => {
  const subs: Record<string, string> = {
    monitor: '车厢状态 · 多温区 · 冷机',
    progress: '路线规划 · 时效追踪 · 站点',
    alerts: '实时预警 · 处置指引 · 闭环',
    upload: '拍照留存 · 凭证归档 · 溯源',
    waybills: '订单管理 · 状态追踪 · 详情',
  }
  return subs[activeTab.value] || '配送人员端'
})

const tempProgress = computed(() => {
  const target = dashboardData.value.temperature?.target || 0
  const current = dashboardData.value.temperature?.current || 0
  const range = 10
  const progress = ((current - (target - range)) / (range * 2)) * 100
  return Math.max(0, Math.min(100, progress))
})

const alertCount = computed(() => alertsData.value.alert_count || 0)

function fmtTime(t: string) {
  return t ? dayjs(t).format('MM-DD HH:mm') : '—'
}

function sevLabel(s: string) {
  const m: Record<string, string> = { critical: '紧急', severe: '严重', warning: '警告', info: '提示' }
  return m[s] || s
}

function reviewLabel(status: string) {
  const map: Record<string, string> = {
    pending_review: '待审核',
    approved: '✅ 已通过',
    rejected: '❌ 已驳回',
  }
  return map[status] || '待审核'
}

function recordTypeLabel(type: string) {
  const map: Record<string, string> = {
    temperature_record: '温度记录表',
    inspection_report: '设备巡检单',
    temperature_log: '温控台账',
    equipment_photo: '设备状态照片',
    other: '其他',
  }
  return map[type] || type
}

function waybillStatusLabel(status: string) {
  const map: Record<string, string> = {
    pending: '待接单',
    accepted: '已接单',
    in_transit: '配送中',
    delivered: '已送达',
    completed: '已完成',
  }
  return map[status] || status
}

function getCurrentSegmentIdx() {
  return Math.floor((progressData.value.route?.progress_percent || 0) / (100 / (progressData.value.route?.total_stations || 1)))
}

async function loadDashboard() {
  try {
    const res: any = await driverAPI.getDashboard()
    dashboardData.value = res
  } catch {
    dashboardData.value = { has_vehicle: false }
  }
}

async function loadProgress() {
  try {
    const res: any = await driverAPI.getDeliveryProgress()
    progressData.value = res
  } catch {
    progressData.value = { success: false, error: '加载失败' }
  }
}

async function loadAlerts() {
  try {
    const severity = alertFilter.value === 'all' ? undefined : alertFilter.value
    const res: any = await driverAPI.getAlerts(20, severity)
    alertsData.value = res
  } catch {
    alertsData.value = { success: false, alerts: [], alert_count: 0 }
  }
}

async function loadUploadHistory() {
  try {
    const res: any = await driverAPI.getUploadHistory(undefined, 20)
    uploadHistory.value = res
  } catch {
    uploadHistory.value = { count: 0, records: [] }
  }
}

async function loadWaybills(status?: string) {
  try {
    const res: any = await driverAPI.getWaybills(status, 20)
    waybillsData.value = res
  } catch {
    waybillsData.value = { count: 0, waybills: [], error: '加载失败' }
  }
}

async function viewWaybillDetail(wb: any) {
  try {
    const res: any = await driverAPI.getWaybillDetail(wb.waybill_id)
    waybillDetail.value = res
  } catch {
    ElMessage.error('加载运单详情失败')
  }
}

function triggerFileInput() {
  uploadFileInput.value?.click()
}

function onUploadFileSelected(e: Event) {
  const input = e.target as HTMLInputElement
  if (input.files && input.files[0]) {
    uploadPhotoFile = input.files[0]
    const reader = new FileReader()
    reader.onload = (ev: any) => {
      uploadPhotoPreview.value = ev.target.result
    }
    reader.readAsDataURL(uploadPhotoFile)
  }
}

function clearUploadPhoto() {
  uploadPhotoPreview.value = ''
  uploadPhotoFile = null
  if (uploadFileInput.value) uploadFileInput.value.value = ''
}

async function submitUpload() {
  if (!uploadForm.value.waybill_id) {
    ElMessage.warning('请输入运单号')
    return
  }
  if (!uploadPhotoFile) {
    ElMessage.warning('请先选择照片')
    return
  }

  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('file', uploadPhotoFile)
    fd.append('waybill_id', uploadForm.value.waybill_id)
    fd.append('record_type', uploadForm.value.record_type)
    fd.append('notes', uploadForm.value.notes)

    const res: any = await driverAPI.uploadRecord(fd)
    if (res.success) {
      ElMessage.success('上传成功，等待审核')
      clearUploadPhoto()
      uploadForm.value = { waybill_id: '', record_type: 'temperature_record', notes: '' }
      await loadUploadHistory()
    } else {
      ElMessage.error(res.message || '上传失败')
    }
  } catch (err: any) {
    const detail = err?.response?.data?.detail || '上传失败，请重试'
    ElMessage.error(detail)
  } finally {
    uploading.value = false
  }
}

function handleAlert(alert: any) {
  handlingAlert.value = alert
  handleNotes.value = ''
}

async function confirmHandleAlert(action: string) {
  if (!handlingAlert.value) return

  try {
    const res: any = await driverAPI.handleAlert(handlingAlert.value.id, action, handleNotes.value)
    if (res.success) {
      ElMessage.success('预警处置记录已提交')
      handlingAlert.value = null
      await loadAlerts()
    } else {
      ElMessage.error(res.message || '处理失败')
    }
  } catch {
    ElMessage.error('处理失败，请重试')
  }
}

let refreshTimer: any = null

onMounted(async () => {
  await loadDashboard()
  await loadAlerts()
  await loadUploadHistory()

  refreshTimer = setInterval(() => {
    if (activeTab.value === 'monitor') {
      loadDashboard()
    } else if (activeTab.value === 'alerts') {
      loadAlerts()
    }
  }, 10000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
.mobile-app {
  display: flex;
  justify-content: center;
  min-height: 100vh;
  background: #f0f2f5;
  padding-bottom: 20px;
}
.mobile-wrap {
  max-width: 420px;
  width: 100%;
  background: #fff;
  overflow: hidden;
  position: relative;
  padding-bottom: 75px;
  min-height: 100vh;
}

.mb-header {
  background: linear-gradient(135deg, #00a8ff, #7c3aed);
  padding: 24px 16px 20px;
  color: #fff;
}
.mb-header-title {
  font-size: 20px;
  font-weight: 800;
}
.mb-header-sub {
  font-size: 12px;
  opacity: 0.8;
  margin-top: 4px;
}

.mb-page {
  padding: 12px;
}

.mb-card {
  background: #fff;
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}
.mbc-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.mbc-icon {
  font-size: 18px;
}
.mbc-title {
  font-size: 14px;
  font-weight: 700;
  color: #1a1a2e;
  flex: 1;
}
.mbc-status {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 10px;
}
.mbc-status.ok {
  background: rgba(0, 210, 160, 0.12);
  color: #059669;
}
.mbc-status.warn {
  background: rgba(239, 68, 68, 0.12);
  color: #ef4444;
}
.mbc-badge {
  font-size: 11px;
  font-weight: 700;
  background: #00a8ff;
  color: #fff;
  padding: 2px 8px;
  border-radius: 10px;
}

.temp-card {
  background: linear-gradient(135deg, #e0f2fe, #f0f9ff);
}
.temp-main {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  margin-bottom: 12px;
}
.temp-current {
  font-size: 48px;
  font-weight: 800;
  color: #0284c7;
}
.temp-target {
  font-size: 13px;
  color: #0369a1;
}
.temp-range {
  margin-top: 8px;
}
.temp-bar {
  height: 8px;
  background: #bae6fd;
  border-radius: 4px;
  overflow: hidden;
}
.temp-fill {
  height: 100%;
  background: #00a8ff;
  border-radius: 4px;
  transition: width 0.3s;
}
.temp-fill.warn {
  background: #ef4444;
}
.temp-labels {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: #64748b;
  margin-top: 4px;
}

.humidity-card {
  background: linear-gradient(135deg, #f3e8ff, #ede9fe);
}
.humidity-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.humidity-value {
  font-size: 32px;
  font-weight: 800;
  color: #7c3aed;
}
.humidity-status {
  font-size: 12px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 10px;
}
.humidity-status.ok {
  background: rgba(16, 185, 129, 0.15);
  color: #059669;
}
.humidity-status.warn {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.cold-machine-card {
  background: #fff;
}
.cmc-status {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 10px;
}
.cmc-status.running {
  background: rgba(16, 185, 129, 0.12);
  color: #059669;
}
.cmc-status.stopped {
  background: rgba(239, 68, 68, 0.12);
  color: #ef4444;
}
.cmc-body {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.cmc-health {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.cmch-label {
  font-size: 12px;
  color: #666;
}
.cmch-value {
  font-size: 28px;
  font-weight: 800;
  color: #10b981;
}
.cmch-value.warn {
  color: #f59e0b;
}
.cmc-info {
  font-size: 11px;
  color: #999;
}

.door-card {
  background: #fff;
  border-left: 4px solid #00d2a0;
}
.door-card.warning {
  border-left-color: #ef4444;
  background: #fef2f2;
}
.dc-status {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 10px;
}
.dc-status.open {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}
.dc-status.closed {
  background: rgba(16, 185, 129, 0.15);
  color: #059669;
}
.dc-open-info {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #f0f0f0;
}
.dco-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  margin-bottom: 4px;
}
.dco-val {
  font-weight: 600;
  color: #333;
}
.dco-val.timeout {
  color: #ef4444;
  animation: pulse 1s infinite;
}
.dco-warning {
  font-size: 11px;
  color: #ef4444;
  font-weight: 600;
}

.zones-card {
  background: #fff;
}
.zones-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.zone-item {
  padding: 10px;
  background: #f8fafc;
  border-radius: 10px;
}
.zone-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.zone-name {
  font-size: 12px;
  font-weight: 600;
  color: #333;
}
.zone-status {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 6px;
}
.zone-status.ok {
  background: rgba(16, 185, 129, 0.15);
  color: #059669;
}
.zone-status.warn {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}
.zone-temp {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.zt-current {
  font-size: 20px;
  font-weight: 800;
}
.zt-target {
  font-size: 11px;
  color: #999;
}
.zone-humidity {
  font-size: 11px;
  color: #666;
}

.location-card {
  background: #fff;
}
.loc-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.loc-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}
.loc-val {
  font-weight: 600;
  color: #333;
}

.progress-card {
  background: #fff;
}
.progress-vehicle {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.pv-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}
.pv-val {
  font-weight: 600;
  color: #333;
}

.route-card {
  background: #fff;
}
.route-progress {
  margin-bottom: 12px;
}
.rp-bar {
  height: 6px;
  background: #e2e8f0;
  border-radius: 3px;
  overflow: hidden;
}
.rp-fill {
  height: 100%;
  background: linear-gradient(90deg, #00a8ff, #7c3aed);
  border-radius: 3px;
}
.rp-text {
  font-size: 11px;
  color: #666;
  margin-top: 4px;
  display: block;
}
.route-segments {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.route-segment {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}
.route-segment.current {
  background: #e0f2fe;
  padding: 6px 10px;
  border-radius: 8px;
}
.rs-num {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 600;
  color: #666;
}
.route-segment.current .rs-num {
  background: #00a8ff;
  color: #fff;
}
.rs-city {
  flex: 1;
  color: #333;
}
.rs-arrow {
  color: #999;
}
.route-empty {
  font-size: 12px;
  color: #999;
  text-align: center;
  padding: 10px;
}

.timing-card {
  background: #fff;
}
.timing-status {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 10px;
}
.timing-status.ok {
  background: rgba(16, 185, 129, 0.12);
  color: #059669;
}
.timing-status.warn {
  background: rgba(245, 158, 11, 0.12);
  color: #d97706;
}
.timing-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.timing-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}
.timing-val {
  font-weight: 600;
  color: #333;
}

.current-waybill-card {
  background: linear-gradient(135deg, #f0f9ff, #fff);
  border: 1px solid #bae6fd;
}
.cwb-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.cwb-id {
  font-size: 13px;
  font-weight: 700;
  font-family: monospace;
  color: #0369a1;
}
.cwb-cargo {
  font-size: 12px;
  color: #333;
}
.cwb-route {
  font-size: 12px;
  color: #666;
}
.cwb-temp {
  font-size: 11px;
  color: #999;
}
.cwb-status {
  font-size: 12px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 8px;
  display: inline-block;
  margin-top: 4px;
}
.cwb-status.ok {
  background: rgba(16, 185, 129, 0.15);
  color: #059669;
}
.cwb-status.warn {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.mb-alerts-filter {
  display: flex;
  gap: 6px;
  margin-bottom: 12px;
  overflow-x: auto;
}
.maf-item {
  padding: 8px 16px;
  font-size: 12px;
  font-weight: 600;
  color: #999;
  background: #f5f5f5;
  border-radius: 20px;
  white-space: nowrap;
  cursor: pointer;
  flex-shrink: 0;
}
.maf-item.active {
  background: #00a8ff;
  color: #fff;
}

.mb-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.mb-card-item {
  padding: 14px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #f0f0f0;
  cursor: pointer;
  transition: all 0.2s;
}
.mb-card-item:active {
  transform: scale(0.98);
}

.alert-item {
  border-left: 4px solid #ccc;
}
.alert-item.critical {
  border-left-color: #ef4444;
  background: #fef2f2;
}
.alert-item.severe {
  border-left-color: #f59e0b;
  background: #fffbeb;
}
.alert-item.warning {
  border-left-color: #3b82f6;
  background: #eff6ff;
}
.ai-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.ai-sev {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
}
.ai-sev.critical {
  background: #fee2e2;
  color: #dc2626;
}
.ai-sev.severe {
  background: #fef3c7;
  color: #d97706;
}
.ai-sev.warning {
  background: #dbeafe;
  color: #2563eb;
}
.ai-sev.info {
  background: #f0f0f0;
  color: #666;
}
.ai-time {
  font-size: 10px;
  color: #999;
}
.ai-message {
  font-size: 13px;
  color: #333;
  font-weight: 500;
  margin-bottom: 6px;
}
.ai-location {
  font-size: 11px;
  color: #666;
  margin-bottom: 4px;
}
.ai-temp {
  font-size: 11px;
  color: #00a8ff;
  font-weight: 600;
}
.ai-suggestions {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed #e0e0e0;
}
.ais-title {
  font-size: 11px;
  font-weight: 600;
  color: #666;
  margin-bottom: 4px;
}
.ais-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
.ais-item {
  font-size: 10px;
  padding: 2px 8px;
  background: #f0f0f0;
  border-radius: 4px;
  color: #333;
}
.ai-actions {
  margin-top: 10px;
}
.aia-btn {
  padding: 6px 16px;
  font-size: 12px;
  font-weight: 600;
  background: #00a8ff;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}
.ai-resolved {
  font-size: 11px;
  color: #059669;
  font-weight: 600;
  margin-top: 8px;
}

.mb-upload-header {
  text-align: center;
  margin-bottom: 16px;
}
.muh-title {
  font-size: 18px;
  font-weight: 700;
  color: #333;
}
.muh-sub {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.upload-card {
  background: #fff;
}
.upload-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.uf-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.uf-item label {
  font-size: 12px;
  font-weight: 600;
  color: #333;
}
.uf-input,
.uf-select {
  padding: 10px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 13px;
}
.uf-textarea {
  padding: 10px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 13px;
  min-height: 60px;
}
.uf-submit-btn {
  padding: 12px;
  background: linear-gradient(135deg, #00a8ff, #7c3aed);
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}
.uf-submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.upload-history-card {
  background: #fff;
}
.uh-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.uh-item {
  padding: 10px;
  background: #f8fafc;
  border-radius: 8px;
}
.uhi-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.uhi-id {
  font-size: 11px;
  font-weight: 600;
  color: #666;
  font-family: monospace;
}
.uhi-status {
  font-size: 10px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
}
.uhi-status.pending_review {
  background: #fef3c7;
  color: #d97706;
}
.uhi-status.approved {
  background: #d1fae5;
  color: #059669;
}
.uhi-status.rejected {
  background: #fee2e2;
  color: #dc2626;
}
.uhi-info {
  display: flex;
  gap: 8px;
  font-size: 10px;
  color: #999;
  margin-bottom: 2px;
}
.uhi-time {
  font-size: 10px;
  color: #ccc;
}
.uh-empty {
  font-size: 12px;
  color: #999;
  text-align: center;
  padding: 10px;
}

.mb-subtab {
  display: flex;
  margin-bottom: 12px;
  background: #f5f5f5;
  border-radius: 10px;
  padding: 3px;
}
.mst-item {
  flex: 1;
  text-align: center;
  padding: 8px 0;
  font-size: 11px;
  font-weight: 600;
  color: #999;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}
.mst-item.active {
  background: #fff;
  color: #00a8ff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.card-pending {
  border-left: 4px solid #f59e0b;
}
.card-accepted {
  border-left: 4px solid #00a8ff;
}
.card-in_transit {
  border-left: 4px solid #7c3aed;
}
.card-delivered {
  border-left: 4px solid #f59e0b;
}
.card-completed {
  border-left: 4px solid #00d2a0;
  opacity: 0.75;
}

.mci-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.mci-id {
  font-size: 12px;
  font-weight: 700;
  color: #333;
  font-family: monospace;
}
.mci-status {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 10px;
}
.mci-status.pending {
  background: #fef3c7;
  color: #d97706;
}
.mci-status.accepted {
  background: #dbeafe;
  color: #2563eb;
}
.mci-status.in_transit {
  background: #ede9fe;
  color: #7c3aed;
}
.mci-status.delivered {
  background: #fef3c7;
  color: #d97706;
}
.mci-status.completed {
  background: #d1fae5;
  color: #059669;
}

.mci-route {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  font-size: 12px;
}
.mci-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #00a8ff;
}
.mci-dot.end {
  background: #ccc;
}
.mci-arrow {
  color: #ccc;
  font-size: 10px;
}
.mci-city {
  color: #666;
}

.mci-meta {
  font-size: 11px;
  color: #999;
  margin-bottom: 6px;
}

.mci-temp-info {
  display: flex;
  gap: 12px;
  font-size: 11px;
  color: #666;
  margin-bottom: 6px;
}

.mci-compliance {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 6px;
  display: inline-block;
}
.mci-compliance.ok {
  background: rgba(16, 185, 129, 0.15);
  color: #059669;
}
.mci-compliance.warn {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.mb-empty {
  text-align: center;
  padding: 60px 20px;
  color: #ccc;
}
.mbe-icon {
  font-size: 48px;
  margin-bottom: 10px;
}
.mb-empty p {
  font-size: 15px;
  color: #999;
  margin: 4px 0;
}
.mb-empty span {
  font-size: 12px;
}

.mb-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  z-index: 1000;
}
.mb-detail {
  width: 100%;
  max-width: 420px;
  max-height: 80vh;
  overflow-y: auto;
  background: #fff;
  border-radius: 16px 16px 0 0;
  padding: 20px;
}
.mbd-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.mbd-id {
  font-size: 14px;
  font-weight: 700;
  font-family: monospace;
}
.mbd-close {
  font-size: 20px;
  color: #999;
  cursor: pointer;
  padding: 4px 8px;
}
.mbd-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.mbd-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  padding: 6px 0;
  border-bottom: 1px solid #f5f5f5;
}
.mbd-row span {
  color: #999;
}
.mbd-row strong {
  font-weight: 600;
}
.text-green {
  color: #059669;
}
.text-red {
  color: #ef4444;
}
.mbd-row strong.warn {
  color: #ef4444;
}

.mbd-section {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}
.mbds-title {
  font-size: 13px;
  font-weight: 700;
  color: #333;
  margin-bottom: 8px;
}
.mbds-stages {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.mbds-stage {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #999;
}
.mbds-stage.done {
  color: #333;
}
.mbds-icon {
  font-size: 14px;
}
.mbds-name {
  flex: 1;
}
.mbds-range {
  font-size: 10px;
  color: #999;
}

.mb-file-input {
  display: none;
}
.mb-camera-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  width: 100%;
  padding: 32px;
  border: 2px dashed #00a8ff;
  border-radius: 14px;
  background: #e8f4fd;
  cursor: pointer;
}
.mc-icon {
  font-size: 36px;
}
.mc-text {
  font-size: 14px;
  font-weight: 600;
  color: #00a8ff;
}
.mb-photo-preview {
  width: 100%;
}
.mb-preview-img {
  width: 100%;
  border-radius: 10px;
  max-height: 300px;
  object-fit: contain;
  background: #f0f0f0;
}
.mpa-btn {
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  margin-right: 8px;
}
.mpa-btn.cancel {
  background: #f0f0f0;
  color: #666;
}

.mb-tabbar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  justify-content: space-around;
  align-items: center;
  background: #fff;
  border-top: 1px solid #f0f0f0;
  padding: 6px 0 8px;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.04);
}
.mt-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 4px 12px;
  cursor: pointer;
  position: relative;
}
.mt-icon {
  font-size: 20px;
}
.mt-label {
  font-size: 10px;
  color: #999;
}
.mt-item.active .mt-label {
  color: #00a8ff;
  font-weight: 600;
}
.mt-badge {
  position: absolute;
  top: -4px;
  right: 4px;
  font-size: 9px;
  font-weight: 700;
  background: #ef4444;
  color: #fff;
  padding: 1px 5px;
  border-radius: 8px;
}

.ha-info {
  margin-bottom: 16px;
}
.hai-sev {
  font-size: 12px;
  font-weight: 700;
  padding: 4px 12px;
  border-radius: 8px;
  margin-bottom: 8px;
  display: inline-block;
}
.hai-sev.critical {
  background: #fee2e2;
  color: #dc2626;
}
.hai-sev.severe {
  background: #fef3c7;
  color: #d97706;
}
.hai-sev.warning {
  background: #dbeafe;
  color: #2563eb;
}
.hai-message {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}
.ha-actions {
  margin-bottom: 16px;
}
.haa-title {
  font-size: 12px;
  font-weight: 600;
  color: #666;
  margin-bottom: 8px;
}
.haa-options {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.haa-btn {
  padding: 8px 14px;
  font-size: 12px;
  font-weight: 600;
  background: #f0f9ff;
  color: #0369a1;
  border: 1px solid #bae6fd;
  border-radius: 8px;
  cursor: pointer;
}
.haa-btn:active {
  background: #00a8ff;
  color: #fff;
  border-color: #00a8ff;
}
.ha-notes {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.ha-notes label {
  font-size: 12px;
  font-weight: 600;
  color: #333;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@media (min-width: 768px) {
  .mobile-wrap {
    border-radius: 16px;
    margin: 20px;
    min-height: auto;
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.08);
  }
}
</style>