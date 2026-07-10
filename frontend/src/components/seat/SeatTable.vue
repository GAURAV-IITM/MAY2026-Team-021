<template>
  <section class="seat-table" aria-labelledby="seat-table-title">
    <div class="seat-table__desktop">
      <DataTable
        :columns="columns"
        :rows="seats"
        row-key="id"
        aria-label="Physical seats"
      >
        <template #cell-select="{ row }">
          <input
            type="checkbox"
            :checked="selectedSeatIds.includes(row.id)"
            :aria-label="`Select ${row.seatNumber}`"
            @change="$emit('toggle-seat', row.id)"
          />
        </template>

        <template #cell-seatNumber="{ row }">
          <strong>{{ row.seatNumber }}</strong>
        </template>

        <template #cell-floor="{ value }">
          Floor {{ value }}
        </template>

        <template #cell-physicalStatus="{ value }">
          <span class="badge" :class="getStatusBadgeClass(value)">
            {{ formatLabel(value) }}
          </span>
        </template>

        <template #cell-occupancy="{ row }">
          {{ getOccupancyLabel(row) }}
        </template>

        <template #cell-notes="{ value }">
          <span class="seat-table__notes">{{ value || 'No notes' }}</span>
        </template>

        <template #actions="{ row }">
          <div class="seat-table__actions">
            <button class="btn btn--outline btn--sm" type="button" @click="$emit('edit', row)">
              Edit
            </button>
            <button class="btn btn--danger btn--sm" type="button" @click="$emit('delete', row)">
              Delete
            </button>
            <SeatActionMenu
              :seat="row"
              @change-status="(seat, status) => $emit('change-status', seat, status)"
              @view-map="$emit('view-map', $event)"
            />
          </div>
        </template>

        <template #empty>
          No seats match the current filters.
        </template>
      </DataTable>
    </div>

    <div class="seat-table__mobile" role="list" aria-label="Physical seats">
      <SeatRow
        v-for="seat in seats"
        :key="seat.id"
        :seat="seat"
        :selected="selectedSeatIds.includes(seat.id)"
        role="listitem"
        @toggle-select="$emit('toggle-seat', $event)"
        @edit="$emit('edit', $event)"
        @delete="$emit('delete', $event)"
        @change-status="(seat, status) => $emit('change-status', seat, status)"
        @view-map="$emit('view-map', $event)"
      />
    </div>
  </section>
</template>

<script setup>
import DataTable from '../common/DataTable.vue'
import SeatActionMenu from './SeatActionMenu.vue'
import SeatRow from './SeatRow.vue'

defineProps({
  seats: {
    type: Array,
    default: () => [],
  },
  selectedSeatIds: {
    type: Array,
    default: () => [],
  },
})

defineEmits(['toggle-seat', 'edit', 'delete', 'change-status', 'view-map'])

const columns = Object.freeze([
  { key: 'select', label: '' },
  { key: 'seatNumber', label: 'Seat Number' },
  { key: 'floor', label: 'Floor' },
  { key: 'physicalStatus', label: 'Current Status' },
  { key: 'occupancy', label: 'Current Occupancy' },
  { key: 'notes', label: 'Notes' },
])

function getOccupancyLabel(seat) {
  return seat.isOccupied || Number(seat.occupiedShiftCount || 0) > 0
    ? 'Occupied'
    : 'Available'
}

function getStatusBadgeClass(status) {
  if (status === 'available') return 'badge--success'
  if (status === 'maintenance') return 'badge--warning'
  if (status === 'blocked') return 'seat-table__badge--blocked'

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
.seat-table__desktop {
  display: block;
}

.seat-table__mobile {
  display: none;
}

.seat-table__notes {
  display: inline-block;
  max-width: 320px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.seat-table__actions {
  position: relative;
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.seat-table__badge--blocked {
  background: var(--color-danger-light);
  color: var(--color-danger);
}

@media (max-width: 720px) {
  .seat-table__desktop {
    display: none;
  }

  .seat-table__mobile {
    display: grid;
    gap: var(--space-3);
  }
}
</style>
