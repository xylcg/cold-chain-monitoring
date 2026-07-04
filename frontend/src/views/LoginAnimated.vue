<template>
  <div class="login-page" @mousemove="onMouseMove">
    <!-- ===== 左侧：卡通角色区 ===== -->
    <div class="left-panel">
      <div class="lp-inner">
        <!-- Brand -->
        <div class="lp-brand">
          <div class="lp-brand-icon">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
            </svg>
          </div>
          <span class="lp-brand-name">YourBrand</span>
        </div>

        <!-- Characters Stage -->
        <div class="chars-stage">
          <!-- Orange Semi-circle -->
          <div ref="orangeRef" class="char char-orange" :class="charClasses.orange" :style="charTransforms.orange">
            <div class="char-face">
              <div class="eyes-row">
                <div ref="oEyeL" class="eye" :class="eyeClasses.orange"><div class="pupil" :style="pupilStyle('oL')"></div></div>
                <div ref="oEyeR" class="eye" :class="eyeClasses.orange"><div class="pupil" :style="pupilStyle('oR')"></div></div>
              </div>
              <div class="mouth" :class="mouthClasses.orange"></div>
            </div>
          </div>

          <!-- Purple Rectangle -->
          <div ref="purpleRef" class="char char-purple" :class="charClasses.purple" :style="charTransforms.purple">
            <div class="char-face">
              <div class="eyes-row">
                <div ref="pEyeL" class="eye" :class="eyeClasses.purple"><div class="pupil" :style="pupilStyle('pL')"></div></div>
                <div ref="pEyeR" class="eye" :class="eyeClasses.purple"><div class="pupil" :style="pupilStyle('pR')"></div></div>
              </div>
              <div class="mouth" :class="mouthClasses.purple"></div>
            </div>
          </div>

          <!-- Black Vertical Rectangle -->
          <div ref="blackRef" class="char char-black" :class="charClasses.black" :style="charTransforms.black">
            <div class="char-face">
              <div class="eyes-row">
                <div ref="bEyeL" class="eye" :class="eyeClasses.black"><div class="pupil" :style="pupilStyle('bL')"></div></div>
                <div ref="bEyeR" class="eye" :class="eyeClasses.black"><div class="pupil" :style="pupilStyle('bR')"></div></div>
              </div>
              <div class="mouth" :class="mouthClasses.black"></div>
            </div>
          </div>

          <!-- Yellow Rounded Rectangle -->
          <div ref="yellowRef" class="char char-yellow" :class="charClasses.yellow" :style="charTransforms.yellow">
            <div class="char-face">
              <div class="eyes-row">
                <div ref="yEyeL" class="eye" :class="eyeClasses.yellow"><div class="pupil" :style="pupilStyle('yL')"></div></div>
                <div ref="yEyeR" class="eye" :class="eyeClasses.yellow"><div class="pupil" :style="pupilStyle('yR')"></div></div>
              </div>
              <div class="mouth" :class="mouthClasses.yellow"></div>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="lp-footer">
          <span>Privacy Policy</span>
          <span class="sep">·</span>
          <span>Terms of Service</span>
          <span class="sep">·</span>
          <span>Contact</span>
        </div>
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
          <h1>欢迎回来！</h1>
          <p>请输入您的账号信息</p>
        </div>

        <form @submit.prevent="handleLogin" class="form-body">
          <div class="field">
            <label>账号</label>
              <input
                v-model="form.username"
                type="text"
                placeholder="请输入账号"
              class="form-input"
              @focus="isEmailFocused = true"
              @blur="isEmailFocused = false"
              autocomplete="off"
              required
            />
          </div>

          <div class="field">
            <label>密码</label>
            <div class="input-wrap">
              <input
                v-model="form.password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="请输入密码"
                class="form-input"
                @focus="isPasswordFocused = true"
                @blur="isPasswordFocused = false"
                required
              />
              <button type="button" class="eye-toggle" @click="showPassword = !showPassword">
                <svg v-if="!showPassword" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>
                </svg>
                <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                  <line x1="1" y1="1" x2="23" y2="23"/>
                </svg>
              </button>
            </div>
          </div>

          <div class="form-options">
            <label class="checkbox-label">
              <input type="checkbox" v-model="rememberMe" />
              <span>Remember for 30 days</span>
            </label>
            <a class="forgot-link">Forgot password?</a>
          </div>

          <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>

          <button type="submit" class="btn-submit" :disabled="loading">
            <span v-if="!loading">登 录</span>
            <span v-else>登录中...</span>
          </button>
        </form>

        <div class="signup-line">
          还没有账号？ <a class="signup-link">联系管理员</a>
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

/* ========== Animation State ========== */
const mouseX = ref(0)
const mouseY = ref(0)
const isEmailFocused = ref(false)
const isPasswordFocused = ref(false)
const loginResult = ref<'idle'|'success'|'error'>('idle')

const blinking = reactive({ orange: false, purple: false, black: false, yellow: false })

/* ========== Refs ========== */
const orangeRef = ref<HTMLDivElement>()
const purpleRef = ref<HTMLDivElement>()
const blackRef = ref<HTMLDivElement>()
const yellowRef = ref<HTMLDivElement>()

const oEyeL = ref<HTMLDivElement>()
const oEyeR = ref<HTMLDivElement>()
const pEyeL = ref<HTMLDivElement>()
const pEyeR = ref<HTMLDivElement>()
const bEyeL = ref<HTMLDivElement>()
const bEyeR = ref<HTMLDivElement>()
const yEyeL = ref<HTMLDivElement>()
const yEyeR = ref<HTMLDivElement>()

/* ========== Pupil Offsets ========== */
const pupils = reactive({
  oL: { x: 0, y: 0 }, oR: { x: 0, y: 0 },
  pL: { x: 0, y: 0 }, pR: { x: 0, y: 0 },
  bL: { x: 0, y: 0 }, bR: { x: 0, y: 0 },
  yL: { x: 0, y: 0 }, yR: { x: 0, y: 0 },
})

function pupilStyle(key: string) {
  const p = pupils[key as keyof typeof pupils]
  return { transform: `translate(${p.x}px, ${p.y}px)` }
}

/* ========== Mouse Tracking ========== */
function calcOffset(eyeEl: HTMLDivElement | undefined, maxDist: number, forced?: { x: number; y: number }) {
  if (!eyeEl || !isAlive.value) return { x: 0, y: 0 }
  if (forced) return forced
  try {
    const rect = eyeEl.getBoundingClientRect()
    const cx = rect.left + rect.width / 2
    const cy = rect.top + rect.height / 2
    const dx = mouseX.value - cx
    const dy = mouseY.value - cy
    const dist = Math.min(Math.sqrt(dx * dx + dy * dy), maxDist)
    const angle = Math.atan2(dy, dx)
    return { x: Math.cos(angle) * dist, y: Math.sin(angle) * dist }
  } catch {
    return { x: 0, y: 0 }
  }
}

const isAlive = ref(true)
onUnmounted(() => { isAlive.value = false })

function onMouseMove(e: MouseEvent) {
  if (!isAlive.value) return
  mouseX.value = e.clientX
  mouseY.value = e.clientY
  updatePupils()
}

function updatePupils() {
  const peek = showPassword.value && form.password.length > 0
  const email = isEmailFocused.value
  const err = loginResult.value === 'error'
  const succ = loginResult.value === 'success'

  // When error or success, eyes don't track
  if (err || succ) {
    pupils.oL = { x: 0, y: 0 }; pupils.oR = { x: 0, y: 0 }
    pupils.pL = { x: 0, y: 0 }; pupils.pR = { x: 0, y: 0 }
    pupils.bL = { x: 0, y: 0 }; pupils.bR = { x: 0, y: 0 }
    pupils.yL = { x: 0, y: 0 }; pupils.yR = { x: 0, y: 0 }
    return
  }

  // Orange: peeks when password shown, otherwise tracks or looks right on email focus
  pupils.oL = calcOffset(oEyeL.value, 7, peek ? { x: 5, y: 0 } : email ? { x: 6, y: -2 } : undefined)
  pupils.oR = calcOffset(oEyeR.value, 7, peek ? { x: 5, y: 0 } : email ? { x: 6, y: -2 } : undefined)

  // Others: closed when peeking, otherwise track or look right on email focus
  pupils.pL = calcOffset(pEyeL.value, 7, email ? { x: 6, y: -2 } : undefined)
  pupils.pR = calcOffset(pEyeR.value, 7, email ? { x: 6, y: -2 } : undefined)
  pupils.bL = calcOffset(bEyeL.value, 6, email ? { x: 5, y: -2 } : undefined)
  pupils.bR = calcOffset(bEyeR.value, 6, email ? { x: 5, y: -2 } : undefined)
  pupils.yL = calcOffset(yEyeL.value, 6, email ? { x: 5, y: -2 } : undefined)
  pupils.yR = calcOffset(yEyeR.value, 6, email ? { x: 5, y: -2 } : undefined)
}

/* ========== Blinking ========== */
function scheduleBlink(char: 'orange'|'purple'|'black'|'yellow') {
  const delay = 3000 + Math.random() * 4000
  setTimeout(() => {
    blinking[char] = true
    setTimeout(() => { blinking[char] = false; scheduleBlink(char) }, 150)
  }, delay)
}

/* ========== Character Classes & Transforms ========== */
const eyeClasses = computed(() => {
  const peek = showPassword.value && form.password.length > 0
  const err = loginResult.value === 'error'
  const succ = loginResult.value === 'success'
  const email = isEmailFocused.value

  return {
    orange: {
      wide: email && !err && !succ,
      squint: err,
      happy: succ,
      blink: blinking.orange && !err && !succ && !peek,
    },
    purple: {
      wide: email && !err && !succ,
      closed: peek && !err && !succ,
      squint: err,
      happy: succ,
      blink: blinking.purple && !err && !succ && !peek,
    },
    black: {
      wide: email && !err && !succ,
      closed: peek && !err && !succ,
      squint: err,
      happy: succ,
      blink: blinking.black && !err && !succ && !peek,
    },
    yellow: {
      wide: email && !err && !succ,
      closed: peek && !err && !succ,
      squint: err,
      happy: succ,
      blink: blinking.yellow && !err && !succ && !peek,
    },
  }
})

const mouthClasses = computed(() => {
  const err = loginResult.value === 'error'
  const succ = loginResult.value === 'success'
  return {
    orange: { smile: !err && !succ, happy: succ, sad: err },
    purple: { flat: !err && !succ, happy: succ, sad: err },
    black: { dot: !err && !succ, happy: succ, sad: err },
    yellow: { flat: !err && !succ, happy: succ, sad: err },
  }
})

const charClasses = computed(() => {
  const err = loginResult.value === 'error'
  const succ = loginResult.value === 'success'
  const email = isEmailFocused.value
  const pwd = isPasswordFocused.value
  return {
    orange: { 'tilt-right': email, 'lean-forward': pwd, shake: err, bounce: succ },
    purple: { 'tilt-right': email, 'lean-forward': pwd, shake: err, bounce: succ },
    black: { 'tilt-right': email, 'lean-forward': pwd, shake: err, bounce: succ },
    yellow: { 'tilt-right': email, 'lean-forward': pwd, shake: err, bounce: succ },
  }
})

const charTransforms = computed(() => {
  // Body tracking: lean toward mouse
  const calcLean = (refEl: HTMLDivElement | undefined) => {
    if (!refEl || !isAlive.value || isEmailFocused.value || isPasswordFocused.value || loginResult.value !== 'idle') return ''
    try {
      const rect = refEl.getBoundingClientRect()
      const cx = rect.left + rect.width / 2
      const dx = mouseX.value - cx
      const skew = Math.max(-8, Math.min(8, -dx / 100))
      return `skewX(${skew}deg)`
    } catch {
      return ''
    }
  }
  return {
    orange: { transform: calcLean(orangeRef.value) },
    purple: { transform: calcLean(purpleRef.value) },
    black: { transform: calcLean(blackRef.value) },
    yellow: { transform: calcLean(yellowRef.value) },
  }
})

/* ========== Login Handler ========== */
async function handleLogin() {
  errorMsg.value = ''
  loginResult.value = 'idle'
  if (!form.username || !form.password) {
    errorMsg.value = '请输入账号和密码'
    return
  }
  loading.value = true
  try {
    const res: any = await authAPI.login(form.username, form.password)
    store.setToken(res.access_token)
    store.setUserInfo(res.username || form.username, res.user_role)
    loginResult.value = 'success'
    const homeMap: Record<string, string> = { admin: '/dashboard', manager: '/boss', driver: '/driver-app', warehouse: '/warehouse', customer: '/customer-app' }
    const homePath = homeMap[res.user_role] || '/dashboard'
    setTimeout(() => {
      ElMessage.success('登录成功')
      router.push(homePath)
    }, 1500)
  } catch {
    // Fallback: allow default credentials without backend
    const validUsers: Record<string, string> = {
      admin: 'admin',
      driver01: 'driver',
      manager01: 'manager',
      warehouse01: 'warehouse',
      customer01: 'customer',
    }
    const valid = validUsers[form.username] && form.password === '123456'
    if (valid) {
      loginResult.value = 'success'
      const role = validUsers[form.username]
      const homeMap: Record<string, string> = { admin: '/dashboard', manager: '/boss', driver: '/driver-app', warehouse: '/warehouse', customer: '/customer-app' }
      store.setToken('mock-token-' + form.username)
      store.setUserInfo(form.username, role)
      setTimeout(() => {
        ElMessage.success('登录成功')
        router.push(homeMap[role] || '/dashboard')
      }, 1500)
    } else {
      loginResult.value = 'error'
      errorMsg.value = '账号或密码错误，请重试。'
      setTimeout(() => { loginResult.value = 'idle' }, 2500)
    }
  } finally {
    loading.value = false
  }
}

/* ========== Lifecycle ========== */
onMounted(() => {
  updatePupils()
  scheduleBlink('orange')
  scheduleBlink('purple')
  scheduleBlink('black')
  scheduleBlink('yellow')
})
</script>

<style scoped>
/* ==================== Layout ==================== */
.login-page {
  display: grid;
  grid-template-columns: 1fr 1fr;
  min-height: 100vh;
  overflow: hidden;
}

/* ==================== Left Panel ==================== */
.left-panel {
  background: #F5F3FF;
  display: flex;
  flex-direction: column;
  position: relative;
}

.lp-inner {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 40px 48px;
}

.lp-brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.lp-brand-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(108, 63, 245, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6C3FF5;
}

.lp-brand-name {
  font-size: 20px;
  font-weight: 700;
  color: #1a1a2e;
  letter-spacing: 0.02em;
}

.lp-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #888;
}
.lp-footer .sep { color: #ccc; }

/* ==================== Characters ==================== */
.chars-stage {
  flex: 1;
  position: relative;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  min-height: 340px;
}

.char {
  position: absolute;
  bottom: 0;
  transition: all 0.6s cubic-bezier(0.4, 0, 0.2, 1);
  transform-origin: bottom center;
}

/* Orange Semi-circle - front left */
.char-orange {
  left: 25px;
  width: 180px;
  height: 135px;
  background: #FF9B6B;
  border-radius: 90px 90px 0 0;
  z-index: 4;
}

/* Purple Rectangle - back left */
.char-purple {
  left: 145px;
  width: 115px;
  height: 240px;
  background: #6C3FF5;
  border-radius: 14px 14px 0 0;
  z-index: 1;
}

/* Black Vertical Rectangle - middle */
.char-black {
  left: 240px;
  width: 76px;
  height: 190px;
  background: #2D2D2D;
  border-radius: 10px 10px 0 0;
  z-index: 2;
}

/* Yellow Rounded Rectangle - front right */
.char-yellow {
  left: 295px;
  width: 105px;
  height: 165px;
  background: #E8D754;
  border-radius: 52px 52px 0 0;
  z-index: 3;
}

/* Face container */
.char-face {
  position: relative;
  width: 100%;
  height: 100%;
}

/* Eyes row */
.eyes-row {
  position: absolute;
  display: flex;
  gap: 20px;
  transition: all 0.5s;
}

.char-orange .eyes-row { top: 36px; left: 44px; gap: 30px; }
.char-purple .eyes-row { top: 44px; left: 22px; gap: 28px; }
.char-black .eyes-row { top: 38px; left: 14px; gap: 18px; }
.char-yellow .eyes-row { top: 36px; left: 22px; gap: 22px; }

/* Eye */
.eye {
  width: 20px;
  height: 20px;
  background: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  transition: all 0.3s ease;
  position: relative;
}

.char-purple .eye { width: 22px; height: 22px; }
.char-black .eye { width: 20px; height: 20px; }
.char-yellow .eye { width: 18px; height: 18px; }

/* Eye states */
.eye.wide { transform: scale(1.45); }
.eye.squint,
.eye.closed,
.eye.blink { height: 4px !important; border-radius: 2px; }
.eye.happy {
  height: 12px !important;
  border-radius: 50% 50% 0 0;
  background: transparent;
  border-top: 4px solid #2D2D2D;
}
.eye.happy .pupil { display: none; }
.eye.squint .pupil,
.eye.closed .pupil,
.eye.blink .pupil { display: none; }

/* Pupil */
.pupil {
  width: 8px;
  height: 8px;
  background: #2D2D2D;
  border-radius: 50%;
  transition: transform 0.08s ease-out;
  flex-shrink: 0;
}

.char-purple .pupil { width: 10px; height: 10px; }
.char-black .pupil { width: 8px; height: 8px; }
.char-yellow .pupil { width: 7px; height: 7px; }

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

.field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.field label {
  font-size: 12px;
  font-weight: 600;
  color: #444;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.form-input {
  width: 100%;
  height: 42px;
  padding: 0 2px;
  background: transparent;
  border: none;
  border-bottom: 1px solid #ddd;
  border-radius: 0;
  font-size: 15px;
  color: #1a1a2e;
  outline: none;
  transition: border-color 0.25s;
}
.form-input:focus {
  border-bottom-color: #1a1a2e;
}
.form-input::placeholder {
  color: #bbb;
}

.input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}
.input-wrap .form-input {
  padding-right: 36px;
}

.eye-toggle {
  position: absolute;
  right: 12px;
  background: none;
  border: none;
  cursor: pointer;
  color: #999;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s;
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
.forgot-link {
  color: #6C3FF5;
  cursor: pointer;
  font-weight: 500;
}
.forgot-link:hover { text-decoration: underline; }

/* Error */
.error-msg {
  padding: 10px 14px;
  font-size: 12px;
  color: #dc2626;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
}

/* Submit Button */
.btn-submit {
  width: 100%;
  height: 48px;
  background: #1a1a2e;
  border: none;
  border-radius: 24px;
  color: #fff;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.25s;
  margin-top: 4px;
}
.btn-submit:hover:not(:disabled) {
  background: #2a2a3e;
  transform: translateY(-1px);
}
.btn-submit:active:not(:disabled) { transform: translateY(0); }
.btn-submit:disabled { opacity: 0.6; cursor: not-allowed; }

/* Google Button */
.btn-google {
  width: 100%;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: #fff;
  border: 1px solid #e5e5e5;
  border-radius: 24px;
  font-size: 14px;
  color: #555;
  cursor: pointer;
  transition: all 0.25s;
  margin-top: 16px;
  font-weight: 500;
}
.btn-google:hover {
  background: #fafafa;
  border-color: #ddd;
}

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
@media (max-width: 900px) {
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