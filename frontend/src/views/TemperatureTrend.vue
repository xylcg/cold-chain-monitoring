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
          <span class="stat-v" :class="getTempClass(currentData.temperature)">{{ currentData.temperature }}°C</span>
        </div>
        <div class="stat-it"><span class="stat-l">当前湿度</span><span class="stat-v">{{ currentData.humidity }}%</span></div>
        <div class="stat-it"><span class="stat-l">车门</span><span class="stat-v" :class="{ warn: currentData.door_status }">{{ currentData.door_status ? '开启' : '关闭' }}</span></div>
        <div class="stat-it" v-if="trendData">
          <span class="stat-l">风险等级</span>
          <el-tag :type="getRiskType(trendData.risk_level)" size="large" effect="dark">{{ getRiskLabel(trendData.risk_level) }}</el-tag>
        </div>
      </div>

      <div class="glass-card" v-if="trendData" style="margin-bottom: 14px;">
        <div class="card-head-row">
          <h3>未来30分钟温度预测</h3>
          <span class="card-note">虚线为置信区间 · 深度学习时序预测</span>
        </div>
        <div ref="chartRef" class="chart-box" />
      </div>

      <div class="glass-card" v-if="anomalyResult">
        <h3 class="sec-title">异常检测 · Z-Score 分析</h3>
        <div class="anomaly-block" :class="{ anomaly: anomalyResult.is_anomaly }">
          <div class="an-icon">
            <svg v-if="anomalyResult.is_anomaly" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--red)" stroke-width="2.3" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            <svg v-else width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--teal)" stroke-width="2.3" stroke-linecap="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
          </div>
          <div class="an-body">
            <div class="an-title">{{ anomalyResult.reason }}</div>
            <div class="an-stats" v-if="anomalyResult.is_anomaly">
              <div class="as"><span class="as-l">当前温度</span><span class="as-v danger">{{ anomalyResult.current_temperature }}°C</span></div>
              <div class="as"><span class="as-l">历史均值</span><span class="as-v">{{ anomalyResult.mean_temperature }}°C</span></div>
              <div class="as"><span class="as-l">Z-Score</span><span class="as-v danger">{{ anomalyResult.z_score }}</span></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onUnmounted, nextTick } from 'vue'
import { useAppStore } from '@/stores/app'
import { temperatureAPI } from '@/api'
import { getTempClass, getRiskType, getRiskLabel } from '@/utils'
import * as echarts from 'echarts'

const store = useAppStore()
const selectedDevice = ref('')
const loading = ref(false)
const currentData = ref<any>(null)
const trendData = ref<any>(null)
const anomalyResult = ref<any>(null)
const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

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
  } catch {} finally { loading.value = false }
}

function renderChart() {
  if (!chartRef.value || !trendData.value) return
  if (!chart) chart = echarts.init(chartRef.value)
  const preds = trendData.value.predictions
  const upper = trendData.value.confidence_upper
  const lower = trendData.value.confidence_lower
  const xAxis = preds.map((_: any, i: number) => `+${i + 1}min`)

  chart.setOption({
    tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: '#e2e8f0', textStyle: { color: '#1e293b', fontSize: 12 } },
    legend: { data: ['预测温度', '置信上界', '置信下界'], textStyle: { color: '#64748b' }, bottom: 0 },
    grid: { left: 50, right: 30, top: 20, bottom: 50 },
    xAxis: {
      type: 'category', data: xAxis,
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#94a3b8', fontSize: 10, fontFamily: "'JetBrains Mono', monospace" },
    },
    yAxis: {
      type: 'value', name: '温度 (°C)',
      nameTextStyle: { color: '#64748b', fontSize: 11 },
      axisLabel: { color: '#94a3b8' },
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
            { offset: 0, color: 'rgba(0,168,255,0.08)' },
            { offset: 1, color: 'rgba(0,168,255,0)' },
          ]),
        },
        markLine: {
          silent: true, symbol: 'none',
          data: [
            { yAxis: 8, lineStyle: { color: '#f59e0b', type: 'dashed', width: 1.5 }, label: { formatter: '预警 8°C', color: '#f59e0b', fontSize: 10 } },
            { yAxis: 15, lineStyle: { color: '#ef4444', type: 'dashed', width: 1.5 }, label: { formatter: '危险 15°C', color: '#ef4444', fontSize: 10 } },
          ],
        },
      },
      {
        name: '置信上界', type: 'line', data: upper,
        smooth: true, symbol: 'none',
        lineStyle: { color: '#94a3b8', type: 'dashed', width: 1, opacity: 0.4 },
        areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1, [{ offset:0, color:'rgba(0,168,255,0.03)' }, { offset:1, color:'rgba(0,168,255,0)' }]) },
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

.card-head-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.card-head-row h3 { font-size: 15px; font-weight: 700; color: var(--text-title); }
.card-note { font-size: 11px; color: var(--text-muted); font-style: italic; }

.chart-box { width: 100%; height: 360px; }

.sec-title { font-size: 15px; font-weight: 700; color: var(--text-title); margin-bottom: 14px; }

.anomaly-block {
  display: flex; gap: 14px; padding: 18px; border-radius: var(--radius);
  background: var(--teal-bg); border: 1px solid rgba(0,210,160,0.12);
}
.anomaly-block.anomaly { background: var(--red-bg); border-color: rgba(239,68,68,0.12); }
.an-icon { flex-shrink: 0; }
.an-title { font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 12px; }
.an-stats { display: flex; gap: 20px; }
.as { display: flex; flex-direction: column; gap: 2px; }
.as-l { font-size: 10px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.03em; }
.as-v { font-family: var(--font-mono); font-size: 16px; font-weight: 600; color: var(--text-primary); }
.as-v.danger { color: var(--red); }

@media (max-width: 800px) { .stat-row { grid-template-columns: repeat(2,1fr); } }
</style>
