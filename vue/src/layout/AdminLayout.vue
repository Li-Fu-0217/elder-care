<template>
  <el-container class="layout layout--admin">
    <el-aside width="240px" class="sidebar">
      <div class="brand">
        <img class="brand-icon" src="@/assets/logo.png" alt="" aria-hidden="true" />
        <span class="brand-text">管理后台</span>
      </div>
      <el-menu
        v-if="menuList.length"
        :key="activeMenu"
        :default-active="activeMenu"
        router
        class="sidebar-menu"
        background-color="transparent"
        text-color="#94a3b8"
        active-text-color="#ffffff"
      >
        <el-menu-item v-for="item in menuList" :key="item.path" :index="item.path">
          <el-icon>
            <component :is="resolveIcon(item.icon)" />
          </el-icon>
          <span>{{ item.name }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container class="main-wrap">
      <el-header class="topbar" height="60px">
        <div class="topbar-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/admin/dashboard' }">后台</el-breadcrumb-item>
            <el-breadcrumb-item v-if="route.path !== '/admin/dashboard'">
              {{ currentTitle }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="topbar-right">
          <ThemeSwitcher />
          <el-tag type="danger" effect="plain" size="small" round>管理员</el-tag>
          <span class="topbar-user">{{ displayName }}</span>
          <el-dropdown trigger="click" placement="bottom-end" teleported @command="handleCommand">
            <span class="topbar-dropdown-trigger" tabindex="-1">
              <UserAvatar :user="userStore.userInfo" :size="36" avatar-class="topbar-avatar" />
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><UserFilled /></el-icon>
                  个人信息
                </el-dropdown-item>
                <el-dropdown-item command="password">
                  <el-icon><Lock /></el-icon>
                  修改密码
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <TagsView scope="admin" />
      <el-main class="main-content">
        <router-view v-slot="{ Component, route: viewRoute }">
          <keep-alive :include="tagsStore.cachedViews">
            <component :is="Component" :key="viewRoute.name" />
          </keep-alive>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
/**
 * 管理后台布局：侧栏动态菜单（/api/menus）、顶栏页签 + keep-alive、个人信息走头像下拉。
 */
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { Menu as MenuIcon } from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import { getMyMenus } from '@/api/menu'
import ThemeSwitcher from '@/components/ThemeSwitcher.vue'
import TagsView from '@/components/TagsView.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { useTagsViewStore } from '@/store/tagsView'
import { teardownSession } from '@/utils/session'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const tagsStore = useTagsViewStore()
const menuList = ref([])
const LAYOUT_LOCK_CLASS = 'admin-layout-lock'

const activeMenu = computed(() => {
  if (route.path.startsWith('/admin/profile')) {
    return route.path === '/admin/profile/password' ? '/admin/profile' : route.path
  }
  return route.path
})

function resolveIcon(name) {
  return ElementPlusIconsVue[name] || MenuIcon
}

onMounted(async () => {
  document.documentElement.classList.add(LAYOUT_LOCK_CLASS)
  if (!userStore.userInfo) {
    await userStore.fetchUser()
  }
  tagsStore.restored = false
  tagsStore.restoreFromStorage(userStore.role, 'admin')
  menuList.value = await getMyMenus()
})

onUnmounted(() => {
  document.documentElement.classList.remove(LAYOUT_LOCK_CLASS)
})

const currentTitle = computed(() => route.meta.title || '数据概览')
const displayName = computed(
  () => userStore.userInfo?.nickname || userStore.userInfo?.username || ''
)
function handleCommand(command) {
  if (command === 'profile') {
    router.push('/admin/profile')
  } else if (command === 'password') {
    router.push('/admin/profile/password')
  } else if (command === 'logout') {
    tagsStore.clear()
    userStore.logout()
    teardownSession()
    router.push('/login')
  }
}
</script>

<style scoped>
.layout {
  width: 100%;
  max-width: 100vw;
  height: 100vh;
  max-height: 100vh;
  overflow: hidden;
  background: var(--app-bg);
}

.sidebar {
  background: var(--app-sidebar-bg);
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.brand {
  height: 60px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.brand-icon {
  width: 36px;
  height: 36px;
  object-fit: contain;
  display: block;
  background: transparent;
}

.brand-text {
  font-size: 17px;
  font-weight: 600;
  color: #f8fafc;
}

.sidebar-menu {
  border-right: none;
  padding: 12px 10px;
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.sidebar-menu :deep(.el-menu-item) {
  height: 44px;
  line-height: 44px;
  margin-bottom: 4px;
  border-radius: var(--app-radius-sm);
}

.sidebar-menu :deep(.el-menu-item:hover) {
  background: var(--app-sidebar-hover) !important;
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  background: var(--app-sidebar-active) !important;
  font-weight: 500;
}

.main-wrap {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.topbar {
  flex-shrink: 0;
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: var(--app-card-bg);
  border-bottom: 1px solid var(--app-border);
  box-shadow: var(--app-shadow);
}

.topbar-left {
  min-width: 0;
  flex: 1;
  overflow: hidden;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.topbar-dropdown-trigger {
  display: inline-flex;
  align-items: center;
  outline: none;
  cursor: pointer;
}

.topbar-user {
  font-size: 14px;
  color: var(--app-text-secondary);
}

.topbar-avatar {
  cursor: pointer;
  background: linear-gradient(135deg, var(--app-primary-light), var(--app-primary-dark));
  color: #fff;
  font-weight: 600;
}

.main-wrap :deep(.tags-view) {
  flex-shrink: 0;
}

.main-content {
  flex: 1;
  min-width: 0;
  min-height: 0;
  --el-main-padding: 0;
  padding: 0 16px 16px;
  overflow: hidden;
}

.main-content :deep(> *) {
  max-width: 100%;
}
</style>

<style>
/* 管理端仅内容区滚动，避免 body 与 el-main 双滚动条及下拉定位偏移 */
html.admin-layout-lock,
html.admin-layout-lock body,
html.admin-layout-lock #app {
  width: 100%;
  height: 100%;
  overflow: hidden;
}

html.admin-layout-lock .layout--admin .main-content {
  overflow-x: hidden;
  overflow-y: auto;
  scrollbar-gutter: stable;
}
</style>
