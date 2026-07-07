<template>
  <div class="quality-page">
    <div class="page-header">
      <div class="ph-left">
        <h2 class="page-title">生鲜品质AI评估</h2>
        <span class="subtitle">📸 上传图片 · AI自动识别品类与品质</span>
      </div>
      <div class="ph-right">
        <div class="ph-stat">
          <span class="phs-icon">🤖</span>
          <span class="phs-text">AI引擎就绪</span>
          <span class="phs-dot"></span>
        </div>
      </div>
    </div>

    <!-- 场景切换：入库质检 / 出库复核 -->
    <div class="scene-switch">
      <div class="scene-item" :class="{ active: sceneMode === 'inbound' }" @click="switchScene('inbound')">
        <div class="scene-icon-wrap" :class="{ active: sceneMode === 'inbound' }">
          <span class="scene-icon">📥</span>
        </div>
        <div class="scene-content">
          <span class="scene-label">入库质检</span>
          <span class="scene-desc">货物到达冷库前拍照，AI判断是否允许入库</span>
        </div>
        <div class="scene-check" v-if="sceneMode === 'inbound'">✓</div>
      </div>
      <div class="scene-item" :class="{ active: sceneMode === 'outbound' }" @click="switchScene('outbound')">
        <div class="scene-icon-wrap" :class="{ active: sceneMode === 'outbound' }">
          <span class="scene-icon">📤</span>
        </div>
        <div class="scene-content">
          <span class="scene-label">出库复核</span>
          <span class="scene-desc">发货前拍照复核，AI判断是否符合出库标准</span>
        </div>
        <div class="scene-check" v-if="sceneMode === 'outbound'">✓</div>
      </div>
    </div>

    <!-- AI视觉识别主区域 -->
    <div class="glass-card main-card">
      <div class="card-header">
        <div class="ch-left">
          <span class="header-icon">🤖</span>
          <span class="header-title">AI图片识别</span>
        </div>
        <span class="header-tip">
          <span class="ht-dot"></span>
          {{ sceneMode === 'inbound' ? '入库质检模式' : '出库复核模式' }}
        </span>
      </div>
      
      <!-- 步骤指示器 -->
      <div class="step-indicator">
        <div class="step" :class="{active: true, done: uploadedImage}">
          <div class="step-circle"><span class="step-num">{{ cameraActive ? '📷' : (uploadedImage ? '✓' : '1') }}</span></div>
          <span class="step-text">{{ cameraActive ? '拍照中' : (uploadedImage ? '已上传' : '上传图片') }}</span>
        </div>
        <div class="step-line" :class="{active: uploadedImage || assessing}"><div class="sl-fill"></div></div>
        <div class="step" :class="{active: assessing, done: assessResult}">
          <div class="step-circle"><span class="step-num">{{ assessResult ? '✓' : '2' }}</span></div>
          <span class="step-text">AI分析</span>
        </div>
        <div class="step-line" :class="{active: assessResult}"><div class="sl-fill"></div></div>
        <div class="step" :class="{active: assessResult}">
          <div class="step-circle"><span class="step-num">3</span></div>
          <span class="step-text">查看结果</span>
        </div>
      </div>

      <!-- 摄像头实时预览 -->
      <div v-if="cameraActive" class="camera-container">
        <div class="cam-view">
          <video ref="qaCameraVideo" class="cam-video" autoplay playsinline muted></video>
          <div class="cam-overlay">
            <div class="cam-crosshair-h"></div>
            <div class="cam-crosshair-v"></div>
            <div class="cam-corner tl"></div><div class="cam-corner tr"></div>
            <div class="cam-corner bl"></div><div class="cam-corner br"></div>
          </div>
        </div>
        <div class="cam-controls">
          <button class="cam-ctrl-btn close-btn" @click="closeCamera">✕ 关闭</button>
          <button class="cam-ctrl-btn shutter-btn" @click="capturePhoto">
            <span class="shutter-inner"></span>
          </button>
          <div class="cam-placeholder"></div>
        </div>
        <div class="cam-hint">将生鲜货物放入框内，点击拍照按钮</div>
      </div>

      <!-- 核心图片上传区 -->
      <div v-if="!cameraActive" class="upload-area" @click="triggerUpload" @dragover.prevent @drop.prevent="handleDrop">
        <input type="file" ref="uploadInput" accept="image/jpeg,image/png,image/jpg,image/webp" class="hidden-input" @change="handleFileSelect" />
        
        <!-- 已上传图片预览 -->
        <div v-if="uploadedImage && !cameraActive" class="upload-preview">
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
            <div class="camera-big-btn" @click.stop="openCamera"
              style="display:flex; flex-direction:column; align-items:center; gap:6px; width:100%; max-width:360px; padding:22px 20px; border:2px solid #00a8ff; border-radius:14px; background:linear-gradient(135deg,#e8f4fd,#f0f9ff); cursor:pointer; transition:all 0.2s; box-sizing:border-box;">
              <span class="cbb-icon" style="font-size:32px;">📷</span>
              <span class="cbb-text" style="font-size:16px; font-weight:700; color:#0369a1;">调用摄像头拍照</span>
              <span class="cbb-sub" style="font-size:11px; color:#6b9cc2;">移动端推荐 · 直接拍摄生鲜实物</span>
            </div>
            <div class="upload-divider"
              style="position:relative; text-align:center; width:100%; max-width:400px; margin:8px 0;">
              <span style="font-size:12px; color:var(--text-muted); background:#fff; padding:0 12px; position:relative; z-index:1;">或从本地上传</span>
              <!-- 左右装饰线用伪元素不可靠，直接用内联元素实现 -->
              <div style="position:absolute; top:50%; left:0; width:calc(50% - 50px); height:1px; background:var(--border);"></div>
              <div style="position:absolute; top:50%; right:0; width:calc(50% - 50px); height:1px; background:var(--border);"></div>
            </div>
            <div class="upload-icon-wrap">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" stroke-linecap="round" opacity="0.3">
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

      <!-- 放行决策卡片（最醒目） -->
      <div v-if="assessResult" class="decision-card" :class="'decision-' + getDecision(assessResult)">
        <div class="dc-top">
          <div class="dc-top-left">
            <span class="dc-scene-tag">{{ sceneMode === 'inbound' ? '📥 入库决策' : '📤 出库决策' }}</span>
          </div>
          <div class="dc-result-badge" :class="'badge-' + getDecision(assessResult)">
            <span class="drb-icon">{{ getDecisionIcon(getDecision(assessResult)) }}</span>
            <span class="drb-text">{{ getDecisionText(getDecision(assessResult)) }}</span>
          </div>
        </div>
        <div class="dc-body">
          <!-- 品质等级大展示 -->
          <div class="dc-grade-showcase">
            <div class="dgs-grade" :style="{ background: getGradeColor(assessResult.grade) }">
              <span class="dgs-letter">{{ assessResult.grade }}</span>
              <span class="dgs-label">级品质</span>
            </div>
            <div class="dgs-score-wrap">
              <div class="dgs-score-num">{{ assessResult.quality_score || 0 }}<small>分</small></div>
              <div class="dgs-score-bar">
                <div class="dsb-track"><div class="dsb-fill" :style="{ width: (assessResult.quality_score||0) + '%', background: getScoreBarColor(assessResult.quality_score||0) }"></div></div>
                <div class="dsb-labels"><span>差</span><span>优</span></div>
              </div>
            </div>
          </div>
          <div class="dc-grid">
            <div class="dc-field"><span class="dcf-icon">📋</span><span class="dcf-label">操作类型</span><span class="dcf-value">{{ sceneMode === 'inbound' ? '入库质检' : '出库复核' }}</span></div>
            <div class="dc-field"><span class="dcf-icon">🏷</span><span class="dcf-label">识别品类</span><span class="dcf-value">{{ assessResult.product_type || '未知' }}</span></div>
            <div class="dc-field"><span class="dcf-icon">🎯</span><span class="dcf-label">置信度</span><span class="dcf-value highlight">{{ ((assessResult.confidence||0)*100).toFixed(1) }}%</span></div>
            <div class="dc-field"><span class="dcf-icon">⏱</span><span class="dcf-label">剩余保鲜期</span><span class="dcf-value" :class="{ warn: (assessResult.remaining_freshness_days||0) < 3 }">{{ assessResult.remaining_freshness_days || '?' }}天</span></div>
            <div class="dc-field"><span class="dcf-icon">📅</span><span class="dcf-label">检测时间</span><span class="dcf-value">{{ new Date().toLocaleString() }}</span></div>
          </div>
          <div v-if="assessResult.defect_detected && assessResult.defects?.length" class="dc-defects">
            <strong>⚠ 检测到缺陷：</strong>
            <span v-for="d in assessResult.defects" :key="d" class="defect-tag-sm">{{ d }}</span>
          </div>
        </div>
        <div class="dc-actions">
          <!-- S/A级：通过 -->
          <template v-if="getDecision(assessResult) === 'pass'">
            <button class="dc-action-btn primary" @click="confirmDecision('pass')">✅ {{ sceneMode === 'inbound' ? '确认入库' : '确认出库' }}</button>
            <button class="dc-action-btn secondary" @click="confirmDecision('hold')">⏸ 暂存待检</button>
          </template>
          <!-- B级：有条件 -->
          <template v-if="getDecision(assessResult) === 'warn'">
            <button class="dc-action-btn primary-warn" @click="confirmDecision('pass')">{{ sceneMode === 'inbound' ? '允许入库(优先处理)' : '允许出库(优先配送)' }}</button>
            <button class="dc-action-btn secondary" @click="confirmDecision('quarantine')">🔒 隔离复检</button>
          </template>
          <!-- C级：降级 -->
          <template v-if="getDecision(assessResult) === 'caution'">
            <button class="dc-action-btn caution" @click="confirmDecision('downgrade')">📉 {{ sceneMode === 'inbound' ? '降级入库' : '降级出库' }}</button>
            <button class="dc-action-btn danger" @click="confirmDecision('reject')">❌ 拒收退货</button>
          </template>
          <!-- D级：拒绝 -->
          <template v-if="getDecision(assessResult) === 'reject'">
            <button class="dc-action-btn danger" @click="confirmDecision('reject')">❌ 确认拒收</button>
            <button class="dc-action-btn secondary" @click="confirmDecision('appeal')">📋 申请特批</button>
          </template>
        </div>
      </div>

      <!-- 评估结果详情（折叠显示，决策卡片已展示核心信息） -->
      <div v-if="assessResult" class="result-details">
        <div class="rd-header" @click="showDetails = !showDetails">
          <span>📊 详细指标与建议</span>
          <span class="rd-toggle">{{ showDetails ? '▼' : '▶' }}</span>
        </div>
        <div v-show="showDetails" class="result-section" style="margin-top:16px">
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
              <div v-if="uploadedImage" class="card-image">
                <img :src="uploadedImage" />
              </div>
              <div class="card-content">
                <div class="info-row"><span>识别品类</span><strong>{{ assessResult.product_type || '未知' }}</strong></div>
                <div class="info-row"><span>品类分类</span><strong>{{ assessResult.category || '其他' }}</strong></div>
                <div class="info-row"><span>品质评分</span><strong>{{ assessResult.quality_score || 0 }}分</strong></div>
                <div class="info-row"><span>置信度</span><strong>{{ ((assessResult.confidence || 0) * 100).toFixed(1) }}%</strong></div>
                <div v-if="assessResult.description" class="info-row info-row-desc"><span>描述</span><strong>{{ assessResult.description }}</strong></div>
              </div>
            </div>

            <!-- 品质详情卡片 -->
            <div class="result-card detail-card">
              <div class="card-title">📋 品质详情</div>
              <div class="card-content">
                <div class="info-row"><span>储存天数</span><strong>{{ assessResult.storage_days }}天</strong></div>
                <div class="info-row"><span>标准保鲜期</span><strong>{{ assessResult.total_freshness_days }}天</strong></div>
                <div class="info-row"><span>剩余保鲜期</span><strong>{{ assessResult.remaining_freshness_days }}天</strong></div>
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
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { qualityAPI } from '@/api'
import { ElMessage } from 'element-plus'

// 场景模式
const sceneMode = ref<'inbound' | 'outbound'>('inbound')
const showDetails = ref(true)

// 摄像头相关
const cameraActive = ref(false)
const cameraStream = ref<MediaStream | null>(null)
const qaCameraVideo = ref<HTMLVideoElement | null>(null)

const assessDays = ref(3)
const assessing = ref(false)
const assessResult = ref<any>(null)
const uploadedImage = ref('')
const selectedFile = ref<File | null>(null)
const uploadInput = ref<HTMLInputElement | null>(null)

const demoImages = [
  { name: '苹果', key: 'apple', icon: '🍎' },
  { name: '草莓', key: 'strawberry', icon: '🍓' },
  { name: '牛肉', key: 'beef', icon: '🥩' },
  { name: '生菜', key: 'lettuce', icon: '🥬' },
]


function switchScene(mode: 'inbound' | 'outbound') {
  sceneMode.value = mode
  // 切换场景时清除之前的上传图片和评估结果
  clearUpload()
}

// ===== 摄像头功能 =====
async function openCamera() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment' },
      audio: false,
    })
    cameraStream.value = stream
    cameraActive.value = true
    await nextTick()
    if (qaCameraVideo.value) {
      qaCameraVideo.value.srcObject = stream
      try { await qaCameraVideo.value.play() } catch {}
    }
  } catch (err: any) {
    ElMessage.error('无法访问摄像头，请检查权限')
  }
}

function closeCamera() {
  if (cameraStream.value) {
    cameraStream.value.getTracks().forEach(t => t.stop())
    cameraStream.value = null
  }
  cameraActive.value = false
}

async function capturePhoto() {
  if (!qaCameraVideo.value) return
  const video = qaCameraVideo.value
  const canvas = document.createElement('canvas')
  canvas.width = video.videoWidth || 640
  canvas.height = video.videoHeight || 480
  const ctx = canvas.getContext('2d')!
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
  const dataUrl = canvas.toDataURL('image/jpeg', 0.85)
  
  // 转为File对象
  const blob = await (await fetch(dataUrl)).blob()
  const file = new File([blob], 'camera_' + Date.now() + '.jpg', { type: 'image/jpeg' })
  
  closeCamera()
  loadFile(file)
}

// ===== 放行决策逻辑 =====
function getDecision(result: any): string {
  if (!result) return 'reject'
  const score = result.quality_score || 0
  if (score >= 78) return 'pass'       // S/A级 → 通过
  if (score >= 60) return 'warn'       // B级 → 有条件放行
  if (score >= 40) return 'caution'    // C级 → 降级处理
  return 'reject'                       // D级 → 拒绝
}

function getDecisionText(decision: string): string {
  const map: Record<string, string> = {
    pass: '准予放行',
    warn: '有条件放行',
    caution: '建议降级',
    reject: '拒绝放行',
  }
  return map[decision] || ''
}

function getDecisionIcon(decision: string): string {
  const map: Record<string, string> = {
    pass: '✅',
    warn: '⚠️',
    caution: '🔶',
    reject: '❌',
  }
  return map[decision] || '❓'
}

function getScoreBarColor(score: number): string {
  if (score >= 78) return 'linear-gradient(90deg, #22c55e, #16a34a)'
  if (score >= 60) return 'linear-gradient(90deg, #f59e0b, #d97706)'
  if (score >= 40) return 'linear-gradient(90deg, #f97316, #ea580c)'
  return 'linear-gradient(90deg, #ef4444, #dc2626)'
}

function getGradeTextColor(grade: string): string {
  if (!grade) return '#6b7280'
  if (grade.includes('S') || grade.includes('A')) return '#059669'
  if (grade.includes('B')) return '#d97706'
  if (grade.includes('C')) return '#ea580c'
  return '#dc2626'
}

function confirmDecision(action: string) {
  const actionMap: Record<string, string> = {
    pass: sceneMode.value === 'inbound' ? '已确认入库，货物可进入冷库存储' : '已确认出库，货物可正常发货',
    hold: '已暂存待检，请安排复检后再次评估',
    quarantine: '已标记隔离复检，货物需隔离存放并重新检测',
    downgrade: '已降级处理，货物将按降低标准入库/出库',
    reject: '已拒收/退货，货物不符合入库/出库标准',
    appeal: '特批申请已提交，等待管理员审批',
  }
  ElMessage.success(actionMap[action] || '操作已记录')
}


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
  // AI品质评估无需预加载数据，纯图片识别
}

async function doAssess() {
  assessing.value = true
  try {
    if (!selectedFile.value) {
      ElMessage.warning('请先上传图片')
      return
    }
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('storage_days', assessDays.value.toString())
    const res = await qualityAPI.assessWithImage(formData)
    assessResult.value = res.data || null
  } catch {
    ElMessage.error('品质评估失败')
  } finally {
    assessing.value = false
  }
}

onMounted(() => { loadData() })

onUnmounted(() => {
  if (cameraStream.value) {
    cameraStream.value.getTracks().forEach(t => t.stop())
  }
})
</script>

<style scoped>
/* ===== 页面基础 ===== */
.quality-page { animation: fadeInUp 0.45s ease-out; }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }

/* ===== 页面头部 ===== */
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid var(--border); }
.ph-left { display: flex; flex-direction: column; gap: 4px; }
.page-title { font-size: 22px; font-weight: 800; color: var(--text-title); margin: 0; }
.subtitle { font-size: 13px; color: var(--text-muted); }
.ph-right { display: flex; align-items: center; }
.ph-stat { display: flex; align-items: center; gap: 8px; padding: 8px 16px; background: linear-gradient(135deg, rgba(0,210,160,0.08), rgba(0,210,160,0.04)); border: 1px solid rgba(0,210,160,0.2); border-radius: 24px; font-size: 13px; color: #059669; font-weight: 600; }
.phs-icon { font-size: 16px; }
.phs-dot { width: 8px; height: 8px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 6px rgba(34,197,94,0.4); animation: pulse-dot 2s ease-in-out infinite; }
@keyframes pulse-dot { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.6; transform: scale(0.8); } }

/* ===== 场景切换 ===== */
.scene-switch { display: flex; gap: 16px; margin-bottom: 24px; }
.scene-item { flex: 1; display: flex; align-items: flex-start; gap: 14px; padding: 18px 20px; border-radius: 16px; border: 2px solid var(--border); background: var(--bg-card); cursor: pointer; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); position: relative; overflow: hidden; }
.scene-item::before { content: ''; position: absolute; inset: 0; background: linear-gradient(135deg, rgba(0,168,255,0.04), rgba(124,58,237,0.02)); opacity: 0; transition: opacity 0.3s; }
.scene-item:hover { border-color: rgba(0,168,255,0.4); transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,168,255,0.08); }
.scene-item:hover::before { opacity: 1; }
.scene-item.active { border-color: var(--accent); background: linear-gradient(135deg, rgba(0,168,255,0.06), rgba(124,58,237,0.04)); box-shadow: 0 4px 20px rgba(0,168,255,0.12); }
.scene-item.active::before { opacity: 1; }
.scene-icon-wrap { width: 48px; height: 48px; border-radius: 14px; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,0.04); border: 1px solid rgba(0,0,0,0.06); flex-shrink: 0; transition: all 0.3s; }
.scene-icon-wrap.active { background: linear-gradient(135deg, rgba(0,168,255,0.12), rgba(124,58,237,0.08)); border-color: rgba(0,168,255,0.2); box-shadow: 0 2px 8px rgba(0,168,255,0.1); }
.scene-icon { font-size: 22px; }
.scene-content { display: flex; flex-direction: column; gap: 4px; flex: 1; }
.scene-label { font-size: 15px; font-weight: 700; color: var(--text-primary); transition: color 0.3s; }
.scene-item.active .scene-label { color: var(--accent); }
.scene-desc { font-size: 12px; color: var(--text-muted); line-height: 1.5; }
.scene-check { width: 24px; height: 24px; border-radius: 50%; background: linear-gradient(135deg, var(--accent), var(--aurora)); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0; animation: popIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); }
@keyframes popIn { from { transform: scale(0); } to { transform: scale(1); } }

/* ===== 主卡片 ===== */
.main-card { margin-bottom: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid var(--border); }
.ch-left { display: flex; align-items: center; gap: 10px; }
.header-icon { font-size: 20px; }
.header-title { font-size: 16px; font-weight: 700; color: var(--text-title); }
.header-tip { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--text-muted); font-weight: 500; padding: 6px 12px; background: rgba(0,0,0,0.03); border-radius: 20px; }
.ht-dot { width: 8px; height: 8px; border-radius: 50%; background: linear-gradient(135deg, var(--accent), var(--aurora)); animation: pulse-dot 2s ease-in-out infinite; }

/* ===== 步骤指示器 ===== */
.step-indicator { display: flex; align-items: center; justify-content: center; gap: 12px; margin-bottom: 28px; padding: 20px 24px; background: rgba(0,0,0,0.02); border-radius: 14px; border: 1px solid rgba(0,0,0,0.04); }
.step { display: flex; flex-direction: column; align-items: center; gap: 6px; }
.step-circle { width: 40px; height: 40px; border-radius: 50%; background: var(--border); display: flex; align-items: center; justify-content: center; transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); box-shadow: 0 2px 6px rgba(0,0,0,0.06); }
.step-num { font-size: 14px; font-weight: 700; color: var(--text-muted); transition: all 0.4s; }
.step-text { font-size: 12px; color: var(--text-muted); font-weight: 500; transition: all 0.4s; }
.step.active .step-circle { background: linear-gradient(135deg, var(--accent), var(--aurora)); box-shadow: 0 4px 12px rgba(0,168,255,0.25); }
.step.active .step-num { color: #fff; }
.step.active .step-text { color: var(--text-primary); font-weight: 600; }
.step.done .step-circle { background: var(--teal); }
.step.done .step-num { color: #fff; }
.step.done .step-text { color: var(--teal); }
.step-line { width: 50px; height: 3px; background: var(--border); border-radius: 2px; overflow: hidden; position: relative; }
.sl-fill { width: 0%; height: 100%; background: linear-gradient(90deg, var(--teal), #22c55e); border-radius: 2px; transition: width 0.6s ease-out; }
.step-line.active .sl-fill { width: 100%; }

/* ===== 上传区域 ===== */
.upload-area { width:100%; min-height:420px; border:2px dashed var(--border); border-radius:18px; cursor:pointer; position:relative; overflow:visible; transition:all 0.3s; background:rgba(0,0,0,0.01); }
.upload-area:hover { border-color:var(--accent); background:rgba(0,168,255,0.02); }
.hidden-input { position:absolute; width:0; height:0; opacity:0; }
.upload-placeholder { width:100%; display:flex; flex-direction:column; align-items:center; justify-content:flex-start; padding:20px 20px 24px; box-sizing:border-box; gap:12px; }
.upload-main { display:flex; flex-direction:column; align-items:center; justify-content:center; width:100%; }
.upload-main h3 { font-size:18px; font-weight:600; color:var(--text-primary); margin:12px 0 4px 0; }
.upload-main p { font-size:13px; color:var(--text-muted); margin:0; }
.upload-icon-wrap { padding:12px; }

/* 拍照大按钮 */
.camera-big-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  width: 100%;
  max-width: 360px;
  padding: 22px 20px;
  border: 2px solid #00a8ff;
  border-radius: 14px;
  background: linear-gradient(135deg, #e8f4fd, #f0f9ff);
  cursor: pointer;
  transition: all 0.2s;
}
.camera-big-btn:hover {
  background: linear-gradient(135deg, #d4ecfb, #e8f4fd);
  box-shadow: 0 4px 14px rgba(0,168,255,0.15);
  transform: translateY(-1px);
}
.camera-big-btn:active {
  transform: scale(0.98);
}
.cbb-icon { font-size: 32px; }
.cbb-text { font-size: 16px; font-weight: 700; color: #0369a1; }
.cbb-sub { font-size: 11px; color: #6b9cc2; margin-top: 2px; }

/* 分隔线 */
.upload-divider {
  position: relative;
  text-align: center;
  width: 100%;
  max-width: 400px;
  margin: 4px 0;
}
.upload-divider::before,
.upload-divider::after {
  content: '';
  position: absolute;
  top: 50%;
  width: calc(50% - 40px);
  height: 1px;
  background: var(--border);
}
.upload-divider::before { left: 0; }
.upload-divider::after { right: 0; }
.upload-divider span {
  font-size: 12px;
  color: var(--text-muted);
  background: #fff;
  padding: 0 10px;
  position: relative;
}
.upload-features { width:100%; max-width:540px; padding-top:12px; border-top:1px dashed var(--border); }
.feature-row { margin-bottom:10px; }
.feature-row:last-child { margin-bottom:0; }
.feature-title { font-size:12px; color:var(--text-muted); font-weight:600; margin-bottom:10px; display: flex; align-items: center; gap: 4px; }
.format-tags { display:flex; flex-wrap:wrap; gap:8px; }
.format-tags span { font-size:12px; padding:6px 14px; background:rgba(0,0,0,0.04); border-radius:20px; border:1px solid rgba(0,0,0,0.06); transition:all 0.2s; }
.format-tags span:hover { background:rgba(0,168,255,0.08); border-color:var(--accent); transform: translateY(-1px); box-shadow: 0 2px 8px rgba(0,168,255,0.08); }
.demo-images { display:flex; gap:14px; justify-content: center; }
.demo-img { cursor:pointer; text-align:center; }
.demo-icon { width:64px; height:64px; border-radius:14px; display:flex; align-items:center; justify-content:center; font-size:32px; border:2px solid transparent; transition:all 0.2s; box-shadow:0 2px 8px rgba(0,0,0,0.06); background:var(--bg-card); }
.demo-img:hover .demo-icon { border-color:var(--accent); transform:scale(1.08); box-shadow:0 4px 16px rgba(0,168,255,0.15); }
.demo-img span { display:block; font-size:11px; color:var(--text-muted); margin-top:6px; font-weight: 500; }
.upload-preview { width:100%; height:100%; position:relative; }
.preview-img { width:100%; height:100%; object-fit:contain; background:rgba(0,0,0,0.02); }
.preview-overlay { position:absolute; bottom:0; left:0; right:0; padding:16px; background:linear-gradient(transparent,rgba(0,0,0,0.7)); }
.preview-status { color:#fff; font-size:14px; font-weight:500; }
.preview-close { position:absolute; top:12px; right:12px; width:36px; height:36px; display:flex; align-items:center; justify-content:center; background:rgba(0,0,0,0.5); color:#fff; border-radius:50%; font-size:16px; cursor:pointer; transition:all 0.2s; }
.preview-close:hover { background:rgba(0,0,0,0.7); transform: scale(1.1); }
.assessing-loader { display:flex; align-items:center; gap:10px; color:#fbbf24; font-size:14px; font-weight:500; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
.loader-ring { width:24px; height:24px; border:3px solid rgba(251,191,36,0.3); border-top-color:#fbbf24; border-radius:50%; animation: spin 1s linear infinite; }

/* ===== 响应式优化 ===== */
@media (max-width: 768px) {
  .page-header { flex-direction: column; align-items: flex-start; gap: 12px; }
  .scene-switch { flex-direction: column; }
  .scene-item { padding: 14px 16px; }
  .step-indicator { padding: 14px 12px; gap: 6px; }
  .step-line { width: 24px; }
  .step-circle { width: 34px; height: 34px; }
  .step-text { font-size: 10px; }
  .upload-area { min-height: 460px; }
  .dc-actions { flex-direction: column; }
  .dc-grade-showcase { flex-direction: column; text-align: center; }
  .dc-grid { grid-template-columns: 1fr; }
}
</style>
