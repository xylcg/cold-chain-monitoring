<template>
  <div class="quality-page">
    <div class="page-header">
      <h2 class="page-title">生鲜品质AI评估</h2>
      <span class="subtitle">📸 上传图片 · AI自动识别品类与品质</span>
    </div>

    <!-- 场景切换：入库质检 / 出库复核 -->
    <div class="scene-switch">
      <div class="scene-item" :class="{ active: sceneMode === 'inbound' }" @click="switchScene('inbound')">
        <span class="scene-icon">📥</span>
        <span class="scene-label">入库质检</span>
        <span class="scene-desc">货物到达冷库前拍照，AI判断是否允许入库</span>
      </div>
      <div class="scene-item" :class="{ active: sceneMode === 'outbound' }" @click="switchScene('outbound')">
        <span class="scene-icon">📤</span>
        <span class="scene-label">出库复核</span>
        <span class="scene-desc">发货前拍照复核，AI判断是否符合出库标准</span>
      </div>
    </div>

    <!-- AI视觉识别主区域 -->
    <div class="glass-card main-card">
      <div class="card-header">
        <span class="header-icon">🤖</span>
        <span class="header-title">AI图片识别</span>
        <span class="header-tip">{{ sceneMode === 'inbound' ? '入库质检模式：拍照识别生鲜状态，决定是否入库' : '出库复核模式：拍照复核生鲜品质，决定是否放行' }}</span>
      </div>
      
      <!-- 步骤指示器 -->
      <div class="step-indicator">
        <div class="step" :class="{active: true, done: uploadedImage}">
          <span class="step-num">1</span>
          <span class="step-text">{{ cameraActive ? '拍照中' : '上传图片' }}</span>
        </div>
        <div class="step-line" :class="{active: uploadedImage || assessing}"></div>
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
            <div class="camera-big-btn" @click.stop="openCamera">
              <span class="cbb-icon">📷</span>
              <span class="cbb-text">调用摄像头拍照</span>
              <span class="cbb-sub">移动端推荐 · 直接拍摄生鲜实物</span>
            </div>
            <div class="upload-divider"><span>或从本地上传</span></div>
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

      <!-- 放行决策卡片（最醒目） -->
      <div v-if="assessResult" class="decision-card" :class="'decision-' + getDecision(assessResult)">
        <div class="dc-top">
          <div class="dc-scene-tag">{{ sceneMode === 'inbound' ? '📥 入库决策' : '📤 出库决策' }}</div>
          <div class="dc-result-badge">{{ getDecisionText(getDecision(assessResult)) }}</div>
        </div>
        <div class="dc-body">
          <div class="dc-grid">
            <div class="dc-field"><span class="dcf-label">操作类型</span><span class="dcf-value">{{ sceneMode === 'inbound' ? '入库质检' : '出库复核' }}</span></div>
            <div class="dc-field"><span class="dcf-label">识别品类</span><span class="dcf-value">{{ assessResult.product_type || '未知' }}</span></div>
            <div class="dc-field"><span class="dcf-label">品质等级</span><span class="dcf-value grade-val" :style="{color:getGradeTextColor(assessResult.grade)}">{{ assessResult.grade }}级 ({{ assessResult.quality_score }}分)</span></div>
            <div class="dc-field"><span class="dcf-label">置信度</span><span class="dcf-value">{{ ((assessResult.confidence||0)*100).toFixed(1) }}%</span></div>
            <div class="dc-field"><span class="dcf-label">剩余保鲜期</span><span class="dcf-value">{{ assessResult.remaining_freshness_days || '?' }}天</span></div>
            <div class="dc-field"><span class="dcf-label">检测时间</span><span class="dcf-value">{{ new Date().toLocaleString() }}</span></div>
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
    pass: '✅ 准予放行',
    warn: '⚠️ 有条件放行',
    caution: '🔶 建议降级',
    reject: '❌ 拒绝放行',
  }
  return map[decision] || ''
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
.quality-page { animation: fadeInUp 0.45s ease-out; }
.page-header { margin-bottom: 20px; }
.subtitle { font-size:13px; color:var(--text-muted); margin-left:12px; }

.main-card { margin-bottom:20px; }
.card-header { font-size:14px; font-weight:600; color:var(--text-title); margin-bottom:16px; display:flex; align-items:center; gap:8px; }
.header-icon { font-size:18px; }
.header-title { flex:1; }
.header-tip { font-size:12px; color:var(--text-muted); font-weight:400; }
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

@media (max-width:1200px) { .stats-row { grid-template-columns:repeat(2,1fr); } }
@media (max-width:768px) { .stats-row { grid-template-columns:1fr; } }

/* ===== 场景切换 ===== */
.scene-switch {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}
.scene-item {
  flex: 1;
  padding: 16px 20px;
  border-radius: 14px;
  border: 2px solid var(--border);
  background: var(--bg-card);
  cursor: pointer;
  transition: all 0.25s;
}
.scene-item:hover { border-color: rgba(0,168,255,0.4); }
.scene-item.active {
  border-color: var(--accent);
  background: linear-gradient(135deg, rgba(0,168,255,0.06), rgba(124,58,237,0.04));
  box-shadow: 0 4px 16px rgba(0,168,255,0.1);
}
.scene-icon { font-size: 24px; display: block; margin-bottom: 6px; }
.scene-label { font-size: 15px; font-weight: 700; color: var(--text-primary); display: block; margin-bottom: 4px; }
.scene-item.active .scene-label { color: var(--accent); }
.scene-desc { font-size: 12px; color: var(--text-muted); line-height: 1.5; }

/* ===== 摄像头视图 ===== */
.camera-container {
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid var(--border);
  background: #000;
  margin-bottom: 4px;
}
.cam-view {
  position: relative;
  width: 100%;
  min-height: 320px;
  background: #000;
}
.cam-video {
  width: 100%;
  min-height: 320px;
  object-fit: cover;
  display: block;
}
.cam-overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.cam-crosshair-h { position:absolute; width:60%; height:1px; top:50%; left:20%; background:rgba(255,255,255,0.3); }
.cam-crosshair-v { position:absolute; height:60%; width:1px; left:50%; top:20%; background:rgba(255,255,255,0.3); }
.cam-corner { position:absolute; width:24px; height:24px; border-color:#00ff88; border-style:solid; }
.cam-corner.tl { top:20%; left:20%; border-width:3px 0 0 3px; }
.cam-corner.tr { top:20%; right:20%; border-width:3px 3px 0 0; }
.cam-corner.bl { bottom:20%; left:20%; border-width:0 0 3px 3px; }
.cam-corner.br { bottom:20%; right:20%; border-width:0 3px 3px 0; }

.cam-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 28px;
  padding: 14px 20px;
  background: #000;
}
.cam-ctrl-btn {
  cursor: pointer;
  border: none;
  background: none;
  font-size: 18px;
}
.close-btn {
  width:44px; height:44px; border-radius:50%;
  background:rgba(255,255,255,0.12); color:#fff;
  display:flex; align-items:center; justify-content:center;
  transition: all 0.15s;
}
.close-btn:active { transform:scale(0.92); }
.shutter-btn {
  width:64px; height:64px; border-radius:50%;
  background:#fff; border:3px solid #ccc;
  display:flex; align-items:center; justify-content:center;
  transition: all 0.12s;
}
.shutter-btn:active { transform: scale(0.9); background: #eee; }
.shutter-inner {
  width:48px; height:48px; border-radius:50%;
  border:3px solid #333;
}
.cam-placeholder { width:64px; height:64px; }
.cam-hint {
  text-align: center;
  font-size: 12px;
  color: #00ff88;
  padding: 8px 12px 10px;
  background: #000;
  text-shadow: 0 1px 3px rgba(0,0,0,0.6);
}

/* 拍照大按钮 */
.camera-big-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 28px 32px;
  border: 2px solid var(--accent);
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(0,168,255,0.08), rgba(124,58,237,0.05));
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 16px;
  max-width: 360px;
  margin-left: auto;
  margin-right: auto;
}
.camera-big-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(0,168,255,0.15);
}
.cbb-icon { font-size: 36px; }
.cbb-text { font-size: 16px; font-weight: 700; color: var(--accent); }
.cbb-sub { font-size: 11px; color: var(--text-muted); }

.upload-divider {
  display: flex; align-items: center; gap: 12px;
  margin: 8px 0 12px; color: var(--text-muted); font-size: 12px;
}
.upload-divider::before, .upload-divider::after {
  content: ''; flex:1; height:1px; background: var(--border);
}

/* ===== 放行决策卡片 ===== */
.decision-card {
  margin-top: 20px;
  border-radius: 16px;
  overflow: hidden;
  border: 2px solid transparent;
  animation: slideUp 0.35s ease-out;
}
@keyframes slideUp { from { opacity:0; transform: translateY(12px); } to { opacity:1; transform: translateY(0); } }

.decision-pass { border-color: #22c55e; background: linear-gradient(135deg, #f0fdf4, #ecfdf5); }
.decision-warn { border-color: #f59e0b; background: linear-gradient(135deg, #fffbeb, #fefce8); }
.decision-caution { border-color: #f97316; background: linear-gradient(135deg, #fff7ed, #fef3e2); }
.decision-reject { border-color: #ef4444; background: linear-gradient(135deg, #fef2f2, #fee2e2); }

.dc-top {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 20px;
}
.dc-scene-tag {
  font-size: 13px; font-weight: 700; color: var(--text-secondary);
}
.dc-result-badge {
  font-size: 14px; font-weight: 700; padding: 4px 14px; border-radius: 8px;
}
.decision-pass .dc-result-badge { background: #d1fae5; color: #059669; }
.decision-warn .dc-result-badge { background: #fef3c7; color: #d97706; }
.decision-caution .dc-result-badge { background: #ffedd5; color: #ea580c; }
.decision-reject .dc-result-badge { background: #fee2e2; color: #dc2626; }

.dc-body { padding: 0 20px; }
.dc-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin-bottom: 12px; }
@media (max-width:600px) { .dc-grid { grid-template-columns: repeat(2, 1fr); } }
.dc-field {
  display: flex; flex-direction: column; gap: 2px;
  padding: 8px 10px; background: rgba(255,255,255,0.6); border-radius: 8px;
}
.dcf-label { font-size: 11px; color: var(--text-muted); }
.dcf-value { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.grade-val { font-family: var(--font-display); font-size: 15px !important; }

.dc-defects {
  padding: 8px 10px; background: rgba(239,68,68,0.08); border-radius: 8px;
  font-size: 12px; color: var(--red); margin-bottom: 12px;
}

.dc-actions {
  display: flex; gap: 10px; padding: 16px 20px;
  background: rgba(255,255,255,0.5);
  border-top: 1px solid rgba(0,0,0,0.05);
}
.dc-action-btn {
  flex: 1; padding: 12px 16px; border-radius: 10px;
  font-size: 13px; font-weight: 700; cursor: pointer; border: none;
  transition: all 0.15s;
}
.dc-action-btn:active { transform: scale(0.97); }
.primary { background: #22c55e; color: #fff; }
.primary-warn { background: #f59e0b; color: #fff; }
.caution { background: #f97316; color: #fff; }
.danger { background: #ef4444; color: #fff; }
.secondary { background: #fff; color: #666; border: 1px solid #ddd; }

.defect-tag-sm {
  display:inline-block; padding:2px 8px; margin:2px 4px; border-radius:4px;
  background:rgba(239,68,68,0.15); color:var(--red); font-size:11px;
}

/* 详情折叠 */
.result-details {
  margin-top: 16px;
  border: 1px solid var(--border);
  border-radius: 12px;
  overflow: hidden;
}
.rd-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px;
  font-size: 13px; font-weight: 600; color: var(--text-title);
  cursor: pointer; background: rgba(0,0,0,0.02); user-select: none;
}
.rd-header:hover { background: rgba(0,0,0,0.04); }
.rd-toggle { font-size: 11px; color: var(--text-muted); }
</style>