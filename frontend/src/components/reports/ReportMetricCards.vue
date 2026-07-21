<template>
  <section class="report-metrics" aria-label="Report summary metrics">
    <article v-for="item in items" :key="item.label" class="report-metric">
      <div class="report-metric__topline">
        <span class="report-metric__icon" :class="`report-metric__icon--${item.tone || 'primary'}`">
          <component :is="item.icon" :size="19" aria-hidden="true" />
        </span>
        <span v-if="item.change !== undefined" class="report-metric__change" :class="getChangeClass(item.change)">
          <TrendingUp v-if="item.change >= 0" :size="14" aria-hidden="true" />
          <TrendingDown v-else :size="14" aria-hidden="true" />
          {{ Math.abs(item.change) }}%
        </span>
      </div>
      <p>{{ item.label }}</p>
      <strong>{{ item.value }}</strong>
      <small>{{ item.detail }}</small>
    </article>
  </section>
</template>

<script setup>
import { TrendingDown, TrendingUp } from '@lucide/vue'

defineProps({
  items: {
    type: Array,
    default: () => [],
  },
})

function getChangeClass(change) {
  return change >= 0 ? 'report-metric__change--positive' : 'report-metric__change--negative'
}
</script>

<style scoped>
.report-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-3);
}

.report-metric {
  min-width: 0;
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-elevated);
  box-shadow: var(--shadow-sm);
}

.report-metric__topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}

.report-metric__icon {
  display: grid;
  width: 36px;
  height: 36px;
  place-items: center;
  border-radius: var(--radius-md);
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.report-metric__icon--success { background: var(--color-success-light); color: var(--color-success); }
.report-metric__icon--warning { background: var(--color-warning-light); color: var(--color-warning); }
.report-metric__icon--danger { background: var(--color-danger-light); color: var(--color-danger); }
.report-metric__icon--info { background: var(--color-info-light); color: var(--color-info); }

.report-metric__change {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--font-size-caption);
  font-weight: var(--font-weight-semibold);
}

.report-metric__change--positive { color: var(--color-success); }
.report-metric__change--negative { color: var(--color-danger); }
.report-metric p, .report-metric small { margin: 0; color: var(--color-text-muted); }
.report-metric p { font-size: var(--font-size-sm); }
.report-metric strong { display: block; margin: var(--space-1) 0; font-size: var(--font-size-h3); line-height: 1.15; }
.report-metric small { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

@media (max-width: 980px) {
  .report-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 520px) {
  .report-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .report-metric { padding: var(--space-3); }
  .report-metric__topline { margin-bottom: var(--space-2); }
  .report-metric__change { display: none; }
  .report-metric strong { font-size: var(--font-size-h4); }
}

@media (max-width: 350px) {
  .report-metrics { grid-template-columns: 1fr; }
}
</style>
