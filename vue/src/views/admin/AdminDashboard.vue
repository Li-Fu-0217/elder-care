<template>
  <div class="page-container admin-dashboard" v-loading="loading">
    <div class="stat-cards">
      <div
        v-for="card in cards"
        :key="card.key"
        class="stat-card"
        :style="{ '--accent': cardColor(card.key) }"
      >
        <div class="stat-card__icon" aria-hidden="true">
          <component :is="cardIcon(card.key)" :size="22" :stroke-width="2" />
        </div>
        <div class="stat-card__body">
          <div class="stat-card__label">{{ card.label }}</div>
          <div class="stat-card__value">{{ card.value }}</div>
        </div>
      </div>
    </div>

    <div class="chart-grid">
      <div class="chart-panel">
        <div class="chart-panel__title">预约状态分布</div>
        <div ref="chartBookingStatus" class="chart-panel__body" />
      </div>
      <div class="chart-panel">
        <div class="chart-panel__title">各服务类型预约量</div>
        <div ref="chartByService" class="chart-panel__body" />
      </div>
      <div class="chart-panel">
        <div class="chart-panel__title">近 7 日预约趋势</div>
        <div ref="chartTrend" class="chart-panel__body" />
      </div>
      <div class="chart-panel">
        <div class="chart-panel__title">助手工具调用分布</div>
        <div ref="chartTools" class="chart-panel__body" />
      </div>
    </div>
  </div>
</template>

<script setup>
defineOptions({ name: 'AdminDashboard' })

import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import {
  Users,
  UserRound,
  CalendarClock,
  BellRing,
  Trophy,
  Pill,
  BookOpen,
  Cpu
} from 'lucide-vue-next'
import { getAdminStats } from '@/api/stats'

const COLORS = [
  '#3b82f6',
  '#10b981',
  '#f59e0b',
  '#ef4444',
  '#8b5cf6',
  '#06b6d4',
  '#ec4899',
  '#84cc16'
]

const CARD_COLORS = {
  elders: '#3b82f6',
  users: '#8b5cf6',
  pendingBookings: '#f59e0b',
  openAlerts: '#ef4444',
  activities: '#10b981',
  missedMeds: '#ec4899',
  knowledge: '#06b6d4',
  toolCalls: '#84cc16'
}

const CARD_ICONS = {
  elders: Users,
  users: UserRound,
  pendingBookings: CalendarClock,
  openAlerts: BellRing,
  activities: Trophy,
  missedMeds: Pill,
  knowledge: BookOpen,
  toolCalls: Cpu
}

const loading = ref(false)
const cards = ref([])
const chartBookingStatus = ref(null)
const chartByService = ref(null)
const chartTrend = ref(null)
const chartTools = ref(null)

const charts = []

function cardColor(key) {
  return CARD_COLORS[key] || COLORS[0]
}

function cardIcon(key) {
  return CARD_ICONS[key] || Users
}

function disposeCharts() {
  while (charts.length) {
    const c = charts.pop()
    c.dispose()
  }
}

function mountChart(el, option) {
  if (!el) return null
  const chart = echarts.init(el)
  chart.setOption(option)
  charts.push(chart)
  return chart
}

function pieOption(title, data) {
  return {
    color: COLORS,
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: {
      bottom: 0,
      type: 'scroll',
      textStyle: { color: '#64748b', fontSize: 12 }
    },
    series: [
      {
        name: title,
        type: 'pie',
        radius: ['42%', '68%'],
        center: ['50%', '46%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 6,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: { color: '#475569', fontSize: 12 },
        data: data.map((d) => ({ name: d.name, value: d.value }))
      }
    ]
  }
}

function barOption(data) {
  return {
    color: COLORS,
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 16, top: 28, bottom: 32 },
    xAxis: {
      type: 'category',
      data: data.map((d) => d.name),
      axisLabel: { color: '#64748b' },
      axisLine: { lineStyle: { color: '#e2e8f0' } }
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: { color: '#64748b' },
      splitLine: { lineStyle: { color: '#f1f5f9' } }
    },
    series: [
      {
        type: 'bar',
        barWidth: 36,
        data: data.map((d, i) => ({
          value: d.value,
          itemStyle: {
            color: COLORS[i % COLORS.length],
            borderRadius: [8, 8, 0, 0]
          }
        }))
      }
    ]
  }
}

function trendOption(dates, series) {
  return {
    color: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'],
    tooltip: { trigger: 'axis' },
    legend: {
      top: 0,
      textStyle: { color: '#64748b', fontSize: 12 }
    },
    grid: { left: 40, right: 16, top: 40, bottom: 28 },
    xAxis: {
      type: 'category',
      data: dates,
      boundaryGap: false,
      axisLabel: { color: '#64748b' },
      axisLine: { lineStyle: { color: '#e2e8f0' } }
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: { color: '#64748b' },
      splitLine: { lineStyle: { color: '#f1f5f9' } }
    },
    series: (series || []).map((s, idx) => ({
      name: s.name,
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 8,
      lineStyle: { width: 3 },
      areaStyle: {
        color: COLORS[idx % COLORS.length] + '33'
      },
      data: s.data
    }))
  }
}

function render(data) {
  disposeCharts()
  cards.value = data.cards || []
  mountChart(
    chartBookingStatus.value,
    pieOption('预约状态', data.bookingStatus || [])
  )
  mountChart(chartByService.value, barOption(data.bookingByService || []))
  mountChart(
    chartTrend.value,
    trendOption(data.bookingTrendDates || [], data.bookingTrendSeries || [])
  )
  mountChart(chartTools.value, pieOption('工具调用', data.toolUsage || []))
}

function onResize() {
  charts.forEach((c) => c.resize())
}

async function loadData() {
  loading.value = true
  try {
    const data = await getAdminStats()
    await nextTick()
    render(data || {})
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', onResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  disposeCharts()
})
</script>

<style scoped>
.admin-dashboard {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 100%;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.stat-card {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: flex-start;
  gap: 14px;
  background: #fff;
  border-radius: 12px;
  padding: 16px 18px 14px;
  border: none;
  box-shadow: none;
}

.stat-card__icon {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--accent, #3b82f6);
  background: color-mix(in srgb, var(--accent, #3b82f6) 14%, #fff);
}

.stat-card__body {
  min-width: 0;
  flex: 1;
}

.stat-card__label {
  font-size: 13px;
  color: #64748b;
}

.stat-card__value {
  margin-top: 6px;
  font-size: 28px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.02em;
  line-height: 1.2;
}

.chart-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.chart-panel {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #eef2f7;
  padding: 14px 14px 8px;
  min-height: 320px;
}

.chart-panel__title {
  font-size: 14px;
  font-weight: 600;
  color: #334155;
  margin-bottom: 4px;
}

.chart-panel__body {
  width: 100%;
  height: 280px;
}

@media (max-width: 1200px) {
  .stat-cards {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .chart-grid {
    grid-template-columns: 1fr;
  }
}
</style>
