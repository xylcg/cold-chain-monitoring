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
    {
      path: '/',
      component: () => import('@/layouts/MainLayout.vue'),
      children: [
        {
          path: 'dashboard',
          name: 'Dashboard',
          component: () => import('@/views/Dashboard.vue'),
          meta: { title: '全局态势图' },
        },
        {
          path: 'monitor',
          name: 'Monitor',
          component: () => import('@/views/DeviceMonitor.vue'),
          meta: { title: '设备监控' },
        },
        {
          path: 'temperature',
          name: 'Temperature',
          component: () => import('@/views/TemperatureTrend.vue'),
          meta: { title: '温度趋势' },
        },
        {
          path: 'alerts',
          name: 'Alerts',
          component: () => import('@/views/AlertCenter.vue'),
          meta: { title: '告警中心' },
        },
        {
          path: 'rules',
          name: 'Rules',
          component: () => import('@/views/AlertRules.vue'),
          meta: { title: '告警规则' },
        },
        {
          path: 'geofence',
          name: 'Geofence',
          component: () => import('@/views/GeofenceManager.vue'),
          meta: { title: '电子围栏' },
        },
        {
          path: 'traceability',
          name: 'Traceability',
          component: () => import('@/views/Traceability.vue'),
          meta: { title: '冷链追溯' },
        },
        {
          path: 'customer',
          name: 'CustomerQuery',
          component: () => import('@/views/CustomerQuery.vue'),
          meta: { title: '客户查询' },
        },
        {
          path: 'tracking',
          name: 'VehicleTracking',
          component: () => import('@/views/VehicleTracking.vue'),
          meta: { title: '车辆追踪' },
        },
        {
          path: 'routes',
          name: 'RoutePlanning',
          component: () => import('@/views/RoutePlanning.vue'),
          meta: { title: '路径规划' },
        },
        {
          path: 'dispatch',
          name: 'MultiZoneDispatch',
          component: () => import('@/views/MultiZoneDispatch.vue'),
          meta: { title: '多温区调度' },
        },
        {
          path: 'maintenance',
          name: 'MaintenancePredict',
          component: () => import('@/views/MaintenancePredict.vue'),
          meta: { title: '故障预测' },
        },
        {
          path: 'quality',
          name: 'QualityAssessment',
          component: () => import('@/views/QualityAssessment.vue'),
          meta: { title: '品质评估' },
        },
        {
          path: 'resources',
          name: 'ResourceManagement',
          component: () => import('@/views/ResourceManagement.vue'),
          meta: { title: '资源调度' },
        },
      ],
    },
    {
      path: '/mobile',
      name: 'MobileApp',
      component: () => import('@/views/MobileApp.vue'),
      meta: { title: '移动端冷链监控' },
    },
  ],
})

export default router
