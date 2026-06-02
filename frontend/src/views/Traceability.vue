<template>
  <div class="trace-page">
    <div class="page-header">
      <h2 class="page-title">全程冷链追溯链</h2>
      <div class="header-right">
        <el-input v-model="searchKeyword" placeholder="输入运单号搜索..." clearable style="width: 260px" @keyup.enter="searchTrace">
          <template #prefix>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          </template>
        </el-input>
        <button class="btn-primary" @click="searchTrace">查询</button>
      </div>
    </div>

    <div class="stats-row" v-if="stats">
      <div class="stat-it">
        <div class="stat-num">{{ stats.total_waybills }}</div>
        <div class="stat-lab">总运单</div>
      </div>
      <div class="stat-it">
        <div class="stat-num">{{ stats.total_records }}</div>
        <div class="stat-lab">追溯记录</div>
      </div>
      <div class="stat-it">
        <div class="stat-num teal">{{ stats.compliance_rate }}%</div>
        <div class="stat-lab">温控达标率</div>
      </div>
      <div class="stat-it">
        <div class="stat-num" :class="stats.violation_waybills > 0 ? 'red' : 'teal'">{{ stats.violation_waybills }}</div>
        <div class="stat-lab">违规运单</div>
      </div>
    </div>

    <div v-if="traceResult" class="glass-card">
      <div class="detail-top">
        <div>
          <h3>运单 {{ traceResult.waybill_id }}</h3>
          <div class="detail-info">
            <span>范围 {{ traceResult.temperature_summary.min }}°C ~ {{ traceResult.temperature_summary.max }}°C</span>
            <span>平均 {{ traceResult.temperature_summary.avg }}°C</span>
            <span>{{ traceResult.stages }} 个环节</span>
          </div>
        </div>
        <span class="comp-badge" :class="traceResult.is_compliant ? 'ok' : 'fail'">
          {{ traceResult.is_compliant ? '温控达标' : '存在违规' }}
        </span>
      </div>

      <div class="timeline">
        <div v-for="(record, idx) in traceResult.records" :key="record.id" class="tl-item">
          <div class="tl-dot" :class="{ active: idx === 0, violation: record.temperature > 8 || record.temperature < -25 }"></div>
          <div class="tl-content">
            <div class="tl-head">
              <span class="tl-stage">{{ record.stage }}</span>
              <span class="tl-time">{{ formatDateTime(record.timestamp) }}</span>
            </div>
            <div class="tl-rows">
              <div class="tl-r"><span class="tll">位置</span><span class="tlv">{{ record.location }}</span></div>
              <div class="tl-r"><span class="tll">温度</span><span class="tlv" :class="{ warn: record.temperature > 8 || record.temperature < -25 }">{{ record.temperature }}°C</span></div>
              <div class="tl-r" v-if="record.humidity"><span class="tll">湿度</span><span class="tlv">{{ record.humidity }}%</span></div>
              <div class="tl-r" v-if="record.operator"><span class="tll">操作人</span><span class="tlv">{{ record.operator }}</span></div>
              <div class="tl-r" v-if="record.notes"><span class="tll">备注</span><span class="tlv">{{ record.notes }}</span></div>
            </div>
          </div>
        </div>
      </div>

      <div class="detail-act">
        <el-button type="primary" @click="downloadReport">下载追溯报告</el-button>
      </div>
    </div>

    <div v-if="searchResults.length > 0 && !traceResult" class="glass-card">
      <h3>搜索结果</h3>
      <div v-for="wb in searchResults" :key="wb.waybill_id" class="result-row" @click="viewTrace(wb.waybill_id)">
        <div class="result-top">
          <code class="rid">{{ wb.waybill_id }}</code>
          <span class="rtag">{{ wb.stages }} 个环节</span>
        </div>
        <div class="result-bot">
          <span>{{ formatDateTime(wb.first_record) }}</span>
          <span>平均 {{ wb.avg_temperature }}°C</span>
        </div>
      </div>
    </div>

    <div v-if="!traceResult && searchResults.length === 0 && !searchKeyword" class="empty-block">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" opacity="0.2">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/>
      </svg>
      <p>输入运单号查询全程冷链追溯记录</p>
      <span>支持按运单号搜索，查看从产地到消费者全链路温控数据</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { traceabilityAPI } from '@/api'
import { formatDateTime } from '@/utils'

const searchKeyword = ref('')
const traceResult = ref<any>(null)
const searchResults = ref<any[]>([])
const stats = ref<any>(null)

async function searchTrace() {
  const kw = searchKeyword.value.trim()
  if (!kw) { traceResult.value = null; searchResults.value = []; return }
  try {
    try { const res = await traceabilityAPI.getRecords(kw); traceResult.value = res; searchResults.value = []; return } catch {}
    const res = await traceabilityAPI.search(kw); searchResults.value = res.waybills || []; traceResult.value = null
    if (searchResults.value.length === 0) ElMessage.info('未找到匹配的运单')
  } catch { ElMessage.error('查询失败') }
}

function viewTrace(waybillId: string) { searchKeyword.value = waybillId; searchTrace() }

async function downloadReport() {
  if (!traceResult.value) return
  try {
    const res = await traceabilityAPI.getReport(traceResult.value.waybill_id, 'text')
    const blob = new Blob([res as any], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = `trace_report_${traceResult.value.waybill_id}.txt`; a.click()
    URL.revokeObjectURL(url); ElMessage.success('报告已下载')
  } catch { ElMessage.error('下载失败') }
}

async function loadStats() { try { stats.value = await traceabilityAPI.getStats() } catch {} }

onMounted(loadStats)
</script>

<style scoped>
.trace-page { animation: fadeInUp 0.45s ease-out; }

.header-right { display: flex; align-items: center; gap: 10px; }

.stats-row { display: grid; grid-template-columns: repeat(4,1fr); gap: 12px; margin-bottom: 20px; }
.stat-it {
  background: var(--bg-card); backdrop-filter: var(--blur-card); -webkit-backdrop-filter: var(--blur-card);
  border: 1px solid var(--border-card); border-radius: var(--radius-lg);
  padding: 16px; text-align: center; box-shadow: var(--shadow-sm);
}
.stat-num { font-family: var(--font-display); font-size: 28px; font-weight: 800; color: var(--text-title); }
.stat-num.teal { color: var(--teal); }
.stat-num.red { color: var(--red); }
.stat-lab { font-size: 11px; color: var(--text-muted); margin-top: 4px; }

.detail-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px; }
.detail-top h3 { font-size: 16px; font-weight: 700; color: var(--text-title); margin-bottom: 4px; }
.detail-info { display: flex; gap: 14px; font-size: 12px; color: var(--text-secondary); font-family: var(--font-mono); }
.comp-badge { font-size: 12px; font-weight: 600; padding: 6px 14px; border-radius: 20px; letter-spacing: 0.03em; }
.comp-badge.ok { background: var(--teal-bg); color: var(--teal); border: 1px solid rgba(0,210,160,0.12); }
.comp-badge.fail { background: var(--red-bg); color: var(--red); border: 1px solid rgba(239,68,68,0.12); }

/* Timeline */
.timeline { position: relative; padding-left: 28px; margin-bottom: 20px; }
.timeline::before { content: ''; position: absolute; left: 8px; top: 0; bottom: 0; width: 1px; background: var(--border-light); }
.tl-item { position: relative; padding-bottom: 16px; }
.tl-item:last-child { padding-bottom: 0; }
.tl-dot {
  position: absolute; left: -24px; top: 8px;
  width: 12px; height: 12px; border-radius: 50%;
  background: var(--accent); border: 3px solid #fff;
  box-shadow: 0 0 6px var(--accent-glow); z-index: 1;
}
.tl-dot.active { background: var(--teal); box-shadow: 0 0 8px rgba(0,210,160,0.3); }
.tl-dot.violation { background: var(--red); box-shadow: 0 0 8px rgba(239,68,68,0.3); }
.tl-content {
  background: var(--bg-input); border: 1px solid var(--border-light);
  border-radius: var(--radius); padding: 12px 14px;
}
.tl-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.tl-stage { font-size: 13px; font-weight: 700; color: var(--accent); }
.tl-time { font-size: 11px; color: var(--text-muted); font-family: var(--font-mono); }
.tl-rows { display: flex; flex-wrap: wrap; gap: 10px; }
.tl-r { display: flex; align-items: center; gap: 4px; font-size: 12px; }
.tll { color: var(--text-muted); }
.tlv { color: var(--text-secondary); }
.tlv.warn { color: var(--red); font-weight: 600; }

.detail-act { display: flex; justify-content: flex-end; }

/* Search results */
.result-row {
  padding: 12px 14px; border: 1px solid var(--border-light); border-radius: var(--radius);
  margin-bottom: 8px; cursor: pointer; transition: all 0.2s;
}
.result-row:hover { border-color: var(--border-focus); background: var(--accent-bg); }
.result-row:last-child { margin-bottom: 0; }
.result-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.rid { font-family: var(--font-mono); font-size: 13px; color: var(--accent); font-weight: 500; }
.rtag { font-size: 11px; background: var(--bg-input); padding: 2px 8px; border-radius: 20px; color: var(--text-muted); }
.result-bot { display: flex; gap: 14px; font-size: 12px; color: var(--text-muted); font-family: var(--font-mono); }

.empty-block { text-align: center; padding: 60px 0; color: var(--text-muted); }
.empty-block p { font-size: 15px; font-weight: 500; margin: 10px 0 4px; color: var(--text-secondary); }
.empty-block span { font-size: 12px; }

@media (max-width:800px) { .stats-row { grid-template-columns: repeat(2,1fr); } }
</style>
