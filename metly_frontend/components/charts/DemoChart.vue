<template>
  <div class="demo-chart-container">
    <div class="chart-wrapper">
      <Line
        :data="chartData"
        :options="chartOptions"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
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

// Generate random trend data with confidence intervals
const generateDemoData = () => {
  const months = ['Jan', 'Feb', 'Mar', 'Apr', 'Maj', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dec']
  const actualData: (number | null)[] = []
  const forecastData: (number | null)[] = []
  const upperBound: (number | null)[] = []
  const lowerBound: (number | null)[] = []
  
  let baseValue = 50
  const currentMonth = new Date().getMonth()
  
  for (let i = 0; i < 12; i++) {
    // Add some randomness to trend
    const trend = Math.sin(i * 0.5) * 10 + (i * 2)
    const randomVariation = (Math.random() - 0.5) * 15
    const value = Math.max(10, baseValue + trend + randomVariation)
    
    // Confidence interval (±10-20% of value)
    const confidenceRange = value * (0.1 + Math.random() * 0.1)
    
    if (i <= currentMonth) {
      // Past/Current data - show actuals
      actualData.push(Math.round(value))
      forecastData.push(null)
      upperBound.push(null)
      lowerBound.push(null)
    } else {
      // Future data - show forecast with confidence
      actualData.push(null)
      forecastData.push(Math.round(value))
      upperBound.push(Math.round(value + confidenceRange))
      lowerBound.push(Math.round(value - confidenceRange))
    }
  }
  
  return { months, actualData, forecastData, upperBound, lowerBound }
}

const demoData = generateDemoData()

// Connect the forecast line to last actual point
const connectedForecastData = computed(() => {
  const data = [...demoData.forecastData]
  const lastActualIndex = demoData.actualData.findLastIndex((val) => val !== null)
  if (lastActualIndex !== -1 && data[lastActualIndex + 1] !== null) {
    data[lastActualIndex] = demoData.actualData[lastActualIndex]
  }
  return data
})

const chartData = computed(() => ({
  labels: demoData.months,
  datasets: [
    {
      label: 'Faktisk Salg',
      data: demoData.actualData,
      borderColor: COLORS.actualLine,
      backgroundColor: COLORS.actualBackground,
      fill: true,
      borderWidth: 3,
      pointRadius: 5,
      pointBackgroundColor: COLORS.actualLine,
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
      tension: 0.4,
    },
    {
      label: 'Forventet Salg',
      data: connectedForecastData.value,
      borderColor: COLORS.forecastLine,
      backgroundColor: COLORS.forecastBackground,
      fill: true,
      borderWidth: 3,
      borderDash: [5, 5],
      pointRadius: 5,
      pointBackgroundColor: COLORS.forecastLine,
      pointBorderColor: '#fff',
      pointBorderWidth: 2,
      tension: 0.4,
      spanGaps: true,
    },
    // Upper confidence bound
    {
      label: 'Øvre konfidens',
      data: demoData.upperBound,
      borderColor: 'rgba(139, 92, 246, 0.3)',
      backgroundColor: 'transparent',
      fill: false,
      borderWidth: 1,
      pointRadius: 0,
      tension: 0.4,
      spanGaps: true,
    },
    // Lower confidence bound with fill between upper
    {
      label: 'Nedre konfidens',
      data: demoData.lowerBound,
      borderColor: 'rgba(139, 92, 246, 0.3)',
      backgroundColor: 'rgba(139, 92, 246, 0.15)',
      fill: '-1', // Fill to previous dataset (upper bound)
      borderWidth: 1,
      pointRadius: 0,
      tension: 0.4,
      spanGaps: true,
    },
  ],
}))

const chartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    intersect: false,
    mode: 'index' as const,
  },
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      titleColor: '#1e293b',
      bodyColor: '#475569',
      borderColor: '#e2e8f0',
      borderWidth: 1,
      padding: 12,
      cornerRadius: 8,
      callbacks: {
        label: function(context: any) {
          const label = context.dataset.label
          const value = context.raw
          if (value === null || value === undefined) return null
          if (label === 'Øvre konfidens' || label === 'Nedre konfidens') {
            return null
          }
          return `${label}: ${value} stk`
        },
      },
    },
  },
  scales: {
    x: {
      grid: {
        color: 'rgba(226, 232, 240, 0.5)',
        drawBorder: false,
      },
      ticks: {
        color: '#64748b',
        font: {
          size: 11,
          family: "'Montserrat', sans-serif",
        },
      },
    },
    y: {
      beginAtZero: true,
      grid: {
        color: 'rgba(226, 232, 240, 0.5)',
        drawBorder: false,
      },
      ticks: {
        color: '#64748b',
        font: {
          size: 11,
          family: "'Montserrat', sans-serif",
        },
        padding: 8,
      },
    },
  },
}))
</script>

<style scoped>
.demo-chart-container {
  width: 100%;
  height: 100%;
}

.chart-wrapper {
  width: 100%;
  height: 200px;
  position: relative;
}

.chart-wrapper canvas {
  max-width: 100% !important;
  height: 100% !important;
}
</style>
