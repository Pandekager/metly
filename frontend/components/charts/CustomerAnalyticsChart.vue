<template>
  <div class="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6 mb-6">
    <h3 class="text-xl font-semibold mb-4 text-slate-900 dark:text-slate-100">
      Kunder og omsætning pr. by
    </h3>
    <div class="h-80">
      <Bar :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale
} from 'chart.js'
import { Bar } from 'vue-chartjs'
import { COLORS } from '~/utils/colors'

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale)

interface CityData {
  city: string
  customer_count: number
  revenue: number
  latitude: number
  longitude: number
}

const props = defineProps<{
  data: CityData[]
}>()

const { isDark } = useTheme()

const chartData = computed(() => {
  if (!props.data || props.data.length === 0) {
    return { labels: [], datasets: [] }
  }
  
  const sortedData = [...props.data].sort((a, b) => b.customer_count - a.customer_count)
  
  return {
    labels: sortedData.map(d => d.city),
    datasets: [
      {
        label: 'Antal kunder',
        backgroundColor: COLORS.actualLine,
        borderColor: COLORS.actualLine,
        borderWidth: 1,
        data: sortedData.map(d => d.customer_count),
        yAxisID: 'y',
        barPercentage: 0.7,
        borderRadius: 8,
        hoverBackgroundColor: 'rgba(255, 255, 255, 0.5)',
        hoverBorderColor: 'rgba(255, 255, 255, 0.5)'
      },
      {
        label: 'Omsætning (DKK)',

        backgroundColor: COLORS.forecastLine,
        borderColor: COLORS.forecastLine,
        borderWidth: 1,
        data: sortedData.map(d => d.revenue),
        yAxisID: 'y1',
        barPercentage: 0.7,
        borderRadius: 8,
        hoverBackgroundColor: 'rgba(255, 255, 255, 0.5)',
        hoverBorderColor: 'rgba(255, 255, 255, 0.5)'
      }
    ]
  }
})

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: {
        color: isDark.value ? '#e2e8f0' : '#334155'
      }
    }
  },
  scales: {
    y: {
      type: 'linear' as const,
      display: true,
      position: 'left' as const,
      beginAtZero: true,
      title: {
        display: true,
        text: 'Antal kunder',
        color: isDark.value ? '#94a3b8' : '#475569'
      },
      ticks: {
        color: isDark.value ? '#94a3b8' : '#475569'
      },
      grid: {
        color: isDark.value ? '#334155' : '#e2e8f0'
      }
    },
    y1: {
      type: 'linear' as const,
      display: true,
      position: 'right' as const,
      beginAtZero: true,
      title: {
        display: true,
        text: 'Omsætning (DKK)',
        color: isDark.value ? '#94a3b8' : '#475569'
      },
      ticks: {
        color: isDark.value ? '#94a3b8' : '#475569',
        callback: function(value: any) {
          return new Intl.NumberFormat('da-DK', {
            style: 'currency',
            currency: 'DKK',
            notation: 'compact',
            maximumFractionDigits: 0
          }).format(value)
        }
      },
      grid: {
        drawOnChartArea: false
      }
    },
    x: {
      ticks: {
        color: isDark.value ? '#94a3b8' : '#475569'
      },
      grid: {
        color: isDark.value ? '#334155' : '#e2e8f0'
      }
    }
  }
}))
</script>
