<template>
  <div class="login-page">
    <!-- 极光背景 -->
    <div class="bg-aura aura-1"></div>
    <div class="bg-aura aura-2"></div>
    <div class="bg-aura aura-3"></div>

    <div class="login-wrapper">
      <div class="login-card">
        <div class="brand-area">
          <div class="brand-icon">
            <svg width="44" height="44" viewBox="0 0 48 48" fill="none">
              <rect x="3" y="3" width="42" height="42" rx="10" stroke="currentColor" stroke-width="2.5" />
              <rect x="16" y="16" width="16" height="16" rx="3" stroke="currentColor" stroke-width="1.5" opacity="0.4" />
              <circle cx="24" cy="24" r="3.5" fill="currentColor" />
            </svg>
          </div>
          <h1 class="brand-name">CRYO<span class="brand-accent">·TRACK</span></h1>
          <p class="brand-desc">冷链物流智能监控平台</p>
          <p class="brand-tech">Deep Learning · 全链路温控 · 实时预警</p>
        </div>

        <div class="split-line"></div>

        <el-form :model="form" :rules="rules" ref="formRef" @submit.prevent="handleLogin" class="login-form">
          <div class="field">
            <label>用户名</label>
            <el-input v-model="form.username" placeholder="请输入用户名" size="large" class="cust-input">
              <template #prefix>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
              </template>
            </el-input>
          </div>
          <div class="field">
            <label>密码</label>
            <el-input v-model="form.password" type="password" placeholder="请输入密码" size="large" show-password class="cust-input" @keyup.enter="handleLogin">
              <template #prefix>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
              </template>
            </el-input>
          </div>
          <button type="submit" class="submit-btn" :disabled="loading">
            <span v-if="!loading">进入系统</span>
            <span v-else class="loader"><i></i><i></i><i></i></span>
          </button>
        </el-form>

        <div class="hint-box">
          <div class="hint-line"><span class="hint-l">账号</span><code>admin / driver01 / manager01</code></div>
          <div class="hint-line"><span class="hint-l">密码</span><code>123456</code></div>
        </div>
      </div>
      <p class="footer-note">Intelligent Cold Chain Monitoring · Real-Time · Secure</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authAPI } from '@/api'
import { useAppStore } from '@/stores/app'

const router = useRouter()
const store = useAppStore()
const form = reactive({ username: 'admin', password: '123456' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}
const formRef = ref()
const loading = ref(false)

async function handleLogin() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    const res: any = await authAPI.login(form.username, form.password)
    store.setToken(res.access_token)
    store.username = res.username
    store.userRole = res.user_role
    ElMessage.success('登录成功')
    router.push('/dashboard')
  } catch {} finally { loading.value = false }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh; display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #eef2ff 0%, #e0f0ff 30%, #f0f4ff 60%, #ede9fe 100%);
  position: relative; overflow: hidden;
}

/* 极光背景 */
.bg-aura {
  position: absolute; border-radius: 50%; filter: blur(100px); opacity: 0.35; pointer-events: none;
}
.aura-1 { width: 600px; height: 600px; background: var(--accent); top: -20%; left: -10%; animation: drift1 16s ease-in-out infinite; }
.aura-2 { width: 500px; height: 500px; background: var(--aurora); bottom: -15%; right: -8%; animation: drift2 20s ease-in-out infinite; }
.aura-3 { width: 350px; height: 350px; background: var(--teal); top: 40%; left: 55%; animation: drift3 14s ease-in-out infinite; }

@keyframes drift1 { 0%,100% { transform: translate(0,0); } 50% { transform: translate(40px,-30px); } }
@keyframes drift2 { 0%,100% { transform: translate(0,0); } 50% { transform: translate(-30px,20px); } }
@keyframes drift3 { 0%,100% { transform: translate(0,0); } 50% { transform: translate(-20px,-15px); } }

.login-wrapper {
  position: relative; z-index: 1; display: flex; flex-direction: column; align-items: center; gap: 28px;
  animation: fadeInUp 0.5s ease-out;
}

.login-card {
  background: rgba(255,255,255,0.78);
  backdrop-filter: blur(30px) saturate(180%);
  -webkit-backdrop-filter: blur(30px) saturate(180%);
  border: 1px solid rgba(0,0,0,0.06);
  border-radius: var(--radius-xl);
  padding: 40px 38px 32px;
  width: 400px;
  box-shadow: 0 8px 40px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.04);
}

/* Brand */
.brand-area { text-align: center; margin-bottom: 24px; }
.brand-icon { color: var(--accent); display: inline-block; margin-bottom: 12px; }
.brand-name { font-family: var(--font-display); font-size: 26px; font-weight: 800; color: var(--text-title); letter-spacing: 0.06em; }
.brand-accent { color: var(--accent); }
.brand-desc { font-size: 13px; color: var(--text-secondary); margin: 6px 0 2px; }
.brand-tech { font-size: 10px; color: var(--text-muted); font-family: var(--font-mono); letter-spacing: 0.04em; }

.split-line {
  height: 1px; background: linear-gradient(90deg, transparent, rgba(0,0,0,0.08), transparent); margin-bottom: 24px;
}

/* Form */
.login-form { display: flex; flex-direction: column; gap: 16px; }
.field { display: flex; flex-direction: column; gap: 5px; }
.field label { font-size: 11px; font-weight: 600; color: var(--text-secondary); letter-spacing: 0.04em; text-transform: uppercase; }
.cust-input :deep(.el-input__wrapper) {
  background: rgba(0,0,0,0.03) !important; border: 1px solid rgba(0,0,0,0.06) !important;
  border-radius: 10px !important; box-shadow: none !important; padding: 4px 12px !important;
}
.cust-input :deep(.el-input__wrapper:hover) { border-color: var(--border-focus) !important; }
.cust-input :deep(.el-input.is-focus .el-input__wrapper) {
  border-color: var(--accent) !important; box-shadow: 0 0 0 3px var(--accent-glow) !important;
}
.cust-input :deep(.el-input__inner) { color: var(--text-primary) !important; font-family: var(--font-body) !important; font-size: 14px !important; }

/* Button */
.submit-btn {
  width: 100%; height: 46px;
  background: linear-gradient(135deg, var(--accent), #0088dd);
  border: none; border-radius: var(--radius);
  color: #fff; font-size: 15px; font-weight: 700; font-family: var(--font-body);
  letter-spacing: 0.08em; cursor: pointer;
  position: relative; overflow: hidden;
  transition: transform 0.2s, box-shadow 0.3s;
  margin-top: 4px;
  box-shadow: 0 2px 12px var(--accent-glow);
}
.submit-btn:hover { transform: translateY(-1px); box-shadow: 0 4px 20px rgba(0,168,255,0.35); }
.submit-btn:active { transform: translateY(0); }
.submit-btn:disabled { opacity: 0.7; cursor: not-allowed; }

.loader { display: flex; gap: 5px; justify-content: center; align-items: center; }
.loader i {
  width: 6px; height: 6px; border-radius: 50%; background: #fff;
  animation: dotBounce 1.4s ease-in-out infinite;
}
.loader i:nth-child(2) { animation-delay: 0.2s; }
.loader i:nth-child(3) { animation-delay: 0.4s; }
@keyframes dotBounce { 0%,80%,100% { opacity: 0.3; transform: scale(0.8); } 40% { opacity: 1; transform: scale(1); } }

/* Hints */
.hint-box { margin-top: 20px; display: flex; flex-direction: column; align-items: center; gap: 4px; }
.hint-line { display: flex; align-items: center; gap: 8px; font-size: 11px; }
.hint-l { color: var(--text-muted); min-width: 32px; text-align: right; }
.hint-line code {
  font-family: var(--font-mono); font-size: 11px; color: var(--text-secondary);
  background: var(--bg-input); padding: 2px 8px; border-radius: 4px;
}

.footer-note {
  font-size: 10px; color: var(--text-muted); font-family: var(--font-mono); letter-spacing: 0.06em;
}

@media (max-width: 440px) {
  .login-card { width: 92vw; padding: 32px 24px; }
  .brand-name { font-size: 22px; }
}
</style>
