<template>
  <article class="stat-card stat-card--dashboard">
    <header class="stat-card__header">
      <div>
        <p class="text-label text-muted m-0">{{ title }}</p>
        <p class="stat-card__value m-0">{{ value }}</p>
      </div>
      <span class="stat-card__icon" aria-hidden="true">{{ icon }}</span>
    </header>
    <p class="stat-card__trend m-0">{{ trend }}</p>
    <footer class="stat-card__footer">
      <slot name="footer">Footer placeholder</slot>
    </footer>
  </article>
</template>

<script setup>
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
    default: 'Trend placeholder',
  },
  icon: {
    type: String,
    default: 'i',
  },
})
</script>

<!--
src/components: Reusable interface building blocks shared across layouts and pages.
TODO:
- Add props for labels, values, trends, and loading states.
-->
