<template>
  <div class="platform-trend" :aria-label="ariaLabel">
    <div v-for="point in points" :key="point.month" class="platform-trend__row">
      <span>{{ formatMonth(point.month) }}</span>
      <div class="platform-trend__track" aria-hidden="true">
        <span :style="{ width: getWidth(point[valueKey]) }"></span>
      </div>
      <strong>{{ formatValue(point[valueKey]) }}</strong>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  points: {
    type: Array,
    default: () => [],
  },
  valueKey: {
    type: String,
    default: 'students',
  },
  ariaLabel: {
    type: String,
    default: 'Platform trend',
  },
})

const maximumValue = computed(() => {
  return Math.max(1, ...props.points.map((point) => Number(point[props.valueKey]) || 0))
})

const numberFormatter = new Intl.NumberFormat('en-IN')

function getWidth(value) {
  return `${Math.max(3, ((Number(value) || 0) / maximumValue.value) * 100)}%`
}

function formatValue(value) {
  return numberFormatter.format(Number(value) || 0)
}

function formatMonth(value) {
  if (!value) return '—'

  const [year, month] = value.split('-').map(Number)

  return new Intl.DateTimeFormat('en-IN', {
    month: 'short',
    timeZone: 'UTC',
  }).format(new Date(Date.UTC(year, month - 1, 1)))
}
</script>

<style scoped>
.platform-trend {
  display: grid;
  gap: var(--space-4);
}

.platform-trend__row {
  display: grid;
  grid-template-columns: 38px minmax(100px, 1fr) 64px;
  align-items: center;
  gap: var(--space-3);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.platform-trend__row strong {
  text-align: right;
}

.platform-trend__track {
  height: 8px;
  overflow: hidden;
  border-radius: var(--radius-pill);
  background: var(--color-surface-secondary);
}

.platform-trend__track span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--color-primary);
}
</style>
