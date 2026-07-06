<template>
  <div class="trace-page">
    <div class="page-header">
      <h2 class="page-title">🔗 全程冷链追溯链</h2>
      <div class="header-right">
        <el-select v-model="searchType" style="width: 100px">
          <el-option label="溯源码" value="code" />
          <el-option label="运单号" value="waybill" />
          <el-option label="货物名称" value="name" />
        </el-select>
        <el-input v-model="searchKeyword" placeholder="输入查询内容..." clearable style="width: 260px" @keyup.enter="searchTrace">
          <template #prefix>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          </template>
        </el-input>
        <button class="btn-primary" @click="searchTrace">查询</button>
        <el-button type="success" @click="showCreateDialog = true">创建运单</el-button>
      </div>
    </div>

    <div class="stats-row" v-if="stats">
      <div class="stat-it">
        <div class="stat-icon">📦</div>
        <div class="stat-num">{{ stats.total_traces }}</div>
        <div class="stat-lab">追溯运单</div>
      </div>
      <div class="stat-it">
        <div class="stat-icon">📋</div>
        <div class="stat-num">{{ stats.total_records }}</div>
        <div class="stat-lab">追溯记录</div>
      </div>
      <div class="stat-it">
        <div class="stat-icon">✅</div>
        <div class="stat-num teal">{{ stats.compliance_rate }}%</div>
        <div class="stat-lab">温控达标率</div>
      </div>
      <div class="stat-it">
        <div class="stat-icon">🔗</div>
        <div class="stat-num" :class="stats.on_chain_count > 0 ? 'teal' : 'text-muted'">{{ stats.on_chain_count }}</div>
        <div class="stat-lab">已上链</div>
      </div>
      <div class="stat-it">
        <div class="stat-icon">✅</div>
        <div class="stat-num">{{ stats.completed_traces }}</div>
        <div class="stat-lab">已完成</div>
      </div>
      <div class="stat-it">
        <div class="stat-icon">🔄</div>
        <div class="stat-num">{{ stats.in_progress_traces }}</div>
        <div class="stat-lab">进行中</div>
      </div>
    </div>

    <div v-if="searchResults.length > 0 && !traceResult" class="glass-card">
      <h3>搜索结果</h3>
      <div class="result-grid">
        <div v-for="item in searchResults" :key="item.trace_code" class="result-card" @click="viewTrace(item.trace_code)">
          <div class="rc-header">
            <code class="rc-code">{{ item.trace_code }}</code>
            <span class="rc-badge" :class="item.status">{{ item.status === 'completed' ? '已完成' : '进行中' }}</span>
          </div>
          <div class="rc-body">
            <div class="rc-name">{{ item.cargo_name }}</div>
            <div class="rc-info">
              <span>{{ item.origin }} → {{ item.destination }}</span>
            </div>
            <div class="rc-meta">
              <span class="rc-temp">{{ item.avg_temperature }}°C</span>
              <span class="rc-count">{{ item.total_records }}条记录</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="traceResult" class="trace-detail">
      <div class="detail-header glass-card">
        <div class="dh-left">
          <div class="dh-title">{{ traceResult.cargo_name }}</div>
          <div class="dh-code">溯源码: <code>{{ traceResult.trace_code }}</code></div>
          <div class="dh-sub">运单号: {{ traceResult.waybill_id }}</div>
        </div>
        <div class="dh-right">
          <div class="compliance-badge" :class="traceResult.is_compliant ? 'ok' : 'fail'">
            {{ traceResult.is_compliant ? '✅ 温控达标' : '⚠️ 温度异常' }}
          </div>
          <div class="temp-summary">
            <div class="ts-item">
              <span class="ts-label">温度范围</span>
              <span class="ts-value">{{ traceResult.temperature_summary.min }} ~ {{ traceResult.temperature_summary.max }}°C</span>
            </div>
            <div class="ts-item">
              <span class="ts-label">平均温度</span>
              <span class="ts-value">{{ traceResult.temperature_summary.avg }}°C</span>
            </div>
          </div>
        </div>
      </div>

      <div class="detail-body">
        <div class="detail-section glass-card">
          <h3>📋 货物信息</h3>
          <div class="info-grid">
            <div class="info-item"><span class="info-label">货物类别</span><span class="info-value">{{ traceResult.cargo_category }}</span></div>
            <div class="info-item"><span class="info-label">发货地</span><span class="info-value">{{ traceResult.origin }}</span></div>
            <div class="info-item"><span class="info-label">收货地</span><span class="info-value">{{ traceResult.destination }}</span></div>
            <div class="info-item"><span class="info-label">数量</span><span class="info-value">{{ traceResult.quantity }} {{ traceResult.unit }}</span></div>
            <div class="info-item"><span class="info-label">温度要求</span><span class="info-value">{{ traceResult.temperature_requirement }}</span></div>
            <div class="info-item"><span class="info-label">高敏货物</span><span class="info-value">{{ traceResult.is_high_sensitivity ? '是' : '否' }}</span></div>
            <div class="info-item"><span class="info-label">状态</span><span class="info-value">{{ traceResult.status }}</span></div>
            <div class="info-item"><span class="info-label">记录数</span><span class="info-value">{{ traceResult.total_stages }}条</span></div>
          </div>
        </div>

        <div class="detail-section glass-card">
          <h3>🔄 全链路环节</h3>
          <div class="timeline">
            <div v-for="stage in traceResult.stages" :key="stage.key" class="tl-stage" :class="{ active: stage.has_records }">
              <div class="tl-icon">{{ stage.icon }}</div>
              <div class="tl-line" v-if="stage.key !== 'sign'"></div>
              <div class="tl-content">
                <div class="tl-name">{{ stage.name }}</div>
                <div v-if="stage.has_records" class="tl-meta">
                  <span>{{ stage.count }}条记录</span>
                  <span>{{ stage.temp_range }}°C</span>
                </div>
                <div v-else class="tl-empty">未记录</div>
              </div>
            </div>
          </div>
        </div>

        <div class="detail-section glass-card">
          <div class="section-header">
            <h3>📈 温度曲线</h3>
          </div>
          <div ref="chartRef" class="chart-box"></div>
        </div>

        <div class="detail-section glass-card">
          <div class="section-header">
            <h3>📝 全程追溯记录</h3>
            <span class="section-count">共 {{ traceResult.records.length }} 条</span>
          </div>
          <div class="records-table">
            <table>
              <thead>
                <tr>
                  <th>环节</th>
                  <th>时间</th>
                  <th>位置</th>
                  <th>温度</th>
                  <th>湿度</th>
                  <th>操作人</th>
                  <th>操作</th>
                  <th>备注</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="record in traceResult.records" :key="record.id" :class="{ violation: isViolation(record) }">
                  <td><span class="stage-tag">{{ getStageName(record.stage) }}</span></td>
                  <td>{{ formatDateTime(record.timestamp) }}</td>
                  <td>{{ record.location }}</td>
                  <td :class="{ warn: isTempViolation(record) }">{{ record.temperature }}°C</td>
                  <td>{{ record.humidity }}%</td>
                  <td>{{ record.operator }}</td>
                  <td>{{ record.action }}</td>
                  <td class="notes-col">{{ record.notes }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div v-if="traceResult.violations && traceResult.violations.length > 0" class="detail-section glass-card violation-section">
          <h3>⚠️ 异常记录（{{ traceResult.violations.length }}条）</h3>
          <div class="violation-list">
            <div v-for="v in traceResult.violations" :key="v.id" class="violation-item">
              <div class="violation-header">
                <span class="violation-stage">{{ getStageName(v.stage) }}</span>
                <span class="violation-time">{{ formatDateTime(v.timestamp) }}</span>
              </div>
              <div class="violation-body">
                <span class="violation-temp">温度: {{ v.temperature }}°C（超出范围）</span>
                <span class="violation-location">{{ v.location }}</span>
                <span class="violation-notes">{{ v.notes }}</span>
              </div>
            </div>
          </div>
        </div>

        <div v-if="traceResult.blockchain" class="detail-section glass-card blockchain-section">
          <h3>🔗 区块链存证信息</h3>
          <div v-if="traceResult.blockchain.on_chain" class="blockchain-content">
            <div class="bc-grid">
              <div class="bc-item">
                <span class="bc-label">存证状态</span>
                <span class="bc-value ok">已上链</span>
              </div>
              <div class="bc-item">
                <span class="bc-label">区块编号</span>
                <span class="bc-value">#{{ traceResult.blockchain.block_number }}</span>
              </div>
              <div class="bc-item">
                <span class="bc-label">区块哈希</span>
                <span class="bc-value mono">{{ traceResult.blockchain.block_hash }}</span>
              </div>
              <div class="bc-item">
                <span class="bc-label">Merkle根</span>
                <span class="bc-value mono">{{ traceResult.blockchain.merkle_root }}</span>
              </div>
              <div class="bc-item">
                <span class="bc-label">存证时间</span>
                <span class="bc-value">{{ formatDateTime(traceResult.blockchain.certified_at) }}</span>
              </div>
              <div class="bc-item">
                <span class="bc-label">链完整性</span>
                <span class="bc-value ok">✓ 验证通过</span>
              </div>
            </div>
            <div class="bc-note">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#28a745" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><polyline points="16 10 10 16 8 14"/></svg>
              数据已通过区块链加密存证，不可篡改，具备司法溯源效力
            </div>
          </div>
          <div v-else class="blockchain-empty">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="1.5" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            <p>数据尚未上链存证</p>
            <el-button type="primary" @click="verifyBlockchain">立即存证</el-button>
          </div>
        </div>

        <div class="detail-actions">
          <el-button type="primary" @click="downloadReport">下载追溯报告</el-button>
          <el-button @click="copyTraceCode">复制溯源码</el-button>
          <el-button @click="showQRCode = true">生成溯源二维码</el-button>
        </div>
      </div>
    </div>

    <div v-if="!traceResult && searchResults.length === 0 && !searchKeyword" class="empty-block">
      <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" opacity="0.2">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
      </svg>
      <p>扫码或输入查询内容</p>
      <span>支持按溯源码、运单号、货物名称搜索，查看完整冷链追溯记录</span>
    </div>

    <el-dialog v-model="showCreateDialog" title="创建运单" width="560px">
      <el-form :model="newWaybill" label-width="90px">
        <el-form-item label="运单号" required>
          <el-input v-model="newWaybill.waybill_id" placeholder="如：WB-20260706-0001" />
          <div class="form-tip">系统自动生成，也可手动输入</div>
        </el-form-item>
        <el-form-item label="货物名称" required>
          <el-input v-model="newWaybill.cargo_name" placeholder="如：有机草莓" />
        </el-form-item>
        <el-form-item label="货物类别">
          <el-select v-model="newWaybill.cargo_category" style="width:100%">
            <el-option label="冷冻食品" value="冷冻食品" />
            <el-option label="冷藏生鲜" value="冷藏生鲜" />
            <el-option label="疫苗医药" value="疫苗医药" />
            <el-option label="化工制剂" value="化工制剂" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>
        <el-form-item label="发货地">
          <el-input v-model="newWaybill.origin" placeholder="如：北京市朝阳区" />
        </el-form-item>
        <el-form-item label="收货地">
          <el-input v-model="newWaybill.destination" placeholder="如：上海市浦东新区" />
        </el-form-item>
        <el-form-item label="数量">
          <el-input-number v-model="newWaybill.quantity" :min="0" :precision="1" style="width:100%" />
        </el-form-item>
        <el-form-item label="单位">
          <el-select v-model="newWaybill.unit" style="width:100%">
            <el-option label="kg" value="kg" />
            <el-option label="吨" value="吨" />
            <el-option label="件" value="件" />
            <el-option label="箱" value="箱" />
            <el-option label="剂" value="剂" />
          </el-select>
        </el-form-item>
        <el-form-item label="温度要求">
          <el-input v-model="newWaybill.temperature_requirement" placeholder="如：0~2℃" />
        </el-form-item>
        <el-form-item label="发货人">
          <el-input v-model="newWaybill.shipper" placeholder="发货人姓名/公司" />
        </el-form-item>
        <el-form-item label="收货人">
          <el-input v-model="newWaybill.receiver" placeholder="收货人姓名/公司" />
        </el-form-item>
        <el-form-item label="高敏货物">
          <el-switch v-model="newWaybill.is_high_sensitivity" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createWaybill" :loading="creating">确认创建</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showQRCode" title="溯源二维码" width="400px" @open="generateQRCode">
      <div class="qrcode-content">
        <div class="qrcode-box">
          <canvas ref="qrCanvasRef" class="qrcode-canvas"></canvas>
          <div class="qrcode-label">{{ currentTraceCode }}</div>
        </div>
        <p class="qrcode-note">消费者扫码即可查看完整冷链追溯记录</p>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { traceabilityAPI } from '@/api'
import { formatDateTime } from '@/utils'
import * as echarts from 'echarts'
import QRCode from 'qrcode'

const searchType = ref('code')
const searchKeyword = ref('')
const traceResult = ref<any>(null)
const searchResults = ref<any[]>([])
const stats = ref<any>(null)
const showCreateDialog = ref(false)
const showQRCode = ref(false)
const creating = ref(false)
const currentTraceCode = ref('')
const chartRef = ref<HTMLElement>()
const qrCanvasRef = ref<HTMLCanvasElement>()
let chartInstance: any = null

/** 生成真实二维码到 canvas */
async function generateQRCode() {
  if (!currentTraceCode.value || !qrCanvasRef.value) return
  const text = currentTraceCode.value
  const canvas = qrCanvasRef.value!
  try {
    await QRCode.toCanvas(canvas, text, {
      width: 180,
      margin: 2,
      color: { dark: '#1a1a1a', light: '#ffffff' },
      errorCorrectionLevel: 'M',
    })
  } catch {
    // 降容：如果 canvas 方式失败则忽略（保留空白）
  }
}

const STAGES_MAP: Record<string, string> = {
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

const newWaybill = ref({
  waybill_id: '',
  cargo_name: '',
  cargo_category: '冷冻食品',
  origin: '',
  destination: '',
  quantity: 0,
  unit: 'kg',
  temperature_requirement: '',
  shipper: '',
  receiver: '',
  is_high_sensitivity: false,
})

function getStageName(stageKey: string) {
  return STAGES_MAP[stageKey] || stageKey
}

function isViolation(record: any) {
  return record.temperature > 8 || record.temperature < -25
}

function isTempViolation(record: any) {
  const req = traceResult.value?.temperature_requirement || ''
  if (!req.includes('~')) return false
  const parts = req.split('~')
  const minReq = parseFloat(parts[0].replace('℃', ''))
  const maxReq = parseFloat(parts[1].replace('℃', ''))
  return record.temperature < minReq || record.temperature > maxReq
}

async function searchTrace() {
  const kw = searchKeyword.value.trim()
  if (!kw) { traceResult.value = null; searchResults.value = []; return }
  try {
    let effectiveType = searchType.value
    if (effectiveType === 'code') {
      if (kw.toUpperCase().startsWith('WB')) {
        effectiveType = 'waybill'
      } else if (kw.toUpperCase().startsWith('CC')) {
        effectiveType = 'code'
      } else {
        const normalized = kw.replace(/[-_]/g, '').toUpperCase()
        if (/^WB\d+$/.test(normalized) || /^WB-\d{8}-\d{4}$/.test(kw)) {
          effectiveType = 'waybill'
        }
      }
    }

    if (effectiveType === 'code') {
      const res: any = await traceabilityAPI.publicQuery(kw)
      if (res && res.error) {
        ElMessage.warning(res.error)
        return
      }
      traceResult.value = res
      searchResults.value = []
      currentTraceCode.value = res?.trace_code || ''
      await nextTick()
      renderChart()
    } else {
      const params: any = {}
      if (effectiveType === 'waybill') params.waybill_id = kw
      if (effectiveType === 'name') params.cargo_name = kw
      const res: any = await traceabilityAPI.search('', params)
      searchResults.value = res?.results || []
      traceResult.value = null
      if (searchResults.value.length === 0) ElMessage.info('未找到匹配的记录')
    }
  } catch { ElMessage.error('查询失败') }
}

async function viewTrace(traceCode: string) {
  searchKeyword.value = traceCode
  searchType.value = 'code'
  try {
    const res: any = await traceabilityAPI.publicQuery(traceCode)
    if (res && res.error) {
      ElMessage.warning(res.error)
      return
    }
    traceResult.value = res
    searchResults.value = []
    currentTraceCode.value = res?.trace_code || ''
    await nextTick()
    renderChart()
  } catch { ElMessage.error('获取详情失败') }
}

function renderChart() {
  if (!chartRef.value || !traceResult.value?.records) return
  if (chartInstance) chartInstance.dispose()
  chartInstance = echarts.init(chartRef.value)

  const records = traceResult.value.records
  const timestamps = records.map((r: any) => r.timestamp)
  const temperatures = records.map((r: any) => r.temperature)
  const humidities = records.map((r: any) => r.humidity)

  const req = traceResult.value.temperature_requirement || ''
  let markLines: any[] = []
  if (req.includes('~')) {
    const parts = req.split('~')
    try {
      const minReq = parseFloat(parts[0].replace('℃', ''))
      const maxReq = parseFloat(parts[1].replace('℃', ''))
      markLines = [
        { yAxis: minReq, lineStyle: { color: '#dc3545', type: 'dashed', width: 1.5 }, label: { formatter: `${minReq}℃`, color: '#dc3545', fontSize: 10 } },
        { yAxis: maxReq, lineStyle: { color: '#dc3545', type: 'dashed', width: 1.5 }, label: { formatter: `${maxReq}℃`, color: '#dc3545', fontSize: 10 } },
      ]
    } catch {}
  }

  chartInstance.setOption({
    tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: '#e2e8f0', textStyle: { color: '#1e293b', fontSize: 12 } },
    legend: { data: ['温度', '湿度'], top: 0 },
    grid: { left: 50, right: 30, top: 40, bottom: 40 },
    xAxis: {
      type: 'category', data: timestamps.map((t: string) => t.slice(11, 16)),
      axisLabel: { color: '#94a3b8', fontSize: 10, rotate: 45 },
      axisLine: { lineStyle: { color: '#e2e8f0' } },
    },
    yAxis: [
      { type: 'value', name: '温度 (℃)', nameTextStyle: { color: '#64748b', fontSize: 11 }, axisLabel: { color: '#94a3b8' }, splitLine: { lineStyle: { color: '#f1f5f9' } } },
      { type: 'value', name: '湿度 (%)', nameTextStyle: { color: '#64748b', fontSize: 11 }, axisLabel: { color: '#94a3b8' }, splitLine: { show: false } },
    ],
    series: [
      {
        name: '温度', type: 'line', yAxisIndex: 0, data: temperatures, smooth: true,
        lineStyle: { color: '#00a8ff', width: 2.5 },
        itemStyle: { color: '#00a8ff' },
        areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1, [{ offset: 0, color: 'rgba(0,168,255,0.1)' }, { offset: 1, color: 'rgba(0,168,255,0)' }]) },
        markLine: { silent: true, symbol: 'none', data: markLines },
      },
      {
        name: '湿度', type: 'line', yAxisIndex: 1, data: humidities, smooth: true,
        lineStyle: { color: '#10b981', width: 2 },
        itemStyle: { color: '#10b981' },
      },
    ],
  })
  window.addEventListener('resize', () => chartInstance?.resize())
}

async function downloadReport() {
  if (!traceResult.value) return
  try {
    const res = await traceabilityAPI.getReport(traceResult.value.trace_code, 'text')
    const blob = new Blob([res as any], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = `trace_report_${traceResult.value.trace_code}.txt`; a.click()
    URL.revokeObjectURL(url); ElMessage.success('报告已下载')
  } catch { ElMessage.error('下载失败') }
}

async function verifyBlockchain() {
  if (!traceResult.value) return
  try {
    await traceabilityAPI.verifyBlockchain(traceResult.value.trace_code)
    await searchTrace()
    ElMessage.success('区块链存证成功')
  } catch { ElMessage.error('存证失败') }
}

function copyTraceCode() {
  if (!traceResult.value) return
  navigator.clipboard.writeText(traceResult.value.trace_code)
  ElMessage.success('溯源码已复制')
}

async function createWaybill() {
  if (!newWaybill.value.cargo_name) {
    ElMessage.warning('请填写货物名称')
    return
  }
  
  if (!newWaybill.value.waybill_id) {
    const now = new Date()
    const dateStr = now.toISOString().slice(0, 10).replace(/-/g, '')
    const randomNum = Math.floor(Math.random() * 9000 + 1000)
    newWaybill.value.waybill_id = `WB-${dateStr}-${randomNum}`
  }
  
  creating.value = true
  try {
    await traceabilityAPI.createWaybill(newWaybill.value)
    ElMessage.success('运单创建成功')
    showCreateDialog.value = false
    newWaybill.value = {
      waybill_id: '', cargo_name: '', cargo_category: '冷冻食品',
      origin: '', destination: '', quantity: 0, unit: 'kg',
      temperature_requirement: '', shipper: '', receiver: '',
      is_high_sensitivity: false,
    }
    loadStats()
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '创建失败')
  } finally {
    creating.value = false
  }
}

async function loadStats() {
  try { stats.value = await traceabilityAPI.getStats() } catch {}
}

onMounted(loadStats)
</script>

<style scoped>
.trace-page { animation: fadeInUp 0.45s ease-out; }

.header-right { display: flex; align-items: center; gap: 10px; }

.stats-row { display: grid; grid-template-columns: repeat(6,1fr); gap: 12px; margin-bottom: 20px; }
.stat-it { background: var(--bg-card); backdrop-filter: var(--blur-card); border: 1px solid var(--border-card); border-radius: var(--radius-lg); padding: 16px; text-align: center; }
.stat-icon { font-size: 24px; margin-bottom: 4px; }
.stat-num { font-family: var(--font-display); font-size: 24px; font-weight: 800; color: var(--text-title); }
.stat-num.teal { color: var(--teal); }
.stat-num.red { color: var(--red); }
.stat-lab { font-size: 11px; color: var(--text-muted); margin-top: 2px; }

.result-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 12px; }
.result-card { background: var(--bg-card); border: 1px solid var(--border-card); border-radius: var(--radius-lg); padding: 16px; cursor: pointer; transition: all 0.2s; }
.result-card:hover { border-color: var(--accent); background: var(--accent-bg); }
.rc-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.rc-code { font-family: var(--font-mono); font-size: 12px; color: var(--accent); }
.rc-badge { font-size: 10px; padding: 2px 8px; border-radius: 20px; }
.rc-badge.已完成 { background: var(--teal-bg); color: var(--teal); }
.rc-badge.进行中 { background: var(--amber-bg); color: var(--amber); }
.rc-name { font-weight: 600; color: var(--text-title); margin-bottom: 4px; }
.rc-info { font-size: 12px; color: var(--text-secondary); }
.rc-meta { display: flex; gap: 12px; margin-top: 8px; font-size: 11px; color: var(--text-muted); }
.rc-temp { font-family: var(--font-mono); color: var(--accent); }

.detail-header { display: flex; justify-content: space-between; align-items: flex-start; padding: 20px; margin-bottom: 16px; }
.dh-title { font-size: 20px; font-weight: 700; color: var(--text-title); }
.dh-code { font-family: var(--font-mono); font-size: 14px; color: var(--accent); margin-top: 4px; }
.dh-sub { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
.compliance-badge { font-size: 14px; font-weight: 600; padding: 8px 20px; border-radius: 20px; }
.compliance-badge.ok { background: var(--teal-bg); color: var(--teal); }
.compliance-badge.fail { background: var(--red-bg); color: var(--red); }
.temp-summary { display: flex; flex-direction: column; gap: 4px; margin-top: 12px; }
.ts-item { display: flex; justify-content: space-between; font-size: 12px; }
.ts-label { color: var(--text-muted); }
.ts-value { font-weight: 600; color: var(--text-primary); }

.detail-body { display: flex; flex-direction: column; gap: 16px; }
.detail-section { padding: 20px; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.section-count { font-size: 12px; color: var(--text-muted); }

.info-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 10px; }
.info-item { display: flex; flex-direction: column; padding: 12px; background: var(--bg-input); border-radius: var(--radius); }
.info-label { font-size: 10px; color: var(--text-muted); letter-spacing: 0.04em; }
.info-value { font-size: 14px; font-weight: 600; color: var(--text-primary); margin-top: 4px; }

.timeline { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
.tl-stage { display: flex; align-items: center; gap: 8px; }
.tl-icon { font-size: 20px; width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; background: var(--bg-input); border-radius: 50%; border: 2px solid var(--border-light); }
.tl-stage.active .tl-icon { background: var(--accent-bg); border-color: var(--accent); }
.tl-line { width: 30px; height: 2px; background: var(--border-light); }
.tl-content { display: flex; flex-direction: column; }
.tl-name { font-size: 12px; font-weight: 500; color: var(--text-secondary); }
.tl-meta { display: flex; gap: 8px; font-size: 10px; color: var(--text-muted); margin-top: 2px; }
.tl-empty { font-size: 10px; color: var(--text-muted); margin-top: 2px; }

.chart-box { width: 100%; height: 300px; }

.records-table { overflow-x: auto; }
.records-table table { width: 100%; border-collapse: collapse; }
.records-table th { text-align: left; padding: 10px; font-size: 11px; color: var(--text-muted); border-bottom: 2px solid var(--border-light); }
.records-table td { padding: 10px; font-size: 12px; color: var(--text-secondary); border-bottom: 1px solid var(--border-light); }
.stage-tag { font-size: 10px; padding: 2px 6px; border-radius: 4px; background: var(--accent-bg); color: var(--accent); }
.notes-col { max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.records-table tr.violation td { background: var(--red-bg); }
.records-table td.warn { color: var(--red); font-weight: 600; }

.violation-section { border-color: var(--red); background: var(--red-bg); }
.violation-section h3 { color: var(--red); }
.violation-list { display: flex; flex-direction: column; gap: 10px; }
.violation-item { background: #fff; border-radius: var(--radius); padding: 12px; }
.violation-header { display: flex; justify-content: space-between; margin-bottom: 6px; }
.violation-stage { font-size: 12px; font-weight: 600; color: var(--red); }
.violation-time { font-size: 11px; color: var(--text-muted); font-family: var(--font-mono); }
.violation-body { display: flex; flex-direction: column; gap: 4px; font-size: 12px; color: var(--text-secondary); }
.violation-temp { color: var(--red); }

.blockchain-section { border-color: var(--accent); }
.bc-grid { display: grid; grid-template-columns: repeat(3,1fr); gap: 12px; }
.bc-item { display: flex; flex-direction: column; padding: 12px; background: var(--bg-input); border-radius: var(--radius); }
.bc-label { font-size: 10px; color: var(--text-muted); }
.bc-value { font-size: 14px; font-weight: 600; color: var(--text-primary); margin-top: 4px; }
.bc-value.ok { color: var(--teal); }
.bc-value.mono { font-family: var(--font-mono); font-size: 11px; word-break: break-all; }
.bc-note { display: flex; align-items: center; gap: 8px; margin-top: 16px; padding: 12px; background: var(--teal-bg); border-radius: var(--radius); font-size: 12px; color: var(--teal); }
.blockchain-empty { display: flex; flex-direction: column; align-items: center; padding: 40px; }
.blockchain-empty p { font-size: 14px; color: var(--text-muted); margin-top: 12px; }

.detail-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 16px; }

.qrcode-content { text-align: center; padding: 20px; }
.qrcode-box { display: flex; flex-direction: column; align-items: center; }
.qrcode-canvas { width: 180px !important; height: 180px !important; border: 1px solid var(--border-light); border-radius: 12px; padding: 8px; background: #fff; }
.qrcode-label { font-family: var(--font-mono); font-size: 12px; color: var(--accent); margin-top: 12px; }
.qrcode-note { font-size: 12px; color: var(--text-muted); margin-top: 16px; }

.form-tip { font-size: 11px; color: var(--text-muted); margin-top: 4px; }

.empty-block { text-align: center; padding: 60px 0; color: var(--text-muted); }
.empty-block p { font-size: 15px; font-weight: 500; margin: 10px 0 4px; color: var(--text-secondary); }
.empty-block span { font-size: 12px; }

@media (max-width:1000px) {
  .stats-row { grid-template-columns: repeat(3,1fr); }
  .result-grid { grid-template-columns: repeat(2,1fr); }
  .info-grid { grid-template-columns: repeat(2,1fr); }
  .bc-grid { grid-template-columns: repeat(2,1fr); }
}
@media (max-width:600px) {
  .stats-row { grid-template-columns: repeat(2,1fr); }
  .result-grid { grid-template-columns: 1fr; }
  .detail-header { flex-direction: column; gap: 12px; }
  .timeline { flex-direction: column; align-items: flex-start; }
  .tl-line { width: 2px; height: 20px; }
}
</style>