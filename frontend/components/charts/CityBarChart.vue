<template>
  <div class="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6 mb-6">
    <h3 class="text-xl font-semibold mb-4 text-slate-900 dark:text-slate-100">
        Kunder pr. by
    </h3>
    <div class="h-80">
      <Bar :key="isDark ? 'dark' : 'light'" :data="chartData" :options="chartOptions" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
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

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale)

interface CityData {
  city: string
  customer_count: number
  revenue: number
}

const props = defineProps<{
  data: {
    city: string
    revenue: number
    order_count: number
  }[]
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
        backgroundColor: 'rgba(99, 102, 241, 0.7)',
        borderColor: 'rgba(99, 102, 241, 1)',
        borderWidth: 1,
        data: sortedData.map(d => d.customer_count)
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
      beginAtZero: true,
      ticks: {
        color: isDark.value ? '#e2e8f0' : '#334155'
      },
      grid: {
        color: isDark.value ? '#334155' : '#e2e8f0'
      }
    },
    x: {
      ticks: {
        color: isDark.value ? '#e2e8f0' : '#334155'
      },
      grid: {
        color: isDark.value ? '#334155' : '#e2e8f0'
      }
    }
  }
}))
</script>