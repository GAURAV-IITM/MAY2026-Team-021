<template>
  <section class="seat-management-page" aria-labelledby="seat-management-title">
    <header class="seat-management-page__header">
      <div>
        <p class="text-label text-muted seat-management-page__eyebrow">
          Seat Management
        </p>
        <h1 id="seat-management-title" class="text-h2 seat-management-page__title">
          Seat Management
        </h1>
        <p class="text-body seat-management-page__description">
          Monitor availability, allocation status, and shift coverage across library seats.
        </p>
      </div>

      <button
        class="btn btn--secondary seat-management-page__refresh-button"
        type="button"
        :disabled="isLoading"
        @click="loadSeatDashboard"
      >
        {{ isLoading ? 'Refreshing' : 'Refresh Seats' }}
      </button>
    </header>

    <div v-if="errorMessage" class="alert alert--danger" role="alert">
      <div>
        <strong>Unable to load seat dashboard.</strong>
        <p class="m-0">{{ errorMessage }}</p>
      </div>

      <button
        class="btn btn--secondary btn--sm"
        type="button"
        @click="loadSeatDashboard"
      >
        Retry
      </button>
    </div>

    <div v-if="isInitialLoading" class="seat-management-page__loading">
      <LoadingSpinner label="Loading seat management dashboard" />
    </div>

    <template v-else-if="!errorMessage">
      <section class="seat-management-page__summary" aria-label="Seat summary">
        <StatCard
          title="Total Seats"
          :value="String(totalSeats)"
          icon="T"
          trend="All configured study seats"
        >
          <template #footer>
            {{ floorCount }} active floors
          </template>
        </StatCard>

        <StatCard
          title="Occupied Seats"
          :value="String(occupiedSeats.length)"
          icon="O"
          trend="Currently assigned"
        >
          <template #footer>
            {{ occupancyPercentage }}% occupancy
          </template>
        </StatCard>

        <StatCard
          title="Available Seats"
          :value="String(availableSeats.length)"
          icon="A"
          trend="Ready for allocation"
        >
          <template #footer>
            {{ reservedSeats.length }} reserved · {{ maintenanceSeats.length }} maintenance
          </template>
        </StatCard>

        <StatCard
          title="Occupancy Percentage"
          :value="`${occupancyPercentage}%`"
          icon="%"
          trend="Mock availability snapshot"
        >
          <template #footer>
            Updated from seat service
          </template>
        </StatCard>
      </section>

      <div class="seat-management-page__grid">
        <section class="card seat-management-page__overview" aria-labelledby="seat-overview-title">
          <header class="card__header seat-management-page__card-header">
            <div>
              <h2 id="seat-overview-title" class="text-h4 m-0">
                Seat Occupancy Overview
              </h2>
              <p class="text-small text-muted m-0">
                Current allocation state from the mock seat service.
              </p>
            </div>
          </header>

          <div class="card__body seat-management-page__overview-body">
            <div class="seat-management-page__meter" aria-label="Occupancy percentage">
              <div class="seat-management-page__meter-track">
                <span
                  class="seat-management-page__meter-fill"
                  :class="`seat-management-page__meter-fill--${occupancyBucket}`"
                ></span>
              </div>

              <div class="seat-management-page__meter-labels">
                <span>0%</span>
                <strong>{{ occupancyPercentage }}% occupied</strong>
                <span>100%</span>
              </div>
            </div>

            <DataTable
              :columns="seatColumns"
              :rows="seats"
              aria-label="Seat occupancy overview"
            >
              <template #cell-seatNumber="{ row }">
                <div class="seat-management-page__seat-cell">
                  <strong>{{ row.seatNumber }}</strong>
                  <span class="text-caption text-muted">Floor {{ row.floor }}</span>
                </div>
              </template>

              <template #cell-status="{ value }">
                <span class="badge" :class="getStatusBadgeClass(value)">
                  {{ formatLabel(value) }}
                </span>
              </template>

              <template #cell-assignedStudent="{ value }">
                {{ value?.name || 'Unassigned' }}
              </template>

              <template #cell-activeShifts="{ value }">
                <span class="seat-management-page__shift-list">
                  {{ formatShiftList(value) }}
                </span>
              </template>

              <template #empty>
                Seat records will appear after the mock service responds.
              </template>
            </DataTable>
          </div>
        </section>

        <aside class="card seat-management-page__quick-actions" aria-labelledby="quick-actions-title">
          <header class="card__header seat-management-page__card-header">
            <div>
              <h2 id="quick-actions-title" class="text-h4 m-0">Quick Actions</h2>
              <p class="text-small text-muted m-0">
                Admin workflows reserved for the next milestone.
              </p>
            </div>
          </header>

          <div class="card__body seat-management-page__action-list">
            <button class="btn btn--primary" type="button">Allocate Seat</button>
            <button class="btn btn--secondary" type="button">Transfer Seat</button>
            <button class="btn btn--outline" type="button">Manage Shifts</button>
            <button class="btn btn--ghost" type="button" @click="focusSeatMap">
              View Seat Map
            </button>
          </div>
        </aside>
      </div>

      <section class="seat-management-page__map-section" aria-labelledby="seat-map-title">
        <header class="seat-management-page__section-header">
          <div>
            <h2
              id="seat-map-title"
              ref="seatMapTitle"
              class="text-h4 m-0"
              tabindex="-1"
            >
              Seat Availability View
            </h2>
            <p class="text-small text-muted m-0">
              Click a seat to view details and inspect its current allocation state.
            </p>
          </div>

          <div class="seat-management-page__legend" aria-label="Seat status legend">
            <span
              v-for="status in seatStatuses"
              :key="status"
              class="seat-management-page__legend-item"
            >
              <span
                class="seat-management-page__legend-dot"
                :class="`seat-management-page__legend-dot--${status}`"
                aria-hidden="true"
              ></span>
              {{ formatLabel(status) }}
            </span>
          </div>
        </header>

        <div class="seat-management-page__map-layout">
          <div class="seat-management-page__seat-grid" role="list" aria-label="Library seat map">
            <button
              v-for="seat in seats"
              :key="seat.id"
              class="seat-management-page__seat-map-card"
              :class="[
                getSeatStatusClass(seat.status),
                {
                  'seat-management-page__seat-map-card--selected':
                    selectedSeat?.id === seat.id,
                },
              ]"
              type="button"
              role="listitem"
              :aria-pressed="String(selectedSeat?.id === seat.id)"
              @click="handleSeatClick(seat)"
            >
              <span class="seat-management-page__seat-map-topline">
                <strong>{{ seat.seatNumber }}</strong>
                <span class="badge" :class="getStatusBadgeClass(seat.status)">
                  {{ formatLabel(seat.status) }}
                </span>
              </span>

              <span class="seat-management-page__seat-map-meta">
                Student: {{ seat.assignedStudent?.name || 'Unassigned' }}
              </span>

              <span class="seat-management-page__seat-map-meta">
                Shift: {{ getCurrentShift(seat) }}
              </span>

              <span class="seat-management-page__seat-map-action">
                View Details
              </span>
            </button>
          </div>

          <aside class="card seat-management-page__seat-panel" aria-label="Selected seat information">
            <template v-if="selectedSeat">
              <header class="card__header seat-management-page__card-header">
                <div>
                  <p class="text-label text-muted m-0">Selected Seat</p>
                  <h3 class="text-h4 m-0">{{ selectedSeat.seatNumber }}</h3>
                </div>
                <span class="badge" :class="getStatusBadgeClass(selectedSeat.status)">
                  {{ formatLabel(selectedSeat.status) }}
                </span>
              </header>

              <div class="card__body seat-management-page__seat-panel-body">
                <div class="seat-management-page__detail-row">
                  <span class="text-small text-muted">Assigned Student</span>
                  <strong>{{ selectedSeat.assignedStudent?.name || 'Unassigned' }}</strong>
                </div>

                <div class="seat-management-page__detail-row">
                  <span class="text-small text-muted">Current Shift</span>
                  <strong>{{ getCurrentShift(selectedSeat) }}</strong>
                </div>

                <div class="seat-management-page__detail-row">
                  <span class="text-small text-muted">Floor</span>
                  <strong>Floor {{ selectedSeat.floor }}</strong>
                </div>

                <div class="seat-management-page__detail-row">
                  <span class="text-small text-muted">Active Shifts</span>
                  <strong>{{ formatShiftList(selectedSeat.activeShifts) }}</strong>
                </div>

                <div class="seat-management-page__detail-row">
                  <span class="text-small text-muted">Notes</span>
                  <strong>{{ selectedSeat.notes || 'No notes available' }}</strong>
                </div>
              </div>
            </template>

            <div v-else class="card__body seat-management-page__seat-panel-empty">
              <p class="text-label text-muted m-0">Seat Details</p>
              <h3 class="text-h4 m-0">No seat selected</h3>
              <p class="text-small text-muted m-0">
                Choose any seat from the map to view status, student, shift, floor, and notes.
              </p>
            </div>
          </aside>
        </div>
      </section>

      <div class="seat-management-page__secondary-grid">
        <section class="card" aria-labelledby="recent-allocations-title">
          <header class="card__header seat-management-page__card-header">
            <div>
              <h2 id="recent-allocations-title" class="text-h4 m-0">
                Recent Allocations
              </h2>
              <p class="text-small text-muted m-0">
                Placeholder allocation feed based on current occupied seats.
              </p>
            </div>
          </header>

          <div class="card__body">
            <DataTable
              :columns="allocationColumns"
              :rows="recentAllocationRows"
              aria-label="Recent seat allocations"
            >
              <template #cell-student="{ row }">
                <div class="seat-management-page__seat-cell">
                  <strong>{{ row.student }}</strong>
                  <span class="text-caption text-muted">{{ row.email }}</span>
                </div>
              </template>

              <template #cell-shifts="{ value }">
                {{ formatShiftList(value) }}
              </template>

              <template #empty>
                Recent allocation history will appear here.
              </template>
            </DataTable>
          </div>
        </section>

        <section class="card" aria-labelledby="seat-statistics-title">
          <header class="card__header seat-management-page__card-header">
            <div>
              <h2 id="seat-statistics-title" class="text-h4 m-0">
                Seat Statistics
              </h2>
              <p class="text-small text-muted m-0">
                Placeholder operating metrics for seat planning.
              </p>
            </div>
          </header>

          <div class="card__body seat-management-page__stats-list">
            <div
              v-for="statistic in seatStatistics"
              :key="statistic.label"
              class="seat-management-page__stat-row"
            >
              <span class="text-small text-muted">{{ statistic.label }}</span>
              <strong>{{ statistic.value }}</strong>
            </div>
          </div>
        </section>
      </div>
    </template>
  </section>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { computed, onMounted, ref } from 'vue'

import DataTable from '../../components/common/DataTable.vue'
import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import StatCard from '../../components/dashboard/StatCard.vue'
import { useSeatStore } from '../../stores/seatStore'

const seatColumns = Object.freeze([
  { key: 'seatNumber', label: 'Seat' },
  { key: 'status', label: 'Status' },
  { key: 'assignedStudent', label: 'Assigned Student' },
  { key: 'activeShifts', label: 'Active Shifts' },
  { key: 'notes', label: 'Notes' },
])

const allocationColumns = Object.freeze([
  { key: 'seatNumber', label: 'Seat' },
  { key: 'student', label: 'Student' },
  { key: 'shifts', label: 'Shifts' },
  { key: 'floor', label: 'Floor' },
])

const seatStatuses = Object.freeze([
  'available',
  'occupied',
  'reserved',
  'maintenance',
])

const seatStore = useSeatStore()
const seatMapTitle = ref(null)

const {
  seats,
  occupiedSeats,
  availableSeats,
  totalSeats,
  occupancyPercentage,
  seatsByShift,
  selectedSeat,
  isLoading,
  errorMessage,
} = storeToRefs(seatStore)

const isInitialLoading = computed(() => {
  return isLoading.value && seats.value.length === 0
})

const maintenanceSeats = computed(() => {
  return seats.value.filter((seat) => seat.status === 'maintenance')
})

const reservedSeats = computed(() => {
  return seats.value.filter((seat) => seat.status === 'reserved')
})

const floorCount = computed(() => {
  return new Set(seats.value.map((seat) => seat.floor)).size
})

const recentAllocationRows = computed(() => {
  return occupiedSeats.value.slice(0, 5).map((seat) => ({
    id: seat.id,
    seatNumber: seat.seatNumber,
    student: seat.assignedStudent?.name || 'Assigned Student',
    email: seat.assignedStudent?.email || 'Email pending',
    shifts: seat.activeShifts || [],
    floor: `Floor ${seat.floor}`,
  }))
})

const seatStatistics = computed(() => {
  return [
    {
      label: 'Morning shift coverage',
      value: `${getShiftSeatCount('morning')} seats`,
    },
    {
      label: 'Afternoon shift coverage',
      value: `${getShiftSeatCount('afternoon')} seats`,
    },
    {
      label: 'Evening shift coverage',
      value: `${getShiftSeatCount('evening')} seats`,
    },
    {
      label: 'Maintenance queue',
      value: `${maintenanceSeats.value.length} seats`,
    },
    {
      label: 'Reserved seats',
      value: `${reservedSeats.value.length} seats`,
    },
  ]
})

const occupancyBucket = computed(() => {
  return Math.min(100, Math.max(0, Math.round(occupancyPercentage.value / 10) * 10))
})

function getShiftSeatCount(shift) {
  return seatsByShift.value[shift]?.length || 0
}

function formatLabel(value) {
  if (!value) return 'Unassigned'

  return String(value)
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())
}

function formatShiftList(shifts = []) {
  if (!Array.isArray(shifts) || shifts.length === 0) return 'No active shifts'

  return shifts.map((shift) => formatLabel(shift)).join(', ')
}

function getCurrentShift(seat) {
  const shift = seat?.activeShifts?.[0]

  return shift ? formatLabel(shift) : 'No active shift'
}

function getStatusBadgeClass(status) {
  if (status === 'available') return 'badge--success'
  if (status === 'occupied') return 'seat-management-page__badge--occupied'
  if (status === 'reserved') return 'seat-management-page__badge--reserved'
  if (status === 'maintenance') return 'badge--warning'

  return 'badge--active'
}

function getSeatStatusClass(status) {
  return `seat-management-page__seat-map-card--${status || 'unknown'}`
}

async function handleSeatClick(seat) {
  try {
    await seatStore.selectSeat(seat.id)
  } catch {
    // Store-owned error state is rendered above the dashboard.
  }
}

function focusSeatMap() {
  seatMapTitle.value?.focus()
  seatMapTitle.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function loadSeatDashboard() {
  try {
    await seatStore.fetchSeats()
  } catch {
    // Store-owned error state is rendered above the dashboard.
  }
}

onMounted(loadSeatDashboard)
</script>

<style scoped>
.seat-management-page {
  display: grid;
  gap: var(--space-6);
}

.seat-management-page__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-5);
}

.seat-management-page__eyebrow,
.seat-management-page__title,
.seat-management-page__description {
  margin: 0;
}

.seat-management-page__title {
  margin-top: var(--space-1);
}

.seat-management-page__description {
  margin-top: var(--space-2);
  max-width: 640px;
  color: var(--color-text-muted);
}

.seat-management-page__refresh-button {
  flex-shrink: 0;
}

.seat-management-page__summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-4);
}

.seat-management-page__loading {
  display: grid;
  min-height: 280px;
  place-items: center;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface-elevated);
}

.seat-management-page__grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(240px, 320px);
  gap: var(--space-5);
  align-items: start;
}

.seat-management-page__map-section {
  display: grid;
  gap: var(--space-4);
}

.seat-management-page__section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-5);
}

.seat-management-page__section-header h2:focus {
  outline: 3px solid var(--color-focus-ring);
  outline-offset: 4px;
}

.seat-management-page__legend {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: var(--space-2);
}

.seat-management-page__legend-item {
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

.seat-management-page__legend-dot {
  width: 10px;
  height: 10px;
  border-radius: var(--radius-pill);
}

.seat-management-page__legend-dot--available {
  background: var(--color-success);
}

.seat-management-page__legend-dot--occupied {
  background: var(--color-primary);
}

.seat-management-page__legend-dot--reserved {
  background: var(--color-info);
}

.seat-management-page__legend-dot--maintenance {
  background: var(--color-warning);
}

.seat-management-page__map-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(260px, 360px);
  gap: var(--space-5);
  align-items: start;
}

.seat-management-page__seat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: var(--space-3);
}

.seat-management-page__seat-map-card {
  display: grid;
  gap: var(--space-2);
  min-height: 148px;
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  border-left-width: 4px;
  border-radius: var(--radius-md);
  background: var(--color-surface-elevated);
  color: var(--color-text-primary);
  text-align: left;
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  transition:
    border-color var(--transition-fast),
    box-shadow var(--transition-fast),
    transform var(--transition-fast);
}

.seat-management-page__seat-map-card:hover {
  transform: translateY(-2px);
  border-color: var(--color-primary);
  box-shadow: var(--shadow-md);
}

.seat-management-page__seat-map-card:focus-visible {
  outline: 3px solid var(--color-focus-ring);
  outline-offset: 2px;
}

.seat-management-page__seat-map-card--selected {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-light), var(--shadow-md);
}

.seat-management-page__seat-map-card--available {
  border-left-color: var(--color-success);
}

.seat-management-page__seat-map-card--occupied {
  border-left-color: var(--color-primary);
}

.seat-management-page__seat-map-card--reserved {
  border-left-color: var(--color-info);
}

.seat-management-page__seat-map-card--maintenance {
  border-left-color: var(--color-warning);
}

.seat-management-page__seat-map-topline {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-2);
}

.seat-management-page__seat-map-meta {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  line-height: var(--line-height-normal);
}

.seat-management-page__seat-map-action {
  align-self: end;
  color: var(--color-primary);
  font-size: var(--font-size-caption);
  font-weight: var(--font-weight-semibold);
}

.seat-management-page__seat-panel {
  position: sticky;
  top: var(--space-5);
}

.seat-management-page__seat-panel-body,
.seat-management-page__seat-panel-empty {
  display: grid;
  gap: var(--space-4);
}

.seat-management-page__detail-row {
  display: grid;
  gap: var(--space-1);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--color-divider);
}

.seat-management-page__detail-row:last-child {
  padding-bottom: 0;
  border-bottom: 0;
}

.seat-management-page__badge--occupied {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.seat-management-page__badge--reserved {
  background: var(--color-info-light);
  color: var(--color-info);
}

.seat-management-page__secondary-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(260px, 0.6fr);
  gap: var(--space-5);
  align-items: start;
}

.seat-management-page__card-header {
  align-items: flex-start;
}

.seat-management-page__overview-body {
  display: grid;
  gap: var(--space-5);
}

.seat-management-page__meter {
  display: grid;
  gap: var(--space-2);
}

.seat-management-page__meter-track {
  overflow: hidden;
  height: 12px;
  border-radius: var(--radius-full);
  background: var(--color-surface-muted);
}

.seat-management-page__meter-fill {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--color-primary);
}

.seat-management-page__meter-fill--0 {
  width: 0;
}

.seat-management-page__meter-fill--10 {
  width: 10%;
}

.seat-management-page__meter-fill--20 {
  width: 20%;
}

.seat-management-page__meter-fill--30 {
  width: 30%;
}

.seat-management-page__meter-fill--40 {
  width: 40%;
}

.seat-management-page__meter-fill--50 {
  width: 50%;
}

.seat-management-page__meter-fill--60 {
  width: 60%;
}

.seat-management-page__meter-fill--70 {
  width: 70%;
}

.seat-management-page__meter-fill--80 {
  width: 80%;
}

.seat-management-page__meter-fill--90 {
  width: 90%;
}

.seat-management-page__meter-fill--100 {
  width: 100%;
}

.seat-management-page__meter-labels {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.seat-management-page__meter-labels strong {
  color: var(--color-text-primary);
}

.seat-management-page__quick-actions {
  position: sticky;
  top: var(--space-5);
}

.seat-management-page__action-list {
  display: grid;
  gap: var(--space-3);
}

.seat-management-page__action-list .btn {
  justify-content: center;
  width: 100%;
}

.seat-management-page__seat-cell {
  display: grid;
  gap: var(--space-1);
  min-width: 150px;
}

.seat-management-page__shift-list {
  white-space: nowrap;
}

.seat-management-page__stats-list {
  display: grid;
  gap: var(--space-3);
}

.seat-management-page__stat-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--color-border);
}

.seat-management-page__stat-row:last-child {
  padding-bottom: 0;
  border-bottom: 0;
}

@media (max-width: 1200px) {
  .seat-management-page__summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .seat-management-page__grid,
  .seat-management-page__map-layout,
  .seat-management-page__secondary-grid {
    grid-template-columns: 1fr;
  }

  .seat-management-page__quick-actions,
  .seat-management-page__seat-panel {
    position: static;
  }
}

@media (max-width: 768px) {
  .seat-management-page__header,
  .seat-management-page__section-header {
    align-items: stretch;
    flex-direction: column;
  }

  .seat-management-page__refresh-button {
    align-self: flex-start;
  }

  .seat-management-page__summary {
    grid-template-columns: 1fr;
  }

  .seat-management-page__meter-labels {
    align-items: flex-start;
    flex-direction: column;
  }

  .seat-management-page__legend {
    justify-content: flex-start;
  }
}

@media (max-width: 480px) {
  .seat-management-page__seat-grid {
    grid-template-columns: 1fr;
  }

  .seat-management-page__stat-row {
    align-items: flex-start;
    flex-direction: column;
    gap: var(--space-1);
  }

  .seat-management-page__shift-list {
    white-space: normal;
  }
}
</style>

<!--
src/pages/admin: Seat management dashboard for library owners and admins.

Responsibilities:
- Fetch seat records through the centralized seat store.
- Render mock-service seat availability metrics.
- Present placeholder allocation, transfer, shift, and seat map actions.

Milestone 3:
- Replace mock seat service calls with FastAPI endpoints through seatService.
-->
