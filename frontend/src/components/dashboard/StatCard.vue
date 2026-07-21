<template>
  <article class="stat-card stat-card--dashboard">
    <header class="stat-card__header">
      <div>
        <p class="text-label text-muted m-0">{{ title }}</p>
        <p class="stat-card__value m-0">{{ value }}</p>
      </div>
      <span class="stat-card__icon" aria-hidden="true">
        <component :is="icon" :size="20" />
      </span>
    </header>
    <p v-if="trend" class="stat-card__trend m-0">{{ trend }}</p>
    <footer class="stat-card__footer">
      <slot name="footer"></slot>
    </footer>
  </article>
</template>

<script setup>
import { ChartNoAxesColumnIncreasing } from '@lucide/vue'

defineProps({
  title: {
    type: String,
    default: 'Statistic',
  },
  value: {
    type: String,
    default: '--',
  },
  trend: {
    type: String,
    default: '',
  },
  icon: {
    type: [Object, Function],
    default: ChartNoAxesColumnIncreasing,
  },
})
</script>
