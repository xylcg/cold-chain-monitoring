<template>
  <div class="customer-page">
    <div class="page-header">
      <h2 class="page-title">客户温控查询服务</h2>
      <div class="header-right">
        <el-input v-model="waybillNo" placeholder="输入运单号查询..." clearable style="width: 260px" @keyup.enter="queryWaybill">
          <template #prefix>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          </template>
        </el-input>
        <button class="btn-primary" @click="queryWaybill">查询</button>
      </div>
    </div>

    <div v-if="waybillInfo" class="glass-card waybill-block">
      <div class="info-head">
        <h3>运单 {{ waybillInfo.waybill_id }}</h3>
        <span class="comp-badge" :class="waybillInfo.is_compliant ? 'ok' : 'fail'">
          {{ waybillInfo.is_compliant ? '温控达标' : '温度异常' }}
        </span>
      </div>

      <div class="info-grid">
        <div class="icard"><span class="icl">货物类型</span><span class="icv">{{ waybillInfo.cargo_type }}</span></div>
        <div class="icard"><span class="icl">温度要求</span><span class="icv">{{ waybillInfo.temperature_requirement }}</span></div>
        <div class="icard icard-hl">
          <span class="icl">当前温度</span>
          <span class="icv ic-temp">{{ waybillInfo.current_temperature }}°C</span>
        </div>
        <div class="icard"><span class="icl">温度范围</span><span class="icv">{{ waybillInfo.temperature_range }}</span></div>
        <div class="icard"><span class="icl">发货地</span><span class="icv">{{ waybillInfo.origin }}</span></div>
        <div class="icard"><span class="icl">目的地</span><span class="icv">{{ waybillInfo.destination }}</span></div>
        <div class="icard"><span class="icl">发车时间</span><span class="icv mono">{{ formatDateTime(waybillInfo.departure_time) }}</span></div>
        <div class="icard"><span class="icl">预计到达</span><span class="icv mono">{{ formatDateTime(waybillInfo.estimated_arrival) }}</span></div>
      </div>

      <div class="info-act">
        <el-button type="primary" @click="downloadCertificate">下载温度证明</el-button>
        <el-button @click="toggleCurve">{{ showCurve ? '隐藏温度曲线' : '查看温度曲线' }}</el-button>
      </div>
    </div>

    <div v-if="showCurve && curveData" class="glass-card">
      <h3>全程温度曲线</h3>
      <div ref="chartRef" class="chart-box"></div>
      <div v-if="curveData.door_events?.length" class="door-block">
        <h4>开门事件记录</h4>
        <div v-for="(evt, idx) in curveData.door_events" :key="idx" class="door-it">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--amber)" stroke-width="2" stroke-linecap="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
          <span>{{ formatDateTime(evt.timestamp) }}</span>
          <span>温度 {{ evt.temperature }}°C</span>
        </div>
      </div>
    </div>

    <div v-if="myOrders.length > 0" class="glass-card">
      <h3>我的运单</h3>
      <div class="order-list">
        <div v-for="order in myOrders" :key="order.waybill_id" class="order-row" @click="waybillNo = order.waybill_id; queryWaybill()">
          <div class="or-top">
            <code class="oid">{{ order.waybill_id }}</code>
            <span class="ostat" :class="order.is_compliant ? 'ok' : 'fail'">{{ order.is_compliant ? '正常' : '异常' }}</span>
          </div>
          <div class="or-bot">
            <span>{{ order.cargo_type }}</span>
            <span>{{ order.origin }} → {{ order.destination }}</span>
            <span class="otemp">{{ order.current_temperature }}°C</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="!waybillInfo && myOrders.length === 0" class="empty-block">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" opacity="0.2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
      <p>输入运单号查询冷链温度信息</p>
      <span>扫码或输入运单号，即可查看货物全程温控数据</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { customerAPI } from '@/api'
import { formatDateTime } from '@/utils'
import * as echarts from 'echarts'

const waybillNo = ref('')
const waybillInfo = ref<any>(null)
const curveData = ref<any>(null)
const showCurve = ref(false)
const myOrders = ref<any[]>([])
const chartRef = ref<HTMLElement>()
let chartInstance: any = null

async function queryWaybill() {
  const id = waybillNo.value.trim()
  if (!id) return
  try {
    const info = await customerAPI.queryWaybill(id)
    waybillInfo.value = info; showCurve.value = false; curveData.value = null
  } catch { ElMessage.error('运单不存在或暂无数据'); waybillInfo.value = null }
}

async function loadCurveData() {
  if (!waybillInfo.value) return
  try {
    const data = await customerAPI.getTemperatureCurve(waybillInfo.value.waybill_id)
    curveData.value = data; await nextTick(); renderChart()
  } catch { ElMessage.error('获取温度曲线失败') }
}

function renderChart() {
  if (!chartRef.value || !curveData.value) return
  if (chartInstance) chartInstance.dispose()
  chartInstance = echarts.init(chartRef.value)

  const timestamps = curveData.value.timestamps.map((t: string) =>
    new Date(t).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  )
  chartInstance.setOption({
    tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: '#e2e8f0', textStyle: { color: '#1e293b', fontSize: 12 } },
    grid: { left: 50, right: 20, top: 20, bottom: 40 },
    xAxis: {
      type: 'category', data: timestamps,
      axisLabel: { color: '#94a3b8', fontSize: 10, interval: Math.max(1, Math.floor(timestamps.length / 6)) },
      axisLine: { lineStyle: { color: '#e2e8f0' } },
    },
    yAxis: {
      type: 'value', name: '温度 (°C)',
      nameTextStyle: { color: '#64748b', fontSize: 11 },
      axisLabel: { color: '#94a3b8' },
      splitLine: { lineStyle: { color: '#f1f5f9' } },
    },
    series: [{
      name: '温度', type: 'line', data: curveData.value.temperatures, smooth: true,
      lineStyle: { color: '#00a8ff', width: 2.5, shadowBlur: 8, shadowColor: 'rgba(0,168,255,0.15)' },
      itemStyle: { color: '#00a8ff' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0,0,0,1, [
          { offset: 0, color: 'rgba(0,168,255,0.1)' },
          { offset: 1, color: 'rgba(0,168,255,0)' },
        ]),
      },
      markLine: {
        silent: true, symbol: 'none',
        data: [{ yAxis: 8, lineStyle: { color: '#f59e0b', type: 'dashed', width: 1.5 }, label: { formatter: '8°C 警戒线', color: '#f59e0b', fontSize: 10 } }],
      },
    }],
  })
  window.addEventListener('resize', () => chartInstance?.resize())
}

function toggleCurve() { showCurve.value = !showCurve.value; if (showCurve.value && !curveData.value) loadCurveData() }

async function downloadCertificate() {
  if (!waybillInfo.value) return
  try {
    const res = await customerAPI.getCertificate(waybillInfo.value.waybill_id)
    const blob = new Blob([res as any], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = `temperature_certificate_${waybillInfo.value.waybill_id}.txt`; a.click()
    URL.revokeObjectURL(url); ElMessage.success('温度证明已下载')
  } catch { ElMessage.error('下载失败') }
}

async function loadMyOrders() { try { const res = await customerAPI.getMyOrders(); myOrders.value = res.orders || [] } catch {} }

onMounted(loadMyOrders)
</script>

<style scoped>
.customer-page { animation: fadeInUp 0.45s ease-out; }

.header-right { display: flex; align-items: center; gap: 10px; }

.waybill-block { margin-bottom: 16px; }

.info-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; }
.info-head h3 { font-size: 16px; font-weight: 700; color: var(--text-title); }
.comp-badge { font-size: 12px; font-weight: 600; padding: 6px 14px; border-radius: 20px; letter-spacing: 0.03em; }
.comp-badge.ok { background: var(--teal-bg); color: var(--teal); border: 1px solid rgba(0,210,160,0.12); }
.comp-badge.fail { background: var(--red-bg); color: var(--red); border: 1px solid rgba(239,68,68,0.12); }

.info-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 10px; margin-bottom: 18px; }
.icard { background: var(--bg-input); border: 1px solid var(--border-light); border-radius: var(--radius); padding: 12px 14px; }
.icard-hl { border-color: var(--border-focus); }
.icl { display: block; font-size: 10px; color: var(--text-muted); letter-spacing: 0.04em; margin-bottom: 4px; }
.icv { font-size: 14px; font-weight: 600; color: var(--text-primary); }
.ic-temp { font-family: var(--font-display); font-size: 20px; color: var(--accent); }
.mono { font-family: var(--font-mono); font-size: 12px; color: var(--text-secondary); }

.info-act { display: flex; gap: 10px; }

.chart-box { width: 100%; height: 340px; margin-bottom: 16px; }

.door-block { padding-top: 14px; border-top: 1px solid var(--border-light); }
.door-block h4 { font-size: 13px; font-weight: 600; color: var(--text-secondary); margin-bottom: 8px; }
.door-it { display: flex; align-items: center; gap: 8px; padding: 4px 0; font-size: 12px; color: var(--text-secondary); font-family: var(--font-mono); }

.order-list { display: flex; flex-direction: column; gap: 8px; }
.order-row {
  padding: 12px 14px; border: 1px solid var(--border-light); border-radius: var(--radius);
  cursor: pointer; transition: all 0.2s;
}
.order-row:hover { border-color: var(--border-focus); background: var(--accent-bg); }
.or-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.oid { font-family: var(--font-mono); font-size: 13px; color: var(--accent); font-weight: 500; }
.ostat { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 20px; }
.ostat.ok { background: var(--teal-bg); color: var(--teal); }
.ostat.fail { background: var(--red-bg); color: var(--red); }
.or-bot { display: flex; gap: 14px; font-size: 12px; color: var(--text-muted); }
.otemp { font-family: var(--font-mono); color: var(--accent); margin-left: auto; }

.empty-block { text-align: center; padding: 60px 0; color: var(--text-muted); }
.empty-block p { font-size: 15px; font-weight: 500; margin: 10px 0 4px; color: var(--text-secondary); }
.empty-block span { font-size: 12px; }

@media (max-width:800px) { .info-grid { grid-template-columns: repeat(2,1fr); } }
</style>
