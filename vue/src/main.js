import { createApp } from 'vue'
import pinia from '@/store/pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import '@/styles/theme.css'
import '@/styles/global.css'
import '@/styles/front.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { initTheme } from '@/utils/theme'

import App from './App.vue'
import router from './router'
import { vAuth } from '@/directives/auth'

initTheme()

const app = createApp(App)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(pinia)
app.use(router)
app.directive('auth', vAuth)
app.use(ElementPlus, { locale: zhCn })

app.mount('#app')
