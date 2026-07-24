<template>
  <div class="shift-availability-summary">
    <p v-if="shifts.length === 0" class="shift-availability-summary__empty">
      No enabled shifts are available.
    </p>

    <article
      v-for="shift in shifts"
      v-else
      :key="shift.id"
      class="shift-availability-summary__row"
    >
      <header class="shift-availability-summary__header">
        <div>
          <strong>{{ formatLabel(shift.name) }}</strong>
          <small>{{ shift.timing }}</small>
        </div>
        <span>{{ shift.totalSeats }} seats</span>
      </header>

      <div
        class="shift-availability-summary__bar"
        role="img"
        :aria-label="getShiftSummaryLabel(shift)"
      >
        <span
          v-for="status in shift.statuses"
          :key="status.key"
          :class="`shift-availability-summary__segment--${status.key}`"
          :style="{ width: getStatusWidth(status.count, shift.totalSeats) }"
        ></span>
      </div>

      <ul class="shift-availability-summary__counts">
        <li v-for="status in shift.statuses" :key="status.key">
          <span
            class="shift-availability-summary__dot"
            :class="`shift-availability-summary__dot--${status.key}`"
            aria-hidden="true"
          ></span>
          <span>{{ status.label }}</span>
          <strong>{{ status.count }}</strong>
        </li>
      </ul>
    </article>
  </div>
</template>

<script setup>
defineProps({
  shifts: {
    type: Array,
    default: () => [],
  },
})

function formatLabel(value) {
  return String(value || '')
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())
}

function getStatusWidth(count, totalSeats) {
  if (!totalSeats) return '0%'

  return `${(count / totalSeats) * 100}%`
}

function getShiftSummaryLabel(shift) {
  const statusSummary = shift.statuses
    .map((status) => `${status.count} ${status.label}`)
    .join(', ')

  return `${formatLabel(shift.name)}: ${statusSummary}`
}
</script>

<style scoped>
.shift-availability-summary {
  display: grid;
}

.shift-availability-summary__row {
  display: grid;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid var(--color-divider);
}

.shift-availability-summary__row:last-child {
  border-bottom: 0;
}

.shift-availability-summary__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
}

.shift-availability-summary__header > div {
  display: grid;
}

.shift-availability-summary__header small,
.shift-availability-summary__header > span {
  color: var(--color-text-muted);
  font-size: var(--font-size-caption);
}

.shift-availability-summary__header > span {
  white-space: nowrap;
}

.shift-availability-summary__bar {
  display: flex;
  width: 100%;
  height: 9px;
  overflow: hidden;
  border-radius: var(--radius-pill);
  background: var(--color-surface-secondary);
}

.shift-availability-summary__bar > span {
  display: block;
  height: 100%;
}

.shift-availability-summary__segment--available,
.shift-availability-summary__dot--available {
  background: var(--color-success);
}

.shift-availability-summary__segment--occupied,
.shift-availability-summary__dot--occupied {
  background: var(--color-primary);
}

.shift-availability-summary__segment--blocked,
.shift-availability-summary__dot--blocked {
  background: var(--color-danger);
}

.shift-availability-summary__segment--reserved,
.shift-availability-summary__dot--reserved {
  background: var(--color-info);
}

.shift-availability-summary__segment--maintenance,
.shift-availability-summary__dot--maintenance {
  background: var(--color-warning);
}

.shift-availability-summary__counts {
  display: grid;
  grid-template-columns: repeat(5, minmax(86px, 1fr));
  gap: var(--space-2);
  padding: 0;
  margin: 0;
  list-style: none;
}

.shift-availability-summary__counts li {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--space-2);
  min-width: 0;
  color: var(--color-text-secondary);
  font-size: var(--font-size-caption);
}

.shift-availability-summary__counts li > span:nth-child(2) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.shift-availability-summary__dot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-pill);
}

.shift-availability-summary__empty {
  padding: var(--space-8) var(--space-5);
  margin: 0;
  color: var(--color-text-muted);
  text-align: center;
}

@media (max-width: 680px) {
  .shift-availability-summary__counts {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
