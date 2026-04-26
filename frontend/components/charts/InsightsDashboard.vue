<template>
  <div class="space-y-8">
    <!-- Header Stats -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm border border-slate-100 dark:border-slate-700">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-blue-100 dark:bg-blue-900/40 flex items-center justify-center">
            <svg class="w-5 h-5 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <div>
            <p class="text-sm text-slate-500 dark:text-slate-400">Total Ordrer</p>
            <p class="text-xl font-bold text-slate-900 dark:text-slate-100">{{ insights.total_orders.toLocaleString() }}</p>
          </div>
        </div>
      </div>

      <div class="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm border border-slate-100 dark:border-slate-700">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-emerald-100 dark:bg-emerald-900/40 flex items-center justify-center">
            <svg class="w-5 h-5 text-emerald-600 dark:text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <p class="text-sm text-slate-500 dark:text-slate-400">Total Omsætning</p>
            <p class="text-xl font-bold text-slate-900 dark:text-slate-100">€{{ formatNumber(insights.total_revenue) }}</p>
          </div>
        </div>
      </div>

      <div class="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm border border-slate-100 dark:border-slate-700">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-rose-100 dark:bg-rose-900/40 flex items-center justify-center">
            <svg class="w-5 h-5 text-rose-600 dark:text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div>
            <p class="text-sm text-slate-500 dark:text-slate-400">Tabt Omsætning</p>
            <p class="text-xl font-bold text-rose-600 dark:text-rose-400">€{{ formatNumber(insights.total_leak_revenue) }}</p>
          </div>
        </div>
      </div>

      <div class="bg-white dark:bg-slate-800 rounded-xl p-5 shadow-sm border border-slate-100 dark:border-slate-700">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-lg bg-amber-100 dark:bg-amber-900/40 flex items-center justify-center">
            <svg class="w-5 h-5 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
            </svg>
          </div>
          <div>
            <p class="text-sm text-slate-500 dark:text-slate-400">Tabt Rate</p>
            <p class="text-xl font-bold text-amber-600 dark:text-amber-400">{{ insights.leak_rate }}%</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Recommendations Section -->
    <div v-if="insights.recommendations?.length" class="bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-indigo-950/30 dark:to-purple-950/30 rounded-2xl p-6 border border-indigo-100 dark:border-indigo-900/50">
      <div class="flex items-center gap-2 mb-4">
        <svg class="w-5 h-5 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
        <h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100">Anbefalinger</h3>
        <span class="ml-auto px-2.5 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300">
          {{ insights.insights_count }} indsigter
        </span>
      </div>

      <div class="grid gap-4">
        <div
          v-for="rec in insights.recommendations"
          :key="rec.priority"
          class="bg-white dark:bg-slate-800 rounded-xl p-4 shadow-sm border border-slate-200 dark:border-slate-700"
        >
          <div class="flex items-start gap-4">
            <div
              :class="[
                'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 font-bold text-sm',
                rec.priority === 1 ? 'bg-rose-100 text-rose-600 dark:bg-rose-900/50 dark:text-rose-400' :
                rec.priority === 2 ? 'bg-amber-100 text-amber-600 dark:bg-amber-900/50 dark:text-amber-400' :
                'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-400'
              ]"
            >
              {{ rec.priority }}
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <span
                  :class="[
                    'px-2 py-0.5 rounded text-xs font-medium',
                    rec.category === 'revenue' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-400' :
                    rec.category === 'operations' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-400' :
                    rec.category === 'retention' ? 'bg-purple-100 text-purple-700 dark:bg-purple-900/50 dark:text-purple-400' :
                    'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-400'
                  ]"
                >
                  {{ categoryLabel(rec.category) }}
                </span>
                <span
                  v-if="rec.potential_impact"
                  :class="[
                    'px-2 py-0.5 rounded text-xs font-medium',
                    rec.potential_impact === 'high' ? 'bg-rose-100 text-rose-700 dark:bg-rose-900/50 dark:text-rose-400' :
                    rec.potential_impact === 'medium' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-400' :
                    'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-400'
                  ]"
                >
                  {{ rec.potential_impact }} impact
                </span>
              </div>
              <h4 class="font-medium text-slate-900 dark:text-slate-100 mb-1">{{ rec.title }}</h4>
              <p class="text-sm text-slate-600 dark:text-slate-400">{{ rec.description }}</p>
              <p v-if="rec.metric_focus" class="mt-2 text-xs font-medium text-indigo-600 dark:text-indigo-400">
                Fokus: {{ rec.metric_focus }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Two Column Layout -->
    <div class="grid lg:grid-cols-2 gap-6">
      <!-- Revenue Leaks -->
      <div class="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-sm border border-slate-100 dark:border-slate-700">
        <div class="flex items-center gap-2 mb-4">
          <svg class="w-5 h-5 text-rose-600 dark:text-rose-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100">Indtægtslækage</h3>
        </div>

        <div v-if="insights.top_revenue_leaks?.length" class="space-y-3">
          <div
            v-for="leak in insights.top_revenue_leaks"
            :key="leak.type"
            class="flex items-center gap-4 p-3 rounded-lg bg-slate-50 dark:bg-slate-900/50"
          >
            <div class="flex-1">
              <div class="flex items-center gap-2">
                <span class="font-medium text-slate-900 dark:text-slate-100">{{ leakLabel(leak.type) }}</span>
                <span
                  :class="[
                    'px-2 py-0.5 rounded text-xs font-medium',
                    leak.severity === 'high' ? 'bg-rose-100 text-rose-700 dark:bg-rose-900/50 dark:text-rose-400' :
                    leak.severity === 'medium' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-400' :
                    'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-400'
                  ]"
                >
                  {{ leak.severity }}
                </span>
              </div>
              <p class="text-sm text-slate-500 dark:text-slate-400">{{ leak.count }} ordrer</p>
            </div>
            <div class="text-right">
              <p class="font-semibold text-rose-600 dark:text-rose-400">-€{{ formatNumber(leak.revenue) }}</p>
              <p class="text-sm text-slate-500 dark:text-slate-400">{{ leak.percentage.toFixed(1) }}%</p>
            </div>
          </div>
        </div>
        <p v-else class="text-slate-500 dark:text-slate-400 text-center py-8">Ingen data tilgængelig</p>
      </div>

      <!-- Retention Metrics -->
      <div class="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-sm border border-slate-100 dark:border-slate-700">
        <div class="flex items-center gap-2 mb-4">
          <svg class="w-5 h-5 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
          <h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100">Kunderetention</h3>
        </div>

        <div v-if="insights.retention_metrics" class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div class="p-4 rounded-lg bg-slate-50 dark:bg-slate-900/50">
              <p class="text-sm text-slate-500 dark:text-slate-400">Samlet Kunder</p>
              <p class="text-2xl font-bold text-slate-900 dark:text-slate-100">{{ insights.retention_metrics.total_customers.toLocaleString() }}</p>
            </div>
            <div class="p-4 rounded-lg bg-slate-50 dark:bg-slate-900/50">
              <p class="text-sm text-slate-500 dark:text-slate-400">Retentionsrate</p>
              <p class="text-2xl font-bold text-emerald-600 dark:text-emerald-400">{{ insights.retention_metrics.retention_rate }}%</p>
            </div>
            <div class="p-4 rounded-lg bg-slate-50 dark:bg-slate-900/50">
              <p class="text-sm text-slate-500 dark:text-slate-400">Gns. LTV</p>
              <p class="text-2xl font-bold text-slate-900 dark:text-slate-100">€{{ formatNumber(insights.retention_metrics.avg_customer_lifetime_value) }}</p>
            </div>
            <div class="p-4 rounded-lg bg-slate-50 dark:bg-slate-900/50">
              <p class="text-sm text-slate-500 dark:text-slate-400">Engangskøb</p>
              <p class="text-2xl font-bold text-amber-600 dark:text-amber-400">{{ insights.retention_metrics.one_time_customer_pct }}%</p>
            </div>
          </div>
        </div>
        <p v-else class="text-slate-500 dark:text-slate-400 text-center py-8">Ingen data tilgængelig</p>
      </div>

      <!-- Bottlenecks -->
      <div class="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-sm border border-slate-100 dark:border-slate-700">
        <div class="flex items-center gap-2 mb-4">
          <svg class="w-5 h-5 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100">Flaskehalse</h3>
        </div>

        <div v-if="insights.top_bottlenecks?.length" class="space-y-3">
          <div
            v-for="bottleneck in insights.top_bottlenecks"
            :key="bottleneck.stage"
            class="p-3 rounded-lg bg-slate-50 dark:bg-slate-900/50"
          >
            <div class="flex items-center justify-between mb-2">
              <span class="font-medium text-slate-900 dark:text-slate-100 text-sm">{{ bottleneck.stage }}</span>
              <span
                :class="[
                  'px-2 py-0.5 rounded text-xs font-medium',
                  bottleneck.severity === 'high' ? 'bg-rose-100 text-rose-700 dark:bg-rose-900/50 dark:text-rose-400' :
                  bottleneck.severity === 'medium' ? 'bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-400' :
                  'bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-400'
                ]"
              >
                {{ bottleneck.severity }}
              </span>
            </div>
            <div class="flex items-center gap-4 text-sm">
              <span class="text-slate-600 dark:text-slate-400">
                <span class="font-medium">{{ bottleneck.avg_duration_hours.toFixed(1) }}h</span> gennemsnit
              </span>
              <span class="text-slate-600 dark:text-slate-400">
                <span class="font-medium text-rose-600 dark:text-rose-400">{{ bottleneck.delay_rate.toFixed(1) }}%</span> forsinket
              </span>
            </div>
          </div>
        </div>
        <p v-else class="text-slate-500 dark:text-slate-400 text-center py-8">Ingen data tilgængelig</p>
      </div>

      <!-- Top Refunded Products -->
      <div class="bg-white dark:bg-slate-800 rounded-2xl p-6 shadow-sm border border-slate-100 dark:border-slate-700">
        <div class="flex items-center gap-2 mb-4">
          <svg class="w-5 h-5 text-slate-600 dark:text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
          </svg>
          <h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100">Mest Returnerede Produkter</h3>
        </div>

        <div v-if="insights.top_refunded_products?.length" class="space-y-3">
          <div
            v-for="product in insights.top_refunded_products.slice(0, 5)"
            :key="product.product_name"
            class="flex items-center gap-4 p-3 rounded-lg bg-slate-50 dark:bg-slate-900/50"
          >
            <div class="flex-1 min-w-0">
              <p class="font-medium text-slate-900 dark:text-slate-100 text-sm truncate">{{ product.product_name }}</p>
              <p class="text-xs text-slate-500 dark:text-slate-400">{{ product.refund_count }} returneringer</p>
            </div>
            <div class="text-right">
              <p
                :class="[
                  'font-semibold',
                  product.refund_rate > 15 ? 'text-rose-600 dark:text-rose-400' :
                  product.refund_rate > 8 ? 'text-amber-600 dark:text-amber-400' :
                  'text-slate-600 dark:text-slate-400'
                ]"
              >
                {{ product.refund_rate }}%
              </p>
              <p class="text-xs text-slate-500 dark:text-slate-400">returrate</p>
            </div>
          </div>
        </div>
        <p v-else class="text-slate-500 dark:text-slate-400 text-center py-8">Ingen data tilgængelig</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'

interface InsightsDashboard {
  total_orders: number
  total_revenue: number
  total_leak_revenue: number
  leak_rate: number
  top_revenue_leaks: Array<{
    type: string
    count: number
    revenue: number
    percentage: number
    severity: 'high' | 'medium' | 'low'
  }>
  top_bottlenecks: Array<{
    stage: string
    avg_duration_hours: number
    orders_count: number
    delay_rate: number
    severity: 'high' | 'medium' | 'low'
  }>
  top_refunded_products: Array<{
    product_name: string
    refund_count: number
    refund_rate: number
    revenue: number
  }>
  retention_metrics: {
    total_customers: number
    retention_rate: number
    avg_customer_lifetime_value: number
    one_time_customer_pct: number
    frequent_customer_pct: number
  }
  recommendations: Array<{
    priority: number
    category: string
    title: string
    description: string
    potential_impact: string
    metric_focus?: string
  }>
  insights_count: number
  critical_issues: number
}

const props = defineProps<{
  data?: InsightsDashboard
}>()

const insights = ref<InsightsDashboard>({
  total_orders: 0,
  total_revenue: 0,
  total_leak_revenue: 0,
  leak_rate: 0,
  top_revenue_leaks: [],
  top_bottlenecks: [],
  top_refunded_products: [],
  retention_metrics: {
    total_customers: 0,
    retention_rate: 0,
    avg_customer_lifetime_value: 0,
    one_time_customer_pct: 0,
    frequent_customer_pct: 0,
  },
  recommendations: [],
  insights_count: 0,
  critical_issues: 0,
})

const loading = ref(false)
const error = ref<string | null>(null)

const fetchInsights = async () => {
  loading.value = true
  error.value = null
  try {
    const data = await $fetch<InsightsDashboard>('/api/insights_dashboard')
    insights.value = data
  } catch (e: any) {
    console.error('Failed to fetch insights dashboard:', e)
    error.value = e?.message || 'Failed to load insights'
  } finally {
    loading.value = false
  }
}

const formatNumber = (value: number): string => {
  if (value >= 1000000) {
    return (value / 1000000).toFixed(1) + 'M'
  }
  if (value >= 1000) {
    return (value / 1000).toFixed(1) + 'K'
  }
  return value.toFixed(0)
}

const leakLabel = (type: string): string => {
  const labels: Record<string, string> = {
    failed_payment: 'Betaling fejlede',
    cancelled: 'Annulleret',
    refunded: 'Refunderet',
  }
  return labels[type] || type
}

const categoryLabel = (category: string): string => {
  const labels: Record<string, string> = {
    revenue: 'Omsætning',
    operations: 'Drift',
    retention: 'Retention',
    products: 'Produkter',
  }
  return labels[category] || category
}

onMounted(() => {
  if (props.data) {
    insights.value = props.data
  } else {
    fetchInsights()
  }
})

watch(() => props.data, (newData) => {
  if (newData) {
    insights.value = newData
  }
})
</script>