<template>
  <div class="temp-trend">
    <div class="page-header">
      <h2 class="page-title">温度趋势预测</h2>
      <div class="header-right">
        <el-select v-model="selectedDevice" placeholder="选择设备..." style="width: 220px" filterable>
          <el-option v-for="d in store.devices" :key="d.device_id" :label="d.device_id" :value="d.device_id" />
        </el-select>
        <button class="btn-primary" @click="fetchTrend" :disabled="loading">
          {{ loading ? '加载中...' : '刷新数据' }}
        </button>
      </div>
    </div>

    <div v-if="!selectedDevice" class="empty-block">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" opacity="0.2">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
      </svg>
      <p>请选择一个设备查看温度趋势与预测</p>
      <span>基于深度学习的时间序列预测，支持未来30分钟温度预测</span>
    </div>

    <div v-else>
      <div class="stat-row" v-if="currentData">
        <div class="stat-it">
          <span class="stat-l">当前温度</span>
          <div class="stat-v-row">
            <span class="stat-v" :class="getTempClass(currentData.temperature)">{{ currentData.temperature }}°C</span>
            <span class="temp-trend-icon" :class="tempTrendDir" :title="tempTrendLabel">{{ tempTrendIcon }}</span>
          </div>
          <span class="stat-sub" v-if="trendData && trendData.target_temperature">目标: {{ trendData.target_temperature }}°C</span>
        </div>
        <div class="stat-it">
          <span class="stat-l">当前湿度</span>
          <span class="stat-v">{{ currentData.humidity }}%</span>
          <span class="stat-sub">适宜范围 60~80%</span>
        </div>
        <div class="stat-it">
          <span class="stat-l">车门状态</span>
          <span class="stat-v" :class="{ warn: currentData.door_status }">{{ currentData.door_status ? '开启' : '关闭' }}</span>
          <span class="stat-sub" :class="{ 'text-danger': currentData.door_status }">{{ currentData.door_status ? '⚠️ 超时开启风险' : '✓ 密封正常' }}</span>
        </div>
        <div class="stat-it" v-if="trendData">
          <span class="stat-l">风险等级</span>
          <el-tag :type="getRiskType(trendData.risk_level)" size="large" effect="dark">{{ getRiskLabel(trendData.risk_level) }}</el-tag>
          <span class="stat-sub" v-if="trendData.model_info">模型: {{ trendData.model_info }}</span>
        </div>
      </div>

      <div class="glass-card" v-if="trendData" style="margin-bottom: 14px;">
        <div class="card-head-row">
          <h3>未来{{ forecastHorizon }}分钟温度预测</h3>
          <span class="card-note">虚线为置信区间 · 深度学习时序预测 (LSTM)</span>
        </div>
        <div ref="chartRef" class="chart-box" />
        <!-- 预测摘要 -->
        <div class="forecast-summary" v-if="trendData.predictions && trendData.predictions.length">
          <div class="fs-item">
            <span class="fs-label">预测终点温度</span>
            <span class="fs-value" :class="getTempClass(lastPredTemp)">{{ lastPredTemp }}°C</span>
          </div>
          <div class="fs-item">
            <span class="fs-label">温度变化趋势</span>
            <span class="fs-value" :class="predChange >= 0 ? 'trend-up' : 'trend-down'">{{ predChange >= 0 ? '↑ 升温' : '↓ 降温' }} {{ Math.abs(predChange).toFixed(1) }}°C</span>
          </div>
          <div class="fs-item">
            <span class="fs-label">置信区间宽度</span>
            <span class="fs-value">{{ confidenceWidth.toFixed(1) }}°C</span>
          </div>
          <div class="fs-item">
            <span class="fs-label">是否超预警线</span>
            <span class="fs-value" :class="willExceedWarning ? 'text-danger' : 'text-safe'">{{ willExceedWarning ? '是 ⚠️' : '否 ✓' }}</span>
          </div>
        </div>
      </div>

      <div class="glass-card" v-if="anomalyResult">
        <h3 class="sec-title">异常检测 · Z-Score 统计分析</h3>
        <div class="anomaly-block" :class="{ anomaly: anomalyResult.is_anomaly }">
          <div class="an-icon">
            <svg v-if="anomalyResult.is_anomaly" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--red)" stroke-width="2.3" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            <svg v-else width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--teal)" stroke-width="2.3" stroke-linecap="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
          </div>
          <div class="an-body">
            <div class="an-title">{{ anomalyResult.reason || '温度处于正常范围' }}</div>
            <div class="an-stats">
              <div class="as"><span class="as-l">当前温度</span><span class="as-v" :class="{ danger: anomalyResult.is_anomaly }">{{ anomalyResult.current_temperature ?? currentData?.temperature ?? '-' }}°C</span></div>
              <div class="as"><span class="as-l">历史均值</span><span class="as-v">{{ anomalyResult.mean_temperature ?? '-' }}°C</span></div>
              <div class="as"><span class="as-l">标准差</span><span class="as-v">{{ anomalyResult.std_temperature ?? '-' }}°C</span></div>
              <div class="as"><span class="as-l">Z-Score</span><span class="as-v" :class="{ danger: Math.abs(anomalyResult.z_score || 0) > 2 }">{{ anomalyResult.z_score ?? '-' }}</span></div>
              <div class="as"><span class="as-l">样本量</span><span class="as-v">{{ anomalyResult.sample_size ?? '-' }} 条</span></div>
              <div class="as"><span class="as-l">检测时间</span><span class="as-v as-time">{{ anomalyResult.check_time || '刚刚' }}</span></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onUnmounted, nextTick } from 'vue'
import { useAppStore } from '@/stores/app'
import { temperatureAPI } from '@/api'
import { ElMessage } from 'element-plus'
import { getTempClass, getRiskType, getRiskLabel } from '@/utils'
import * as echarts from 'echarts'

const store = useAppStore()
const selectedDevice = ref('')
const loading = ref(false)
const currentData = ref<any>(null)
const trendData = ref<any>(null)
const anomalyResult = ref<any>(null)
const chartRef = ref<HTMLElement>()
const forecastHorizon = ref(30)
let chart: echarts.ECharts | null = null

// 温度趋势方向（基于预测数据）
const tempTrendDir = computed(() => {
  if (!trendData.value?.predictions || trendData.value.predictions.length < 2) return ''
  const preds = trendData.value.predictions
  const first = Number(preds[0])
  const last = Number(preds[preds.length - 1])
  if (Math.abs(last - first) < 0.3) return 'stable'
  return last > first ? 'up' : 'down'
})
const tempTrendIcon = computed(() => {
  const m: Record<string, string> = { up: '↑', down: '↓', stable: '→' }
  return m[tempTrendDir.value] || '→'
})
const tempTrendLabel = computed(() => {
  const m: Record<string, string> = { up: '升温趋势', down: '降温趋势', stable: '温度稳定' }
  return m[tempTrendDir.value] || ''
})

// 预测摘要计算属性
const lastPredTemp = computed(() => {
  if (!trendData.value?.predictions?.length) return 0
  const arr = trendData.value.predictions
  return Number(arr[arr.length - 1])
})
const predChange = computed(() => {
  if (!trendData.value?.predictions?.length || !currentData.value) return 0
  return lastPredTemp.value - Number(currentData.value.temperature)
})
const confidenceWidth = computed(() => {
  if (!trendData.value?.confidence_upper?.length || !trendData.value?.confidence_lower?.length) return 0
  const upper = trendData.value.confidence_upper
  const lower = trendData.value.confidence_lower
  // 取末端置信区间宽度
  return Number(upper[upper.length - 1]) - Number(lower[lower.length - 1])
})
const willExceedWarning = computed(() => {
  if (!trendData.value?.predictions) return false
  const WARNING_THRESHOLD = 8 // 预警线 8°C（冷藏），冷冻场景用 -10°C 作为下界
  return trendData.value.predictions.some((p: any) => Number(p) > WARNING_THRESHOLD)
})

async function fetchTrend() {
  if (!selectedDevice.value) return
  loading.value = true
  try {
    const [current, trend, anomaly] = await Promise.all([
      temperatureAPI.getCurrent(selectedDevice.value),
      temperatureAPI.getTrend(selectedDevice.value, 30),
      temperatureAPI.checkAnomaly(selectedDevice.value),
    ])
    currentData.value = current
    trendData.value = trend
    anomalyResult.value = anomaly
    await nextTick()
    renderChart()
  } catch {
    ElMessage.warning('获取温度趋势失败')
  } finally { loading.value = false }
}

function renderChart() {
  if (!chartRef.value || !trendData.value) return
  if (!chart) chart = echarts.init(chartRef.value)
  const preds = trendData.value.predictions
  const upper = trendData.value.confidence_upper
  const lower = trendData.value.confidence_lower
  const xAxis = preds.map((_: any, i: number) => `+${i + 1}min`)

  // 动态计算 Y 轴范围：基于数据最小/最大值留出余量
  const allValues = [...preds, ...upper, ...lower].map(Number).filter(v => isFinite(v))
  const dataMin = Math.min(...allValues)
  const dataMax = Math.max(...allValues)
  const padding = Math.max(Math.abs(dataMax - dataMin) * 0.15, 2)
  const yMin = Math.floor((dataMin - padding) / 5) * 5
  const yMax = Math.ceil((dataMax + padding) / 5) * 5

  // 当前温度值（用于标记线）
  const currentTemp = currentData.value ? Number(currentData.value.temperature) : null

  chart.setOption({
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#fff',
      borderColor: '#e2e8f0',
      textStyle: { color: '#1e293b', fontSize: 12 },
      formatter(params: any) {
        let s = `<b>${(params[0]?.axisValue || '')}</b>`
        params.forEach((p: any) => {
          s += `<br/>${p.marker} ${p.seriesName}: <b>${p.data}°C</b>`
        })
        return s
      },
    },
    legend: { data: ['预测温度', '置信上界', '置信下界'], textStyle: { color: '#64748b' }, bottom: 0 },
    grid: { left: 50, right: 30, top: 24, bottom: 50 },
    xAxis: {
      type: 'category', data: xAxis,
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#94a3b8', fontSize: 10, fontFamily: "'JetBrains Mono', monospace" },
    },
    yAxis: {
      type: 'value', name: '温度 (°C)',
      min: yMin, max: yMax,
      nameTextStyle: { color: '#64748b', fontSize: 11 },
      axisLabel: { color: '#94a3b8', formatter: '{value}°C' },
      splitLine: { lineStyle: { color: '#f1f5f9' } },
    },
    series: [
      {
        name: '预测温度', type: 'line', data: preds,
        smooth: true, symbol: 'circle', symbolSize: 5,
        lineStyle: { color: '#00a8ff', width: 2.5, shadowBlur: 8, shadowColor: 'rgba(0,168,255,0.2)' },
        itemStyle: { color: '#00a8ff' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(0,168,255,0.10)' },
            { offset: 1, color: 'rgba(0,168,255,0)' },
          ]),
        },
        markLine: {
          silent: true, symbol: 'none',
          label: { fontSize: 10 },
          data: [
            ...(currentTemp != null ? [{
              yAxis: currentTemp,
              lineStyle: { color: '#6366f1', type: 'solid', width: 1.5 },
              label: { formatter: `当前 ${currentTemp}°C`, color: '#6366f1' },
            }] : []),
            { yAxis: 8, lineStyle: { color: '#f59e0b', type: 'dashed', width: 1.5 }, label: { formatter: '预警 8°C', color: '#f59e0b' } },
            { yAxis: 15, lineStyle: { color: '#ef4444', type: 'dashed', width: 1.5 }, label: { formatter: '危险 15°C', color: '#ef4444' } },
          ],
        },
      },
      {
        name: '置信上界', type: 'line', data: upper,
        smooth: true, symbol: 'none',
        lineStyle: { color: '#94a3b8', type: 'dashed', width: 1, opacity: 0.4 },
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(0,168,255,0.04)' }, { offset: 1, color: 'rgba(0,168,255,0)' }]) },
      },
      {
        name: '置信下界', type: 'line', data: lower,
        smooth: true, symbol: 'none',
        lineStyle: { color: '#94a3b8', type: 'dashed', width: 1, opacity: 0.4 },
      },
    ],
  }, true)
}

watch(selectedDevice, () => { fetchTrend() })
onUnmounted(() => { chart?.dispose() })
</script>

<style scoped>
.temp-trend { animation: fadeInUp 0.45s ease-out; }

.header-right { display: flex; align-items: center; gap: 10px; }

.empty-block {
  text-align: center; padding: 80px 0; color: var(--text-muted);
}
.empty-block p { font-size: 15px; font-weight: 500; margin: 12px 0 4px; color: var(--text-secondary); }
.empty-block span { font-size: 12px; }

.stat-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 16px; }
.stat-it {
  background: var(--bg-card); backdrop-filter: var(--blur-card); -webkit-backdrop-filter: var(--blur-card);
  border: 1px solid var(--border-card); border-radius: var(--radius-lg); padding: 16px 18px;
  text-align: center; box-shadow: var(--shadow-sm);
}
.stat-l { display: block; font-size: 10px; color: var(--text-muted); letter-spacing: 0.04em; margin-bottom: 6px; }
.stat-v { font-family: var(--font-display); font-size: 22px; font-weight: 800; color: var(--text-title); }
.stat-v.warn { color: var(--amber); }
.stat-v-row { display: flex; align-items: center; justify-content: center; gap: 6px; }
.temp-trend-icon { font-size: 16px; font-weight: 700; }
.temp-trend-icon.up { color: #ef4444; }
.temp-trend-icon.down { color: #00a8ff; }
.temp-trend-icon.stable { color: var(--teal); }
.stat-sub { display: block; font-size: 10px; color: var(--text-muted); margin-top: 4px; }
.stat-sub.text-danger { color: var(--red); font-weight: 600; }

.card-head-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.card-head-row h3 { font-size: 15px; font-weight: 700; color: var(--text-title); }
.card-note { font-size: 11px; color: var(--text-muted); font-style: italic; }

.chart-box { width: 100%; height: 360px; }

/* 预测摘要 */
.forecast-summary {
  display: flex; gap: 12px; padding: 14px 18px;
  background: rgba(0,168,255,0.03); border-top: 1px solid var(--border-card);
  border-radius: 0 0 var(--radius) var(--radius);
  margin: 0 -20px -20px; flex-wrap: wrap;
}
.fs-item { display: flex; flex-direction: column; gap: 2px; min-width: 100px; }
.fs-label { font-size: 10px; color: var(--text-muted); letter-spacing: 0.03em; }
.fs-value { font-family: var(--font-mono); font-size: 13px; font-weight: 700; color: var(--text-title); }
.trend-up { color: #ef4444; }
.trend-down { color: #00a8ff; }
.text-danger { color: var(--red) !important; }
.text-safe { color: var(--teal) !important; }

.sec-title { font-size: 15px; font-weight: 700; color: var(--text-title); margin-bottom: 14px; }

.anomaly-block {
  display: flex; gap: 14px; padding: 18px; border-radius: var(--radius);
  background: var(--teal-bg); border: 1px solid rgba(0,210,160,0.12);
}
.anomaly-block.anomaly { background: var(--red-bg); border-color: rgba(239,68,68,0.12); }
.an-icon { flex-shrink: 0; padding-top: 2px; }
.an-title { font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 12px; }
.an-stats { display: flex; gap: 20px; flex-wrap: wrap; }
.as { display: flex; flex-direction: column; gap: 2px; }
.as-l { font-size: 10px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.03em; }
.as-v { font-family: var(--font-mono); font-size: 15px; font-weight: 600; color: var(--text-primary); }
.as-v.danger { color: var(--red); }
.as-time { font-size: 13px !important; font-weight: 400 !important; color: var(--text-muted) !important; }

@media (max-width: 800px) { .stat-row { grid-template-columns: repeat(2,1fr); } .forecast-summary { gap: 8px; } .an-stats { gap: 12px; } }
</style>
