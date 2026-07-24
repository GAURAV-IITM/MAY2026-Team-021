<template>
  <section class="seat-summary-cards" aria-label="Seat summary">
    <article v-for="card in cards" :key="card.key" class="seat-summary-cards__card">
      <header><span class="text-label text-muted">{{ card.label }}</span><component :is="card.icon" :size="19" aria-hidden="true" /></header>
      <strong>{{ card.value }}</strong>
    </article>
  </section>
</template>

<script setup>
import { Armchair, CircleCheckBig, UserRoundCheck, Wrench } from '@lucide/vue'
import { computed } from 'vue'

const props = defineProps({
  summary: {
    type: Object,
    default: () => ({
      total: 0,
      available: 0,
      occupied: 0,
      maintenance: 0,
    }),
  },
})

const cards = computed(() => [
  { key: 'total', label: 'Total Seats', value: props.summary.total || 0, icon: Armchair },
  { key: 'available', label: 'Available', value: props.summary.available || 0, icon: CircleCheckBig },
  { key: 'occupied', label: 'Occupied', value: props.summary.occupied || 0, icon: UserRoundCheck },
  { key: 'maintenance', label: 'Maintenance', value: props.summary.maintenance || 0, icon: Wrench },
])
</script>

<style scoped>
.seat-summary-cards {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-4);
}

.seat-summary-cards__card {
  display: grid;
  gap: var(--space-2);
  min-height: 112px;
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-elevated);
  box-shadow: var(--shadow-sm);
}

.seat-summary-cards__card header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  color: var(--color-primary);
}

.seat-summary-cards__card strong {
  color: var(--color-text-primary);
  font-size: var(--font-size-h2);
  font-weight: var(--font-weight-bold);
  line-height: var(--line-height-tight);
}

@media (max-width: 900px) {
  .seat-summary-cards {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 520px) {
  .seat-summary-cards {
    grid-template-columns: 1fr;
  }
}
</style>
