<template>
  <div class="quality-page">
    <div class="page-header">
      <h2 class="page-title">生鲜品质AI评估</h2>
      <span class="subtitle">ResNet50-CNN + Vision Transformer · 计算机视觉无损检测</span>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card" v-for="s in statsCards" :key="s.label">
        <div class="stat-icon" :style="{background:s.bg,color:s.color}">{{ s.icon }}</div>
        <div class="stat-info">
          <div class="stat-value" :style="{color:s.color}">{{ s.value }}</div>
          <div class="stat-label">{{ s.label }}</div>
        </div>
      </div>
    </div>

    <!-- 快速评估 -->
    <div class="glass-card" style="margin-bottom:20px">
      <div class="card-header">快速品质评估</div>
      <div class="assess-form">
        <div class="form-group">
          <label>品类选择</label>
          <select v-model="assessProduct" class="select-input">
            <option v-for="p in products" :key="p.key" :value="p.key">{{ p.name }} ({{ p.category }})</option>
          </select>
        </div>
        <div class="form-group">
          <label>已储存天数</label>
          <input type="number" v-model="assessDays" min="0" max="999" class="select-input" />
        </div>
        <button class="btn btn-primary" @click="doAssess" :disabled="assessing">
          {{ assessing ? '评估中...' : 'AI 评估' }}
        </button>
      </div>

      <!-- 评估结果 -->
      <div v-if="assessResult" class="assess-result">
        <div class="ar-grade" :style="{color:assessResult.grade_color}">
          <span class="ar-big">{{ assessResult.grade }}</span>
          <span class="ar-score">{{ assessResult.overall_score }}分</span>
        </div>
        <div class="ar-detail">
          <div class="ar-row"><span>品类</span><strong>{{ assessResult.product_type }}</strong></div>
          <div class="ar-row"><span>储存天数</span><strong>{{ assessResult.storage_days }}天</strong></div>
          <div class="ar-row"><span>剩余保鲜期</span><strong>{{ assessResult.remaining_shelf_life_days }}天 ({{ assessResult.remaining_ratio_percent }}%)</strong></div>
          <div class="ar-row"><span>模型置信度</span><strong>{{ (assessResult.model_confidence * 100).toFixed(1) }}%</strong></div>
          <div class="ar-row"><span>模型</span><strong>{{ assessResult.model_used }}</strong></div>
        </div>
        <div class="ar-indicators">
          <h4>各项指标评分</h4>
          <div v-for="(score, name) in assessResult.indicators" :key="name" class="ind-row">
            <span class="ind-name">{{ name }}</span>
            <div class="ind-bar"><div :style="{width:score+'%',background:score>=80?'var(--teal)':score>=60?'var(--amber)':'var(--red)'}"></div></div>
            <span class="ind-value">{{ score }}</span>
          </div>
        </div>
        <div class="ar-recommendation" :class="{warn:assessResult.grade.includes('D')||assessResult.grade.includes('C')}">
          <strong>建议：</strong>{{ assessResult.recommendation }}
        </div>
        <div v-if="assessResult.defect_detected" class="ar-defects">
          <strong>检测到缺陷：</strong>
          <span v-for="d in assessResult.defect_details" :key="d" class="defect-tag">{{ d }}</span>
        </div>
      </div>
    </div>

    <!-- 批次列表 -->
    <div class="glass-card">
      <div class="card-header">品质批次列表
        <div class="header-filters">
          <select v-model="batchFilter" class="mini-select">
            <option value="">全部分类</option>
            <option value="水果">水果</option>
            <option value="蔬菜">蔬菜</option>
            <option value="肉类">肉类</option>
            <option value="海鲜">海鲜</option>
            <option value="乳制品">乳制品</option>
          </select>
        </div>
      </div>
      <div class="batch-grid">
        <div v-for="b in filteredBatches" :key="b.batch_id" class="batch-card" :class="'grade-'+b.grade[0]">
          <div class="bc-head">
            <span class="bc-id">{{ b.batch_id }}</span>
            <span class="bc-grade" :style="{color:gradeColor(b.grade)}">{{ b.grade[0]+'级' }}</span>
          </div>
          <div class="bc-info">
            <div class="bc-row"><span>品类</span><strong>{{ b.product_type }}</strong></div>
            <div class="bc-row"><span>产地</span><strong>{{ b.origin }}</strong></div>
            <div class="bc-row"><span>重量</span><strong>{{ b.quantity_kg }}kg</strong></div>
            <div class="bc-row"><span>储存</span><strong>{{ b.storage_days }}天 @ {{ b.storage_temp_c }}°C</strong></div>
            <div class="bc-row"><span>剩余</span><strong>{{ b.remaining_shelf_life_days }}天</strong></div>
            <div class="bc-row"><span>评分</span><strong :style="{color:gradeColor(b.grade)}">{{ b.overall_score }}分</strong></div>
          </div>
          <div class="bc-status" :class="b.status">
            {{ b.status === 'in_storage' ? '正常储存' : '待处理' }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { qualityAPI } from '@/api'
import { ElMessage } from 'element-plus'

const products = ref<any[]>([])
const batches = ref<any[]>([])
const stats = ref<any>({})
const assessProduct = ref('apple')
const assessDays = ref(3)
const assessing = ref(false)
const assessResult = ref<any>(null)
const batchFilter = ref('')

const statsCards = computed(() => [
  { label: '批次总数', value: stats.value.total_batches || 0, icon: '📦', bg: 'rgba(0,168,255,0.12)', color: 'var(--accent)' },
  { label: '瑕疵率', value: (stats.value.defect_rate || 0) + '%', icon: '⚠', bg: 'var(--red-bg)', color: 'var(--red)' },
  { label: '平均品质评分', value: (stats.value.avg_quality_score || 0), icon: '⭐', bg: 'rgba(0,210,160,0.12)', color: 'var(--teal)' },
  { label: '支持品类', value: stats.value.products_supported || 0, icon: '🏷', bg: 'rgba(124,58,237,0.12)', color: 'var(--aurora)' },
])

const filteredBatches = computed(() => {
  if (!batchFilter.value) return batches.value
  return batches.value.filter((b: any) => b.category === batchFilter.value)
})

function gradeColor(grade: string) {
  if (grade.includes('S')) return '#00d2a0'
  if (grade.includes('A')) return '#22c55e'
  if (grade.includes('B')) return '#f59e0b'
  if (grade.includes('C')) return '#f97316'
  return '#ef4444'
}

async function loadData() {
  try {
    const [pRes, bRes, sRes] = await Promise.all([
      qualityAPI.getProducts(), qualityAPI.getBatches(), qualityAPI.getStats()
    ])
    products.value = pRes.products || []
    batches.value = bRes.batches || []
    stats.value = sRes
  } catch {}
}

async function doAssess() {
  assessing.value = true
  try {
    assessResult.value = await qualityAPI.assess(assessProduct.value, assessDays.value)
  } catch {
    ElMessage.error('品质评估失败')
  } finally {
    assessing.value = false
  }
}

onMounted(() => { loadData() })
</script>

<style scoped>
.quality-page { animation: fadeInUp 0.45s ease-out; }
.page-header { margin-bottom: 16px; }
.subtitle { font-size:13px; color:var(--text-muted); margin-left:12px; }
.stats-row { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:20px; }
.stat-card { display:flex; align-items:center; gap:12px; padding:16px; background:var(--bg-card); border-radius:var(--radius); border:1px solid var(--border); }
.stat-icon { width:40px; height:40px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:20px; flex-shrink:0; }
.stat-value { font-family:var(--font-display); font-size:26px; font-weight:700; line-height:1; }
.stat-label { font-size:12px; color:var(--text-muted); margin-top:2px; }
.card-header { font-size:14px; font-weight:600; color:var(--text-title); margin-bottom:14px; display:flex; align-items:center; justify-content:space-between; }
.header-filters { display:flex; gap:6px; }
.mini-select { padding:3px 8px; font-size:11px; border:1px solid var(--border); border-radius:4px; background:var(--bg-card); color:var(--text-primary); }

.assess-form { display:flex; gap:12px; align-items:flex-end; margin-bottom:16px; flex-wrap:wrap; }
.form-group { display:flex; flex-direction:column; gap:4px; }
.form-group label { font-size:11px; color:var(--text-muted); font-weight:500; }
.select-input { padding:8px 10px; border:1px solid var(--border); border-radius:6px; background:var(--bg-card); color:var(--text-primary); font-size:13px; min-width:140px; }

.btn { padding:8px 18px; border-radius:6px; font-size:13px; cursor:pointer; border:1px solid var(--border); background:var(--bg-card); color:var(--text-secondary); }
.btn-primary { background:linear-gradient(135deg,var(--accent),var(--aurora)); color:#fff; border:none; }
.btn-primary:disabled { opacity:.6; cursor:not-allowed; }

.assess-result { margin-top:16px; padding:16px; background:rgba(0,0,0,0.02); border-radius:var(--radius); }
.ar-grade { text-align:center; margin-bottom:12px; }
.ar-big { font-family:var(--font-display); font-size:36px; font-weight:800; }
.ar-score { font-size:14px; margin-left:10px; }
.ar-detail { display:grid; grid-template-columns:repeat(2,1fr); gap:6px; margin-bottom:14px; }
.ar-row { display:flex; justify-content:space-between; padding:4px 0; font-size:12px; border-bottom:1px solid rgba(0,0,0,0.03); }
.ar-row span { color:var(--text-muted); }
.ar-indicators { margin-bottom:12px; }
.ar-indicators h4 { font-size:12px; margin-bottom:8px; color:var(--text-title); }
.ind-row { display:flex; align-items:center; gap:8px; margin-bottom:5px; }
.ind-name { width:80px; font-size:11px; color:var(--text-muted); }
.ind-bar { flex:1; height:6px; background:var(--border); border-radius:3px; overflow:hidden; }
.ind-bar div { height:100%; border-radius:3px; transition:width .5s; }
.ind-value { width:30px; text-align:right; font-size:11px; font-weight:600; font-family:var(--font-mono); }
.ar-recommendation { padding:8px 12px; border-radius:6px; background:rgba(0,210,160,0.08); font-size:12px; margin-bottom:8px; }
.ar-recommendation.warn { background:var(--red-bg); }
.ar-defects { font-size:12px; }
.defect-tag { display:inline-block; padding:2px 8px; margin:2px 4px; border-radius:4px; background:var(--red-bg); color:var(--red); font-size:11px; }

.batch-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(220px,1fr)); gap:12px; }
.batch-card { padding:12px; border-radius:var(--radius); border:1px solid var(--border); background:var(--bg-elevated); border-left:3px solid var(--teal); }
.batch-card.grade-D { border-left-color:var(--red); }
.batch-card.grade-C { border-left-color:#f97316; }
.batch-card.grade-B { border-left-color:var(--amber); }
.bc-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:8px; }
.bc-id { font-family:var(--font-mono); font-size:11px; font-weight:600; }
.bc-grade { font-family:var(--font-display); font-size:18px; font-weight:700; }
.bc-info { margin-bottom:8px; }
.bc-row { display:flex; justify-content:space-between; font-size:11px; padding:2px 0; }
.bc-row span { color:var(--text-muted); }
.bc-status { text-align:center; padding:4px; border-radius:4px; font-size:11px; font-weight:500; }
.bc-status.in_storage { background:rgba(0,210,160,0.08); color:var(--teal); }
.bc-status.to_dispose { background:var(--red-bg); color:var(--red); }

@media (max-width:1200px) { .stats-row { grid-template-columns:repeat(2,1fr); } }
</style>
