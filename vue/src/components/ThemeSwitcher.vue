<template>
  <el-dropdown trigger="click" placement="bottom-end" @command="selectTheme">
    <el-button class="theme-trigger" circle title="切换主题色">
      <el-icon :size="18"><Brush /></el-icon>
    </el-button>
    <template #dropdown>
      <el-dropdown-menu class="theme-dropdown">
        <el-dropdown-item
          v-for="item in themeOptions"
          :key="item.id"
          :command="item.id"
          :class="{ 'is-active': currentId === item.id }"
        >
          <span class="theme-picker__dot" :style="{ background: item.color }" />
          <span class="theme-picker__label">{{ item.label }}</span>
          <el-icon v-if="currentId === item.id" class="theme-picker__check"><Check /></el-icon>
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Brush, Check } from '@element-plus/icons-vue'
import { themeOptions, applyTheme, getStoredThemeId } from '@/utils/theme'

const currentId = ref('blue')

function selectTheme(id) {
  currentId.value = applyTheme(id)
}

onMounted(() => {
  currentId.value = applyTheme(getStoredThemeId())
})
</script>

<style scoped>
.theme-trigger {
  border: 1px solid var(--app-border);
  color: var(--app-text-secondary);
  background: var(--app-card-bg);
}

.theme-trigger:hover {
  color: var(--app-primary);
  border-color: var(--el-color-primary-light-7);
  background: var(--el-color-primary-light-9);
}

.theme-dropdown :deep(.el-dropdown-menu__item) {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 120px;
}

.theme-dropdown :deep(.el-dropdown-menu__item.is-active) {
  color: var(--app-primary);
  background: var(--el-color-primary-light-9);
}

.theme-picker__dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: inset 0 0 0 1px rgba(15, 23, 42, 0.1);
}

.theme-picker__label {
  flex: 1;
}

.theme-picker__check {
  color: var(--app-primary);
  font-size: 14px;
}
</style>
