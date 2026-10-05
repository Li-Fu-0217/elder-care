<template>
  <div class="front-page home-portal">
    <!-- Hero：全宽首屏，文案与顶栏标语错开 -->
    <section class="hero">
      <div
        class="hero__media"
        aria-hidden="true"
        :style="{ backgroundImage: `url(${bannerImg})` }"
      />
      <div class="hero__veil" aria-hidden="true" />
      <div class="front-shell hero__inner">
        <div class="hero__content">
          <h1 class="hero__title">
            <span>智慧养老</span>
            <span class="hero__title-dot"> · </span>
            <span class="hero__title-accent">幸福晚年</span>
          </h1>
          <p class="hero__desc">{{ heroDesc }}</p>
          <div class="hero__actions">
            <el-button class="hero__cta" type="primary" size="large" @click="$router.push('/user/agent')">
              打开智能助手
            </el-button>
            <el-button class="hero__cta-ghost" size="large" @click="$router.push('/user/bookings')">
              了解更多服务
            </el-button>
          </div>
          <ul class="hero__pills">
            <li>贴心服务</li>
            <li>健康守护</li>
            <li>幸福生活</li>
          </ul>
        </div>
      </div>
    </section>

    <div class="front-shell home-body">
      <div class="home-grid">
        <div class="home-grid__main">
          <!-- 常用功能 -->
          <section class="panel">
            <h2 class="front-section-title">常用功能</h2>
            <p class="front-section-desc">常用服务入口，点击即可办理</p>
            <div class="quick-grid">
              <button
                v-for="item in quickActions"
                :key="item.path"
                type="button"
                class="quick-card"
                @click="$router.push(item.path)"
              >
                <span class="quick-card__icon" :style="{ background: item.tone }">
                  <component :is="item.icon" :size="26" :stroke-width="2" />
                </span>
                <span class="quick-card__name">{{ item.name }}</span>
              </button>
            </div>
          </section>

          <!-- 便捷服务 -->
          <section class="panel">
            <h2 class="front-section-title">便捷服务</h2>
            <p class="front-section-desc">预约社区体检、上门护理与家政保洁</p>
            <div class="service-row">
              <article v-for="s in services" :key="s.type" class="service-card" :class="`service-card--${s.tone}`">
                <div class="service-card__icon">
                  <component :is="s.icon" :size="28" :stroke-width="2" />
                </div>
                <h3>{{ s.name }}</h3>
                <p>{{ s.desc }}</p>
                <el-button round size="small" @click="goBook(s.type)">去预约</el-button>
              </article>
            </div>
          </section>

          <!-- 健康管理入口 -->
          <section class="panel">
            <h2 class="front-section-title">健康管理</h2>
            <p class="front-section-desc">档案、用药与漏服提醒，守护长辈日常</p>
            <div class="health-row">
              <article
                v-for="h in healthEntries"
                :key="h.title"
                class="health-card"
                role="button"
                tabindex="0"
                @click="$router.push(h.path)"
                @keyup.enter="$router.push(h.path)"
              >
                <div class="health-card__left">
                  <span class="health-card__badge" :style="{ background: h.tone }">
                    <component :is="h.icon" :size="22" :stroke-width="2" />
                  </span>
                  <div>
                    <h3>{{ h.title }}</h3>
                    <p>{{ h.desc }}</p>
                  </div>
                </div>
                <el-button text type="primary">{{ h.action }}</el-button>
              </article>
            </div>
          </section>
        </div>

        <aside class="home-grid__side">
          <section class="side-panel">
            <h3>温馨提醒</h3>
            <el-empty v-if="!reminders.length" description="暂无提醒" :image-size="56" />
            <ul v-else class="remind-list">
              <li v-for="(r, i) in reminders" :key="i" :class="`remind-list__item is-${r.level}`">
                <strong>{{ r.title }}</strong>
                <span>{{ r.text }}</span>
              </li>
            </ul>
            <el-button class="side-panel__btn" round @click="$router.push('/user/care')">
              查看关怀看板
            </el-button>
          </section>

          <section class="side-panel side-panel--agent">
            <h3>智能助手</h3>
            <p>用自然语言查询用药、预约体检，一句话就能办。</p>
            <el-button type="primary" round class="side-panel__btn" @click="$router.push('/user/agent')">
              开始对话
            </el-button>
          </section>

          <section class="side-panel side-panel--sos">
            <h3>紧急求助</h3>
            <p>一键向社区工作人员发起站内告警；危急情况请同时拨打急救电话。</p>
            <el-button class="sos-btn" :loading="sosLoading" @click="triggerSos">一键紧急求助</el-button>
            <a class="sos-hotline" :href="`tel:${hotline}`">热线 {{ hotline }}</a>
          </section>
        </aside>
      </div>
    </div>
  </div>
</template>

<script setup>
defineOptions({ name: 'FrontHome' })

import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Bell,
  Calendar,
  Eye,
  FileText,
  House,
  MessageCircle,
  TriangleAlert,
  Trophy,
  UserRound
} from 'lucide-vue-next'
import { useUserStore } from '@/store/user'
import { getCareDashboard } from '@/api/care'
import { getMyElders } from '@/api/elder'
import { createEmergencyAlert } from '@/api/community'
import { SITE_HERO_DESC, SITE_HOTLINE } from '@/config/site'
import { formatDateTime } from '@/utils/format'
import bannerImg from '@/assets/banner2.png'

const router = useRouter()
const userStore = useUserStore()
const heroDesc = SITE_HERO_DESC
const hotline = SITE_HOTLINE
const dashboard = ref({ elders: [], recentMissed: [], recentBookings: [] })
const sosLoading = ref(false)

const quickActions = [
  { name: '服务预约', path: '/user/bookings', icon: Calendar, tone: '#2f9b6a' },
  { name: '关怀看板', path: '/user/care', icon: Eye, tone: '#3b8fd9' },
  { name: '健康档案', path: '/user/care', icon: FileText, tone: '#4fae5a' },
  { name: '智能助手', path: '/user/agent', icon: MessageCircle, tone: '#f08a24' },
  { name: '活动天地', path: '/user/activities', icon: Trophy, tone: '#e89a2e' },
  { name: '个人中心', path: '/user/profile', icon: UserRound, tone: '#6b86ab' }
]

const services = [
  {
    type: 'health_check',
    name: '社区体检',
    desc: '血压血糖、常规检查，就近预约',
    icon: FileText,
    tone: 'green'
  },
  {
    type: 'nursing',
    name: '上门护理',
    desc: '护士上门测血压与用药指导',
    icon: Bell,
    tone: 'blue'
  },
  {
    type: 'housekeeping',
    name: '家政保洁',
    desc: '居家清洁整理，省心省力',
    icon: House,
    tone: 'orange'
  }
]

const healthEntries = [
  {
    title: '健康档案',
    desc: '查看绑定长辈的慢性病与用药摘要',
    action: '立即查看',
    path: '/user/care',
    icon: FileText,
    tone: '#2f9b6a'
  },
  {
    title: '用药提醒',
    desc: '漏服与待服一览，一键标记已服',
    action: '去打卡',
    path: '/user/medications',
    icon: TriangleAlert,
    tone: '#f08a24'
  },
  {
    title: '服务记录',
    desc: '近期预约与办理进度',
    action: '去看看',
    path: '/user/bookings',
    icon: Calendar,
    tone: '#3b8fd9'
  },
  {
    title: '智能问询',
    desc: '自然语言发起查药、约体检',
    action: '去对话',
    path: '/user/agent',
    icon: MessageCircle,
    tone: '#5b6bc0'
  }
]

const reminders = computed(() => {
  const list = []
  const missed = dashboard.value.recentMissed || []
  missed.slice(0, 3).forEach((m) => {
    list.push({
      level: 'warn',
      title: '用药提醒',
      text: `${m.elderName || '长辈'}「${m.drugName || '药品'}」计划 ${formatDateTime(m.plannedTime)} 疑似漏服`
    })
  })
  const books = dashboard.value.recentBookings || []
  books.slice(0, 2).forEach((b) => {
    list.push({
      level: 'info',
      title: '预约提醒',
      text: `${b.elderName || ''} ${b.catalogName || '服务'} · ${formatDateTime(b.bookingTime)}`
    })
  })
  if (!list.length) {
    const name = userStore.userInfo?.nickname || '您'
    list.push({
      level: 'info',
      title: '欢迎',
      text: `${name}，今天也记得关心家人的用药与预约哦。`
    })
  }
  return list
})

function goBook() {
  router.push('/user/bookings')
}

async function triggerSos() {
  const elders = (await getMyElders()) || []
  if (!elders.length) {
    ElMessage.warning('请先绑定老人后再发起求助')
    return
  }
  await ElMessageBox.confirm(`确认为「${elders[0].name}」发起紧急求助？`, '紧急求助', {
    type: 'warning',
    confirmButtonText: '立即求助'
  })
  sosLoading.value = true
  try {
    await createEmergencyAlert({
      elderId: elders[0].id,
      location: elders[0].address || '住址未填写',
      message: '前台一键紧急求助'
    })
    ElMessage.success('已通知社区工作人员（站内告警）')
  } finally {
    sosLoading.value = false
  }
}

onMounted(async () => {
  try {
    dashboard.value = (await getCareDashboard()) || dashboard.value
  } catch {
    /* 首页提醒失败不阻断 */
  }
})
</script>

<style scoped>
.home-portal {
  padding-bottom: 40px;
}

.hero {
  position: relative;
  /* 接近素材 2:1，减少上下裁切导致头顶被切 */
  min-height: clamp(360px, 42vw, 520px);
  display: flex;
  align-items: center;
  overflow: hidden;
  margin-bottom: 28px;
}

.hero__media {
  position: absolute;
  inset: 0;
  /* 焦点偏右上：完整露出人脸，右侧老人为主 */
  background-position: 68% 12%;
  background-size: cover;
  background-repeat: no-repeat;
}

/* 整幅轻遮罩，去掉左侧硬切边，照片更完整 */
.hero__veil {
  position: absolute;
  inset: 0;
  background: rgba(18, 42, 32, 0.46);
}

.hero__inner {
  position: relative;
  z-index: 1;
  width: 100%;
  padding-top: 56px;
  padding-bottom: 56px;
  box-sizing: border-box;
}

.hero__content {
  max-width: 520px;
  color: #fff;
}

.hero__title {
  margin: 0 0 14px;
  font-size: clamp(32px, 4.2vw, 46px);
  font-weight: 800;
  letter-spacing: 0.02em;
  line-height: 1.3;
  color: #fff;
  text-shadow: 0 2px 12px rgba(0, 0, 0, 0.35);
}

.hero__title-dot {
  font-weight: 700;
}

.hero__title-accent {
  color: #8fd9b0;
}

.hero__desc {
  margin: 0 0 28px;
  max-width: 440px;
  font-size: clamp(16px, 1.5vw, 18px);
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.92);
  text-shadow: 0 1px 8px rgba(0, 0, 0, 0.3);
}

.hero__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 28px;
}

.hero__cta {
  --el-button-bg-color: #2f9b6a;
  --el-button-border-color: #2f9b6a;
  --el-button-hover-bg-color: #247a53;
  --el-button-hover-border-color: #247a53;
  font-weight: 700;
  padding: 12px 22px;
  border-radius: 999px;
}

.hero__cta-ghost {
  background: rgba(255, 255, 255, 0.16);
  border-color: rgba(255, 255, 255, 0.55);
  color: #fff;
  border-radius: 999px;
  font-weight: 600;
}

.hero__cta-ghost:hover {
  background: rgba(255, 255, 255, 0.28);
  border-color: #fff;
  color: #fff;
}

.hero__pills {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  list-style: none;
  margin: 0;
  padding: 0;
}

.hero__pills li {
  padding: 7px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  border: 1px solid rgba(255, 255, 255, 0.28);
  font-size: 13px;
  backdrop-filter: blur(4px);
}

.home-body {
  padding-bottom: 8px;
}

.home-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: 20px;
  align-items: start;
}

.panel {
  background: #fff;
  border-radius: 18px;
  padding: 20px 20px 18px;
  margin-bottom: 18px;
  border: 1px solid var(--care-line);
  box-shadow: 0 8px 24px rgba(30, 42, 36, 0.04);
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.quick-card {
  border: 1px solid var(--care-line);
  background: #fbfdfc;
  border-radius: 14px;
  padding: 16px 12px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.quick-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(47, 155, 106, 0.12);
}

.quick-card__icon {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.quick-card__name {
  font-size: 14px;
  font-weight: 700;
  color: var(--care-ink);
}

.service-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.service-card {
  border-radius: 16px;
  padding: 18px 16px;
  color: #fff;
  min-height: 168px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.service-card h3 {
  margin: 0;
  font-size: 18px;
}

.service-card p {
  margin: 0;
  flex: 1;
  font-size: 13px;
  line-height: 1.5;
  opacity: 0.92;
}

.service-card--green {
  background: #2f9b6a;
}
.service-card--blue {
  background: #3b8fd9;
}
.service-card--orange {
  background: #f08a24;
}

.service-card :deep(.el-button) {
  align-self: flex-start;
  background: rgba(255, 255, 255, 0.95);
  border: none;
  color: #1e2a24;
  font-weight: 700;
}

.health-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.health-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px;
  border-radius: 14px;
  border: 1px solid var(--care-line);
  background: #fbfdfc;
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.health-card:hover {
  border-color: #9fd4b8;
  box-shadow: 0 8px 18px rgba(47, 155, 106, 0.1);
}

.health-card__left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.health-card__badge {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.health-card h3 {
  margin: 0 0 4px;
  font-size: 15px;
}

.health-card p {
  margin: 0;
  font-size: 12px;
  color: var(--care-muted);
  line-height: 1.4;
}

.side-panel {
  background: #fff;
  border-radius: 18px;
  padding: 18px;
  margin-bottom: 16px;
  border: 1px solid var(--care-line);
  box-shadow: 0 8px 24px rgba(30, 42, 36, 0.04);
}

.side-panel h3 {
  margin: 0 0 10px;
  font-size: 17px;
}

.side-panel p {
  margin: 0 0 12px;
  font-size: 13px;
  color: var(--care-muted);
  line-height: 1.55;
}

.side-panel__btn {
  width: 100%;
}

.remind-list {
  list-style: none;
  margin: 0 0 14px;
  padding: 0;
}

.remind-list__item {
  padding: 10px 12px;
  border-radius: 12px;
  margin-bottom: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 13px;
  line-height: 1.45;
}

.remind-list__item.is-warn {
  background: var(--care-orange-soft);
  color: #8a4b10;
}

.remind-list__item.is-info {
  background: var(--care-green-soft);
  color: #1e4d36;
}

.side-panel--agent {
  background: #e8f6ef;
  border-color: #bfe2d0;
}

.side-panel--sos {
  background: #fff1ef;
  border-color: #f5c4bc;
}

.sos-btn {
  display: block;
  width: 100%;
  text-align: center;
  padding: 12px;
  border-radius: 999px;
  background: var(--care-coral);
  border: none;
  color: #fff;
  font-weight: 800;
  font-size: 15px;
  margin-bottom: 10px;
}

.sos-btn:hover {
  filter: brightness(1.05);
  background: var(--care-coral);
  color: #fff;
}

.sos-hotline {
  display: block;
  text-align: left;
  color: var(--care-coral);
  font-weight: 700;
  text-decoration: none;
  font-size: 14px;
}

@media (max-width: 980px) {
  .home-grid {
    grid-template-columns: 1fr;
  }

  .quick-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .service-row,
  .health-row {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 560px) {
  .quick-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .hero {
    min-height: 340px;
    align-items: flex-end;
  }

  .hero__media {
    background-position: 62% 8%;
  }

  .hero__veil {
    background: rgba(18, 42, 32, 0.58);
  }

  .hero__inner {
    padding-top: 40px;
    padding-bottom: 40px;
  }

  .hero__content {
    max-width: none;
  }

  .hero__actions {
    margin-bottom: 22px;
  }
}
</style>
