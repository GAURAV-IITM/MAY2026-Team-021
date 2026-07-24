<template>
  <section class="seat-allocation-card" :class="{ 'seat-allocation-card--compact': compact }">
    <div v-if="seat" class="seat-allocation-card__seat">
      <span class="seat-allocation-card__seat-number">{{ seat.seatNumber }}</span>
      <div>
        <p class="text-label text-muted m-0">Allocated Seat</p>
        <h2 class="seat-allocation-card__title">{{ seat.seatType }} Seat</h2>
        <p class="seat-allocation-card__location">Floor {{ seat.floor }}</p>
      </div>
      <span class="badge badge--success">Active</span>
    </div>

    <div v-if="seat" class="seat-allocation-card__shifts">
      <article v-for="allocation in allocations" :key="allocation.id">
        <div>
          <strong>{{ formatLabel(allocation.shiftName) }}</strong>
          <span>{{ allocation.startTime }} - {{ allocation.endTime }}</span>
        </div>
        <div class="seat-allocation-card__period">
          <span>Allocation Period</span>
          <strong>{{ formatDate(allocation.startDate) }} - {{ formatDate(allocation.endDate) }}</strong>
        </div>
      </article>
    </div>

    <div v-else class="seat-allocation-card__empty">
      <strong>No active seat allocation</strong>
      <span>Your seat details will appear after an administrator assigns a seat.</span>
    </div>
  </section>
</template>

<script setup>
defineProps({
  seat: { type: Object, default: null },
  allocations: { type: Array, default: () => [] },
  compact: { type: Boolean, default: false },
})

function formatLabel(value) {
  return String(value || '').replace(/[-_]/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase())
}

function formatDate(value) {
  if (!value) return '—'
  return new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short' }).format(new Date(`${value}T00:00:00`))
}
</script>

<style scoped>
.seat-allocation-card {
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface-elevated);
  box-shadow: var(--shadow-sm);
}

.seat-allocation-card__seat {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-5);
  border-bottom: 1px solid var(--color-divider);
}

.seat-allocation-card__seat-number {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 72px;
  height: 72px;
  border: 2px solid var(--color-primary);
  border-radius: var(--radius-md);
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-size: var(--font-size-h3);
  font-weight: var(--font-weight-bold);
}

.seat-allocation-card__title,
.seat-allocation-card__location { margin: 0; }
.seat-allocation-card__title { margin-top: var(--space-1); font-size: var(--font-size-h4); }
.seat-allocation-card__location { margin-top: var(--space-1); color: var(--color-text-muted); }
.seat-allocation-card__shifts { display: grid; }
.seat-allocation-card__shifts article {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid var(--color-divider);
}
.seat-allocation-card__shifts article:last-child { border-bottom: 0; }
.seat-allocation-card__shifts article > div { display: grid; }
.seat-allocation-card__shifts span { color: var(--color-text-muted); font-size: var(--font-size-caption); }
.seat-allocation-card__period { justify-items: end; text-align: right; }
.seat-allocation-card__period strong { font-size: var(--font-size-sm); }
.seat-allocation-card__empty { display: grid; gap: var(--space-2); padding: var(--space-8); color: var(--color-text-muted); text-align: center; }
.seat-allocation-card--compact .seat-allocation-card__seat-number { width: 58px; height: 58px; font-size: var(--font-size-h4); }

@media (max-width: 600px) {
  .seat-allocation-card__seat { grid-template-columns: auto minmax(0, 1fr); }
  .seat-allocation-card__seat > .badge { grid-column: 1 / -1; justify-self: start; }
  .seat-allocation-card__shifts article { grid-template-columns: 1fr; }
  .seat-allocation-card__period { justify-items: start; text-align: left; }
}
</style>
