<template>
  <div class="page-container page-container--center">
    <div class="content-card password-page">
      <div class="card-head">
        <div>
          <h1>修改密码</h1>
          <span class="card-head__meta">修改成功后请使用新密码重新登录</span>
        </div>
        <el-button @click="$router.push(`${scopeBase}/profile`)">返回</el-button>
      </div>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        class="password-form"
      >
        <el-form-item label="原密码" prop="oldPassword">
          <el-input v-model="form.oldPassword" type="password" show-password placeholder="请输入原密码" />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input v-model="form.newPassword" type="password" show-password placeholder="3-50 个字符" />
        </el-form-item>
        <el-form-item label="确认新密码" prop="confirmPassword">
          <el-input v-model="form.confirmPassword" type="password" show-password placeholder="再次输入新密码" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">确认修改</el-button>
          <el-button @click="resetForm">清空</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
defineOptions({ name: 'ChangePassword' })

import { ref, reactive, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getScopeBasePath } from '@/utils/route'
import { ElMessage, ElMessageBox } from 'element-plus'
import { changePassword } from '@/api/profile'
import { useUserStore } from '@/store/user'
import { teardownSession } from '@/utils/session'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const scopeBase = computed(() => getScopeBasePath(route.path))
const formRef = ref()
const submitting = ref(false)

const form = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const validateConfirm = (rule, value, callback) => {
  if (value !== form.newPassword) {
    callback(new Error('两次输入的新密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  oldPassword: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 3, max: 50, message: '长度为 3-50 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' }
  ]
}

function resetForm() {
  formRef.value?.resetFields()
  form.oldPassword = ''
  form.newPassword = ''
  form.confirmPassword = ''
}

async function handleSubmit() {
  await formRef.value.validate()
  submitting.value = true
  try {
    await changePassword({
      oldPassword: form.oldPassword,
      newPassword: form.newPassword,
      confirmPassword: form.confirmPassword
    })
    await ElMessageBox.alert('密码已修改，请重新登录', '提示', { type: 'success' })
    userStore.logout()
    teardownSession()
    router.push('/login')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.password-form {
  margin-top: 8px;
}
</style>
