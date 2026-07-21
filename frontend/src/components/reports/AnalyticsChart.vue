<template>
  <div class="analytics-chart" :style="{ '--chart-height': `${height}px` }">
    <component
      :is="chartComponent"
      :data="data"
      :options="mergedOptions"
      :aria-label="ariaLabel"
      role="img"
    />
  </div>
</template>

<script setup>
import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from 'chart.js'
import { computed } from 'vue'
import { Bar, Doughnut, Line } from 'vue-chartjs'

ChartJS.register(
  ArcElement,
  BarElement,
  CategoryScale,
  Filler,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
)

const props = defineProps({
  type: {
    type: String,
    default: 'bar',
  },
  data: {
    type: Object,
    required: true,
  },
  options: {
    type: Object,
    default: () => ({}),
  },
  height: {
    type: Number,
    default: 280,
  },
  ariaLabel: {
    type: String,
    default: 'Analytics chart',
  },
})

const chartComponent = computed(() => {
  if (props.type === 'line') return Line
  if (props.type === 'doughnut') return Doughnut
  return Bar
})

const mergedOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  animation: {
    duration: 350,
  },
  scales:
    props.type === 'doughnut'
      ? undefined
      : {
          x: {
            grid: { display: false },
            ticks: { color: '#6b7280' },
            stacked: false,
          },
          y: {
            beginAtZero: true,
            grid: { color: '#e5e7eb' },
            ticks: { color: '#6b7280', precision: 0 },
            stacked: false,
          },
        },
  ...props.options,
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        boxWidth: 10,
        boxHeight: 10,
        color: '#374151',
        padding: 16,
        usePointStyle: true,
        font: { size: 12 },
      },
      ...props.options.plugins?.legend,
    },
    tooltip: {
      padding: 12,
      backgroundColor: '#111827',
      titleColor: '#ffffff',
      bodyColor: '#ffffff',
      cornerRadius: 6,
      ...props.options.plugins?.tooltip,
    },
    ...props.options.plugins,
  },
}))
</script>

<style scoped>
.analytics-chart {
  position: relative;
  width: 100%;
  height: var(--chart-height);
  min-height: 220px;
}
</style>
