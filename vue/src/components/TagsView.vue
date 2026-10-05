<template>
  <div class="tags-view">
    <div ref="scrollRef" class="tags-view__scroll">
      <router-link
        v-for="tag in tagsStore.visitedViews"
        :key="tag.path"
        :to="tag.fullPath"
        class="tags-view__item"
        :class="{ 'is-active': isActive(tag) }"
        @click.middle.prevent="closeTag(tag)"
      >
        <span class="tags-view__title">{{ tag.title }}</span>
        <el-icon
          v-if="!tag.affix"
          class="tags-view__close"
          @click.prevent.stop="closeTag(tag)"
        >
          <Close />
        </el-icon>
      </router-link>
    </div>
    <el-dropdown trigger="click" @command="handleMenu">
      <el-button class="tags-view__menu-btn" size="small" :icon="ArrowDown" />
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item command="others">关闭其他</el-dropdown-item>
          <el-dropdown-item command="all">关闭全部</el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Close, ArrowDown } from '@element-plus/icons-vue'
import { useTagsViewStore } from '@/store/tagsView'

const props = defineProps({
  scope: {
    type: String,
    required: true
  }
})

const route = useRoute()
const router = useRouter()
const tagsStore = useTagsViewStore()
const scrollRef = ref(null)

const homePath = props.scope === 'admin' ? '/admin/dashboard' : '/user/home'

function isActive(tag) {
  return tag.path === route.path
}

function addCurrentTag() {
  tagsStore.addView(route)
}

function closeTag(tag) {
  if (tag.affix) {
    return
  }
  const active = tag.path === route.path
  tagsStore.delView(tag)
  if (active) {
    const last = tagsStore.visitedViews[tagsStore.visitedViews.length - 1]
    router.push(last?.fullPath || homePath)
  }
}

function handleMenu(command) {
  const current = tagsStore.visitedViews.find((v) => v.path === route.path)
  if (!current) {
    return
  }
  if (command === 'others') {
    tagsStore.delOthers(current)
    if (!tagsStore.visitedViews.some((v) => v.path === route.path)) {
      router.push(current.fullPath)
    }
  } else if (command === 'all') {
    tagsStore.delAll()
    router.push(homePath)
  }
}

watch(
  () => route.fullPath,
  () => {
    if (!tagsStore.restored || tagsStore.activeScope !== props.scope) {
      return
    }
    addCurrentTag()
    nextTick(() => {
      const el = scrollRef.value?.querySelector('.tags-view__item.is-active')
      el?.scrollIntoView({ inline: 'nearest', block: 'nearest', behavior: 'smooth' })
    })
  },
  { immediate: true }
)

watch(
  () => tagsStore.restored,
  (ready) => {
    if (ready && tagsStore.activeScope === props.scope) {
      addCurrentTag()
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.tags-view {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px 12px;
  margin-bottom: 12px;
  background: var(--app-card-bg);
  border-bottom: 1px solid var(--app-border);
}

.tags-view__scroll {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
  overflow-x: auto;
  scrollbar-width: none;
}

.tags-view__scroll::-webkit-scrollbar {
  display: none;
}

.tags-view__item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 28px;
  padding: 0 10px;
  font-size: 12px;
  color: var(--app-text-secondary);
  background: #f8fafc;
  border: 1px solid var(--app-border);
  border-radius: 4px;
  text-decoration: none;
  white-space: nowrap;
}

.tags-view__item:hover {
  color: var(--app-primary);
  border-color: var(--el-color-primary-light-5);
}

.tags-view__item.is-active {
  color: var(--app-primary);
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary-light-5);
}

.tags-view__close {
  font-size: 12px;
  border-radius: 50%;
  padding: 1px;
}

.tags-view__close:hover {
  color: #fff;
  background: #94a3b8;
}

.tags-view__menu-btn {
  flex-shrink: 0;
  border: 1px solid var(--app-border);
}
</style>
