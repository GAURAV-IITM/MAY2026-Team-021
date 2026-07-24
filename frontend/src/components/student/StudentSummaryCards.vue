<template>
  <section class="student-summary" :aria-label="ariaLabel">
    <article
      v-for="item in items"
      :key="item.label"
      class="student-summary__card"
      :class="`student-summary__card--${item.tone || 'primary'}`"
    >
      <div class="student-summary__header">
        <span class="text-label text-muted">{{ item.label }}</span>
        <span class="student-summary__icon" aria-hidden="true">
          <component :is="item.icon || CircleGauge" :size="19" />
        </span>
      </div>
      <strong class="student-summary__value">{{ item.value }}</strong>
      <span class="student-summary__detail">{{ item.detail }}</span>
    </article>
  </section>
</template>

<script setup>
import { CircleGauge } from '@lucide/vue'

defineProps({
  items: { type: Array, default: () => [] },
  ariaLabel: { type: String, default: 'Student summary' },
})
</script>

<style scoped>
.student-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-4);
}

.student-summary__card {
  display: grid;
  gap: var(--space-3);
  min-width: 0;
  padding: var(--space-5);
  border: 1px solid var(--color-border);
  border-top: 3px solid var(--color-primary);
  border-radius: var(--radius-lg);
  background: var(--color-surface-elevated);
  box-shadow: var(--shadow-sm);
}

.student-summary__card--success { border-top-color: var(--color-success); }
.student-summary__card--info { border-top-color: var(--color-info); }
.student-summary__card--warning { border-top-color: var(--color-warning); }
.student-summary__card--danger { border-top-color: var(--color-danger); }

.student-summary__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
}

.student-summary__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  flex: 0 0 38px;
  border-radius: var(--radius-md);
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-weight: var(--font-weight-bold);
}

.student-summary__value {
  overflow-wrap: anywhere;
  font-size: var(--font-size-h3);
  line-height: var(--line-height-tight);
}

.student-summary__detail {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

@media (max-width: 1050px) {
  .student-summary { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 560px) {
  .student-summary { grid-template-columns: 1fr; }
}
</style>
