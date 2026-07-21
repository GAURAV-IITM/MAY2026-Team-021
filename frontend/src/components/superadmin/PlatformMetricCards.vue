<template>
  <section class="platform-metrics" :aria-label="ariaLabel">
    <article
      v-for="item in items"
      :key="item.label"
      class="platform-metric"
      :class="`platform-metric--${item.tone || 'primary'}`"
    >
      <div class="platform-metric__header">
        <span class="text-label text-muted">{{ item.label }}</span>
        <span class="platform-metric__icon" aria-hidden="true">
          <component :is="item.icon || CircleGauge" :size="19" />
        </span>
      </div>
      <strong class="platform-metric__value">{{ item.value }}</strong>
      <span class="platform-metric__detail">{{ item.detail }}</span>
    </article>
  </section>
</template>

<script setup>
import { CircleGauge } from '@lucide/vue'

defineProps({
  items: {
    type: Array,
    default: () => [],
  },
  ariaLabel: {
    type: String,
    default: 'Platform metrics',
  },
})
</script>

<style scoped>
.platform-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-4);
}

.platform-metric {
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

.platform-metric--success {
  border-top-color: var(--color-success);
}

.platform-metric--info {
  border-top-color: var(--color-info);
}

.platform-metric--warning {
  border-top-color: var(--color-warning);
}

.platform-metric--danger {
  border-top-color: var(--color-danger);
}

.platform-metric__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
}

.platform-metric__icon {
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

.platform-metric__value {
  font-size: var(--font-size-h2);
  line-height: var(--line-height-tight);
}

.platform-metric__detail {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

@media (max-width: 1100px) {
  .platform-metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 560px) {
  .platform-metrics {
    grid-template-columns: 1fr;
  }
}
</style>
