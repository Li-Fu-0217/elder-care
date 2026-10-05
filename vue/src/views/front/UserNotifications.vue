<template>
  <div class="front-page notify-page">
    <div class="front-shell">
      <section class="page-head">
        <h1>消息中心</h1>
        <p>智能助手提醒、用药与紧急告警等站内消息</p>
      </section>

      <div class="notify-toolbar">
        <el-radio-group v-model="filter" @change="handleSearch">
          <el-radio-button label="all">全部</el-radio-button>
          <el-radio-button label="unread">未读</el-radio-button>
          <el-radio-button label="read">已读</el-radio-button>
        </el-radio-group>
        <span class="notify-toolbar__spacer" />
        <el-button round :disabled="!unreadHint" :loading="markingAll" @click="handleReadAll">
          全部已读
        </el-button>
        <el-button type="primary" plain round @click="$router.push('/user/agent')">智能助手</el-button>
      </div>

      <div class="notify-card" v-loading="loading">
        <el-empty v-if="!loading && !list.length" description="暂无消息" :image-size="72" />
        <button
          v-for="row in list"
          :key="row.id"
          type="button"
          class="notify-row"
          :class="{ 'is-unread': row.isRead === 0 }"
          @click="openRow(row)"
        >
          <div class="notify-row__main">
            <div class="notify-row__title">
              <span v-if="row.isRead === 0" class="notify-dot" aria-hidden="true" />
              <span>{{ row.title }}</span>
              <el-tag size="small" effect="light" round>{{ typeLabel(row.msgType) }}</el-tag>
            </div>
            <p class="notify-row__content">{{ row.content }}</p>
            <div class="notify-row__meta">
              <span v-if="row.elderName">{{ row.elderName }}</span>
              <span>{{ formatDateTime(row.createTime) }}</span>
            </div>
          </div>
        </button>

        <div v-if="page.total > page.size" class="notify-footer">
          <el-pagination
            v-model:current-page="page.current"
            v-model:page-size="page.size"
            :total="page.total"
            background
            layout="total, prev, pager, next"
            small
            @current-change="loadList"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  getNotifications,
  markAllNotificationsRead,
  markNotificationRead
} from '@/api/notify'

defineOptions({ name: 'user_notifications' })

const loading = ref(false)
const markingAll = ref(false)
const filter = ref('all')
const list = ref([])
const page = reactive({ current: 1, size: 10, total: 0 })

const unreadHint = computed(() => list.value.some((r) => r.isRead === 0) || filter.value === 'unread')

const TYPE_MAP = {
  agent_notify: '智能提醒',
  medication: '用药提醒',
  booking: '预约通知',
  emergency: '紧急告警',
  system: '系统通知'
}

function typeLabel(t) {
  return TYPE_MAP[t] || '通知'
}

function formatDateTime(v) {
  if (!v) return '-'
  return String(v).replace('T', ' ').slice(0, 19)
}

function handleSearch() {
  page.current = 1
  loadList()
}

async function loadList() {
  loading.value = true
  try {
    const params = { current: page.current, size: page.size }
    if (filter.value === 'unread') params.isRead = 0
    if (filter.value === 'read') params.isRead = 1
    const data = await getNotifications(params)
    list.value = data?.records || []
    page.total = data?.total || 0
  } finally {
    loading.value = false
  }
}

async function openRow(row) {
  if (row.isRead === 0) {
    try {
      await markNotificationRead(row.id)
      row.isRead = 1
    } catch {
      /* ignore */
    }
  }
}

async function handleReadAll() {
  markingAll.value = true
  try {
    await markAllNotificationsRead()
    ElMessage.success('已全部标为已读')
    await loadList()
  } finally {
    markingAll.value = false
  }
}

onMounted(loadList)
</script>

<style scoped>
.notify-page {
  padding: 28px 0 48px;
}

.notify-page .page-head {
  margin: 0 0 18px;
}

.notify-page .page-head h1 {
  margin: 0 0 6px;
  font-size: 26px;
  font-weight: 700;
  color: var(--care-ink, #1e2a24);
}

.notify-page .page-head p {
  margin: 0;
  color: var(--care-muted, #5c6b62);
  font-size: 14px;
}

.notify-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.notify-toolbar__spacer {
  flex: 1;
}

.notify-card {
  background: #fff;
  border-radius: 16px;
  padding: 4px 8px;
  box-shadow: 0 8px 28px rgba(26, 46, 34, 0.06);
}

.notify-card :deep(.el-empty) {
  padding: 36px 0;
}

.notify-row {
  display: block;
  width: 100%;
  text-align: left;
  border: 0;
  background: transparent;
  border-bottom: 1px solid #eef2ef;
  padding: 14px 10px;
  cursor: pointer;
  font: inherit;
  color: inherit;
}

.notify-row:last-of-type {
  border-bottom: 0;
}

.notify-row:hover {
  background: #f7faf8;
}

.notify-row.is-unread .notify-row__title {
  font-weight: 700;
}

.notify-row__title {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 6px;
  color: #1a2e22;
}

.notify-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #c45c26;
  flex-shrink: 0;
}

.notify-row__content {
  margin: 0 0 8px;
  color: #3d4f44;
  line-height: 1.55;
  font-size: 14px;
}

.notify-row__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  color: #8a968e;
  font-size: 13px;
}

.notify-footer {
  display: flex;
  justify-content: flex-end;
  padding: 8px 8px 4px;
  border-top: 1px solid #eef2ef;
}
</style>
