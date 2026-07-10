<template>
  <article
    class="seat-row"
    :class="{ 'seat-row--selected': selected }"
  >
    <header class="seat-row__header">
      <label class="checkbox">
        <input
          type="checkbox"
          :checked="selected"
          :aria-label="`Select ${seat.seatNumber}`"
          @change="$emit('toggle-select', seat.id)"
        />
        <span>{{ seat.seatNumber }}</span>
      </label>
      <span class="badge" :class="statusBadgeClass">
        {{ formatLabel(seat.physicalStatus) }}
      </span>
    </header>

    <dl class="seat-row__details">
      <div>
        <dt>Floor</dt>
        <dd>Floor {{ seat.floor }}</dd>
      </div>
      <div>
        <dt>Current Occupancy</dt>
        <dd>{{ occupancyLabel }}</dd>
      </div>
      <div>
        <dt>Notes</dt>
        <dd>{{ seat.notes || 'No notes' }}</dd>
      </div>
    </dl>

    <footer class="seat-row__actions">
      <button class="btn btn--outline btn--sm" type="button" @click="$emit('edit', seat)">
        Edit
      </button>
      <button class="btn btn--danger btn--sm" type="button" @click="$emit('delete', seat)">
        Delete
      </button>
      <SeatActionMenu
        :seat="seat"
        placement="top"
        @change-status="(rowSeat, status) => $emit('change-status', rowSeat, status)"
        @view-map="$emit('view-map', $event)"
      />
    </footer>
  </article>
</template>

<script setup>
import { computed } from 'vue'

import SeatActionMenu from './SeatActionMenu.vue'

const props = defineProps({
  seat: {
    type: Object,
    required: true,
  },
  selected: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['toggle-select', 'edit', 'delete', 'change-status', 'view-map'])

const occupancyLabel = computed(() => {
  return props.seat.isOccupied || Number(props.seat.occupiedShiftCount || 0) > 0
    ? 'Occupied'
    : 'Available'
})

const statusBadgeClass = computed(() => getStatusBadgeClass(props.seat.physicalStatus))

function getStatusBadgeClass(status) {
  if (status === 'available') return 'badge--success'
  if (status === 'maintenance') return 'badge--warning'
  if (status === 'blocked') return 'seat-row__badge--blocked'

  return 'badge--active'
}

function formatLabel(value) {
  if (!value) return 'Unassigned'

  return String(value)
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())
}
</script>

<style scoped>
.seat-row {
  display: grid;
  gap: var(--space-4);
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-elevated);
  box-shadow: var(--shadow-sm);
}

.seat-row--selected {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-light), var(--shadow-sm);
}

.seat-row__header,
.seat-row__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
}

.seat-row__details {
  display: grid;
  gap: var(--space-3);
  margin: 0;
}

.seat-row__details div {
  display: grid;
  gap: var(--space-1);
}

.seat-row__details dt {
  color: var(--color-text-muted);
  font-size: var(--font-size-caption);
  font-weight: var(--font-weight-semibold);
}

.seat-row__details dd {
  margin: 0;
  color: var(--color-text-primary);
}

.seat-row__badge--blocked {
  background: var(--color-danger-light);
  color: var(--color-danger);
}
</style>
