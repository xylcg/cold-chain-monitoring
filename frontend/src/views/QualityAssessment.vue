<template>
  <div class="quality-page">
    <div class="page-header">
      <h2 class="page-title">生鲜品质AI评估</h2>
      <span class="subtitle">📸 上传图片 · AI自动识别品类与品质</span>
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

    <!-- AI视觉识别主区域 -->
    <div class="glass-card main-card">
      <div class="card-header">
        <span class="header-icon">🤖</span>
        <span class="header-title">AI图片识别</span>
        <span class="header-tip">上传生鲜图片，AI自动识别品类与品质</span>
      </div>
      
      <!-- 步骤指示器 -->
      <div class="step-indicator">
        <div class="step" :class="{active: true, done: uploadedImage}">
          <span class="step-num">1</span>
          <span class="step-text">上传图片</span>
        </div>
        <div class="step-line" :class="{active: uploadedImage}"></div>
        <div class="step" :class="{active: assessing, done: assessResult}">
          <span class="step-num">2</span>
          <span class="step-text">AI分析</span>
        </div>
        <div class="step-line" :class="{active: assessResult}"></div>
        <div class="step" :class="{active: assessResult}">
          <span class="step-num">3</span>
          <span class="step-text">查看结果</span>
        </div>
      </div>

      <!-- 核心图片上传区 -->
      <div class="upload-area" @click="triggerUpload" @dragover.prevent @drop.prevent="handleDrop">
        <input type="file" ref="uploadInput" accept="image/jpeg,image/png,image/jpg,image/webp" class="hidden-input" @change="handleFileSelect" />
        
        <!-- 已上传图片预览 -->
        <div v-if="uploadedImage" class="upload-preview">
          <img :src="uploadedImage" class="preview-img" />
          <div class="preview-overlay">
            <div v-if="assessing" class="assessing-loader">
              <div class="loader-ring"></div>
              <span>AI正在分析中...</span>
            </div>
            <span v-else class="preview-status">✓ 已上传，点击重新选择</span>
          </div>
          <span class="preview-close" @click.stop="clearUpload">✕</span>
        </div>
        
        <!-- 上传占位 -->
        <div v-else class="upload-placeholder">
          <div class="upload-main">
            <div class="upload-icon-wrap">
              <svg width="72" height="72" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" opacity="0.35">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                <polyline points="17 8 12 3 7 8"/>
                <line x1="12" y1="3" x2="12" y2="15"/>
              </svg>
            </div>
            <h3>点击或拖拽图片到此处</h3>
            <p>支持 JPG、PNG、WEBP 格式，最大10MB</p>
          </div>
          
          <div class="upload-features">
            <div class="feature-row">
              <div class="feature-title">🎯 支持品类</div>
              <div class="format-tags">
                <span>🍎 水果</span>
                <span>🥬 蔬菜</span>
                <span>🥩 肉类</span>
                <span>🦐 海鲜</span>
                <span>🥛 乳制品</span>
                <span>🧈 豆制品</span>
                <span>🥚 蛋类</span>
                <span>💉 医药制品</span>
                <span>🌼 花卉</span>
                <span>❄ 冷冻食品</span>
                <span>🍱 熟食预制菜</span>
                <span>🥤 饮料</span>
              </div>
            </div>
            <div class="feature-row">
              <div class="feature-title">👀 快速体验</div>
              <div class="demo-images">
                <div v-for="(img, idx) in demoImages" :key="idx" class="demo-img" @click.stop="loadDemoImage(img)">
                  <div class="demo-icon">{{ img.icon }}</div>
                  <span>{{ img.name }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 评估参数 -->
      <div class="advanced-panel">
        <div class="advanced-toggle" @click="showAdvanced = !showAdvanced">
          <span>{{ showAdvanced ? '▼' : '▲' }}</span>
          <span>评估参数设置</span>
        </div>
        <div v-if="showAdvanced" class="advanced-content">
          <div class="form-row">
            <div class="form-group">
              <label>品类选择（AI识别不准确时手动指定）</label>
              <select v-model="assessProduct" class="select-input">
                <option value="">AI自动识别</option>
                <option v-for="p in products" :key="p.key" :value="p.key">{{ p.name }} ({{ p.category }})</option>
              </select>
            </div>
            <div class="form-group">
              <label>已储存天数</label>
              <input type="number" v-model="assessDays" min="0" max="999" class="select-input" placeholder="0" />
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>储存条件</label>
              <select v-model="storageCondition" class="select-input">
                <option value="">自动检测</option>
                <option value="refrigerated">冷藏 (2-8°C)</option>
                <option value="frozen">冷冻 (-18°C以下)</option>
                <option value="room">常温 (15-25°C)</option>
                <option value="cold">低温 (0-2°C)</option>
              </select>
            </div>
            <div class="form-group">
              <label>包装状态</label>
              <select v-model="packageStatus" class="select-input">
                <option value="">自动检测</option>
                <option value="intact">完好</option>
                <option value="damaged">破损</option>
                <option value="opened">已开封</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>运输方式</label>
              <select v-model="transportMode" class="select-input">
                <option value="">未知</option>
                <option value="air">空运</option>
                <option value="land">陆运</option>
                <option value="sea">海运</option>
                <option value="express">冷链快递</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <!-- 评估结果 -->
      <div v-if="assessResult" class="result-section">
        <div class="result-header">
          <span>📊 评估结果</span>
          <button class="btn btn-secondary" @click="clearResult">重新评估</button>
        </div>
        
        <!-- 品质等级徽章 -->
        <div class="grade-badge" :style="{background:getGradeColor(assessResult.grade)}">
          <span class="grade-text">{{ assessResult.grade }}</span>
          <span class="grade-score">{{ assessResult.quality_score }}分</span>
        </div>

        <!-- 详细结果 -->
        <div class="result-grid">
          <!-- AI识别卡片 -->
          <div class="result-card ai-card">
            <div class="card-title">🤖 AI视觉评估</div>
            <div v-if="assessResult.image_url" class="card-image">
              <img :src="assessResult.image_url" />
            </div>
            <div class="card-content">
              <div class="info-row">
                <span>识别品类</span>
                <strong>{{ assessResult.product_type || '未知' }}</strong>
              </div>
              <div class="info-row">
                <span>品类分类</span>
                <strong>{{ assessResult.category || '其他' }}</strong>
              </div>
              <div class="info-row">
                <span>品质评分</span>
                <strong>{{ assessResult.quality_score || 0 }}分</strong>
              </div>
              <div class="info-row">
                <span>置信度</span>
                <strong>{{ ((assessResult.confidence || 0) * 100).toFixed(1) }}%</strong>
              </div>
              <div v-if="assessResult.description" class="info-row info-row-desc">
                <span>描述</span>
                <strong>{{ assessResult.description }}</strong>
              </div>
            </div>
          </div>

          <!-- 品质详情卡片 -->
          <div class="result-card detail-card">
            <div class="card-title">📋 品质详情</div>
            <div class="card-content">
              <div class="info-row">
                <span>品类</span>
                <strong>{{ assessResult.product_type }}</strong>
              </div>
              <div class="info-row">
                <span>储存天数</span>
                <strong>{{ assessResult.storage_days }}天</strong>
              </div>
              <div class="info-row">
                <span>标准保鲜期</span>
                <strong>{{ assessResult.total_freshness_days }}天</strong>
              </div>
              <div class="info-row">
                <span>剩余保鲜期</span>
                <strong>{{ assessResult.remaining_freshness_days }}天</strong>
              </div>
            </div>
            <div class="recommendation-box" :class="{warn:assessResult.grade.includes('D')||assessResult.grade.includes('C')}">
              <strong>💡 建议：</strong>{{ assessResult.suggestion }}
            </div>
          </div>
        </div>

        <!-- 指标评分 -->
        <div class="indicators-section">
          <div class="section-title">📈 各项指标评分</div>
          <div class="indicators-grid">
            <div v-for="(score, name) in assessResult.indicators" :key="name" class="indicator-item">
              <span class="ind-name">{{ name }}</span>
              <div class="ind-bar-wrap">
                <div class="ind-bar" :style="{width:score+'%',background:getIndicatorColor(score)}"></div>
              </div>
              <span class="ind-value" :style="{color:getIndicatorColor(score)}">{{ score }}</span>
            </div>
          </div>
        </div>

        <!-- 缺陷检测 -->
        <div v-if="assessResult.defect_detected" class="defects-section">
          <strong>⚠ 检测到缺陷：</strong>
          <span v-for="d in assessResult.defects" :key="d" class="defect-tag">{{ d }}</span>
        </div>
      </div>
    </div>

    <!-- 批次列表（可折叠） -->
    <div class="glass-card batch-card-container">
      <div class="card-header" @click="showBatchList = !showBatchList">
        <span>📦 品质批次列表</span>
        <div class="header-right">
          <span class="toggle-icon">{{ showBatchList ? '▼' : '▲' }}</span>
          <select v-model="batchFilter" class="mini-select">
            <option value="">全部分类</option>
            <option value="水果">水果</option>
            <option value="蔬菜">蔬菜</option>
            <option value="肉类">肉类</option>
            <option value="海鲜">海鲜</option>
            <option value="乳制品">乳制品</option>
            <option value="豆制品">豆制品</option>
            <option value="蛋类">蛋类</option>
            <option value="医药制品">医药制品</option>
            <option value="花卉">花卉</option>
            <option value="冷冻食品">冷冻食品</option>
            <option value="熟食预制菜">熟食预制菜</option>
            <option value="饮料">饮料</option>
          </select>
        </div>
      </div>
      <div v-if="showBatchList" class="batch-grid">
        <div v-for="b in filteredBatches" :key="b.batch_id" class="batch-item" :class="'grade-'+(b.grade?.charAt(0) || 'B')">
          <div class="batch-header">
            <span class="batch-id">{{ b.batch_id }}</span>
            <span class="batch-grade" :style="{color:getGradeColor(b.grade)}">{{ (b.grade?.charAt(0) || 'B') }}级</span>
          </div>
          <div class="batch-info">
            <div class="bi-row"><span>品类</span><strong>{{ b.product_type }}</strong></div>
            <div class="bi-row"><span>产地</span><strong>{{ b.origin }}</strong></div>
            <div class="bi-row"><span>重量</span><strong>{{ b.quantity_kg }}kg</strong></div>
            <div class="bi-row"><span>储存</span><strong>{{ b.storage_days }}天 @ {{ b.storage_temp_c }}°C</strong></div>
            <div class="bi-row"><span>剩余</span><strong>{{ b.remaining_shelf_life_days }}天</strong></div>
            <div class="bi-row"><span>评分</span><strong :style="{color:getGradeColor(b.grade)}">{{ b.quality_score || b.overall_score }}分</strong></div>
          </div>
          <div class="batch-status" :class="b.status">
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
const assessProduct = ref('')
const assessDays = ref(3)
const assessing = ref(false)
const assessResult = ref<any>(null)
const batchFilter = ref('')
const uploadedImage = ref('')
const selectedFile = ref<File | null>(null)
const uploadInput = ref<HTMLInputElement | null>(null)
const showAdvanced = ref(false)
const showBatchList = ref(true)
const storageCondition = ref('')
const packageStatus = ref('')
const transportMode = ref('')

const demoImages = [
  { name: '苹果', key: 'apple', icon: '🍎' },
  { name: '草莓', key: 'strawberry', icon: '🍓' },
  { name: '牛肉', key: 'beef', icon: '🥩' },
  { name: '生菜', key: 'lettuce', icon: '🥬' },
]

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

function getGradeColor(grade: string) {
  if (!grade) return '#6b7280'
  if (grade.includes('S')) return 'linear-gradient(135deg, #00d2a0, #22c55e)'
  if (grade.includes('A')) return 'linear-gradient(135deg, #22c55e, #16a34a)'
  if (grade.includes('B')) return 'linear-gradient(135deg, #f59e0b, #d97706)'
  if (grade.includes('C')) return 'linear-gradient(135deg, #f97316, #ea580c)'
  return 'linear-gradient(135deg, #ef4444, #dc2626)'
}

function getIndicatorColor(score: number) {
  if (score >= 80) return 'var(--teal)'
  if (score >= 60) return 'var(--amber)'
  return 'var(--red)'
}

function triggerUpload() {
  if (!assessing.value) {
    uploadInput.value?.click()
  }
}

function handleFileSelect(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    loadFile(file)
  }
}

function handleDrop(e: DragEvent) {
  const file = e.dataTransfer?.files[0]
  if (file && file.type.startsWith('image/')) {
    loadFile(file)
  }
}

function loadFile(file: File) {
  if (!file.type.startsWith('image/')) {
    ElMessage.warning('请上传图片文件')
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.warning('图片大小不能超过10MB')
    return
  }
  selectedFile.value = file
  assessResult.value = null
  const reader = new FileReader()
  reader.onload = (e) => {
    uploadedImage.value = e.target?.result as string
    doAssess()
  }
  reader.readAsDataURL(file)
}

async function loadDemoImage(img: any) {
  try {
    assessing.value = true
    const res = await qualityAPI.getDemo(img.key)
    assessResult.value = res.data || res || null
    if (assessResult.value) {
      uploadedImage.value = ''
    }
  } catch {
    ElMessage.warning('快速体验加载失败')
  } finally {
    assessing.value = false
  }
}

function clearUpload() {
  uploadedImage.value = ''
  selectedFile.value = null
  assessResult.value = null
  if (uploadInput.value) {
    uploadInput.value.value = ''
  }
}

function clearResult() {
  assessResult.value = null
}

async function loadData() {
  try {
    const [pRes, bRes, sRes] = await Promise.all([
      qualityAPI.getProducts(), qualityAPI.getBatches(), qualityAPI.getStats()
    ])
    products.value = pRes.products || []
    batches.value = bRes.batches || []
    stats.value = sRes
  } catch {
    ElMessage.warning('加载品质数据失败，请检查网络')
  }
}

async function doAssess() {
  assessing.value = true
  try {
    if (selectedFile.value) {
      const formData = new FormData()
      formData.append('file', selectedFile.value)
      if (assessProduct.value) {
        formData.append('product_type', assessProduct.value)
      }
      formData.append('storage_days', assessDays.value.toString())
      if (storageCondition.value) {
        formData.append('storage_condition', storageCondition.value)
      }
      if (packageStatus.value) {
        formData.append('package_status', packageStatus.value)
      }
      if (transportMode.value) {
        formData.append('transport_mode', transportMode.value)
      }
      const res = await qualityAPI.assessWithImage(formData)
      assessResult.value = res.data || null
    } else {
      if (!assessProduct.value) {
        ElMessage.warning('请选择品类或上传图片')
        return
      }
      const res = await qualityAPI.assess(assessProduct.value, assessDays.value)
      assessResult.value = res.data || null
    }
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
.page-header { margin-bottom: 20px; }
.subtitle { font-size:13px; color:var(--text-muted); margin-left:12px; }

.stats-row { display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:20px; }
.stat-card { display:flex; align-items:center; gap:12px; padding:16px; background:var(--bg-card); border-radius:var(--radius); border:1px solid var(--border); }
.stat-icon { width:40px; height:40px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:20px; flex-shrink:0; }
.stat-value { font-family:var(--font-display); font-size:26px; font-weight:700; line-height:1; }
.stat-label { font-size:12px; color:var(--text-muted); margin-top:2px; }

.main-card { margin-bottom:20px; }
.card-header { font-size:14px; font-weight:600; color:var(--text-title); margin-bottom:16px; display:flex; align-items:center; gap:8px; }
.header-icon { font-size:18px; }
.header-title { flex:1; }
.header-tip { font-size:12px; color:var(--text-muted); font-weight:400; }
.header-right { display:flex; align-items:center; gap:8px; }
.toggle-icon { font-size:10px; color:var(--text-muted); }

.step-indicator { display:flex; align-items:center; justify-content:center; gap:8px; margin-bottom:24px; padding:16px; background:rgba(0,0,0,0.02); border-radius:12px; }
.step { display:flex; flex-direction:column; align-items:center; gap:4px; }
.step-num { width:32px; height:32px; border-radius:50%; background:var(--border); color:var(--text-muted); display:flex; align-items:center; justify-content:center; font-size:14px; font-weight:600; transition:all 0.3s; }
.step-text { font-size:11px; color:var(--text-muted); }
.step.active .step-num { background:linear-gradient(135deg,var(--accent),var(--aurora)); color:#fff; }
.step.active .step-text { color:var(--text-primary); font-weight:500; }
.step.done .step-num { background:var(--teal); color:#fff; }
.step-line { width:40px; height:2px; background:var(--border); transition:all 0.3s; }
.step-line.active { background:var(--teal); }

.upload-area { width:100%; height:380px; border:2px dashed var(--border); border-radius:16px; cursor:pointer; position:relative; overflow:hidden; transition:all 0.3s; background:rgba(0,0,0,0.01); }
.upload-area:hover { border-color:var(--accent); background:rgba(0,168,255,0.02); }

.hidden-input { position:absolute; width:0; height:0; opacity:0; }

.upload-placeholder { width:100%; height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; padding:24px; box-sizing:border-box; }

.upload-main { display:flex; flex-direction:column; align-items:center; justify-content:center; flex:1; }
.upload-main h3 { font-size:18px; font-weight:500; color:var(--text-primary); margin:16px 0 8px 0; }
.upload-main p { font-size:13px; color:var(--text-muted); margin:0; }
.upload-icon-wrap { padding:24px; }

.upload-features { width:100%; max-width:500px; padding-top:16px; border-top:1px dashed var(--border); }
.feature-row { margin-bottom:12px; }
.feature-row:last-child { margin-bottom:0; }
.feature-title { font-size:12px; color:var(--text-muted); font-weight:500; margin-bottom:8px; }

.format-tags { display:flex; flex-wrap:wrap; gap:8px; }
.format-tags span { font-size:12px; padding:5px 12px; background:rgba(0,0,0,0.04); border-radius:20px; border:1px solid rgba(0,0,0,0.06); transition:all 0.2s; }
.format-tags span:hover { background:rgba(0,168,255,0.08); border-color:var(--accent); }

.demo-images { display:flex; gap:14px; }
.demo-img { cursor:pointer; text-align:center; }
.demo-icon { width:64px; height:64px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:32px; border:2px solid transparent; transition:all 0.2s; box-shadow:0 2px 8px rgba(0,0,0,0.06); background:var(--bg-card); }
.demo-img:hover .demo-icon { border-color:var(--accent); transform:scale(1.08); box-shadow:0 4px 12px rgba(0,168,255,0.15); }
.demo-img span { display:block; font-size:11px; color:var(--text-muted); margin-top:6px; }

.upload-preview { width:100%; height:100%; position:relative; }
.preview-img { width:100%; height:100%; object-fit:contain; background:rgba(0,0,0,0.02); }
.preview-overlay { position:absolute; bottom:0; left:0; right:0; padding:16px; background:linear-gradient(transparent,rgba(0,0,0,0.7)); }
.preview-status { color:#fff; font-size:14px; font-weight:500; }
.preview-close { position:absolute; top:12px; right:12px; width:32px; height:32px; display:flex; align-items:center; justify-content:center; background:rgba(0,0,0,0.5); color:#fff; border-radius:50%; font-size:16px; cursor:pointer; transition:all 0.2s; }
.preview-close:hover { background:rgba(0,0,0,0.7); }

.assessing-loader { display:flex; align-items:center; gap:10px; color:#fbbf24; font-size:14px; font-weight:500; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
.loader-ring { width:24px; height:24px; border:3px solid rgba(251,191,36,0.3); border-top-color:#fbbf24; border-radius:50%; animation: spin 1s linear infinite; }

.advanced-panel { margin-top:16px; }
.advanced-toggle { display:flex; align-items:center; gap:6px; font-size:12px; color:var(--text-muted); cursor:pointer; padding:10px 12px; border-radius:8px; background:rgba(0,0,0,0.02); }
.advanced-toggle:hover { background:rgba(0,0,0,0.04); }
.advanced-content { margin-top:12px; padding:16px; background:rgba(0,0,0,0.02); border-radius:12px; }
.form-row { display:flex; gap:20px; flex-wrap:wrap; margin-bottom:16px; }
.form-row:last-child { margin-bottom:0; }

.form-group { display:flex; flex-direction:column; gap:6px; min-width:200px; flex:1; }
.form-group label { font-size:12px; color:var(--text-muted); font-weight:500; }
.select-input { padding:10px 12px; border:1px solid var(--border); border-radius:8px; background:var(--bg-card); color:var(--text-primary); font-size:13px; min-width:180px; }

.btn { padding:8px 18px; border-radius:8px; font-size:13px; cursor:pointer; border:1px solid var(--border); background:var(--bg-card); color:var(--text-secondary); transition:all 0.2s; }
.btn:hover { background:rgba(0,0,0,0.04); }
.btn-secondary { font-size:12px; padding:6px 14px; }

.result-section { margin-top:24px; padding:20px; background:rgba(0,0,0,0.02); border-radius:16px; }
.result-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; font-size:15px; font-weight:600; color:var(--text-title); }

.grade-badge { display:flex; align-items:center; justify-content:center; gap:12px; padding:24px; border-radius:16px; margin-bottom:20px; }
.grade-text { font-family:var(--font-display); font-size:48px; font-weight:800; color:#fff; }
.grade-score { font-size:20px; color:rgba(255,255,255,0.9); font-weight:600; }

.result-grid { display:grid; grid-template-columns:320px 1fr; gap:16px; margin-bottom:20px; }
@media (max-width:900px) { .result-grid { grid-template-columns:1fr; } }

.result-card { background:var(--bg-card); border-radius:12px; border:1px solid var(--border); overflow:hidden; }
.card-title { padding:12px 16px; font-size:13px; font-weight:600; color:var(--text-title); border-bottom:1px solid var(--border); }
.card-image { padding:12px; text-align:center; }
.card-image img { max-width:100%; max-height:180px; border-radius:8px; object-fit:cover; }
.card-content { padding:12px 16px; }
.info-row { display:flex; justify-content:space-between; padding:6px 0; font-size:12px; border-bottom:1px solid rgba(0,0,0,0.03); align-items:center; }
.info-row span { color:var(--text-muted); flex-shrink:0; width:60px; }
.info-row strong { color:var(--text-primary); flex:1; margin-left:12px; }
.info-row-desc { align-items:flex-start; }
.info-row-desc span { flex-shrink:0; width:60px; }
.info-row-desc strong { flex:1; margin-left:12px; text-align:left; line-height:1.6; word-break:break-word; }

.recommendation-box { margin:12px 16px 16px; padding:12px; border-radius:8px; background:rgba(0,210,160,0.08); font-size:12px; }
.recommendation-box.warn { background:var(--red-bg); }

.indicators-section { margin-bottom:16px; }
.section-title { font-size:13px; font-weight:600; color:var(--text-title); margin-bottom:12px; }
.indicators-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); gap:12px; }
.indicator-item { display:flex; align-items:center; gap:10px; padding:10px 12px; background:var(--bg-card); border-radius:8px; }
.ind-name { width:80px; font-size:12px; color:var(--text-muted); flex-shrink:0; }
.ind-bar-wrap { flex:1; height:8px; background:var(--border); border-radius:4px; overflow:hidden; }
.ind-bar { height:100%; border-radius:4px; transition:width 0.5s; }
.ind-value { width:40px; text-align:right; font-size:13px; font-weight:600; font-family:var(--font-mono); }

.defects-section { padding:12px; background:var(--red-bg); border-radius:8px; font-size:12px; }
.defect-tag { display:inline-block; padding:4px 10px; margin:4px 6px; border-radius:4px; background:rgba(239,68,68,0.2); color:var(--red); font-size:11px; }

.batch-card-container { cursor:pointer; }
.mini-select { padding:4px 10px; font-size:12px; border:1px solid var(--border); border-radius:6px; background:var(--bg-card); color:var(--text-primary); }

.batch-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); gap:14px; margin-top:14px; }
.batch-item { padding:14px; border-radius:12px; border:1px solid var(--border); background:var(--bg-elevated); border-left:4px solid var(--teal); transition:all 0.2s; }
.batch-item:hover { box-shadow:0 2px 8px rgba(0,0,0,0.06); }
.batch-item.grade-D { border-left-color:var(--red); }
.batch-item.grade-C { border-left-color:#f97316; }
.batch-item.grade-B { border-left-color:var(--amber); }

.batch-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:10px; }
.batch-id { font-family:var(--font-mono); font-size:12px; font-weight:600; color:var(--text-secondary); }
.batch-grade { font-family:var(--font-display); font-size:20px; font-weight:700; }

.batch-info { margin-bottom:10px; }
.bi-row { display:flex; justify-content:space-between; font-size:12px; padding:3px 0; }
.bi-row span { color:var(--text-muted); }
.bi-row strong { color:var(--text-primary); }

.batch-status { text-align:center; padding:6px; border-radius:6px; font-size:12px; font-weight:500; }
.batch-status.in_storage { background:rgba(0,210,160,0.08); color:var(--teal); }
.batch-status.to_dispose { background:var(--red-bg); color:var(--red); }

@media (max-width:1200px) { .stats-row { grid-template-columns:repeat(2,1fr); } }
@media (max-width:768px) { .stats-row { grid-template-columns:1fr; } }
</style>