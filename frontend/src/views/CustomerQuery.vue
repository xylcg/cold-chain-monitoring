<template>
  <div class="customer-page">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">客户温控查询服务</h2>
        <p class="page-subtitle">输入运单号，查询货物全程温控信息</p>
      </div>
      <div class="header-right">
        <el-input v-model="waybillNo" placeholder="输入运单号查询..." clearable style="width: 320px" @keyup.enter="queryWaybill">
          <template #prefix>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          </template>
        </el-input>
        <button class="btn-primary" @click="queryWaybill">查询</button>
      </div>
    </div>

    <div v-if="queryResult" class="main-content">
      <div class="glass-card waybill-block">
        <div class="info-head">
          <div class="head-left">
            <h3>{{ queryResult.cargo_name }}</h3>
            <div class="code-row">
              <code class="waybill-code">{{ queryResult.waybill_id }}</code>
              <code class="trace-code">{{ queryResult.trace_code }}</code>
            </div>
          </div>
          <span class="comp-badge" :class="queryResult.is_compliant ? 'ok' : 'fail'">
            {{ queryResult.is_compliant ? '✅ 温控达标' : '❌ 温度异常' }}
          </span>
        </div>

        <div class="info-grid">
          <div class="info-card">
            <span class="info-label">货物类别</span>
            <span class="info-value">{{ queryResult.cargo_category }}</span>
            <span v-if="queryResult.is_high_sensitivity" class="sensitivity-tag">高敏货物</span>
          </div>
          <div class="info-card">
            <span class="info-label">温度要求</span>
            <span class="info-value">{{ queryResult.temperature_requirement }}</span>
          </div>
          <div class="info-card highlight">
            <span class="info-label">当前温度</span>
            <span class="info-value temp-value">{{ queryResult.current_temperature }}°C</span>
          </div>
          <div class="info-card">
            <span class="info-label">当前湿度</span>
            <span class="info-value">{{ queryResult.current_humidity }}%</span>
          </div>
          <div class="info-card">
            <span class="info-label">温度范围</span>
            <span class="info-value">{{ queryResult.temperature_summary?.range }}</span>
          </div>
          <div class="info-card">
            <span class="info-label">发货地</span>
            <span class="info-value">{{ queryResult.origin }}</span>
          </div>
          <div class="info-card">
            <span class="info-label">目的地</span>
            <span class="info-value">{{ queryResult.destination }}</span>
          </div>
          <div class="info-card">
            <span class="info-label">数量</span>
            <span class="info-value">{{ queryResult.quantity }} {{ queryResult.unit }}</span>
          </div>
        </div>

        <div class="info-footer">
          <span class="footer-item">状态: {{ queryResult.status }}</span>
          <span class="footer-item">完成 {{ queryResult.completed_stages }}/{{ queryResult.total_stages }} 环节</span>
          <span v-if="queryResult.violations_count > 0" class="footer-item warning">
            ⚠️ {{ queryResult.violations_count }} 次温度异常
          </span>
          <span v-if="queryResult.blockchain?.on_chain" class="footer-item success">
            🔗 已区块链存证
          </span>
          <span class="footer-item time">更新时间: {{ formatDateTime(queryResult.last_update) }}</span>
        </div>
      </div>

      <div class="glass-card">
        <div class="section-header">
          <h3 class="section-title">🌡️ 全程温度曲线</h3>
          <div class="section-actions">
            <button class="action-btn" @click="toggleHumidity">
              {{ showHumidity ? '隐藏湿度' : '显示湿度' }}
            </button>
            <button class="action-btn" @click="toggleAnomalyMark">
              {{ showAnomalyMark ? '隐藏异常标记' : '显示异常标记' }}
            </button>
          </div>
        </div>
        <div ref="chartRef" class="chart-box"></div>

        <div v-if="curveData?.door_events?.length" class="door-events">
          <h4>🚪 开门事件记录</h4>
          <div v-for="(evt, idx) in curveData.door_events" :key="idx" class="door-item">
            <span class="door-time">{{ formatDateTime(evt.timestamp) }}</span>
            <span class="door-temp">{{ evt.temperature }}°C</span>
            <span class="door-location">{{ evt.location }}</span>
            <span class="door-action">{{ evt.action }}</span>
          </div>
        </div>
      </div>

      <div class="glass-card">
        <h3 class="section-title">📋 冷链追溯详情</h3>
        <div class="timeline">
          <div v-for="stage in queryResult.stages" :key="stage.key" class="timeline-item" :class="{ completed: stage.has_records }">
            <div class="timeline-dot">
              <span class="stage-icon">{{ stage.icon }}</span>
            </div>
            <div class="timeline-content">
              <div class="stage-header">
                <span class="stage-name">{{ stage.name }}</span>
                <span v-if="stage.has_records" class="stage-count">{{ stage.count }}条记录</span>
              </div>
              <div v-if="stage.has_records" class="stage-details">
                <span class="stage-time">{{ formatDateTime(stage.first_time) }} ~ {{ formatDateTime(stage.last_time) }}</span>
                <span class="stage-temp">温度 {{ stage.temp_range }}</span>
              </div>
              <div v-else class="stage-pending">待处理</div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="queryResult.violations_count > 0" class="glass-card alert-card">
        <h3 class="section-title">⚠️ 温度异常记录</h3>
        <div class="violations-list">
          <div v-for="(v, idx) in queryResult.violations" :key="idx" class="violation-item">
            <div class="violation-header">
              <span class="violation-stage">{{ getStageName(v.stage) }}</span>
              <span class="violation-time">{{ formatDateTime(v.timestamp) }}</span>
            </div>
            <div class="violation-temp">
              <span class="temp-label">异常温度</span>
              <span class="temp-value error">{{ v.temperature }}°C</span>
              <span class="temp-req">标准: {{ queryResult.temperature_requirement }}</span>
            </div>
            <p class="violation-notes">{{ v.notes }}</p>
          </div>
        </div>
      </div>

      <div v-if="alertsData?.alerts?.length" class="glass-card">
        <h3 class="section-title">🔔 预警告警记录</h3>
        <div class="alerts-list">
          <div v-for="(alert, idx) in alertsData.alerts" :key="idx" class="alert-item" :class="alert.severity">
            <span class="alert-icon">{{ getAlertIcon(alert.severity) }}</span>
            <div class="alert-content">
              <div class="alert-header">
                <span class="alert-type">{{ getAlertTypeLabel(alert.type) }}</span>
                <span class="alert-severity">{{ getAlertSeverityLabel(alert.severity) }}</span>
              </div>
              <p class="alert-message">{{ alert.message }}</p>
              <div class="alert-meta">
                <span>{{ formatDateTime(alert.timestamp) }}</span>
                <span v-if="alert.location">{{ alert.location }}</span>
                <span v-if="alert.temperature">{{ alert.temperature }}°C</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="glass-card">
        <h3 class="section-title">🔗 区块链存证信息</h3>
        <div class="blockchain-info">
          <div class="blockchain-item">
            <span class="info-label">存证状态</span>
            <span class="info-value" :class="queryResult.blockchain?.on_chain ? 'success' : 'pending'">
              {{ queryResult.blockchain?.on_chain ? '已上链' : '待存证' }}
            </span>
          </div>
          <div v-if="queryResult.blockchain?.on_chain" class="blockchain-details">
            <div class="blockchain-item">
              <span class="info-label">区块编号</span>
              <code class="info-value">#{{ queryResult.blockchain.block_number }}</code>
            </div>
            <div class="blockchain-item">
              <span class="info-label">区块哈希</span>
              <code class="info-value">{{ queryResult.blockchain.block_hash?.slice(0, 16) }}...</code>
            </div>
            <div class="blockchain-item">
              <span class="info-label">Merkle根</span>
              <code class="info-value">{{ queryResult.blockchain.merkle_root?.slice(0, 16) }}...</code>
            </div>
            <div class="blockchain-item">
              <span class="info-label">存证时间</span>
              <span class="info-value">{{ formatDateTime(queryResult.blockchain.certified_at) }}</span>
            </div>
          </div>
        </div>
        <button class="btn-primary" style="margin-top:12px;" @click="verifyBlockchain">验证区块链</button>
      </div>

      <div class="download-section">
        <h3 class="section-title">📄 温控证明文件下载</h3>
        <div class="download-buttons">
          <button class="btn-primary" @click="downloadCertificate('text', 'simple')">下载简易版证明 (.txt)</button>
          <button class="btn-secondary" @click="downloadCertificate('html', 'full')">下载完整版证明 (.html)</button>
          <button class="btn-secondary" @click="downloadCertificate('text', 'full')">下载完整版证明 (.txt)</button>
        </div>
      </div>
    </div>

    <div v-else class="empty-block">
      <div class="empty-icon">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" opacity="0.3">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
      </div>
      <p>输入运单号查询冷链温度信息</p>
      <span>扫码或输入运单号，即可查看货物全程温控数据</span>
      <div class="demo-codes">
        <span class="demo-label">示例运单号:</span>
        <button class="demo-code" @click="waybillNo = 'WB20260706001'; queryWaybill()">WB20260706001</button>
        <button class="demo-code" @click="waybillNo = 'WB20260706002'; queryWaybill()">WB20260706002</button>
        <button class="demo-code" @click="waybillNo = 'WB20260706003'; queryWaybill()">WB20260706003</button>
      </div>
    </div>

    <el-dialog v-model="showBlockchainVerify" title="区块链验证结果" width="500px">
      <div v-if="verifyResult" class="verify-content">
        <div class="verify-status" :class="verifyResult.verified ? 'success' : 'fail'">
          <span class="status-icon">{{ verifyResult.verified ? '✅' : '❌' }}</span>
          <span class="status-text">{{ verifyResult.message }}</span>
        </div>
        <div class="verify-details">
          <div class="verify-item">
            <span class="verify-label">运单号</span>
            <code>{{ verifyResult.waybill_id }}</code>
          </div>
          <div class="verify-item">
            <span class="verify-label">溯源码</span>
            <code>{{ verifyResult.trace_code }}</code>
          </div>
          <div class="verify-item">
            <span class="verify-label">区块哈希验证</span>
            <span :class="verifyResult.block_hash_valid ? 'success' : 'fail'">
              {{ verifyResult.block_hash_valid ? '通过' : '失败' }}
            </span>
          </div>
          <div class="verify-item">
            <span class="verify-label">链完整性</span>
            <span :class="verifyResult.chain_integrity ? 'success' : 'fail'">
              {{ verifyResult.chain_integrity ? '完整' : '异常' }}
            </span>
          </div>
          <div class="verify-item">
            <span class="verify-label">Merkle根验证</span>
            <span :class="verifyResult.merkle_integrity ? 'success' : 'fail'">
              {{ verifyResult.merkle_integrity ? '通过' : '失败' }}
            </span>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { customerAPI } from '@/api'
import * as echarts from 'echarts'

const waybillNo = ref('')
const queryResult = ref<any>(null)
const curveData = ref<any>(null)
const alertsData = ref<any>(null)
const showHumidity = ref(false)
const showAnomalyMark = ref(true)
const chartRef = ref<HTMLElement>()
const showBlockchainVerify = ref(false)
const verifyResult = ref<any>(null)
let chartInstance: any = null

const stageNames: Record<string, string> = {
  precool: '产地预冷',
  warehouse_in: '仓储入库',
  warehouse_store: '仓储存储',
  loading: '装车发车',
  transport: '干线运输',
  transit_in: '枢纽中转入仓',
  transit_out: '枢纽中转出仓',
  last_mile: '末端配送',
  sign: '消费者签收',
}

const alertTypeLabels: Record<string, string> = {
  temperature_anomaly: '温度异常',
  humidity_anomaly: '湿度异常',
  cold_engine_failure: '冷机故障',
  door_open: '车门开启',
  geofence_breach: '电子围栏越界',
  route_deviation: '路线偏离',
}

const alertSeverityLabels: Record<string, string> = {
  normal: '一般',
  severe: '严重',
  critical: '紧急',
}

function getStageName(stage: string) {
  return stageNames[stage] || stage
}

function getAlertTypeLabel(type: string) {
  return alertTypeLabels[type] || type
}

function getAlertSeverityLabel(severity: string) {
  return alertSeverityLabels[severity] || severity
}

function getAlertIcon(severity: string) {
  switch (severity) {
    case 'critical': return '🔴'
    case 'severe': return '🟠'
    default: return '🟡'
  }
}

function formatDateTime(timestamp: string) {
  if (!timestamp) return '-'
  try {
    const dt = new Date(timestamp)
    return dt.toLocaleString('zh-CN', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit',
    })
  } catch {
    return timestamp
  }
}

async function queryWaybill() {
  const id = waybillNo.value.trim()
  if (!id) return
  try {
    const res: any = await customerAPI.queryWaybill(id)
    if (res.error) {
      ElMessage.error(res.error)
      queryResult.value = null
      return
    }
    queryResult.value = res
    curveData.value = null
    alertsData.value = null
    await loadCurveData()
    await loadAlertsData()
  } catch {
    ElMessage.error('运单不存在或暂无数据')
    queryResult.value = null
  }
}

async function loadCurveData() {
  if (!queryResult.value) return
  try {
    const data = await customerAPI.getTemperatureCurve(queryResult.value.waybill_id)
    curveData.value = data
    await nextTick()
    renderChart()
  } catch {
    ElMessage.error('获取温度曲线失败')
  }
}

async function loadAlertsData() {
  if (!queryResult.value) return
  try {
    const data = await customerAPI.getWaybillAlerts(queryResult.value.waybill_id)
    alertsData.value = data
  } catch {
    alertsData.value = null
  }
}

function renderChart() {
  if (!chartRef.value || !curveData.value) return
  if (chartInstance) chartInstance.dispose()
  chartInstance = echarts.init(chartRef.value)

  const points = curveData.value.points || []
  const timestamps = points.map((p: any) => {
    const dt = new Date(p.timestamp)
    return dt.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  })
  const temperatures = points.map((p: any) => p.temperature)
  const humidities = points.map((p: any) => p.humidity)

  const threshold = curveData.value.threshold || {}
  const markLines: any[] = []
  if (threshold.min) {
    markLines.push({
      yAxis: threshold.min,
      lineStyle: { color: '#00a8ff', type: 'dashed', width: 1.5 },
      label: { formatter: `${threshold.min}℃ 下限`, color: '#00a8ff', fontSize: 10 },
    })
  }
  if (threshold.max) {
    markLines.push({
      yAxis: threshold.max,
      lineStyle: { color: '#f59e0b', type: 'dashed', width: 1.5 },
      label: { formatter: `${threshold.max}℃ 上限`, color: '#f59e0b', fontSize: 10 },
    })
  }

  const series: any[] = [{
    name: '温度', type: 'line', data: temperatures, smooth: true,
    lineStyle: { color: '#00a8ff', width: 2.5, shadowBlur: 8, shadowColor: 'rgba(0,168,255,0.15)' },
    itemStyle: { color: '#00a8ff' },
    areaStyle: {
      color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: 'rgba(0,168,255,0.15)' },
        { offset: 1, color: 'rgba(0,168,255,0)' },
      ]),
    },
    markLine: { silent: true, symbol: 'none', data: markLines },
  }]

  if (showHumidity.value) {
    series.push({
      name: '湿度', type: 'line', data: humidities, smooth: true,
      lineStyle: { color: '#8b5cf6', width: 2, type: 'dashed' },
      itemStyle: { color: '#8b5cf6' },
      yAxisIndex: 1,
    })
  }

  const yAxes: any[] = [{
    type: 'value', name: '温度 (°C)',
    nameTextStyle: { color: '#64748b', fontSize: 11 },
    axisLabel: { color: '#94a3b8' },
    splitLine: { lineStyle: { color: '#f1f5f9' } },
  }]

  if (showHumidity.value) {
    yAxes.push({
      type: 'value', name: '湿度 (%)',
      nameTextStyle: { color: '#8b5cf6', fontSize: 11 },
      axisLabel: { color: '#94a3b8' },
      splitLine: { show: false },
    })
  }

  chartInstance.setOption({
    tooltip: {
      trigger: 'axis', backgroundColor: '#fff', borderColor: '#e2e8f0',
      textStyle: { color: '#1e293b', fontSize: 12 },
      formatter: (params: any) => {
        const point = points[params[0].dataIndex]
        let result = `<div style="font-weight:bold;margin-bottom:5px;">${point.timestamp}</div>`
        params.forEach((p: any) => {
          result += `<div>${p.marker} ${p.seriesName}: ${p.value}${p.seriesName === '温度' ? '°C' : '%'}</div>`
        })
        if (point.location) result += `<div style="color:#64748b;font-size:11px;margin-top:5px;">位置: ${point.location}</div>`
        if (point.action) result += `<div style="color:#64748b;font-size:11px;">操作: ${point.action}</div>`
        if (point.stage_name) result += `<div style="color:#64748b;font-size:11px;">环节: ${point.stage_name}</div>`
        return result
      },
    },
    legend: { data: ['温度', '湿度'], top: 0 },
    grid: { left: 60, right: 60, top: 40, bottom: 50 },
    xAxis: {
      type: 'category', data: timestamps,
      axisLabel: { color: '#94a3b8', fontSize: 10, interval: Math.max(1, Math.floor(timestamps.length / 8)) },
      axisLine: { lineStyle: { color: '#e2e8f0' } },
    },
    yAxis: yAxes,
    series,
  })

  window.addEventListener('resize', () => chartInstance?.resize())
}

function toggleHumidity() {
  showHumidity.value = !showHumidity.value
  renderChart()
}

function toggleAnomalyMark() {
  showAnomalyMark.value = !showAnomalyMark.value
  renderChart()
}

async function downloadCertificate(format: string, version: string) {
  if (!queryResult.value) return
  try {
    const res = await customerAPI.getCertificate(queryResult.value.waybill_id, format, version)
    const blob = new Blob([res as any], { type: format === 'html' ? 'text/html' : 'text/plain' })
    const url = URL.createObjectURL(blob)
    const ext = format === 'html' ? 'html' : 'txt'
    const filename = `温控证明_${queryResult.value.waybill_id}_${version}.${ext}`
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('温控证明已下载')
  } catch {
    ElMessage.error('下载失败')
  }
}

async function verifyBlockchain() {
  if (!queryResult.value) return
  try {
    const res: any = await customerAPI.verifyBlockchain(queryResult.value.waybill_id)
    verifyResult.value = res
    showBlockchainVerify.value = true
  } catch {
    ElMessage.error('验证失败')
  }
}

onMounted(() => {})
</script>

<style scoped>
.customer-page { animation: fadeInUp 0.45s ease-out; max-width: 1000px; margin: 0 auto; }

.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; flex-wrap: wrap; gap: 16px; }

.header-left { display: flex; flex-direction: column; gap: 4px; }
.page-title { font-size: 22px; font-weight: 700; color: var(--text-title); margin: 0; }
.page-subtitle { font-size: 13px; color: var(--text-muted); margin: 0; }

.header-right { display: flex; align-items: center; gap: 10px; }

.main-content { display: flex; flex-direction: column; gap: 16px; }

.waybill-block { margin-bottom: 0; }

.info-head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }

.head-left { display: flex; flex-direction: column; gap: 8px; }
.head-left h3 { font-size: 18px; font-weight: 700; color: var(--text-title); margin: 0; }

.code-row { display: flex; gap: 8px; flex-wrap: wrap; }
.waybill-code { font-family: var(--font-mono); font-size: 13px; color: var(--accent); background: var(--accent-bg); padding: 3px 8px; border-radius: 4px; }
.trace-code { font-family: var(--font-mono); font-size: 12px; color: var(--text-muted); background: var(--bg-input); padding: 3px 8px; border-radius: 4px; }

.comp-badge { font-size: 12px; font-weight: 600; padding: 8px 16px; border-radius: 20px; letter-spacing: 0.03em; }
.comp-badge.ok { background: var(--teal-bg); color: var(--teal); border: 1px solid rgba(0,210,160,0.12); }
.comp-badge.fail { background: var(--red-bg); color: var(--red); border: 1px solid rgba(239,68,68,0.12); }

.info-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }

.info-card {
  background: var(--bg-input); border: 1px solid var(--border-light);
  border-radius: var(--radius); padding: 14px; position: relative;
}
.info-card.highlight { border-color: var(--border-focus); background: linear-gradient(135deg, var(--accent-bg), #fff); }

.info-label { display: block; font-size: 10px; color: var(--text-muted); letter-spacing: 0.04em; margin-bottom: 6px; }
.info-value { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.info-value.temp-value { font-family: var(--font-display); font-size: 24px; color: var(--accent); }
.info-value.success { color: var(--teal); }
.info-value.pending { color: var(--amber); }

.sensitivity-tag {
  position: absolute; top: 8px; right: 8px;
  font-size: 10px; padding: 2px 6px; border-radius: 4px;
  background: var(--red-bg); color: var(--red);
}

.info-footer {
  display: flex; gap: 16px; padding-top: 14px;
  border-top: 1px solid var(--border-light);
  flex-wrap: wrap;
}

.footer-item { font-size: 12px; color: var(--text-secondary); }
.footer-item.warning { color: var(--amber); }
.footer-item.success { color: var(--teal); }
.footer-item.time { margin-left: auto; color: var(--text-muted); }

.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.section-title { font-size: 15px; font-weight: 700; color: var(--text-title); margin: 0; }

.section-actions { display: flex; gap: 8px; }

.action-btn {
  padding: 5px 12px; font-size: 11px; border-radius: 4px;
  border: 1px solid var(--border-light); background: transparent;
  color: var(--text-secondary); cursor: pointer; transition: all 0.2s;
}
.action-btn:hover { border-color: var(--accent); color: var(--accent); }

.chart-box { width: 100%; height: 360px; }

.door-events { margin-top: 16px; padding-top: 14px; border-top: 1px solid var(--border-light); }
.door-events h4 { font-size: 13px; font-weight: 600; color: var(--text-secondary); margin: 0 0 10px; }

.door-item {
  display: flex; gap: 12px; padding: 8px 0; font-size: 12px; color: var(--text-secondary);
  border-bottom: 1px solid var(--border-light);
}
.door-item:last-child { border-bottom: none; }
.door-time { font-family: var(--font-mono); }
.door-temp { color: var(--accent); font-weight: 600; }
.door-action { color: var(--amber); margin-left: auto; }

.timeline { position: relative; padding-left: 24px; }
.timeline::before {
  content: ''; position: absolute; left: 8px; top: 0; bottom: 0;
  width: 2px; background: var(--border-light);
}

.timeline-item { position: relative; padding: 12px 0 12px 20px; }
.timeline-item.completed .timeline-dot { background: var(--accent); }

.timeline-dot {
  position: absolute; left: -24px; width: 18px; height: 18px;
  border-radius: 50%; background: var(--border-light);
  display: flex; align-items: center; justify-content: center;
}

.stage-icon { font-size: 12px; }

.timeline-content { display: flex; flex-direction: column; gap: 4px; }

.stage-header { display: flex; justify-content: space-between; align-items: center; }
.stage-name { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.stage-count { font-size: 11px; color: var(--text-muted); font-family: var(--font-mono); }

.stage-details { display: flex; gap: 12px; font-size: 12px; color: var(--text-secondary); }
.stage-pending { font-size: 12px; color: var(--text-muted); }

.alert-card { border-left: 3px solid var(--amber); }

.violations-list { display: flex; flex-direction: column; gap: 12px; }

.violation-item {
  padding: 14px; background: var(--red-bg); border-radius: var(--radius);
  border: 1px solid rgba(239,68,68,0.1);
}

.violation-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.violation-stage { font-size: 13px; font-weight: 600; color: var(--red); }
.violation-time { font-size: 11px; color: var(--text-muted); font-family: var(--font-mono); }

.violation-temp { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.temp-label { font-size: 11px; color: var(--text-muted); }
.temp-value.error { font-family: var(--font-display); font-size: 18px; font-weight: 700; color: var(--red); }
.temp-req { font-size: 11px; color: var(--text-secondary); }

.violation-notes { font-size: 12px; color: var(--text-secondary); margin: 0; line-height: 1.5; }

.alerts-list { display: flex; flex-direction: column; gap: 10px; }

.alert-item {
  display: flex; gap: 12px; padding: 12px; border-radius: var(--radius);
  border: 1px solid var(--border-light); background: var(--bg-input);
}
.alert-item.critical { border-color: rgba(239,68,68,0.3); background: rgba(239,68,68,0.05); }
.alert-item.severe { border-color: rgba(251,146,60,0.3); background: rgba(251,146,60,0.05); }

.alert-icon { font-size: 18px; }

.alert-content { flex: 1; display: flex; flex-direction: column; gap: 4px; }

.alert-header { display: flex; gap: 8px; align-items: center; }
.alert-type { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.alert-severity { font-size: 10px; padding: 2px 6px; border-radius: 4px; }
.alert-severity.critical { background: var(--red-bg); color: var(--red); }
.alert-severity.severe { background: var(--amber-bg); color: var(--amber); }
.alert-severity.normal { background: var(--blue-bg); color: var(--blue); }

.alert-message { font-size: 12px; color: var(--text-secondary); margin: 0; line-height: 1.4; }

.alert-meta { display: flex; gap: 12px; font-size: 11px; color: var(--text-muted); }

.blockchain-info { display: flex; flex-direction: column; gap: 10px; }

.blockchain-item { display: flex; justify-content: space-between; align-items: center; }
.blockchain-item .info-label { font-size: 12px; }
.blockchain-item .info-value { font-size: 13px; font-family: var(--font-mono); color: var(--text-primary); }

.blockchain-details { margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--border-light); }

.download-section { background: var(--bg-card); border-radius: var(--radius-lg); padding: 20px; }

.download-buttons { display: flex; gap: 10px; margin-top: 14px; flex-wrap: wrap; }

.btn-secondary {
  padding: 8px 16px; font-size: 13px; border-radius: var(--radius);
  border: 1px solid var(--border-light); background: transparent;
  color: var(--text-secondary); cursor: pointer; transition: all 0.2s;
}
.btn-secondary:hover { border-color: var(--accent); color: var(--accent); }

.empty-block { text-align: center; padding: 80px 0; color: var(--text-muted); }

.empty-icon { margin-bottom: 20px; }

.empty-block p { font-size: 16px; font-weight: 500; margin: 10px 0 4px; color: var(--text-secondary); }
.empty-block span { font-size: 13px; }

.demo-codes { margin-top: 24px; display: flex; flex-direction: column; align-items: center; gap: 10px; }
.demo-label { font-size: 12px; color: var(--text-muted); }
.demo-code {
  padding: 8px 16px; font-size: 13px; font-family: var(--font-mono);
  border-radius: 4px; border: 1px solid var(--border-light);
  background: var(--bg-input); color: var(--accent); cursor: pointer;
  transition: all 0.2s;
}
.demo-code:hover { border-color: var(--accent); background: var(--accent-bg); }

.verify-content { display: flex; flex-direction: column; gap: 16px; }

.verify-status {
  display: flex; align-items: center; gap: 10px; padding: 15px;
  border-radius: 8px; font-size: 14px; font-weight: 600;
}
.verify-status.success { background: var(--teal-bg); color: var(--teal); }
.verify-status.fail { background: var(--red-bg); color: var(--red); }

.status-icon { font-size: 20px; }

.verify-details { display: flex; flex-direction: column; gap: 10px; }

.verify-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid var(--border-light); }
.verify-label { font-size: 12px; color: var(--text-muted); }
.verify-item code { font-size: 13px; color: var(--accent); font-family: var(--font-mono); }
.verify-item span.success { color: var(--teal); font-weight: 600; }
.verify-item span.fail { color: var(--red); font-weight: 600; }

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 900px) {
  .info-grid { grid-template-columns: repeat(2, 1fr); }
  .download-buttons { flex-direction: column; }
  .page-header { flex-direction: column; align-items: stretch; }
  .header-right { justify-content: flex-end; }
}

@media (max-width: 600px) {
  .info-grid { grid-template-columns: 1fr; }
  .header-right { flex-direction: column; }
  .header-right .el-input { width: 100% !important; }
}
</style>
