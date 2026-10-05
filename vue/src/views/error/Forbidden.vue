<template>
  <div class="forbidden-page">
    <el-result icon="warning" title="403" sub-title="抱歉，您没有权限访问该页面">
      <template #extra>
        <el-button type="primary" @click="goHome">返回首页</el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { getScopeBasePath } from '@/utils/route'

const route = useRoute()
const router = useRouter()

function goHome() {
  const base = getScopeBasePath(route.path)
  if (base === '/admin') {
    router.push('/admin/dashboard')
  } else if (base === '/user') {
    router.push('/user/home')
  } else {
    router.push('/login')
  }
}
</script>

<style scoped>
.forbidden-page {
  min-height: 60vh;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
