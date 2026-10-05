<template>
  <div class="auth-page">
    <div class="auth-panel auth-panel--brand">
      <div class="brand-content">
        <h1>社区养老助手</h1>
        <p>适老化社区服务 · 智能助手联动<br />健康关怀 · 预约服务 · 安心守护</p>
      </div>
    </div>
    <div class="auth-panel auth-panel--form">
      <el-card class="auth-card" shadow="never">
        <h2 class="title">登录</h2>
        <p class="subtitle">请输入您的账号信息</p>
        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-width="0"
          size="large"
          @keyup.enter="handleLogin"
        >
          <el-form-item prop="username">
            <el-input v-model="form.username" placeholder="用户名" :prefix-icon="User" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="密码"
              :prefix-icon="Lock"
              show-password
            />
          </el-form-item>
          <el-form-item prop="captchaCode">
            <div class="captcha-row">
              <el-input
                v-model="form.captchaCode"
                placeholder="验证码"
                maxlength="4"
                class="captcha-input"
              />
              <button
                type="button"
                class="captcha-img-btn"
                title="点击刷新验证码"
                @click="refreshCaptcha"
              >
                <img v-if="captchaImage" :src="captchaImage" alt="验证码" />
                <span v-else>加载中</span>
              </button>
            </div>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" class="submit-btn" :loading="loading" @click="handleLogin">
              登录
            </el-button>
          </el-form-item>
          <div class="footer-link">
            还没有账号？<router-link to="/register">立即注册</router-link>
          </div>
        </el-form>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import { getRoleHomePath } from '@/utils/route'
import { getMyMenus } from '@/api/menu'
import { getCaptcha } from '@/api/auth'
import { setupDynamicRoutes } from '@/router/dynamicRoutes'
import loginBg from '@/assets/login.jpg'

const loginBgUrl = `url(${loginBg})`

const router = useRouter()
const userStore = useUserStore()
const formRef = ref()
const loading = ref(false)
const captchaImage = ref('')

const form = reactive({
  username: '',
  password: '',
  captchaId: '',
  captchaCode: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  captchaCode: [{ required: true, message: '请输入验证码', trigger: 'blur' }]
}

async function refreshCaptcha() {
  try {
    const data = await getCaptcha()
    form.captchaId = data.captchaId
    form.captchaCode = ''
    captchaImage.value = data.imageBase64
  } catch {
    captchaImage.value = ''
  }
}

async function handleLogin() {
  await formRef.value.validate()
  loading.value = true
  try {
    const data = await userStore.login({
      username: form.username,
      password: form.password,
      captchaId: form.captchaId,
      captchaCode: form.captchaCode
    })
    const menus = await getMyMenus()
    setupDynamicRoutes(router, menus)
    ElMessage.success('登录成功')
    router.push(getRoleHomePath(data.user.role))
  } catch {
    await refreshCaptcha()
  } finally {
    loading.value = false
  }
}

onMounted(refreshCaptcha)
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
}

.auth-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.auth-panel--brand {
  position: relative;
  background: center / cover no-repeat;
  background-image: v-bind(loginBgUrl);
  color: #fff;
  padding: 48px;
  overflow: hidden;
}

.brand-content {
  position: relative;
  z-index: 1;
  max-width: 400px;
}

.brand-content h1 {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 16px;
  text-shadow: 0 2px 12px rgba(0, 0, 0, 0.35);
}

.brand-content p {
  font-size: 15px;
  line-height: 1.8;
  opacity: 0.95;
  text-shadow: 0 1px 8px rgba(0, 0, 0, 0.3);
}

.auth-panel--form {
  background: var(--app-bg);
  padding: 24px;
}

.auth-card {
  width: 100%;
  max-width: 400px;
  border: 1px solid var(--app-border);
  border-radius: var(--app-radius);
  padding: 8px 4px 4px;
}

.title {
  font-size: 24px;
  font-weight: 600;
  color: var(--app-text);
}

.subtitle {
  margin: 8px 0 28px;
  font-size: 14px;
  color: var(--app-text-secondary);
}

.captcha-row {
  display: flex;
  width: 100%;
  gap: 10px;
  align-items: stretch;
}

.captcha-input {
  flex: 1;
  min-width: 0;
}

.captcha-img-btn {
  flex: none;
  width: 120px;
  height: 40px;
  padding: 0;
  border: 1px solid var(--app-border);
  border-radius: 8px;
  background: #f8fafc;
  cursor: pointer;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--app-text-secondary);
  font-size: 12px;
}

.captcha-img-btn:hover {
  border-color: var(--app-primary);
}

.captcha-img-btn img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.submit-btn {
  width: 100%;
  height: 44px;
  font-size: 15px;
}

.footer-link {
  text-align: center;
  font-size: 14px;
  color: var(--app-text-secondary);
}

.footer-link a {
  color: var(--app-primary);
  text-decoration: none;
  font-weight: 500;
}

.footer-link a:hover {
  text-decoration: underline;
}

@media (max-width: 768px) {
  .auth-panel--brand {
    display: none;
  }
}
</style>
