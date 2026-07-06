import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import App from './App.vue'
import router from './router'
import './styles/global.css'

const app = createApp(App)

// 全局错误处理——防止单组件崩溃导致整页白屏
app.config.errorHandler = (err, instance, info) => {
  console.error('[Vue Error]', err, info)
  // 不弹 ElMessage 避免循环引用，只打印日志
}

// 注册所有 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })
app.mount('#app')

// PWA: 提示用户安装
window.addEventListener('beforeinstallprompt', (e) => {
  // 保存安装事件，可在需要时触发
  ;(window as any).__pwaInstallEvent = e
})

// PWA: 安装成功后通知
window.addEventListener('appinstalled', () => {
  console.log('PWA 已安装到设备')
})
