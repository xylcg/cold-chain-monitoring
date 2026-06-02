<template>
  <div class="main-layout">
    <!-- 玻璃态悬浮导航 -->
    <nav class="nav-glass">
      <div class="nav-inner">
        <router-link to="/dashboard" class="nav-brand" @click="closeMobile">
          <span class="brand-icon">◆</span>
          <span class="brand-text">
            <span class="brand-name">CRYO</span><span class="brand-dot">·</span><span class="brand-sub">TRACK</span>
          </span>
        </router-link>

        <div class="nav-links">
          <div class="nav-group-label">监控</div>
          <router-link to="/dashboard" class="nav-link" :class="{ active: activeMenu === '/dashboard' }">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
            <span>全局态势</span>
          </router-link>
          <router-link to="/tracking" class="nav-link" :class="{ active: activeMenu === '/tracking' }">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="10" r="3"/><path d="M12 21.7C17.3 17 20 13 20 10a8 8 0 1 0-16 0c0 3 2.7 7 8 11.7z"/></svg>
            <span>车辆追踪</span>
          </router-link>
          <router-link to="/monitor" class="nav-link" :class="{ active: activeMenu === '/monitor' }">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
            <span>设备监控</span>
          </router-link>
          <router-link to="/temperature" class="nav-link" :class="{ active: activeMenu === '/temperature' }">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
            <span>温度趋势</span>
          </router-link>
          <router-link to="/alerts" class="nav-link" :class="{ active: activeMenu === '/alerts' }">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
            <span>告警中心</span>
            <span v-if="store.kpi.active_alerts > 0" class="nav-badge">{{ store.kpi.active_alerts }}</span>
          </router-link>

          <div class="nav-group-label">AI 智能</div>
          <router-link to="/routes" class="nav-link" :class="{ active: activeMenu === '/routes' }">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="3 12 7 5 17 19 21 12"/></svg>
            <span>路径规划</span>
          </router-link>
          <router-link to="/dispatch" class="nav-link" :class="{ active: activeMenu === '/dispatch' }">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>
            <span>多温区调度</span>
          </router-link>
          <router-link to="/maintenance" class="nav-link" :class="{ active: activeMenu === '/maintenance' }">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
            <span>故障预测</span>
          </router-link>
          <router-link to="/quality" class="nav-link" :class="{ active: activeMenu === '/quality' }">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
            <span>品质评估</span>
          </router-link>

          <div class="nav-group-label">管理</div>
          <router-link to="/rules" class="nav-link" :class="{ active: activeMenu === '/rules' }">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
            <span>告警规则</span>
          </router-link>
          <router-link to="/geofence" class="nav-link" :class="{ active: activeMenu === '/geofence' }">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="12" cy="10" r="3"/><path d="M12 21.7C17.3 17 20 13 20 10a8 8 0 1 0-16 0c0 3 2.7 7 8 11.7z"/></svg>
            <span>电子围栏</span>
          </router-link>
          <router-link to="/resources" class="nav-link" :class="{ active: activeMenu === '/resources' }">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>
            <span>资源调度</span>
          </router-link>
          <router-link to="/traceability" class="nav-link" :class="{ active: activeMenu === '/traceability' }">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
            <span>冷链追溯</span>
          </router-link>
          <router-link to="/customer" class="nav-link" :class="{ active: activeMenu === '/customer' }">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            <span>客户查询</span>
          </router-link>


        </div>

        <div class="nav-footer">
          <div class="nav-user">
            <div class="user-avatar">{{ (store.username || 'A')[0].toUpperCase() }}</div>
            <span class="user-name">{{ store.username || 'admin' }}</span>
          </div>
          <button class="btn-logout" @click="handleLogout" title="退出">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
          </button>
        </div>
      </div>
    </nav>

    <!-- 主内容区 -->
    <main class="main-content">
      <div class="content-padding">
        <router-view v-slot="{ Component }">
          <transition name="page-fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'

const route = useRoute()
const router = useRouter()
const store = useAppStore()

const activeMenu = computed(() => route.path)

function handleLogout() {
  store.logout()
  router.push('/login')
}

function closeMobile() {}

onMounted(() => {
  store.startAutoRefresh(10000)
})

onUnmounted(() => {
  store.stopAutoRefresh()
})
</script>

<style scoped>
.main-layout {
  display: flex;
  min-height: 100vh;
  background: var(--bg-page);
}

/* ===== 玻璃态悬浮导航 ===== */
.nav-glass {
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  width: 230px;
  z-index: 100;
  padding: 12px;
  pointer-events: none;
}

.nav-inner {
  height: 100%;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 18px;
  padding: 20px 14px 14px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06), 0 1px 4px rgba(0, 0, 0, 0.04);
  pointer-events: auto;
  overflow: hidden;
}

/* Brand */
.nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 6px 18px;
  margin-bottom: 8px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  text-decoration: none;
  cursor: pointer;
}

.brand-icon {
  font-size: 20px;
  color: var(--accent);
  filter: drop-shadow(0 0 6px var(--accent-glow));
}

.brand-text {
  display: flex;
  align-items: baseline;
  gap: 1px;
}

.brand-name {
  font-family: var(--font-display);
  font-size: 16px;
  font-weight: 800;
  color: var(--text-title);
  letter-spacing: 0.06em;
}

.brand-dot {
  font-family: var(--font-body);
  color: var(--accent);
  font-weight: 700;
  font-size: 14px;
}

.brand-sub {
  font-family: var(--font-display);
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  letter-spacing: 0.04em;
}

/* Nav links area */
.nav-links {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 0 2px;
}

.nav-group-label {
  font-size: 10px;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  padding: 10px 8px 4px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 9px 10px;
  border-radius: 10px;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.25s ease;
  position: relative;
  white-space: nowrap;
}

.nav-link:hover {
  background: rgba(0, 168, 255, 0.06);
  color: var(--accent);
}

.nav-link.active {
  background: linear-gradient(135deg, rgba(0, 168, 255, 0.1), rgba(124, 58, 237, 0.08));
  color: var(--accent);
  font-weight: 600;
}

.nav-link.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 8px;
  bottom: 8px;
  width: 3px;
  border-radius: 2px;
  background: var(--accent);
  box-shadow: 0 0 8px var(--accent-glow);
}

.nav-badge {
  margin-left: auto;
  min-width: 18px;
  height: 18px;
  background: var(--red);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  font-family: var(--font-mono);
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 5px;
  animation: pulse-badge 2s ease-in-out infinite;
}

@keyframes pulse-badge {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

/* Footer */
.nav-footer {
  margin-top: auto;
  padding-top: 12px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.nav-user {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.user-avatar {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--accent), var(--aurora));
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  font-family: var(--font-display);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.user-name {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.btn-logout {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.25s;
}
.btn-logout:hover {
  border-color: var(--red);
  color: var(--red);
  background: var(--red-bg);
}

/* ===== 主内容区 ===== */
.main-content {
  flex: 1;
  margin-left: 230px;
  overflow-y: auto;
  overflow-x: hidden;
  min-height: 100vh;
}

.content-padding {
  padding: 28px 32px 60px;
  max-width: 1400px;
}

/* 页面过渡 */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.page-fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}
.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

@media (max-width: 1024px) {
  .nav-glass { width: 180px; }
  .main-content { margin-left: 180px; }
  .content-padding { padding: 20px 16px 40px; }
}
</style>
