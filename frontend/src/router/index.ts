import { createRouter, createWebHashHistory } from 'vue-router'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      redirect: '/dashboard',
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/LoginAnimated.vue'),
    },
    // ===== 移动端页面（独立布局，无顶部导航）=====
    {
      path: '/driver-app',
      name: 'DriverApp',
      component: () => import('@/views/MobileApp.vue'),
      meta: { title: '司机工作台', roles: ['driver'] },
    },
    {
      path: '/customer-app',
      name: 'CustomerApp',
      component: () => import('@/views/CustomerOrders.vue'),
      meta: { title: '冷链配送', roles: ['customer'] },
    },
    {
      path: '/public/trace/:traceCode',
      name: 'PublicTraceQuery',
      component: () => import('@/views/CustomerQuery.vue'),
      meta: { title: '冷链溯源查询', public: true },
    },
    // ===== PC 端页面（MainLayout 布局，仅 admin/warehouse）=====
    {
      path: '/',
      component: () => import('@/layouts/MainLayout.vue'),
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/Dashboard.vue'),
          meta: { title: '全局态势图', roles: ['admin', 'warehouse'] },
        },
        {
          path: 'boss',
          name: 'BossDashboard',
          component: () => import('@/views/BossDashboard.vue'),
          meta: { title: '经营分析看板', roles: ['admin'] },
        },
        {
          path: 'warehouse',
          name: 'WarehouseDashboard',
          component: () => import('@/views/WarehouseDashboard.vue'),
          meta: { title: '仓库管理工作台', roles: ['admin', 'warehouse'] },
        },
        {
          path: 'monitor',
          name: 'Monitor',
          component: () => import('@/views/DeviceMonitor.vue'),
          meta: { title: '设备监控', roles: ['admin'] },
        },
        {
          path: 'temperature',
          name: 'Temperature',
          component: () => import('@/views/TemperatureTrend.vue'),
          meta: { title: '温度趋势', roles: ['admin', 'warehouse'] },
        },
        {
          path: 'alerts',
          name: 'Alerts',
          component: () => import('@/views/AlertCenter.vue'),
          meta: { title: '告警中心', roles: ['admin', 'warehouse'] },
        },
        {
          path: 'rules',
          name: 'Rules',
          component: () => import('@/views/AlertRules.vue'),
          meta: { title: '告警规则', roles: ['admin'] },
        },
        {
          path: 'geofence',
          name: 'Geofence',
          component: () => import('@/views/GeofenceManager.vue'),
          meta: { title: '电子围栏', roles: ['admin'] },
        },
        {
          path: 'traceability',
          name: 'Traceability',
          component: () => import('@/views/Traceability.vue'),
          meta: { title: '冷链追溯', roles: ['admin', 'warehouse'] },
        },
        {
          path: '/customer',
          name: 'CustomerQuery',
          component: () => import('@/views/CustomerQuery.vue'),
          meta: { title: '客户查询', roles: ['admin', 'warehouse'] },
        },
        {
          path: 'tracking',
          name: 'VehicleTracking',
          component: () => import('@/views/VehicleTracking.vue'),
          meta: { title: '车辆追踪', roles: ['admin', 'warehouse'] },
        },
        {
          path: 'routes',
          name: 'RoutePlanning',
          component: () => import('@/views/RoutePlanning.vue'),
          meta: { title: '路径规划', roles: ['admin', 'warehouse'] },
        },
        {
          path: 'dispatch',
          name: 'MultiZoneDispatch',
          component: () => import('@/views/MultiZoneDispatch.vue'),
          meta: { title: '多温区调度', roles: ['admin', 'warehouse'] },
        },
        {
          path: 'maintenance',
          name: 'MaintenancePredict',
          component: () => import('@/views/MaintenancePredict.vue'),
          meta: { title: '故障预测', roles: ['admin', 'warehouse'] },
        },
        {
          path: 'quality',
          name: 'QualityAssessment',
          component: () => import('@/views/QualityAssessment.vue'),
          meta: { title: '品质评估', roles: ['admin', 'warehouse'] },
        },
        {
          path: 'resources',
          name: 'ResourceManagement',
          component: () => import('@/views/ResourceManagement.vue'),
          meta: { title: '资源调度', roles: ['admin', 'warehouse'] },
        },
        {
          path: 'manager-orders',
          name: 'ManagerOrders',
          component: () => import('@/views/ManagerOrders.vue'),
          meta: { title: '订单管理中心', roles: ['admin', 'warehouse'] },
        },
      ],
    },
  ],
})

// 导航守卫：4 角色体系
// admin/warehouse → PC端 (MainLayout)
// driver → 移动端 /driver-app
// customer → 移动端 /customer-app
router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem('token')
  const userRole = localStorage.getItem('userRole') || ''
  const isDriver = userRole === 'driver'
  const isCustomer = userRole === 'customer'
  const homePath = isDriver ? '/driver-app' : isCustomer ? '/customer-app' : '/dashboard'

  // 公开页面无需校验（消费者扫码查询）
  if (to.meta.public) {
    return next()
  }

  // 登录页无需校验
  if (to.path === '/login') {
    if (token) return next(homePath)
    return next()
  }

  // 未登录 → 跳转登录
  if (!token) return next('/login')

  // 访问根路径 → 根据角色跳转
  if (to.path === '/') return next(homePath)

  // 角色权限检查 - admin 拥有所有页面访问权限
  const allowedRoles = to.meta.roles as string[] | undefined
  if (allowedRoles && allowedRoles.length > 0 && userRole !== 'admin') {
    // warehouse 可以访问含 warehouse 角色的页面 + 含 admin 角色的页面（上级覆盖）
    if (userRole === 'warehouse') {
      // warehouse 可访问标记了 warehouse 或 admin 的页面（仓储人员需要看全局态势图）
      if (!allowedRoles.includes('warehouse') && !allowedRoles.includes('admin')) {
        return next(homePath)
      }
    } else if (!allowedRoles.includes(userRole)) {
      return next(homePath)
    }
  }

  // driver/customer 只允许访问自己的移动端页面
  if ((isDriver || isCustomer) && to.path !== '/login') {
    const mobilePaths = isDriver ? ['/driver-app'] : ['/customer-app']
    if (!mobilePaths.includes(to.path)) {
      return next(homePath)
    }
  }

  next()
})

export default router
