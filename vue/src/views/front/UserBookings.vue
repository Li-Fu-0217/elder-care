<template>
  <div class="front-page booking-page">
    <div class="front-shell">
      <section class="page-head">
        <h1>服务中心</h1>
        <p>为绑定老人预约体检、护理或家政服务</p>
      </section>

      <section class="book-layout">
        <div class="book-card book-card--form">
          <h2 class="book-card__title">提交预约</h2>
          <el-form label-width="90px">
            <el-form-item label="选择老人">
              <el-select v-model="form.elderId" placeholder="请选择" class="book-field">
                <el-option v-for="e in elders" :key="e.id" :label="e.name" :value="e.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="服务项目">
              <el-select v-model="form.catalogId" placeholder="请选择" class="book-field" @change="loadSlots">
                <el-option
                  v-for="c in catalogs"
                  :key="c.id"
                  :label="`${c.name}（${c.serviceType}）`"
                  :value="c.id"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="预约时段">
              <el-select v-model="form.bookingTime" placeholder="先选服务再选时段" class="book-field">
                <el-option v-for="s in slots" :key="s" :label="s" :value="s" />
              </el-select>
            </el-form-item>
            <el-form-item label="备注">
              <el-input v-model="form.remark" type="textarea" :rows="2" class="book-field" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" round :loading="submitting" @click="submit">提交预约</el-button>
              <el-button round @click="$router.push('/user/agent')">用智能助手预约</el-button>
            </el-form-item>
          </el-form>
        </div>

        <aside class="book-rules">
          <h3>预约须知</h3>
          <ul class="book-rules__list">
            <li>仅可为已绑定的老人提交预约</li>
            <li>请先选择服务项目，再选择可预约时段</li>
            <li>提交后状态为待确认，由社区工作人员审核</li>
            <li>如需改期或取消，请联系社区服务热线</li>
          </ul>

          <div v-if="selectedCatalog" class="book-rules__service">
            <h4>当前服务</h4>
            <p class="book-rules__service-name">{{ selectedCatalog.name }}</p>
            <p v-if="selectedCatalog.description" class="book-rules__service-desc">
              {{ selectedCatalog.description }}
            </p>
            <p v-if="selectedCatalog.durationMinutes" class="book-rules__service-meta">
              预计时长约 {{ selectedCatalog.durationMinutes }} 分钟
            </p>
          </div>

          <div class="book-rules__tip">
            也可在智能助手中说「帮我爸约下周体检」，自动完成查档与预约。
          </div>

          <div class="book-rules__hotline">
            <span class="book-rules__hotline-label">社区服务热线</span>
            <a :href="`tel:${hotline}`">{{ hotline }}</a>
          </div>
        </aside>
      </section>

      <div class="book-card book-card--table">
        <h2>我的预约</h2>
        <el-table :data="myBookings" empty-text="暂无预约" style="width: 100%">
          <el-table-column prop="elderName" label="老人" min-width="90" />
          <el-table-column prop="catalogName" label="服务" min-width="110" />
          <el-table-column prop="bookingTime" label="时间" min-width="160">
            <template #default="{ row }">{{ formatDateTime(row.bookingTime) }}</template>
          </el-table-column>
          <el-table-column prop="status" label="状态" min-width="100">
            <template #default="{ row }">
              <el-tag :type="bookingStatusTagType(row.status)" effect="light" round>
                {{ bookingStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="source" label="来源" min-width="100">
            <template #default="{ row }">
              <el-tag :type="bookingSourceTagType(row.source)" effect="plain" round>
                {{ bookingSourceLabel(row.source) }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup>
defineOptions({ name: 'UserBookings' })

import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getMyElders } from '@/api/elder'
import {
  getServiceCatalog,
  getServiceSlots,
  createBooking,
  getMyBookings
} from '@/api/service'
import { SITE_HOTLINE } from '@/config/site'
import {
  formatDateTime,
  bookingStatusLabel,
  bookingStatusTagType,
  bookingSourceLabel,
  bookingSourceTagType
} from '@/utils/format'

const hotline = SITE_HOTLINE
const elders = ref([])
const catalogs = ref([])
const slots = ref([])
const myBookings = ref([])
const submitting = ref(false)
const form = reactive({
  elderId: null,
  catalogId: null,
  bookingTime: '',
  remark: ''
})

const selectedCatalog = computed(() =>
  catalogs.value.find((c) => c.id === form.catalogId) || null
)

async function loadSlots() {
  form.bookingTime = ''
  if (!form.catalogId) {
    slots.value = []
    return
  }
  const list = await getServiceSlots({ catalogId: form.catalogId, days: 7 })
  const item = (list || []).find((x) => x.catalogId === form.catalogId)
  slots.value = item?.slots || []
}

async function loadMine() {
  const data = await getMyBookings({ current: 1, size: 20 })
  myBookings.value = data.records || []
}

async function submit() {
  if (!form.elderId || !form.catalogId || !form.bookingTime) {
    ElMessage.warning('请完整填写预约信息')
    return
  }
  submitting.value = true
  try {
    await createBooking({
      elderId: form.elderId,
      catalogId: form.catalogId,
      bookingTime: form.bookingTime.replace(' ', 'T'),
      remark: form.remark
    })
    ElMessage.success('预约成功')
    form.bookingTime = ''
    form.remark = ''
    await loadSlots()
    await loadMine()
  } finally {
    submitting.value = false
  }
}

onMounted(async () => {
  elders.value = (await getMyElders()) || []
  catalogs.value = (await getServiceCatalog()) || []
  if (elders.value.length) form.elderId = elders.value[0].id
  await loadMine()
})
</script>

<style scoped>
.booking-page {
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

.book-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 16px;
  align-items: start;
  margin-bottom: 16px;
}

.book-card {
  background: #fff;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 8px 24px rgba(30, 42, 36, 0.05);
  border: 1px solid var(--care-line);
}

.book-card__title {
  margin: 0 0 16px;
  font-size: 16px;
  font-weight: 700;
  color: var(--care-ink);
}

.book-card h2 {
  margin: 0 0 12px;
  font-size: 16px;
}

.book-field {
  width: 100%;
  max-width: 420px;
}

.book-rules {
  background: #fff;
  border-radius: 16px;
  padding: 20px;
  border: 1px solid var(--care-line);
  box-shadow: 0 8px 24px rgba(30, 42, 36, 0.04);
}

.book-rules h3 {
  margin: 0 0 12px;
  font-size: 17px;
  font-weight: 700;
  color: var(--care-ink);
}

.book-rules h4 {
  margin: 0 0 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--care-muted);
}

.book-rules__list {
  margin: 0 0 16px;
  padding-left: 18px;
  font-size: 13px;
  line-height: 1.65;
  color: var(--care-muted);
}

.book-rules__list li + li {
  margin-top: 6px;
}

.book-rules__service {
  margin-bottom: 14px;
  padding: 12px;
  border-radius: 12px;
  background: var(--care-green-soft);
  border: 1px solid rgba(47, 155, 106, 0.18);
}

.book-rules__service-name {
  margin: 0 0 6px;
  font-size: 15px;
  font-weight: 700;
  color: var(--care-green-dark);
}

.book-rules__service-desc,
.book-rules__service-meta {
  margin: 0;
  font-size: 13px;
  line-height: 1.55;
  color: var(--care-muted);
}

.book-rules__service-meta {
  margin-top: 6px;
}

.book-rules__tip {
  margin-bottom: 16px;
  padding: 10px 12px;
  border-radius: 10px;
  background: #f6f9f7;
  font-size: 13px;
  line-height: 1.55;
  color: var(--care-muted);
}

.book-rules__hotline {
  padding-top: 14px;
  border-top: 1px solid var(--care-line);
}

.book-rules__hotline-label {
  display: block;
  margin-bottom: 4px;
  font-size: 12px;
  color: var(--care-muted);
}

.book-rules__hotline a {
  font-size: 20px;
  font-weight: 800;
  color: var(--care-green-dark);
  text-decoration: none;
  letter-spacing: 0.02em;
}

@media (max-width: 900px) {
  .book-layout {
    grid-template-columns: 1fr;
  }

  .book-field {
    max-width: none;
  }
}
</style>
