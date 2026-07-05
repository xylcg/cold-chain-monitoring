<template>
  <div class="main-layout">
    <!-- 顶部导航栏 -->
    <nav class="top-nav">
      <div class="nav-inner" @mouseleave="scheduleClose">
        <!-- Logo -->
        <router-link :to="homePath" class="nav-brand">
          <span class="brand-icon">◆</span>
          <span class="brand-text">
            <span class="brand-name">CRYO</span><span class="brand-dot">·</span><span class="brand-sub">TRACK</span>
          </span>
        </router-link>

        <!-- 导航分组 -->
        <div class="nav-groups">
          <div
            v-for="group in navGroups"
            :key="group.label"
            class="nav-group"
            @mouseenter="openDropdown(group.label)"
          >
            <div class="nav-group-trigger" :class="{ active: activeDropdown === group.label }">
              <span>{{ group.label }}</span>
              <svg class="chevron" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg>
            </div>
          </div>
        </div>

        <!-- 右侧 -->
        <div class="nav-right">
          <div class="nav-user">
            <div class="user-avatar">{{ (store.username || 'A')[0].toUpperCase() }}</div>
            <div class="user-info">
              <span class="user-name">{{ store.username || 'admin' }}</span>
              <span class="user-role" :class="'role-' + userRole">{{ roleLabel }}</span>
            </div>
          </div>
          <button class="btn-logout" @click="handleLogout" title="退出">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
          </button>
        </div>
      </div>

      <!-- 下拉面板 -->
      <div v-show="activeDropdown" class="dropdown-panel" @mouseenter="cancelClose" @mouseleave="scheduleClose">
        <div class="dropdown-inner">
          <div class="dropdown-grid" :style="gridStyle">
            <router-link
              v-for="item in currentItems"
              :key="item.path"
              :to="item.path"
              class="dropdown-item"
              :class="{ active: activeMenu === item.path }"
              @click="handleNavClick"
            >
              <div class="dropdown-icon">
                <svg class="item-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <g v-html="item.icon"></g>
                </svg>
              </div>
              <div class="dropdown-text">
                <div class="dropdown-title">{{ item.title }}</div>
                <div class="dropdown-desc">{{ item.desc }}</div>
              </div>
            </router-link>
          </div>
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
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '@/stores/app'

const route = useRoute()
const router = useRouter()
const store = useAppStore()

const activeMenu = computed(() => route.path)
const activeDropdown = ref<string | null>(null)
let closeTimer: ReturnType<typeof setTimeout> | null = null

// 角色
const userRole = computed(() => store.userRole || 'admin')
const roleLabel = computed(() => {
  const m: Record<string, string> = { admin: '调度员', driver: '司机', warehouse: '仓管维修', customer: '顾客' }
  return m[userRole.value] || '调度员'
})
const homePath = computed(() => {
  if (userRole.value === 'warehouse') return '/warehouse'
  return '/dashboard'
})

function openDropdown(label: string) {
  cancelClose()
  activeDropdown.value = label
}

function scheduleClose() {
  closeTimer = setTimeout(() => {
    activeDropdown.value = null
  }, 150)
}

function cancelClose() {
  if (closeTimer) {
    clearTimeout(closeTimer)
    closeTimer = null
  }
}

function handleNavClick() {
  cancelClose()
  activeDropdown.value = null
}

const currentItems = computed(() => {
  const group = navGroups.value.find(g => g.label === activeDropdown.value)
  return group?.items || []
})

const gridStyle = computed(() => {
  const group = navGroups.value.find(g => g.label === activeDropdown.value)
  const cols = group?.cols || 2
  return { gridTemplateColumns: `repeat(${cols}, 1fr)` }
})

function handleLogout() {
  store.logout()
  router.push('/login')
}

// 路由角色映射（用于导航过滤）- admin/warehouse 仅 PC 端
const routeRoles: Record<string, string[]> = {
  '/dashboard': ['admin'],
  '/boss': ['admin'],
  '/warehouse': ['warehouse'],
  '/tracking': ['admin', 'warehouse'],
  '/monitor': ['admin'],
  '/temperature': ['admin', 'warehouse'],
  '/alerts': ['admin', 'warehouse'],
  '/dispatch': ['admin', 'warehouse'],
  '/maintenance': ['warehouse'],
  '/quality': ['warehouse'],
  '/rules': ['admin'],
  '/geofence': ['admin'],
  '/resources': ['admin', 'warehouse'],
  '/traceability': ['admin', 'warehouse'],
  '/customer': ['admin', 'warehouse'],
  '/manager-orders': ['admin', 'warehouse'],
}

function hasAccess(path: string): boolean {
  const roles = routeRoles[path]
  if (!roles) return true
  return roles.includes(userRole.value)
}

// 基础导航定义
const allNavGroups = [
  {
    label: '监控中心',
    cols: 3,
    items: [
      { path: '/dashboard', title: '全局态势', desc: '实时监控全网冷链状态', icon: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>' },
      { path: '/boss', title: '运营总览', desc: '冷链运营全局数据总览', icon: '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="9" cy="9" r="2"/><path d="M21 15l-3.5-3.5L15 14l-3-3-3 3"/><path d="M15 14v7"/><path d="M9 17v4"/>' },
      { path: '/warehouse', title: '仓管维修工作台', desc: '品质质检 · 冷机故障预测', icon: '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>' },
      { path: '/tracking', title: '车辆追踪', desc: 'GPS 定位与轨迹回放', icon: '<circle cx="12" cy="10" r="3"/><path d="M12 21.7C17.3 17 20 13 20 10a8 8 0 1 0-16 0c0 3 2.7 7 8 11.7z"/>' },
      { path: '/monitor', title: '设备监控', desc: '传感器状态在线监测', icon: '<rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>' },
      { path: '/temperature', title: '温度趋势', desc: '历史温度曲线与预测', icon: '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>' },
      { path: '/alerts', title: '告警中心', desc: '异常预警与实时处理', icon: '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>' },
    ],
  },
  {
    label: 'AI 智能',
    cols: 2,
    items: [
      { path: '/routes', title: '路径规划', desc: '智能冷链配送路径优化', icon: '<polyline points="3 12 7 5 17 19 21 12"/>' },
      { path: '/dispatch', title: '多温区调度', desc: '车厢温区智能分配', icon: '<rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/>' },
      { path: '/maintenance', title: '故障预测', desc: '冷机设备预测性维护', icon: '<path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>' },
      { path: '/quality', title: '品质评估', desc: '生鲜品质 AI 评估', icon: '<path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>' },
    ],
  },
  {
    label: '运营管理',
    cols: 3,
    items: [
      { path: '/rules', title: '告警规则', desc: '规则配置与阈值管理', icon: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09A1.65 1.65 0 0 0 19.4 15z"/>' },
      { path: '/geofence', title: '电子围栏', desc: '地理围栏与越界预警', icon: '<circle cx="12" cy="10" r="3"/><path d="M12 21.7C17.3 17 20 13 20 10a8 8 0 1 0-16 0c0 3 2.7 7 8 11.7z"/>' },
      { path: '/resources', title: '资源调度', desc: '冷链资源智能分配', icon: '<rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/>' },
      { path: '/traceability', title: '冷链追溯', desc: '全链路追溯与溯源', icon: '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>' },
      { path: '/customer', title: '客户查询', desc: '客户温控查询服务', icon: '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>' },
      { path: '/manager-orders', title: '订单管理', desc: '创建运单 · 调度分配 · 司机消息', icon: '<rect x="2" y="2" width="20" height="20" rx="2"/><line x1="2" y1="7" x2="22" y2="7"/><line x1="7" y1="7" x2="7" y2="22"/><rect x="10" y="11" width="5" height="3" rx="1"/><rect x="10" y="16" width="8" height="3" rx="1"/>' },
    ],
  },
]

// 根据角色过滤导航
const navGroups = computed(() => {
  return allNavGroups
    .map(group => ({
      ...group,
      items: group.items.filter(item => hasAccess(item.path)),
    }))
    .filter(group => group.items.length > 0)
})

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
  flex-direction: column;
  min-height: 100vh;
  background: var(--bg-page);
}

/* ===== 顶部导航栏 ===== */
.top-nav {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 56px;
  z-index: 1000;
  background: #0a0a0a;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.nav-inner {
  max-width: 1400px;
  margin: 0 auto;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

/* Brand */
.nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  flex-shrink: 0;
  margin-right: 32px;
}

.brand-icon {
  font-size: 20px;
  color: var(--accent);
  filter: drop-shadow(0 0 6px rgba(0, 168, 255, 0.4));
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
  color: #fff;
  letter-spacing: 0.06em;
}

.brand-dot {
  color: var(--accent);
  font-weight: 700;
  font-size: 14px;
}

.brand-sub {
  font-family: var(--font-display);
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.55);
  letter-spacing: 0.04em;
}

/* Nav groups */
.nav-groups {
  display: flex;
  align-items: center;
  gap: 4px;
  flex: 1;
}

.nav-group {
  position: relative;
}

.nav-group-trigger {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.65);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
}

.nav-group-trigger:hover,
.nav-group-trigger.active {
  color: #fff;
  background: rgba(255, 255, 255, 0.08);
}

.chevron {
  transition: transform 0.2s ease;
  opacity: 0.6;
}

.nav-group-trigger.active .chevron {
  transform: rotate(180deg);
}

/* Dropdown panel */
.dropdown-panel {
  position: absolute;
  top: 56px;
  left: 0;
  right: 0;
  display: flex;
  justify-content: center;
  padding: 10px 0 16px;
  z-index: 1001;
  pointer-events: none;
}

.dropdown-inner {
  pointer-events: auto;
  background: #111;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 20px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.02);
  max-width: 800px;
  width: 100%;
  margin: 0 24px;
}

.dropdown-grid {
  display: grid;
  gap: 4px;
}

.dropdown-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border-radius: 10px;
  text-decoration: none;
  color: rgba(255, 255, 255, 0.5);
  transition: all 0.2s ease;
  cursor: pointer;
}

.dropdown-item:hover {
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.8);
}

.dropdown-item.active {
  background: rgba(0, 168, 255, 0.1);
  color: var(--accent);
}

.dropdown-item.active .dropdown-title {
  color: var(--accent);
}

.dropdown-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: rgba(255, 255, 255, 0.7);
}

.dropdown-item:hover .dropdown-icon {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.12);
}

.dropdown-item.active .dropdown-icon {
  color: var(--accent);
  border-color: rgba(0, 168, 255, 0.3);
  background: rgba(0, 168, 255, 0.08);
}

.item-icon {
  width: 20px;
  height: 20px;
}

.dropdown-text {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.dropdown-title {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  line-height: 1.3;
}

.dropdown-desc {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  line-height: 1.4;
}

/* Right side */
.nav-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.nav-user {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--accent), var(--aurora));
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  font-family: var(--font-display);
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-info {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.user-name {
  font-size: 13px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.8);
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-role {
  font-size: 10px;
  font-weight: 500;
  padding: 0px 5px;
  border-radius: 3px;
  line-height: 1.6;
  display: inline-block;
  max-width: fit-content;
}

.role-admin {
  background: rgba(0, 168, 255, 0.15);
  color: var(--accent);
}

.role-manager {
  background: rgba(124, 58, 237, 0.15);
  color: var(--aurora);
}

.role-driver {
  background: rgba(0, 210, 160, 0.15);
  color: var(--teal);
}

.role-warehouse {
  background: rgba(245, 158, 11, 0.15);
  color: var(--amber);
}

.role-customer {
  background: rgba(236, 72, 153, 0.15);
  color: #ec4899;
}

.btn-logout {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: transparent;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.25s;
}

.btn-logout:hover {
  border-color: rgba(239, 68, 68, 0.4);
  color: var(--red);
  background: var(--red-bg);
}

/* ===== 主内容区 ===== */
.main-content {
  flex: 1;
  padding-top: 56px;
  overflow-x: hidden;
  min-height: 100vh;
}

.content-padding {
  padding: 28px 32px 60px;
  max-width: 1400px;
  margin: 0 auto;
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
  .nav-inner { padding: 0 16px; }
  .dropdown-inner { margin: 0 16px; }
  .content-padding { padding: 20px 16px 40px; }
  .user-name { display: none; }
}
</style>