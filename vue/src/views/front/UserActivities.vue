<template>
  <div class="front-page activity-page">
    <div class="front-shell">
      <section class="page-head">
        <h1>活动天地</h1>
        <p>浏览社区活动并为绑定长辈报名</p>
      </section>

      <div class="activity-grid">
        <article v-for="a in activities" :key="a.id" class="activity-card">
          <h3>{{ a.title }}</h3>
          <p class="activity-card__meta">
            {{ formatDateTime(a.startTime) }} · {{ a.location || '地点待定' }}
          </p>
          <p class="activity-card__desc">{{ a.content || '暂无详情' }}</p>
          <div class="activity-card__foot">
            <span>已报 {{ a.registeredCount }}/{{ a.capacity ?? '不限' }}</span>
            <el-button type="primary" round size="small" @click="openRegister(a)">报名</el-button>
          </div>
        </article>
      </div>

      <div class="mine-card">
        <h2>我的报名</h2>
        <el-table :data="mine" empty-text="暂无报名" style="width: 100%">
          <el-table-column prop="activityTitle" label="活动" min-width="160" />
          <el-table-column prop="elderName" label="老人" min-width="100" />
          <el-table-column prop="createTime" label="报名时间" min-width="170">
            <template #default="{ row }">{{ formatDateTime(row.createTime) }}</template>
          </el-table-column>
          <el-table-column prop="status" label="状态" min-width="100">
            <template #default="{ row }">
              <el-tag :type="registrationStatusTagType(row.status)" effect="light" round>
                {{ registrationStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <el-dialog v-model="visible" title="活动报名" width="400px" append-to-body>
      <el-form label-width="80px">
        <el-form-item label="活动">{{ current?.title }}</el-form-item>
        <el-form-item label="老人">
          <el-select v-model="elderId" style="width: 100%">
            <el-option v-for="e in elders" :key="e.id" :label="e.name" :value="e.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submit">确认报名</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
defineOptions({ name: 'UserActivities' })

import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getMyElders } from '@/api/elder'
import { getActivities, registerActivity, getMyRegistrations } from '@/api/community'
import {
  formatDateTime,
  registrationStatusLabel,
  registrationStatusTagType
} from '@/utils/format'

const activities = ref([])
const mine = ref([])
const elders = ref([])
const visible = ref(false)
const current = ref(null)
const elderId = ref(null)
const submitting = ref(false)

function openRegister(a) {
  current.value = a
  if (elders.value.length) elderId.value = elders.value[0].id
  visible.value = true
}

async function submit() {
  if (!elderId.value || !current.value) return
  submitting.value = true
  try {
    await registerActivity(current.value.id, { elderId: elderId.value })
    ElMessage.success('报名成功')
    visible.value = false
    await refresh()
  } finally {
    submitting.value = false
  }
}

async function refresh() {
  activities.value = (await getActivities()) || []
  mine.value = (await getMyRegistrations()) || []
}

onMounted(async () => {
  elders.value = (await getMyElders()) || []
  await refresh()
})
</script>

<style scoped>
.activity-page {
  padding: 28px 0 48px;
}
.page-head h1 {
  margin: 0 0 8px;
  font-size: 28px;
  font-weight: 800;
  color: var(--care-ink);
}
.page-head p {
  margin: 0 0 20px;
  color: var(--care-muted);
}
.activity-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 20px;
}
.activity-card {
  background: #fff;
  border: 1px solid var(--care-line);
  border-radius: 16px;
  padding: 18px;
  box-shadow: 0 8px 24px rgba(30, 42, 36, 0.04);
}
.activity-card h3 {
  margin: 0 0 8px;
  font-size: 17px;
}
.activity-card__meta {
  margin: 0 0 8px;
  font-size: 12px;
  color: var(--care-muted);
}
.activity-card__desc {
  margin: 0 0 14px;
  font-size: 13px;
  color: #334155;
  line-height: 1.5;
  min-height: 40px;
}
.activity-card__foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  color: var(--care-muted);
}
.mine-card {
  background: #fff;
  border-radius: 16px;
  padding: 18px;
  border: 1px solid var(--care-line);
}
.mine-card h2 {
  margin: 0 0 12px;
  font-size: 16px;
}
@media (max-width: 900px) {
  .activity-grid {
    grid-template-columns: 1fr;
  }
}
</style>
