<template>
  <div class="bg-white dark:bg-slate-800 rounded-xl shadow-lg p-6 mb-6">
    <h3 class="text-xl font-semibold mb-4 text-slate-900 dark:text-slate-100">
        Omsætning pr. by (DKK)
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
  data: CityData[]
}>()

const { isDark } = useTheme()

console.log("CityRevenueChart received props.data:", props.data)

watch(() => props.data, (newData) => {
  console.log("CityRevenueChart data changed:", newData)
}, { immediate: true })

const formatCurrency = (value: number) => {
  return new Intl.NumberFormat('da-DK', {
    style: 'currency',
    currency: 'DKK',
    maximumFractionDigits: 0
  }).format(value)
}

const chartData = computed(() => {
  const sortedData = [...props.data].sort((a, b) => b.revenue - a.revenue)
  
  return {
    labels: sortedData.map(d => d.city),
    datasets: [
      {
        label: 'Omsætning',
        backgroundColor: 'rgba(16, 185, 129, 0.7)',
        borderColor: 'rgba(16, 185, 129, 1)',
        borderWidth: 1,
        data: sortedData.map(d => d.revenue)
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
    },
    tooltip: {
      callbacks: {
        label: function(context: any) {
          return `Omsætning: ${formatCurrency(context.raw)}`
        }
      }
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        color: isDark.value ? '#e2e8f0' : '#334155',
        callback: function(value: any) {
          return formatCurrency(value)
        }
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