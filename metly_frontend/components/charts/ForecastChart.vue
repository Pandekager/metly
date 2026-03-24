<template>
  <div class="forecast-chart-container">
    <div class="top-section">
      <div class="filter-section">
        <div class="filter-group">
          <label for="subcategory" class="filter-label text-slate-700 dark:text-slate-200 font-semibold text-sm mb-2 block">Kategori</label>
          <select
            id="subcategory"
            v-model="selectedGroup"
            class="filter-select w-full p-4 text-sm border border-slate-200 dark:border-slate-600 rounded-lg cursor-pointer transition-all duration-200 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-100"
          >
            <option value="all">Alle</option>
            <option
              v-for="group in subcategoryNames"
              :key="group"
              :value="group"
            >
              {{ group }}
            </option>
          </select>
        </div>
      </div>

      <div class="monthly-cards">
        <div
          v-for="([month, summary], index) in Object.entries(monthlySummaries)"
          :key="month"
          class="monthly-card flex-1 min-w-[180px] p-4 border border-slate-200 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-800"
        >
          <h3 class="text-lg font-normal text-slate-800 dark:text-slate-200 mb-2">{{ month }}</h3>
          <p
            class="text-base font-semibold"
            :class="getTrendColor(summary, index)"
          >
            {{ summary.hasForecast ? 'Forventet' : 'Faktisk' }} salg:
            {{ summary.amount || 0 }} stk.
          </p>
        </div>
      </div>
    </div>

    <div class="chart-wrapper">
      <Line
        v-if="filteredForecasts.length > 0"
        :data="chartData"
        :options="chartOptions"
        ref="chartRef"
      />
      <div v-else class="empty-state">
        <p class="empty-text text-slate-500 dark:text-slate-400">Ingen data tilgængelig for den valgte kategori</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import { Line } from 'vue-chartjs'
import { COLORS } from '~/utils/colors'
import type { Forecast } from '~/types/forecast'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

const props = defineProps<{
  forecasts: Forecast[]
}>()

const selectedGroup = ref<string>('all')
const chartRef = ref<any>(null)

const subcategoryNames = computed(() => {
  const groups = new Set(
    props.forecasts.map((f) => f.subcategory_name || 'Ukategoriseret')
  )
  return Array.from(groups).sort()
})

const filteredForecasts = computed(() => {
  if (selectedGroup.value === 'all') return props.forecasts
  return props.forecasts.filter(
    (f) => f.subcategory_name === selectedGroup.value
  )
})

const formatDate = (input: string | Date) => {
  const d = new Date(input)
  const dd = String(d.getDate()).padStart(2, '0')
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const yyyy = d.getFullYear()
  return `${dd}-${mm}-${yyyy}`
}

const chartData = computed(() => {
  if (selectedGroup.value === 'all') {
    const map = new Map<
      string,
      {
        dateISO: string
        hasActual: boolean
        actual: number
        hasForecast: boolean
        forecast: number
      }
    >()

    for (const f of props.forecasts) {
      const dateISO = new Date(f.date).toISOString().split('T')[0]
      const entry = map.get(dateISO) ?? {
        dateISO,
        hasActual: false,
        actual: 0,
        hasForecast: false,
        forecast: 0,
      }
      if (f.is_forecast) {
        entry.hasForecast = true
        entry.forecast += f.amount ?? 0
      } else {
        entry.hasActual = true
        entry.actual += f.amount ?? 0
      }
      map.set(dateISO, entry)
    }

    const sortedEntries = Array.from(map.values()).sort(
      (a, b) => new Date(a.dateISO).getTime() - new Date(b.dateISO).getTime()
    )

    const labels = sortedEntries.map((s) => formatDate(s.dateISO))
    const actualData = sortedEntries.map((s) =>
      s.hasActual ? s.actual : null
    )
    const forecastData = sortedEntries.map((s) =>
      s.hasForecast ? s.forecast : null
    )

    let lastActualIndex = -1
    for (let i = 0; i < actualData.length; i++) {
      if (actualData[i] !== null) lastActualIndex = i
    }
    const firstForecastIndex = forecastData.findIndex(
      (value) => value !== null
    )
    if (
      lastActualIndex !== -1 &&
      firstForecastIndex !== -1 &&
      firstForecastIndex > lastActualIndex
    ) {
      forecastData[lastActualIndex] = actualData[lastActualIndex!]
    }

    return {
      labels,
      datasets: [
        {
          label: 'Faktisk Salg',
          data: actualData,
          borderColor: COLORS.actualLine,
          backgroundColor: COLORS.actualBackground,
          fill: true,
          borderWidth: 2,
          pointRadius: 3,
          pointBackgroundColor: COLORS.actualLine,
          tension: 0.4,
        },
        {
          label: 'Forventet Salg',
          data: forecastData,
          borderColor: COLORS.forecastLine,
          backgroundColor: COLORS.forecastBackground,
          fill: true,
          borderWidth: 2,
          pointRadius: 3,
          pointBackgroundColor: COLORS.forecastLine,
          tension: 0.4,
          spanGaps: true,
        },
      ],
    }
  }

  const sortedData = [...filteredForecasts.value].sort(
    (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
  )

  const actualData = sortedData.map((f) => (f.is_forecast ? null : f.amount))
  const forecastData = sortedData.map((f) => (f.is_forecast ? f.amount : null))

  let lastActualIndex = -1
  for (let i = 0; i < actualData.length; i++) {
    if (actualData[i] !== null) lastActualIndex = i
  }
  const firstForecastIndex = forecastData.findIndex((value) => value !== null)
  if (
    lastActualIndex !== -1 &&
    firstForecastIndex !== -1 &&
    firstForecastIndex > lastActualIndex
  ) {
    forecastData[lastActualIndex] = actualData[lastActualIndex!]
  }

  return {
    labels: sortedData.map((f) => formatDate(f.date)),
    datasets: [
      {
        label: 'Faktisk Salg',
        data: actualData,
        borderColor: COLORS.actualLine,
        backgroundColor: COLORS.actualBackground,
        fill: true,
        borderWidth: 2,
        pointRadius: 3,
        pointBackgroundColor: COLORS.actualLine,
        tension: 0.4,
      },
      {
        label: 'Forventet Salg',
        data: forecastData,
        borderColor: COLORS.forecastLine,
        backgroundColor: COLORS.forecastBackground,
        fill: true,
        borderWidth: 2,
        pointRadius: 3,
        pointBackgroundColor: COLORS.forecastLine,
        tension: 0.4,
        spanGaps: true,
      },
    ],
  }
})

const { isDark } = useTheme()

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { 
      display: true,
      labels: {
        color: isDark.value ? '#94a3b8' : '#475569'
      }
    },
    tooltip: {
      backgroundColor: isDark.value ? '#1e293b' : '#ffffff',
      titleColor: isDark.value ? '#e2e8f0' : '#1e293b',
      bodyColor: isDark.value ? '#cbd5e1' : '#475569',
      borderColor: isDark.value ? '#475569' : '#e2e8f0',
      borderWidth: 1,
      callbacks: {
        label: function (context: any) {
          const value = context.raw
          return value ? `${context.dataset.label}: ${value}` : null
        },
      },
    },
  },
  scales: {
    x: {
      grid: { color: isDark.value ? '#334155' : '#cbd5e1' },
      ticks: { color: isDark.value ? '#94a3b8' : '#475569' },
    },
    y: {
      beginAtZero: true,
      grid: { color: isDark.value ? '#334155' : '#cbd5e1' },
      ticks: {
        color: isDark.value ? '#94a3b8' : '#475569',
        stepSize: 1,
        callback: function (value: any) {
          const v =
            typeof value === 'object' && value !== null
              ? (value as any).value
              : value
          return Number.isInteger(Number(v)) ? String(v) : null
        },
        precision: 0,
      },
    },
  },
}))

type MonthlySummary = {
  amount: number
  hasForecast: boolean
  hasActual: boolean
}

const monthlySummaries = computed(() => {
  const summaries: Record<string, MonthlySummary> = {}

  filteredForecasts.value.forEach((forecast) => {
    const date = new Date(forecast.date)
    const month = date.toLocaleString('default', {
      month: 'long',
      year: 'numeric',
    })

    if (!summaries[month]) {
      summaries[month] = { amount: 0, hasForecast: false, hasActual: false }
    }

    if (forecast.is_forecast) {
      summaries[month].hasForecast = true
    } else {
      summaries[month].hasActual = true
    }

    summaries[month].amount += forecast.amount || 0
  })

  return summaries
})

const getTrendColor = (summary: MonthlySummary, index: number): string => {
  const values = Object.values(monthlySummaries.value)
  const prev = values[index - 1] as MonthlySummary | undefined
  if (!prev) return 'text-slate-600 dark:text-slate-400'
  const diff = summary.amount - prev.amount
  const tol = Math.max(1, Math.abs(prev.amount) * 0.01)
  if (Math.abs(diff) <= tol) return 'text-slate-600 dark:text-slate-400'
  if (diff > 0) return 'text-green-600'
  return 'text-red-500'
}
</script>

<style scoped>
.forecast-chart-container {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
}

.top-section {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  margin-bottom: 24px;
  gap: 16px;
}

.filter-section {
  flex: 0 0 auto;
  display: flex;
  justify-content: flex-start;
}

.filter-group {
  width: 100%;
  min-width: 200px;
}

.filter-select:hover {
  border-color: #cbd5e1;
}

.filter-select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.monthly-cards {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  flex: 1 1 auto;
}

.chart-wrapper {
  width: 100%;
  max-width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  border-radius: 12px;
  min-height: 450px;
  position: relative;
  overflow: hidden;
}

.chart-wrapper canvas {
  max-width: 100% !important;
  height: auto !important;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  font-size: 16px;
}

.empty-text {
  margin: 0;
}

@media (max-width: 768px) {
  .top-section {
    flex-direction: column;
  }

  .filter-section {
    width: 100%;
  }

  .filter-group {
    min-width: 100%;
  }

  .monthly-cards {
    width: 100%;
  }

  .chart-wrapper {
    padding: 1rem;
    min-height: 350px;
  }
}

@media (max-width: 640px) {
  .chart-wrapper {
    padding: 0.5rem;
    min-height: 300px;
  }
}
</style>
