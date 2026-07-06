<template>
  <div class="login-page" @mousemove="onMouseMove">
    <!-- ===== 左侧：品牌视觉 + 动画角色区 ===== -->
    <div class="left-panel">
      <!-- 装饰元素 -->
      <div class="decor-blur decor-blur-1"></div>
      <div class="decor-blur decor-blur-2"></div>
      <div class="decor-grid"></div>

      <!-- Brand -->
      <div class="lp-brand">
        <div class="lp-brand-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
          </svg>
        </div>
        <span class="lp-brand-name">ColdChain Pro</span>
      </div>

      <!-- Characters Stage -->
      <div class="chars-stage">
          <!-- 紫色高个子 - 后排左 -->
          <div ref="purpleRef" class="char char-purple" :class="charClasses.purple">
            <div class="char-face">
              <div class="eyes-row">
                <div class="eye" :class="eyeClasses.purple"><div ref="pPupilL" class="pupil"></div></div>
                <div class="eye" :class="eyeClasses.purple"><div ref="pPupilR" class="pupil"></div></div>
              </div>
              <div class="mouth" :class="mouthClasses.purple"></div>
            </div>
          </div>

          <!-- 黑色中等 - 中排 -->
          <div ref="blackRef" class="char char-black" :class="charClasses.black">
            <div class="char-face">
              <div class="eyes-row">
                <div class="eye" :class="eyeClasses.black"><div ref="bPupilL" class="pupil"></div></div>
                <div class="eye" :class="eyeClasses.black"><div ref="bPupilR" class="pupil"></div></div>
              </div>
              <div class="mouth" :class="mouthClasses.black"></div>
            </div>
          </div>

          <!-- 橘色半圆 - 前排左 -->
          <div ref="orangeRef" class="char char-orange" :class="charClasses.orange">
            <div class="char-face">
              <div class="eyes-row">
                <div class="eye eye-plain" :class="eyeClasses.orange"><div ref="oPupilL" class="pupil"></div></div>
                <div class="eye eye-plain" :class="eyeClasses.orange"><div ref="oPupilR" class="pupil"></div></div>
              </div>
              <div class="mouth" :class="mouthClasses.orange"></div>
            </div>
          </div>

          <!-- 黄色圆角矩形 - 前排右 -->
          <div ref="yellowRef" class="char char-yellow" :class="charClasses.yellow">
            <div class="char-face">
              <div class="eyes-row">
                <div class="eye eye-plain" :class="eyeClasses.yellow"><div ref="yPupilL" class="pupil"></div></div>
                <div class="eye eye-plain" :class="eyeClasses.yellow"><div ref="yPupilR" class="pupil"></div></div>
              </div>
              <div ref="yMouthRef" class="mouth" :class="mouthClasses.yellow"></div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="lp-footer">
          <span>隐私政策</span>
          <span class="sep">·</span>
          <span>服务条款</span>
          <span class="sep">·</span>
          <span>联系我们</span>
        </div>
      </div>

    <!-- ===== 右侧：登录表单区 ===== -->
    <div class="right-panel">
      <div class="form-card">
        <!-- Mobile Brand -->
        <div class="mob-brand">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6C3FF5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
          </svg>
          <span>YourBrand</span>
        </div>

        <div class="form-header">
          <h1>欢迎回来</h1>
          <p>登录冷链智能监控平台</p>
        </div>

        <form @submit.prevent="handleLogin" class="form-body">
          <!-- 账号 -->
          <div class="field-group">
            <label class="field-label">账号</label>
            <div class="input-box">
              <svg class="input-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
              </svg>
              <input
                v-model="form.username"
                type="text"
                placeholder="请输入账号"
                class="form-input"
                @focus="onEmailFocus"
                @blur="onEmailBlur"
                autocomplete="off"
                required
              />
            </div>
          </div>

          <!-- 密码 -->
          <div class="field-group">
            <label class="field-label">密码</label>
            <div class="input-box">
              <svg class="input-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
              </svg>
              <input
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="请输入密码"
                class="form-input"
                @focus="isPasswordFocused = true"
                @blur="isPasswordFocused = false"
                required
              />
              <button type="button" class="eye-toggle" @click="showPassword = !showPassword" :title="showPassword ? '隐藏密码' : '显示密码'">
                <svg v-if="!showPassword" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                </svg>
                <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                  <line x1="1" y1="1" x2="23" y2="23"/>
                </svg>
              </button>
            </div>
          </div>

          <div class="form-options">
            <label class="checkbox-label">
              <input type="checkbox" v-model="rememberMe" />
              <span>记住登录状态</span>
            </label>
          </div>

          <div v-if="errorMsg" class="error-msg">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
            {{ errorMsg }}
          </div>

          <button type="submit" class="btn-submit" :disabled="loading">
            <svg v-if="loading" class="spinner" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <path d="M12 2v4m0 12v4M2 12h4m12 0h4"/>
            </svg>
            <span>{{ loading ? '登录中...' : '登 录' }}</span>
          </button>
        </form>

        <div class="divider"><span>或</span></div>

        <button type="button" class="btn-sso" @click="handleSSO">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="4"/><path d="M8 12h8M12 8v8"/>
          </svg>
          企业账号单点登录
        </button>

        <div class="signup-line">
          还没有账号？ <a class="signup-link">联系管理员申请开通</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authAPI } from '@/api'
import { useAppStore } from '@/stores/app'

const router = useRouter()
const store = useAppStore()

/* ========== Form State ========== */
const form = reactive({ username: '', password: '' })
const showPassword = ref(false)
const rememberMe = ref(false)
const loading = ref(false)
const errorMsg = ref('')
const loginResult = ref<'idle'|'success'|'error'>('idle')

/* ========== Animation State ========== */
const mouseX = ref(0)
const mouseY = ref(0)
const isEmailFocused = ref(false)
const isPasswordFocused = ref(false)
const isLooking = ref(false)
const isAlive = ref(true)

/* ========== Refs ========== */
const purpleRef = ref<HTMLDivElement>()
const blackRef = ref<HTMLDivElement>()
const orangeRef = ref<HTMLDivElement>()
const yellowRef = ref<HTMLDivElement>()
const yMouthRef = ref<HTMLDivElement>()

const pPupilL = ref<HTMLDivElement>()
const pPupilR = ref<HTMLDivElement>()
const bPupilL = ref<HTMLDivElement>()
const bPupilR = ref<HTMLDivElement>()
const oPupilL = ref<HTMLDivElement>()
const oPupilR = ref<HTMLDivElement>()
const yPupilL = ref<HTMLDivElement>()
const yPupilR = ref<HTMLDivElement>()

/* ========== Blinking ========== */
const blinking = reactive({ purple: false, black: false })
let blinkTimers: number[] = []
let rafId = 0

/* ========== Eye Tracking (RAF) ========== */
function calcEyeOffset(el: HTMLElement | undefined, maxDist: number) {
  if (!el) return { x: 0, y: 0 }
  const rect = el.getBoundingClientRect()
  const cx = rect.left + rect.width / 2
  const cy = rect.top + rect.height / 2
  const dx = mouseX.value - cx
  const dy = mouseY.value - cy
  const dist = Math.min(Math.sqrt(dx * dx + dy * dy), maxDist)
  if (dist === 0) return { x: 0, y: 0 }
  const angle = Math.atan2(dy, dx)
  return { x: Math.cos(angle) * dist, y: Math.sin(angle) * dist }
}

function setPupil(el: HTMLDivElement | undefined, o: { x: number; y: number }) {
  if (!el) return
  el.style.transform = `translate(${o.x}px, ${o.y}px)`
}

function updateAllEyes() {
  if (!isAlive.value) return
  const showing = showPassword.value && form.password.length > 0
  const email = isEmailFocused.value
  const err = loginResult.value === 'error'
  const succ = loginResult.value === 'success'
  const looking = isLooking.value

  if (err || succ) {
    ;[pPupilL,pPupilR,bPupilL,bPupilR,oPupilL,oPupilR,yPupilL,yPupilR].forEach(p => setPupil(p.value, {x:0,y:0}))
    return
  }

  if (showing) {
    setPupil(pPupilL.value, {x:-5,y:-5}); setPupil(pPupilR.value, {x:-5,y:-5})
    setPupil(bPupilL.value, {x:-4,y:-4}); setPupil(bPupilR.value, {x:-4,y:-4})
    setPupil(oPupilL.value, {x:-5,y:-4}); setPupil(oPupilR.value, {x:-5,y:-4})
    setPupil(yPupilL.value, {x:-5,y:-4}); setPupil(yPupilR.value, {x:-5,y:-4})
    return
  }

  if (looking) {
    setPupil(pPupilL.value, {x:3,y:4}); setPupil(pPupilR.value, {x:3,y:4})
    setPupil(bPupilL.value, {x:0,y:-4}); setPupil(bPupilR.value, {x:0,y:-4})
    return
  }

  const fp = email ? {x:5,y:-2} : undefined
  setPupil(pPupilL.value, fp || calcEyeOffset(pPupilL.value, 7))
  setPupil(pPupilR.value, fp || calcEyeOffset(pPupilR.value, 7))
  setPupil(bPupilL.value, fp || calcEyeOffset(bPupilL.value, 6))
  setPupil(bPupilR.value, fp || calcEyeOffset(bPupilR.value, 6))
  setPupil(oPupilL.value, fp || calcEyeOffset(oPupilL.value, 7))
  setPupil(oPupilR.value, fp || calcEyeOffset(oPupilR.value, 7))
  setPupil(yPupilL.value, fp || calcEyeOffset(yPupilL.value, 6))
  setPupil(yPupilR.value, fp || calcEyeOffset(yPupilR.value, 6))
}

function animateLoop() {
  if (!isAlive.value) return
  updateAllEyes()
  rafId = requestAnimationFrame(animateLoop)
}

function onMouseMove(e: MouseEvent) {
  mouseX.value = e.clientX
  mouseY.value = e.clientY
}

/* ========== Blink Scheduler ========== */
function scheduleBlink(char: 'purple' | 'black') {
  const delay = 2500 + Math.random() * 5000
  const t = window.setTimeout(() => {
    if (!isAlive.value) return
    blinking[char] = true
    setTimeout(() => { blinking[char] = false; if (isAlive.value) scheduleBlink(char) }, 150)
  }, delay)
  blinkTimers.push(t)
}

/* ========== Focus Handlers ========== */
function onEmailFocus() {
  isEmailFocused.value = true
  isLooking.value = true
  setTimeout(() => { if (isAlive.value) isLooking.value = false }, 800)
}
function onEmailBlur() {
  isEmailFocused.value = false
  isLooking.value = false
}

/* ========== Computed Classes ========== */
const eyeClasses = computed(() => {
  const peek = showPassword.value && form.password.length > 0
  const err = loginResult.value === 'error'
  const succ = loginResult.value === 'success'
  const email = isEmailFocused.value
  const mk = (char: string) => ({
    wide: email && !err && !succ,
    squint: err,
    happy: succ,
    closed: peek && !err && !succ && (char === 'purple' || char === 'black'),
    blink: (blinking as any)[char] && !err && !succ && !peek,
  })
  return { orange: mk('orange'), purple: mk('purple'), black: mk('black'), yellow: mk('yellow') }
})

const mouthClasses = computed(() => {
  const err = loginResult.value === 'error'
  const succ = loginResult.value === 'success'
  const peek = showPassword.value && form.password.length > 0
  return {
    orange: { smile: !err && !succ, happy: succ, sad: err, flat: peek },
    purple: { flat: !err && !succ && !peek, happy: succ, sad: err, dot: peek },
    black: { dot: !err && !succ && !peek, happy: succ, sad: err, flat: peek },
    yellow: { flat: !err && !succ && !peek, happy: succ, sad: err, smile: peek },
  }
})

const charClasses = computed(() => {
  const err = loginResult.value === 'error'
  const succ = loginResult.value === 'success'
  const email = isEmailFocused.value
  const pwd = isPasswordFocused.value
  const peek = showPassword.value && form.password.length > 0
  return {
    orange: { 'tilt-right': email && !peek, 'lean-forward': pwd && !peek, shake: err, bounce: succ, 'hide-peek': peek },
    purple: { 'tilt-right': email && !peek, 'lean-forward': pwd && !peek, shake: err, bounce: succ, 'hide-peek': peek, 'look-each': isLooking.value },
    black: { 'tilt-right': email && !peek, 'lean-forward': pwd && !peek, shake: err, bounce: succ, 'hide-peek': peek, 'look-each': isLooking.value },
    yellow: { 'tilt-right': email && !peek, 'lean-forward': pwd && !peek, shake: err, bounce: succ, 'hide-peek': peek },
  }
})

/* ========== Login Handler ========== */
async function handleLogin() {
  errorMsg.value = ''
  loginResult.value = 'idle'
  if (!form.username || !form.password) { errorMsg.value = '请输入账号和密码'; return }
  loading.value = true
  try {
    const res: any = await authAPI.login(form.username, form.password)
    store.setToken(res.access_token)
    store.setUserInfo(res.username || form.username, res.user_role)
    loginResult.value = 'success'
    const homeMap: Record<string, string> = { admin: '/dashboard', manager: '/boss', driver: '/driver-app', warehouse: '/warehouse', customer: '/customer-app' }
    const isMobile = window.innerWidth < 768 || /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent)
    const target = isMobile ? '/mobile' : (homeMap[res.user_role] || '/dashboard')
    setTimeout(() => { ElMessage.success('登录成功'); router.push(target) }, 1500)
  } catch {
    const validUsers: Record<string, string> = { admin: 'admin', driver01: 'driver', manager01: 'manager', warehouse01: 'warehouse', customer01: 'customer' }
    const valid = validUsers[form.username] && form.password === '123456'
    if (valid) {
      loginResult.value = 'success'
      const role = validUsers[form.username]
      const homeMap: Record<string, string> = { admin: '/dashboard', manager: '/boss', driver: '/driver-app', warehouse: '/warehouse', customer: '/customer-app' }
      const isMobile = window.innerWidth < 768 || /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent)
      const target = isMobile ? '/mobile' : (homeMap[role] || '/dashboard')
      store.setToken('mock-token-' + form.username)
      store.setUserInfo(form.username, role)
      setTimeout(() => { ElMessage.success('登录成功'); router.push(target) }, 1500)
    } else {
      loginResult.value = 'error'
      errorMsg.value = '账号或密码错误，请重试'
      setTimeout(() => { loginResult.value = 'idle' }, 2500)
    }
  } finally { loading.value = false }
}

function handleSSO() { ElMessage.info('企业单点登录功能开发中') }

/* ========== Lifecycle ========== */
onMounted(() => {
  rafId = requestAnimationFrame(animateLoop)
  scheduleBlink('purple')
  scheduleBlink('black')
})

onUnmounted(() => {
  isAlive.value = false
  cancelAnimationFrame(rafId)
  blinkTimers.forEach(clearTimeout)
})
</script>

<style scoped>
/* ==================== Layout ==================== */
.login-page {
  display: grid;
  grid-template-columns: 1fr 1fr;
  min-height: 100vh;
  overflow: hidden;
  background: #fff;
}

/* ==================== Left Panel - Dark Blue Gradient ==================== */
.left-panel {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 48px;
  background: linear-gradient(145deg, #0f172a 0%, #1e3a8a 50%, #1e40af 100%);
  overflow: hidden;
}

/* Decorative blurs */
.decor-blur {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  pointer-events: none;
  z-index: 0;
}
.decor-blur-1 { top: 10%; right: -5%; width: 320px; height: 320px; background: rgba(59,130,246,0.25); }
.decor-blur-2 { bottom: 5%; left: -10%; width: 400px; height: 400px; background: rgba(30,64,175,0.35); }
.decor-grid {
  position: absolute; inset: 0;
  background-image: linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
  background-size: 48px 48px;
  pointer-events: none;
  z-index: 1;
}

/* Brand */
.lp-brand {
  position: relative; z-index: 10;
  display: flex; align-items: center; gap: 12px;
}
.lp-brand-icon {
  width: 40px; height: 40px;
  border-radius: 10px;
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.2);
  display: flex; align-items: center; justify-content: center;
  color: rgba(255,255,255,0.9);
  backdrop-filter: blur(8px);
}
.lp-brand-name {
  font-size: 20px; font-weight: 700;
  color: #fff; letter-spacing: 0.5px;
}

/* Footer */
.lp-footer {
  position: relative; z-index: 10;
  display: flex; align-items: center; gap: 12px;
  font-size: 13px; color: rgba(255,255,255,0.4);
}
.lp-footer .sep { color: rgba(255,255,255,0.2); }
.lp-footer span { cursor: pointer; transition: color 0.2s; }
.lp-footer span:hover { color: rgba(255,255,255,0.75); }

/* ==================== Characters ==================== */
.chars-stage {
  position: relative; z-index: 10;
  flex: 1;
  display: flex; align-items: flex-end; justify-content: center;
  min-height: 380px;
}

.char {
  position: absolute; bottom: 0;
  transition: transform 0.5s cubic-bezier(0.4,0,0.2,1), left 0.5s cubic-bezier(0.4,0,0.2,1), height 0.5s cubic-bezier(0.4,0,0.2,1);
  transform-origin: bottom center;
}

.char-purple { left: 70px;  width: 140px; height: 340px; background: #6C3FF5; border-radius: 14px 14px 0 0; z-index: 1; }
.char-black  { left: 210px; width: 90px;  height: 260px; background: #2D2D2D; border-radius: 10px 10px 0 0; z-index: 2; }
.char-orange { left: 5px;   width: 200px; height: 160px; background: #FF9B6B; border-radius: 100px 100px 0 0; z-index: 4; }
.char-yellow { left: 280px; width: 120px; height: 190px; background: #E8D754; border-radius: 60px 60px 0 0; z-index: 3; }

/* Face & Eyes */
.char-face { position: relative; width: 100%; height: 100%; }
.eyes-row { position: absolute; display: flex; transition: all 0.4s cubic-bezier(0.4,0,0.2,1); }

.char-purple .eyes-row { top: 44px; left: 28px; gap: 32px; }
.char-black .eyes-row  { top: 36px; left: 16px; gap: 22px; }
.char-orange .eyes-row { top: 42px; left: 54px; gap: 34px; }
.char-yellow .eyes-row { top: 38px; left: 28px; gap: 24px; }

.eye {
  background: #fff; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  overflow: hidden; transition: all 0.3s ease; position: relative;
}
.char-purple .eye { width: 22px; height: 22px; }
.char-black .eye  { width: 20px; height: 20px; }
.char-orange .eye { width: 18px; height: 18px; }
.char-yellow .eye { width: 18px; height: 18px; }

.eye.wide { transform: scale(1.45); }
.eye.squint, .eye.closed, .eye.blink { height: 4px !important; border-radius: 2px; }
.eye.happy {
  height: 12px !important; border-radius: 50% 50% 0 0;
  background: transparent; border-top: 4px solid #2D2D2D;
}
.eye.happy .pupil, .eye.squint .pupil, .eye.closed .pupil, .eye.blink .pupil { display: none; }

.pupil {
  background: #2D2D2D; border-radius: 50%;
  flex-shrink: 0; will-change: transform;
}
.char-purple .pupil { width: 10px; height: 10px; }
.char-black .pupil  { width: 8px; height: 8px; }
.char-orange .pupil { width: 8px; height: 8px; }
.char-yellow .pupil { width: 8px; height: 8px; }

/* Mouth */
.mouth {
  position: absolute;
  transition: all 0.4s ease;
}

/* Mouth shapes */
.mouth.smile {
  width: 30px; height: 12px;
  border-bottom: 3px solid #2D2D2D;
  border-radius: 0 0 50% 50%;
}
.mouth.flat {
  width: 22px; height: 4px;
  background: #2D2D2D;
  border-radius: 2px;
}
.mouth.dot {
  width: 6px; height: 6px;
  background: #2D2D2D;
  border-radius: 50%;
}
.mouth.happy {
  width: 34px; height: 14px;
  border-bottom: 4px solid #2D2D2D;
  border-radius: 0 0 50% 50%;
}
.mouth.sad {
  width: 24px; height: 10px;
  border-top: 3px solid #2D2D2D;
  border-radius: 50% 50% 0 0;
}

/* Mouth positions */
.char-orange .mouth { top: 72px; left: 58px; }
.char-orange .mouth.happy { left: 56px; }
.char-orange .mouth.sad { left: 60px; }

.char-purple .mouth { top: 84px; left: 32px; }
.char-purple .mouth.happy { left: 28px; }
.char-purple .mouth.sad { left: 34px; }

.char-black .mouth { top: 68px; left: 28px; }
.char-black .mouth.happy { left: 24px; }
.char-black .mouth.sad { left: 28px; }

.char-yellow .mouth { top: 68px; left: 32px; }
.char-yellow .mouth.happy { left: 28px; }
.char-yellow .mouth.sad { left: 32px; }

/* Body animations */
.char.tilt-right { transform: skewX(-10deg) rotate(-6deg) translateX(18px) !important; }
.char.lean-forward { transform: skewX(-5deg) translateY(-18px) !important; }
.char.hide-peek { transform: skewX(5deg) rotate(3deg) translateX(-10px) !important; }
.char.look-each { transform: translateX(-4px) !important; }

.char.shake {
  animation: shake 0.5s ease-in-out;
}
.char.bounce {
  animation: bounce 0.7s ease-in-out;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-14px) rotate(-3deg); }
  40% { transform: translateX(10px) rotate(2deg); }
  60% { transform: translateX(-8px) rotate(-1deg); }
  80% { transform: translateX(6px) rotate(1deg); }
}

@keyframes bounce {
  0% { transform: translateY(0) scaleY(1); }
  30% { transform: translateY(-40px) scaleY(0.85); }
  50% { transform: translateY(-5px) scaleY(1.05); }
  70% { transform: translateY(-25px) scaleY(0.95); }
  85% { transform: translateY(-2px) scaleY(1.02); }
  100% { transform: translateY(0) scaleY(1); }
}

/* ==================== Right Panel ==================== */
.right-panel {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px;
}

.form-card {
  width: 100%;
  max-width: 400px;
  padding: 40px 0;
}

.mob-brand {
  display: none;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 32px;
  font-size: 18px;
  font-weight: 700;
  color: #1a1a2e;
}

.form-header {
  text-align: center;
  margin-bottom: 28px;
}
.form-header h1 {
  font-size: 24px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 6px;
}
.form-header p {
  font-size: 13px;
  color: #888;
}

/* Form */
.form-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* Field Group */
.field-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.field-label {
  font-size: 12px;
  font-weight: 600;
  color: #444;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding-left: 4px;
}

/* Input Box (rounded) */
.input-box {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 48px;
  padding: 0 16px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  transition: border-color 0.25s, box-shadow 0.25s;
}
.input-box:focus-within {
  border-color: #6C3FF5;
  box-shadow: 0 0 0 3px rgba(108,63,245,0.1);
  background: #fff;
}
.input-icon {
  color: #9ca3af;
  flex-shrink: 0;
  transition: color 0.25s;
}
.input-box:focus-within .input-icon {
  color: #6C3FF5;
}

.form-input {
  flex: 1;
  height: 100%;
  background: transparent;
  border: none;
  outline: none;
  font-size: 15px;
  color: #1a1a2e;
}
.form-input::placeholder {
  color: #bbb;
}

.eye-toggle {
  background: none;
  border: none;
  cursor: pointer;
  color: #999;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
  flex-shrink: 0;
}
.eye-toggle:hover { color: #444; }

/* Options */
.form-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
}
.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: #555;
}
.checkbox-label input {
  width: 16px;
  height: 16px;
  accent-color: #6C3FF5;
  cursor: pointer;
}
/* Divider */
.divider {
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 8px 0;
  color: #bbb;
  font-size: 13px;
}
.divider::before,
.divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background: #e5e7eb;
}

/* SSO Button */
.btn-sso {
  width: 100%;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: #fff;
  border: 1px solid #e5e5e5;
  border-radius: 12px;
  font-size: 14px;
  color: #555;
  cursor: pointer;
  transition: all 0.25s;
  font-weight: 500;
}
.btn-sso:hover {
  background: #fafafa;
  border-color: #ccc;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

/* Spinner */
.spinner {
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Error */
.error-msg {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  font-size: 12px;
  color: #dc2626;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 10px;
}

/* Submit Button */
.btn-submit {
  width: 100%;
  height: 48px;
  background: #1a1a2e;
  border: none;
  border-radius: 12px;
  color: #fff;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.25s;
  margin-top: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.btn-submit:hover:not(:disabled) {
  background: #2a2a3e;
  transform: translateY(-1px);
}
.btn-submit:active:not(:disabled) { transform: translateY(0); }
.btn-submit:disabled { opacity: 0.6; cursor: not-allowed; }



/* Sign Up */
.signup-line {
  text-align: center;
  font-size: 13px;
  color: #888;
  margin-top: 24px;
}
.signup-link {
  color: #6C3FF5;
  font-weight: 600;
  cursor: pointer;
}
.signup-link:hover { text-decoration: underline; }

/* ==================== Responsive ==================== */
@media (max-width: 1024px) {
  .login-page {
    grid-template-columns: 1fr;
  }
  .left-panel {
    display: none;
  }
  .mob-brand {
    display: flex;
  }
  .right-panel {
    padding: 24px 20px;
  }
  .form-card {
    padding: 32px 24px;
  }
}
</style>