<template>
  <div class="front-page care-page">
    <div class="front-shell">
      <section class="care-hero">
        <div>
          <h1 class="care-hero__title">关怀看板</h1>
          <p class="care-hero__desc">查看绑定老人的漏服提醒、服药打卡入口、近期预约与健康摘要</p>
        </div>
        <div class="care-hero__actions">
          <el-button round @click="openBind">绑定老人</el-button>
          <el-button round @click="$router.push('/user/medications')">服药打卡</el-button>
          <el-button type="primary" round @click="$router.push('/user/agent')">智能助手</el-button>
        </div>
      </section>

      <el-row :gutter="16" class="care-grid">
        <el-col :xs="24" :md="8">
          <div class="care-panel">
            <div class="care-panel__head">
              <h2>我的老人</h2>
              <el-button type="primary" link @click="openBind">添加绑定</el-button>
            </div>
            <el-empty
              v-if="!bindings.length"
              description="暂未绑定老人，点击上方添加"
              :image-size="64"
            />
            <div
              v-for="b in bindings"
              :key="b.id"
              class="elder-card"
            >
              <div class="elder-card__main" @click="goElder(b.elderId)">
                <div class="elder-card__name">{{ b.elderName }}</div>
                <div class="elder-card__meta">
                  关系：{{ b.relation || '家属' }}
                </div>
              </div>
              <el-button type="danger" link @click.stop="handleUnbind(b)">解绑</el-button>
            </div>
          </div>
        </el-col>
        <el-col :xs="24" :md="8">
          <div class="care-panel">
            <div class="care-panel__head">
              <h2>近期漏服</h2>
              <el-button type="primary" link @click="$router.push('/user/medications')">去打卡</el-button>
            </div>
            <el-empty v-if="!dashboard.recentMissed?.length" description="暂无漏服" :image-size="64" />
            <div v-for="m in dashboard.recentMissed" :key="m.id" class="miss-item">
              <span class="miss-item__drug">{{ m.drugName }}</span>
              <span class="miss-item__time">{{ formatDateTime(m.plannedTime) }}</span>
            </div>
          </div>
        </el-col>
        <el-col :xs="24" :md="8">
          <div class="care-panel">
            <h2>近期预约</h2>
            <el-empty v-if="!dashboard.recentBookings?.length" description="暂无预约" :image-size="64" />
            <div v-for="b in dashboard.recentBookings" :key="b.id" class="book-item">
              <div class="book-item__head">
                <span>{{ b.catalogName }} · {{ b.elderName }}</span>
                <el-tag :type="bookingStatusTagType(b.status)" effect="light" round size="small">
                  {{ bookingStatusLabel(b.status) }}
                </el-tag>
              </div>
              <div class="book-item__time">{{ formatDateTime(b.bookingTime) }}</div>
            </div>
            <div class="care-panel__actions">
              <el-button round @click="$router.push('/user/bookings')">去预约服务</el-button>
              <el-button type="primary" round @click="$router.push('/user/agent')">打开智能助手</el-button>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <el-dialog
      v-model="bindVisible"
      title="绑定老人"
      width="420px"
      destroy-on-close
      append-to-body
    >
      <p class="bind-tip">请填写与档案一致的老人姓名、手机号完成绑定。</p>
      <el-form :model="bindForm" label-width="80px">
        <el-form-item label="姓名" required>
          <el-input v-model="bindForm.elderName" placeholder="老人姓名" />
        </el-form-item>
        <el-form-item label="手机号" required>
          <el-input v-model="bindForm.elderPhone" placeholder="档案中的手机号" />
        </el-form-item>
        <el-form-item label="关系">
          <el-select v-model="bindForm.relation" style="width: 100%">
            <el-option label="儿子" value="儿子" />
            <el-option label="女儿" value="女儿" />
            <el-option label="配偶" value="配偶" />
            <el-option label="家属" value="家属" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="bindVisible = false">取消</el-button>
        <el-button type="primary" :loading="binding" @click="submitBind">确认绑定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * 子女关怀看板：绑定/解绑老人、漏服与预约摘要入口。
 */
defineOptions({ name: 'CareDashboard' })

import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getCareDashboard } from '@/api/care'
import { getMyBindings, selfBindFamily, selfUnbindFamily } from '@/api/elder'
import {
  formatDateTime,
  bookingStatusLabel,
  bookingStatusTagType
} from '@/utils/format'

const router = useRouter()
const dashboard = reactive({ elders: [], recentMissed: [], recentBookings: [] })
const bindings = ref([])
const bindVisible = ref(false)
const binding = ref(false)
const bindForm = reactive({
  elderName: '',
  elderPhone: '',
  relation: '家属'
})

function goElder(id) {
  router.push(`/user/elders/${id}`)
}

function openBind() {
  bindForm.elderName = ''
  bindForm.elderPhone = ''
  bindForm.relation = '家属'
  bindVisible.value = true
}

async function loadAll() {
  const [dash, binds] = await Promise.all([getCareDashboard(), getMyBindings()])
  Object.assign(dashboard, dash || {})
  bindings.value = binds || []
}

async function submitBind() {
  if (!bindForm.elderName.trim() || !bindForm.elderPhone.trim()) {
    ElMessage.warning('请填写姓名与手机号')
    return
  }
  binding.value = true
  try {
    await selfBindFamily({
      elderName: bindForm.elderName.trim(),
      elderPhone: bindForm.elderPhone.trim(),
      relation: bindForm.relation
    })
    ElMessage.success('绑定成功')
    bindVisible.value = false
    await loadAll()
  } finally {
    binding.value = false
  }
}

async function handleUnbind(row) {
  await ElMessageBox.confirm(`确定解绑「${row.elderName}」？`, '提示', { type: 'warning' })
  await selfUnbindFamily(row.id)
  ElMessage.success('已解绑')
  await loadAll()
}

onMounted(loadAll)
</script>

<style scoped>
.care-page {
  padding: 28px 0 48px;
}
.care-hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}
.care-hero__title {
  margin: 0 0 8px;
  font-size: 28px;
  font-weight: 800;
  color: var(--care-ink);
}
.care-hero__desc {
  margin: 0;
  color: var(--care-muted);
}
.care-hero__actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.care-panel {
  background: #fff;
  border-radius: 16px;
  padding: 16px 18px;
  box-shadow: 0 8px 24px rgba(30, 42, 36, 0.05);
  border: 1px solid var(--care-line);
  min-height: 280px;
  margin-bottom: 16px;
}
.care-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.care-panel__head h2,
.care-panel h2 {
  margin: 0 0 12px;
  font-size: 16px;
  color: var(--care-ink);
}
.care-panel__head h2 {
  margin-bottom: 0;
}
.care-panel__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}
.elder-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 12px;
  border-radius: 12px;
  background: var(--care-green-soft);
  margin-bottom: 8px;
}
.elder-card__main {
  min-width: 0;
  flex: 1;
  cursor: pointer;
}
.elder-card__name {
  font-weight: 700;
  color: var(--care-ink);
}
.elder-card__meta {
  font-size: 13px;
  color: var(--care-muted);
  margin-top: 4px;
}
.bind-tip {
  margin: 0 0 12px;
  font-size: 13px;
  color: #64748b;
  line-height: 1.5;
}
.miss-item,
.book-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 0;
  border-bottom: 1px solid #eef4f0;
  font-size: 14px;
}

.book-item__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.miss-item__drug {
  color: #c2410c;
  font-weight: 700;
}
.miss-item__time,
.book-item__time {
  color: #94a3b8;
  font-size: 12px;
}
</style>
