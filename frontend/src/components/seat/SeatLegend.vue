<template>
  <div class="seat-legend" aria-label="Seat status legend">
    <span
      v-for="item in legendItems"
      :key="item.status"
      class="seat-legend__item"
    >
      <span
        class="seat-legend__indicator"
        :class="`seat-legend__indicator--${item.status}`"
        aria-hidden="true"
      ></span>
      {{ item.label }}
    </span>
  </div>
</template>

<script setup>
const legendItems = Object.freeze([
  { status: 'available', label: 'Available' },
  { status: 'occupied', label: 'Occupied' },
  { status: 'reserved', label: 'Reserved' },
  { status: 'maintenance', label: 'Maintenance' },
])
</script>

<style scoped>
.seat-legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.seat-legend__item {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  min-height: 28px;
  padding: 0 var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
  background: var(--color-surface-elevated);
  color: var(--color-text-secondary);
  font-size: var(--font-size-caption);
  font-weight: var(--font-weight-semibold);
}

.seat-legend__indicator {
  width: 10px;
  height: 10px;
  border-radius: var(--radius-pill);
}

.seat-legend__indicator--available {
  background: var(--color-success);
}

.seat-legend__indicator--occupied {
  background: var(--color-primary);
}

.seat-legend__indicator--reserved {
  background: var(--color-info);
}

.seat-legend__indicator--maintenance {
  background: var(--color-warning);
}
</style>

<!--
src/components/seat: Reusable seat status legend for seat map and allocation views.
TODO:
- Keep status colors aligned with backend-provided seat states in Milestone 3.
-->
