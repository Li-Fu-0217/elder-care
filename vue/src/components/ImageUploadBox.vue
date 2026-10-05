<template>
  <div class="image-upload-box">
    <el-upload
      class="image-upload-box__upload"
      :class="[`image-upload-box--${shape}`]"
      :show-file-list="false"
      :accept="accept"
      :http-request="onUpload"
      :disabled="loading || disabled"
    >
      <div
        class="image-upload-box__trigger"
        :class="{ 'is-loading': loading, 'has-image': !!src }"
      >
        <img v-if="src" class="image-upload-box__img" :src="src" alt="" />
        <span v-else class="image-upload-box__text">{{ placeholder }}</span>
        <div v-if="loading" class="image-upload-box__mask">
          <span class="image-upload-box__loading-text">上传中</span>
        </div>
        <div v-else-if="src" class="image-upload-box__hover">
          <span>更换图片</span>
        </div>
      </div>
    </el-upload>
    <p v-if="hint" class="image-upload-box__hint">{{ hint }}</p>
    <el-button
      v-if="clearable && src && !loading"
      type="danger"
      link
      class="image-upload-box__clear"
      @click="emit('clear')"
    >
      移除
    </el-button>
  </div>
</template>

<script setup>
defineOptions({ name: 'ImageUploadBox' })

const props = defineProps({
  src: {
    type: String,
    default: ''
  },
  /** square 方形（头像等）；rectangle 矩形（封面、横幅等） */
  shape: {
    type: String,
    default: 'square',
    validator: (v) => ['square', 'rectangle'].includes(v)
  },
  placeholder: {
    type: String,
    default: '上传图片'
  },
  hint: {
    type: String,
    default: ''
  },
  accept: {
    type: String,
    default: 'image/jpeg,image/png,image/gif,image/webp'
  },
  loading: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  },
  clearable: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['upload', 'clear'])

function onUpload(options) {
  emit('upload', options)
}
</script>

<style scoped>
.image-upload-box {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
}

.image-upload-box__upload :deep(.el-upload) {
  display: block;
  line-height: 1;
}

.image-upload-box__trigger {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 8px;
  background: #f8fafc;
  border: 1px dashed var(--app-border);
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}

.image-upload-box__trigger:hover {
  border-color: var(--app-primary);
  background: #f0f7ff;
}

.image-upload-box__trigger.is-loading {
  cursor: wait;
}

.image-upload-box--square .image-upload-box__trigger {
  width: 120px;
  aspect-ratio: 1;
}

.image-upload-box--rectangle .image-upload-box__trigger {
  width: 160px;
  aspect-ratio: 4 / 3;
}

.image-upload-box__text {
  padding: 0 12px;
  font-size: 13px;
  color: var(--app-text-secondary);
  text-align: center;
  line-height: 1.4;
  user-select: none;
}

.image-upload-box__img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}

.image-upload-box__hover {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.45);
  color: #fff;
  font-size: 13px;
  opacity: 0;
  transition: opacity 0.2s;
  pointer-events: none;
}

.image-upload-box__trigger.has-image:hover .image-upload-box__hover {
  opacity: 1;
}

.image-upload-box__mask {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.75);
}

.image-upload-box__loading-text {
  font-size: 13px;
  color: var(--app-text-secondary);
}

.image-upload-box__hint {
  margin: 0;
  font-size: 12px;
  color: var(--app-text-secondary);
  line-height: 1.5;
}

.image-upload-box__clear {
  padding: 0;
  height: auto;
}
</style>
