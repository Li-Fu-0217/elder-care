<template>
  <div class="front-layout">
    <header class="front-header">
      <div class="front-header__shell">
        <router-link to="/user/home" class="front-brand front-brand--aside">
          <img class="front-brand__logo" src="@/assets/logo.png" alt="" aria-hidden="true" />
          <span class="front-brand__text">
            <span class="front-brand__name">{{ siteName }}</span>
            <span class="front-brand__tag">{{ siteTagline }}</span>
          </span>
        </router-link>

        <div class="front-header__content">
          <nav v-if="navMenus.length" class="front-nav front-nav--desktop" aria-label="主导航">
            <router-link
              v-for="item in navMenus"
              :key="item.path"
              :to="item.path"
              class="front-nav__item"
              :class="{ 'is-active': activeMenu === item.path }"
            >
              {{ item.name }}
            </router-link>
          </nav>
        </div>

        <div class="front-header__right">
          <el-badge :value="unreadCount" :hidden="!unreadCount" :max="99" class="front-bell-badge">
            <el-button
              class="front-bell-btn"
              circle
              aria-label="消息中心"
              @click="router.push('/user/notifications')"
            >
              <Bell :size="20" :stroke-width="2" />
            </el-button>
          </el-badge>

          <el-button
            v-if="navMenus.length"
            class="front-menu-btn"
            circle
            aria-label="打开菜单"
            @click="drawerVisible = true"
          >
            <Menu :size="20" :stroke-width="2" />
          </el-button>

          <el-dropdown trigger="click" @command="handleCommand">
            <div class="front-user" role="button" tabindex="0">
              <UserAvatar :user="userStore.userInfo" :size="40" avatar-class="front-user__avatar" />
              <span class="front-user__meta">
                <span class="front-user__name">{{ displayName }}</span>
              </span>
              <ChevronDown class="front-user__arrow" :size="16" :stroke-width="2" />
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <User :size="16" :stroke-width="2" />
                  个人信息
                </el-dropdown-item>
                <el-dropdown-item command="password">
                  <Lock :size="16" :stroke-width="2" />
                  修改密码
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <LogOut :size="16" :stroke-width="2" />
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </header>

    <el-drawer
      v-model="drawerVisible"
      direction="rtl"
      size="78%"
      :with-header="false"
      class="front-drawer"
    >
      <div class="front-drawer__head">
        <span class="front-drawer__title">菜单</span>
        <el-button circle aria-label="关闭菜单" @click="drawerVisible = false">
          <X :size="18" :stroke-width="2" />
        </el-button>
      </div>
      <nav class="front-nav front-nav--mobile" aria-label="主导航">
        <router-link
          v-for="item in navMenus"
          :key="item.path"
          :to="item.path"
          class="front-nav__item"
          :class="{ 'is-active': activeMenu === item.path }"
          @click="drawerVisible = false"
        >
          {{ item.name }}
        </router-link>
      </nav>
    </el-drawer>

    <main class="front-main">
      <router-view v-slot="{ Component, route: viewRoute }">
        <keep-alive :include="tagsStore.cachedViews">
          <component :is="Component" :key="viewRoute.name" />
        </keep-alive>
      </router-view>
    </main>

    <FrontFooter />
  </div>
</template>

<script setup>
import { computed, ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Bell, ChevronDown, User, Lock, LogOut, Menu, X } from 'lucide-vue-next'
import { useUserStore } from '@/store/user'
import { useTagsViewStore } from '@/store/tagsView'
import { teardownSession } from '@/utils/session'
import { SITE_NAME, SITE_TAGLINE } from '@/config/site'
import { FRONT_NAV_ITEMS } from '@/config/frontNav'
import { getUnreadCount } from '@/api/notify'
import FrontFooter from '@/components/front/FrontFooter.vue'
import UserAvatar from '@/components/UserAvatar.vue'

const HOME_MENU_PATH = '/user/home'
const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const tagsStore = useTagsViewStore()
const siteName = SITE_NAME
const siteTagline = SITE_TAGLINE
const navMenus = FRONT_NAV_ITEMS
const drawerVisible = ref(false)
const unreadCount = ref(0)

const activeMenu = computed(() => {
  if (route.path === HOME_MENU_PATH || route.path.startsWith(`${HOME_MENU_PATH}/`)) {
    return HOME_MENU_PATH
  }
  return route.path
})

async function refreshUnread() {
  try {
    const data = await getUnreadCount()
    unreadCount.value = data?.count || 0
  } catch {
    unreadCount.value = 0
  }
}

onMounted(async () => {
  if (!userStore.userInfo) {
    await userStore.fetchUser()
  }
  tagsStore.restored = false
  tagsStore.restoreFromStorage(userStore.role, 'user')
  await refreshUnread()
})

watch(
  () => route.path,
  (path) => {
    if (path.startsWith('/user')) {
      refreshUnread()
    }
  }
)

const displayName = computed(
  () => userStore.userInfo?.nickname || userStore.userInfo?.username || '用户'
)

function handleCommand(command) {
  if (command === 'profile') {
    router.push('/user/profile')
  } else if (command === 'password') {
    router.push('/user/profile/password')
  } else if (command === 'logout') {
    tagsStore.clear()
    userStore.logout()
    teardownSession()
    router.push('/login')
  }
}
</script>

<style scoped>
.front-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--app-bg);
  color: var(--app-text);
}

.front-header {
  position: sticky;
  top: 0;
  z-index: 50;
  width: 100%;
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--app-border);
  box-shadow: 0 1px 0 rgba(47, 155, 106, 0.06);
}

.front-header__shell {
  display: grid;
  grid-template-columns: 1fr min(1180px, 100%) 1fr;
  align-items: center;
  min-height: 68px;
}

.front-brand--aside {
  grid-column: 1;
  justify-self: start;
  padding-left: 20px;
}

.front-header__content {
  grid-column: 2;
  padding: 0 16px;
  height: 68px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

.front-header__right {
  grid-column: 3;
  justify-self: end;
  display: flex;
  align-items: center;
  gap: 8px;
  padding-right: 20px;
}

.front-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: inherit;
}

.front-brand__logo {
  width: 40px;
  height: 40px;
  object-fit: contain;
  display: block;
  background: transparent;
}

.front-brand__text {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.front-brand__name {
  font-size: 17px;
  font-weight: 700;
  color: var(--care-ink);
  letter-spacing: 0.02em;
}

.front-brand__tag {
  font-size: 11px;
  color: var(--care-green);
  font-weight: 500;
}

.front-nav {
  display: flex;
  align-items: center;
  gap: 6px;
}

.front-nav__item {
  display: inline-flex;
  align-items: center;
  padding: 9px 16px;
  font-size: 15px;
  font-weight: 600;
  color: var(--care-muted);
  text-decoration: none;
  border-radius: 999px;
  transition: color 0.2s, background-color 0.2s;
}

.front-nav__item:hover {
  color: var(--care-green-dark);
  background: var(--care-green-soft);
}

.front-nav__item.is-active {
  color: #fff;
  background: var(--care-green);
  box-shadow: 0 4px 12px rgba(47, 155, 106, 0.28);
}

.front-nav--mobile {
  flex-direction: column;
  align-items: stretch;
  gap: 6px;
  padding: 10px 12px;
}

.front-nav--mobile .front-nav__item {
  padding: 14px 16px;
  border-radius: 12px;
}

.front-bell-badge {
  display: inline-flex;
  line-height: 1;
}

.front-bell-btn {
  border: none;
  color: var(--care-muted);
  background: transparent;
}

.front-bell-btn:hover {
  color: var(--care-green-dark);
  background: var(--care-green-soft);
}

.front-menu-btn {
  display: none;
  border: none;
  color: var(--care-muted);
}

.front-user {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 10px 4px 4px;
  border-radius: 999px;
  cursor: pointer;
  border: 1px solid transparent;
  transition: background-color 0.2s, border-color 0.2s;
}

.front-user:hover {
  background: var(--care-green-soft);
  border-color: var(--care-line);
}

.front-user__avatar {
  background: var(--care-green-soft);
  color: var(--care-green-dark);
  font-weight: 700;
}

.front-user__meta {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.front-user__name {
  font-size: 14px;
  font-weight: 600;
  color: var(--care-ink);
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.front-user__arrow {
  font-size: 12px;
  color: var(--care-muted);
}

.front-drawer__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid var(--app-border);
}

.front-drawer__title {
  font-size: 16px;
  font-weight: 700;
}

.front-main {
  flex: 1;
  width: 100%;
  padding: 0;
  box-sizing: border-box;
}

:deep(.el-dropdown-menu__item) {
  display: flex;
  align-items: center;
  gap: 8px;
}

@media (max-width: 900px) {
  .front-header__shell {
    grid-template-columns: auto 1fr auto;
  }

  .front-header__content {
    display: none;
  }

  .front-menu-btn {
    display: inline-flex;
  }

  .front-brand__tag {
    display: none;
  }
}

@media (min-width: 901px) {
  .front-menu-btn {
    display: none !important;
  }
}
</style>
