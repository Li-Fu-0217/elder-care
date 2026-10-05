<template>
  <el-avatar :size="size" :src="src" :class="avatarClass">
    {{ showFallback ? fallback : '' }}
  </el-avatar>
</template>

<script setup>
/** 统一头像展示：有 avatar 路径显示图片，否则显示昵称/用户名首字母 */
import { computed } from 'vue'
import { resolveAvatarUrl, avatarFallbackText } from '@/utils/avatar'

const props = defineProps({
  user: {
    type: Object,
    default: null
  },
  size: {
    type: [Number, String],
    default: 36
  },
  avatarClass: {
    type: String,
    default: ''
  }
})

const src = computed(() => resolveAvatarUrl(props.user?.avatar))
const fallback = computed(() => avatarFallbackText(props.user))
const showFallback = computed(() => !src.value)
</script>
