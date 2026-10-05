<template>
  <div class="icon-picker">
    <el-popover
      v-model:visible="popoverVisible"
      placement="bottom-start"
      :width="400"
      trigger="click"
      popper-class="icon-picker-popper"
    >
      <template #reference>
        <el-button class="icon-picker__trigger" :class="{ 'is-empty': !modelValue }">
          <el-icon v-if="modelValue" :size="18">
            <component :is="resolveIcon(modelValue)" />
          </el-icon>
          <span class="icon-picker__label">{{ modelValue || placeholder }}</span>
          <el-icon class="icon-picker__arrow"><ArrowDown /></el-icon>
        </el-button>
      </template>
      <el-input
        v-model="filter"
        placeholder="搜索图标名称"
        clearable
        :prefix-icon="Search"
        class="icon-picker__search"
      />
      <div class="icon-picker__grid">
        <button
          v-for="name in filteredIcons"
          :key="name"
          type="button"
          class="icon-picker__item"
          :class="{ 'is-active': modelValue === name }"
          :title="name"
          @click="selectIcon(name)"
        >
          <el-icon :size="20">
            <component :is="resolveIcon(name)" />
          </el-icon>
        </button>
        <div v-if="!filteredIcons.length" class="icon-picker__empty">无匹配图标</div>
      </div>
    </el-popover>
    <el-button v-if="modelValue" type="info" link @click="clearIcon">清除</el-button>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ArrowDown, Search } from '@element-plus/icons-vue'
import { iconNames, resolveIcon } from '@/utils/icon'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: '选择图标' }
})

const emit = defineEmits(['update:modelValue'])

const popoverVisible = ref(false)
const filter = ref('')

const filteredIcons = computed(() => {
  const q = filter.value.trim().toLowerCase()
  if (!q) return iconNames
  return iconNames.filter((name) => name.toLowerCase().includes(q))
})

function selectIcon(name) {
  emit('update:modelValue', name)
  popoverVisible.value = false
  filter.value = ''
}

function clearIcon() {
  emit('update:modelValue', '')
}
</script>

<style scoped>
.icon-picker {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.icon-picker__trigger {
  flex: 1;
  justify-content: flex-start;
  min-width: 0;
}

.icon-picker__trigger.is-empty .icon-picker__label {
  color: var(--el-text-color-placeholder);
}

.icon-picker__label {
  flex: 1;
  margin: 0 8px;
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.icon-picker__arrow {
  margin-left: auto;
  color: var(--el-text-color-secondary);
}

.icon-picker__search {
  margin-bottom: 10px;
}

.icon-picker__grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 6px;
  max-height: 240px;
  overflow-y: auto;
}

.icon-picker__item {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 36px;
  padding: 0;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  background: var(--el-fill-color-blank);
  cursor: pointer;
  color: var(--el-text-color-regular);
  transition: border-color 0.15s, color 0.15s, background 0.15s;
}

.icon-picker__item:hover {
  border-color: var(--app-primary, var(--el-color-primary));
  color: var(--app-primary, var(--el-color-primary));
}

.icon-picker__item.is-active {
  border-color: var(--app-primary, var(--el-color-primary));
  background: var(--el-color-primary-light-9);
  color: var(--app-primary, var(--el-color-primary));
}

.icon-picker__empty {
  grid-column: 1 / -1;
  padding: 24px 0;
  text-align: center;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}
</style>

<style>
.icon-picker-popper {
  padding: 12px !important;
}
</style>
