<template>
  <div class="front-page agent-chat-page">
    <div class="front-shell">
      <section class="chat-head">
        <h1>智能助手</h1>
        <p>用自然语言办理查漏服、约体检等服务</p>
      </section>

      <section class="chat-layout">
        <div class="chat-main">
          <div class="chat-toolbar">
            <el-select v-model="elderId" placeholder="选择老人" class="chat-toolbar__select">
              <el-option v-for="e in elders" :key="e.id" :label="e.name" :value="e.id" />
            </el-select>
            <span class="chat-toolbar__spacer" />
            <el-button round @click="newSession">新会话</el-button>
          </div>

          <div ref="listRef" class="chat-messages">
            <div v-if="!messages.length && !sending" class="chat-empty">
              <div class="chat-empty__icon" aria-hidden="true">
                <Sparkles :size="28" :stroke-width="2" />
              </div>
              <p class="chat-empty__title">可以这样问，或直接输入您的需求</p>
              <div class="chat-empty__prompts">
                <button
                  v-for="text in samplePrompts"
                  :key="text"
                  type="button"
                  class="chat-prompt"
                  :disabled="!elderId || sending"
                  @click="sendQuick(text)"
                >
                  <MessageCircle :size="16" :stroke-width="2" />
                  <span>{{ text }}</span>
                </button>
              </div>
            </div>

            <div
              v-for="(m, idx) in messages"
              :key="idx"
              class="chat-row"
              :class="m.role === 'user' ? 'is-user' : 'is-bot'"
            >
              <span class="chat-row__avatar" :class="m.role === 'user' ? 'is-user' : 'is-bot'">
                <UserRound v-if="m.role === 'user'" :size="18" :stroke-width="2" />
                <Bot v-else :size="18" :stroke-width="2" />
              </span>
              <div class="chat-bubble">
                <div class="chat-bubble__role">{{ m.role === 'user' ? '我' : '助手' }}</div>
                <div class="chat-bubble__text">{{ m.content }}</div>
                <AgentThoughtSteps
                  v-if="m.role === 'assistant' && m.steps?.length"
                  :steps="m.steps"
                  :animate="m.animate !== false"
                />
                <div v-if="m.pendingConfirm?.options?.length" class="chat-quick">
                  <el-button
                    v-for="opt in m.pendingConfirm.options"
                    :key="opt"
                    type="primary"
                    plain
                    round
                    size="small"
                    @click="sendQuick(opt)"
                  >
                    {{ opt }}
                  </el-button>
                </div>
              </div>
            </div>

            <div v-if="sending" class="chat-row is-bot">
              <span class="chat-row__avatar is-bot">
                <Bot :size="18" :stroke-width="2" />
              </span>
              <div class="chat-bubble">
                <div class="chat-bubble__role">助手</div>
                <div class="chat-bubble__text chat-bubble__text--loading">
                  <span class="chat-dots"><i /><i /><i /></span>
                  正在为您办理…
                </div>
              </div>
            </div>
          </div>

          <div class="chat-input">
            <el-input
              ref="inputRef"
              v-model="input"
              type="textarea"
              :rows="2"
              :disabled="!elderId || sending"
              placeholder="输入需求，Enter 发送（Shift+Enter 换行）"
              @keydown.enter.exact.prevent="send"
            />
            <el-button type="primary" round :loading="sending" :disabled="!elderId" @click="send">
              发送
            </el-button>
          </div>
          <p class="chat-input__hint">
            请先选择老人；无可用时段时可去「服务中心」预约，用药可到「服药打卡」标记
          </p>
        </div>

        <aside class="chat-aside">
          <h3>使用说明</h3>
          <ul class="chat-aside__list">
            <li>选择要服务的绑定老人</li>
            <li>用一句话描述需求，助手会自动查档、查药、约服务</li>
            <li>回复下方可展开「办理过程」查看助手如何处理</li>
            <li>需要选时段时，点击助手给出的快捷选项即可</li>
            <li>无时段或网络异常时，可改去「服务中心」「服药打卡」办理</li>
          </ul>

          <div v-if="selectedElder" class="chat-aside__elder">
            <h4>当前老人</h4>
            <p class="chat-aside__elder-name">{{ selectedElder.name }}</p>
            <p v-if="selectedElder.chronicDiseases" class="chat-aside__elder-meta">
              {{ selectedElder.chronicDiseases }}
            </p>
          </div>
        </aside>
      </section>
    </div>
  </div>
</template>

<script setup>
/**
 * 智能助手对话页：选择绑定老人 → 多轮 Agent（演示/真模型）→ 展示办理步骤与待确认时段。
 */
defineOptions({ name: 'AgentChat' })

import { ref, computed, nextTick, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Bot, MessageCircle, Sparkles, UserRound } from 'lucide-vue-next'
import { getMyElders } from '@/api/elder'
import { agentChat } from '@/api/agent'
import AgentThoughtSteps from '@/components/AgentThoughtSteps.vue'

const samplePrompts = [
  '我爸最近老忘记吃降压药，而且这周想约一次体检',
  '帮我看看最近有没有漏服记录',
  '帮我爸约下周的社区体检',
  '社区居家养老补贴怎么申请？标准是多少？',
  '老年人吃降压药有哪些注意事项？漏服怎么办？'
]

const elders = ref([])
const elderId = ref(null)
const sessionId = ref(null)
const input = ref('')
const sending = ref(false)
const demoMode = ref(true)
const messages = ref([])
const listRef = ref(null)
const inputRef = ref(null)

const selectedElder = computed(() => elders.value.find((e) => e.id === elderId.value) || null)

async function newSession() {
  if (!messages.value.length) return
  try {
    await ElMessageBox.confirm('确定开始新会话？当前对话记录将被清空。', '新会话', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    sessionId.value = null
    messages.value = []
  } catch {
    /* cancelled */
  }
}

async function scrollBottom() {
  await nextTick()
  const el = listRef.value
  if (el) el.scrollTop = el.scrollHeight
}

async function sendQuick(text) {
  input.value = text
  await send()
}

async function send() {
  const text = input.value.trim()
  if (!text) return
  if (!elderId.value) {
    ElMessage.warning('请先选择要服务的绑定老人')
    return
  }
  if (sending.value) return

  messages.value.push({ role: 'user', content: text })
  input.value = ''
  sending.value = true
  await scrollBottom()
  try {
    const data = await agentChat({
      sessionId: sessionId.value || undefined,
      elderId: elderId.value,
      message: text
    })
    sessionId.value = data.sessionId
    demoMode.value = data.demoMode !== false
    messages.value.push({
      role: 'assistant',
      content: data.reply,
      steps: data.steps || [],
      pendingConfirm: data.pendingConfirm,
      animate: true
    })
    await scrollBottom()
    inputRef.value?.focus?.()
  } catch (err) {
    const msg = String(err?.message || '')
    const isTimeout = /timeout|超时/i.test(msg)
    messages.value.push({
      role: 'assistant',
      content: isTimeout
        ? '请求超时了。请检查网络后重试；也可以直接前往「服务中心」手动预约，或到「服药打卡」查看用药记录。'
        : '抱歉，请求未能完成。请稍后重试，或改用「服务中心」「服药打卡」手动办理。',
      steps: [],
      animate: false
    })
    await scrollBottom()
  } finally {
    sending.value = false
  }
}

onMounted(async () => {
  elders.value = (await getMyElders()) || []
  if (elders.value.length) elderId.value = elders.value[0].id
})
</script>

<style scoped>
.agent-chat-page {
  padding: 28px 0 48px;
}

.chat-head h1 {
  margin: 0 0 6px;
  font-size: 28px;
  font-weight: 800;
  color: var(--care-ink);
}

.chat-head p {
  margin: 0 0 18px;
  color: var(--care-muted);
}

.chat-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: 16px;
  align-items: start;
}

.chat-main {
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(30, 42, 36, 0.05);
  border: 1px solid var(--care-line);
  display: flex;
  flex-direction: column;
  min-height: min(72vh, 640px);
}

.chat-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  padding: 14px 16px;
  border-bottom: 1px solid var(--care-line);
}

.chat-toolbar__select {
  width: 160px;
}

.chat-toolbar__spacer {
  flex: 1;
}

.chat-messages {
  flex: 1;
  min-height: 360px;
  padding: 18px 16px;
  overflow-y: auto;
}

.chat-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px 12px 20px;
  text-align: center;
}

.chat-empty__icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--care-green-soft);
  color: var(--care-green-dark);
  margin-bottom: 14px;
}

.chat-empty__title {
  margin: 0 0 16px;
  font-size: 15px;
  color: var(--care-muted);
}

.chat-empty__prompts {
  width: 100%;
  max-width: 520px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.chat-prompt {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  width: 100%;
  padding: 12px 14px;
  border: 1px solid var(--care-line);
  border-radius: 12px;
  background: #fbfdfc;
  color: var(--care-ink);
  font-size: 14px;
  line-height: 1.55;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.chat-prompt:hover:not(:disabled) {
  border-color: #9fd4b8;
  box-shadow: 0 6px 16px rgba(47, 155, 106, 0.1);
}

.chat-prompt:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.chat-prompt svg {
  flex-shrink: 0;
  margin-top: 2px;
  color: var(--care-green);
}

.chat-row {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
  max-width: 88%;
  align-items: flex-start;
}

.chat-row.is-user {
  flex-direction: row-reverse;
  margin-left: auto;
}

.chat-row.is-bot {
  margin-right: auto;
}

.chat-row__avatar {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.chat-row__avatar.is-bot {
  background: var(--care-green-soft);
  color: var(--care-green-dark);
}

.chat-row__avatar.is-user {
  background: #eef2f7;
  color: #475569;
}

.chat-bubble {
  min-width: 0;
  max-width: calc(100% - 46px);
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.chat-row.is-user .chat-bubble {
  align-items: flex-end;
}

.chat-bubble__role {
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 4px;
}

.chat-row.is-user .chat-bubble__role {
  text-align: right;
}

.chat-bubble__text {
  display: inline-block;
  padding: 11px 14px;
  border-radius: 14px;
  background: #f1f5f9;
  color: #0f172a;
  white-space: pre-wrap;
  line-height: 1.6;
  font-size: 15px;
  max-width: 100%;
  text-align: left;
}

.chat-row.is-user .chat-bubble__text {
  background: var(--care-green);
  color: #fff;
  border-bottom-right-radius: 4px;
}

.chat-row.is-bot .chat-bubble__text {
  border-bottom-left-radius: 4px;
}

.chat-bubble__text--loading {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--care-muted);
}

.chat-dots {
  display: inline-flex;
  gap: 4px;
}

.chat-dots i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--care-green);
  animation: chat-dot 1.2s infinite ease-in-out;
}

.chat-dots i:nth-child(2) {
  animation-delay: 0.15s;
}

.chat-dots i:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes chat-dot {
  0%,
  80%,
  100% {
    opacity: 0.35;
    transform: scale(0.85);
  }
  40% {
    opacity: 1;
    transform: scale(1);
  }
}

.chat-quick {
  margin-top: 10px;
  width: 100%;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chat-input {
  display: flex;
  gap: 10px;
  padding: 14px 16px 8px;
  border-top: 1px solid var(--care-line);
  align-items: flex-end;
}

.chat-input .el-textarea {
  flex: 1;
}

.chat-input__hint {
  margin: 0;
  padding: 0 16px 12px;
  font-size: 12px;
  color: #94a3b8;
}

.chat-aside {
  background: #fff;
  border-radius: 16px;
  padding: 18px;
  border: 1px solid var(--care-line);
  box-shadow: 0 8px 24px rgba(30, 42, 36, 0.04);
}

.chat-aside h3 {
  margin: 0 0 10px;
  font-size: 16px;
  font-weight: 700;
  color: var(--care-ink);
}

.chat-aside h3:not(:first-child) {
  margin-top: 18px;
}

.chat-aside h4 {
  margin: 0 0 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--care-muted);
}

.chat-aside__list {
  margin: 0;
  padding-left: 18px;
  font-size: 13px;
  line-height: 1.65;
  color: var(--care-muted);
}

.chat-aside__list li + li {
  margin-top: 6px;
}

.chat-aside__elder {
  margin-top: 16px;
  padding: 12px;
  border-radius: 12px;
  background: var(--care-green-soft);
  border: 1px solid rgba(47, 155, 106, 0.18);
}

.chat-aside__elder-name {
  margin: 0 0 4px;
  font-size: 15px;
  font-weight: 700;
  color: var(--care-green-dark);
}

.chat-aside__elder-meta {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--care-muted);
}

@media (max-width: 900px) {
  .chat-layout {
    grid-template-columns: 1fr;
  }

  .chat-aside {
    order: -1;
  }

  .chat-row {
    max-width: 100%;
  }
}
</style>
