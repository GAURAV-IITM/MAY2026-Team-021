<template>
  <section class="seat-map-page" aria-labelledby="seat-map-title">
    <header class="seat-map-page__header">
      <div>
        <p class="text-label text-muted seat-map-page__eyebrow">
          Seat Availability
        </p>
        <h1 id="seat-map-title" class="text-h2 seat-map-page__title">
          Seat Map
        </h1>
        <p class="text-body seat-map-page__description">
          Select a shift to inspect seat availability for that time window.
        </p>
      </div>

      <div class="seat-map-page__header-actions">
        <RouterLink
          class="btn btn--secondary"
          :to="{ name: 'adminSeatManagement' }"
        >
          Back to Overview
        </RouterLink>
        <button
          class="btn btn--secondary"
          type="button"
          :disabled="isLoading"
          @click="loadSeatMap"
        >
          {{ isLoading ? 'Refreshing' : 'Refresh' }}
        </button>
      </div>
    </header>

    <div v-if="errorMessage" class="alert alert--danger" role="alert">
      <div>
        <strong>Unable to load seat map.</strong>
        <p class="m-0">{{ errorMessage }}</p>
      </div>

      <button class="btn btn--secondary btn--sm" type="button" @click="loadSeatMap">
        Retry
      </button>
    </div>

    <div v-if="isInitialLoading" class="seat-map-page__loading">
      <LoadingSpinner label="Loading seat availability map" />
    </div>

    <template v-else-if="!errorMessage">
      <section class="card seat-map-page__toolbar" aria-label="Shift selection">
        <div class="seat-map-page__shift-tabs" role="tablist" aria-label="Shifts">
          <button
            v-for="shift in enabledShifts"
            :key="shift.id"
            class="seat-map-page__shift-tab"
            :class="{ 'seat-map-page__shift-tab--active': selectedShiftId === shift.id }"
            type="button"
            role="tab"
            :aria-selected="String(selectedShiftId === shift.id)"
            @click="selectShift(shift.id)"
          >
            <strong>{{ shift.name }}</strong>
            <span>{{ formatTimeRange(shift.startTime, shift.endTime) }}</span>
          </button>
        </div>

        <div class="seat-map-page__shift-summary" aria-live="polite">
          <span class="badge badge--success">
            {{ selectedShiftSummary.available }} Available
          </span>
          <span class="badge seat-map-page__badge--occupied">
            {{ selectedShiftSummary.occupied }} Allotted
          </span>
          <span class="badge seat-map-page__badge--blocked">
            {{ selectedShiftSummary.blocked }} Blocked
          </span>
          <span class="badge seat-map-page__badge--reserved">
            {{ selectedShiftSummary.reserved }} Reserved
          </span>
          <span class="badge badge--warning">
            {{ selectedShiftSummary.maintenance }} Maintenance
          </span>
        </div>
      </section>

      <section class="seat-map-page__section-header">
        <div>
          <h2 class="text-h4 m-0">Seat Availability View</h2>
          <p class="text-small text-muted m-0">
            Cards show availability for {{ selectedShiftName }} only.
          </p>
        </div>

        <div class="seat-map-page__legend" aria-label="Seat status legend">
          <span
            v-for="item in legendItems"
            :key="item.status"
            class="seat-map-page__legend-item"
          >
            <span
              class="seat-map-page__legend-indicator"
              :class="`seat-map-page__legend-indicator--${item.status}`"
              aria-hidden="true"
            ></span>
            {{ item.label }}
          </span>
        </div>
      </section>

      <div class="seat-map-page__layout">
        <div class="seat-map-page__groups" aria-label="Seat groups by floor">
          <section
            v-for="group in floorGroups"
            :key="group.id"
            class="seat-map-page__group"
            :aria-labelledby="`${group.id}-title`"
          >
            <header class="seat-map-page__group-header">
              <div>
                <h3 :id="`${group.id}-title`" class="text-h4 m-0">
                  {{ group.label }}
                </h3>
                <p class="text-small text-muted m-0">
                  {{ group.seats.length }} seats
                </p>
              </div>
            </header>

            <div class="seat-map-page__seat-grid" role="list">
              <button
                v-for="seat in group.seats"
                :key="seat.id"
                class="seat-map-page__seat-card"
                :class="[
                  `seat-map-page__seat-card--${getSeatCardStatus(seat).key}`,
                  { 'seat-map-page__seat-card--selected': selectedSeat?.id === seat.id },
                ]"
                type="button"
                role="listitem"
                :aria-pressed="String(selectedSeat?.id === seat.id)"
                @click="handleSeatClick(seat)"
              >
                <strong>{{ seat.seatNumber }}</strong>
                <span class="badge" :class="getStatusBadgeClass(getSeatCardStatus(seat).key)">
                  {{ getSeatCardStatus(seat).label }}
                </span>
                <small>{{ getSeatCardStatus(seat).detail }}</small>
              </button>
            </div>
          </section>
        </div>

        <aside class="card seat-map-page__details" aria-label="Selected seat details">
          <template v-if="selectedSeat">
            <header class="card__header seat-map-page__card-header">
              <div>
                <p class="text-label text-muted m-0">Selected Seat</p>
                <h3 class="text-h4 m-0">{{ selectedSeat.seatNumber }}</h3>
              </div>
              <span
                class="badge"
                :class="getStatusBadgeClass(selectedShiftAvailability.key)"
              >
                {{ selectedShiftAvailability.label }}
              </span>
            </header>

            <div class="card__body seat-map-page__details-body">
              <div class="seat-map-page__detail-row">
                <span class="text-small text-muted">Selected Shift</span>
                <strong>{{ selectedShiftName }}</strong>
                <small>{{ selectedShiftTimeRange }}</small>
              </div>

              <div class="seat-map-page__detail-row">
                <span class="text-small text-muted">Availability</span>
                <strong>{{ selectedShiftAvailability.label }}</strong>
                <small>{{ selectedShiftAvailability.detail }}</small>
              </div>

              <div class="seat-map-page__detail-row">
                <span class="text-small text-muted">Physical Status</span>
                <strong>{{ formatLabel(selectedSeat.physicalStatus) }}</strong>
              </div>

              <div class="seat-map-page__detail-row">
                <span class="text-small text-muted">Floor</span>
                <strong>Floor {{ selectedSeat.floor }}</strong>
              </div>

              <div class="seat-map-page__detail-row">
                <span class="text-small text-muted">Notes</span>
                <strong>{{ selectedSeat.notes || 'No notes available' }}</strong>
              </div>
            </div>
          </template>

          <div v-else class="card__body seat-map-page__details-empty">
            <p class="text-label text-muted m-0">Seat Details</p>
            <h3 class="text-h4 m-0">No seat selected</h3>
            <p class="text-small text-muted m-0">
              Choose a seat to inspect its status for {{ selectedShiftName }}.
            </p>
          </div>
        </aside>
      </div>
    </template>
  </section>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'

import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import { useSeatStore } from '../../stores/seatStore'
import {
  getSeatShiftAvailability,
  getSeatStatusForShift,
  summarizeSeatStatusesForShift,
} from '../../utils/seatAvailability'

const legendItems = Object.freeze([
  { status: 'available', label: 'Available' },
  { status: 'occupied', label: 'Allotted' },
  { status: 'blocked', label: 'Blocked' },
  { status: 'reserved', label: 'Reserved' },
  { status: 'maintenance', label: 'Maintenance' },
])

const seatStore = useSeatStore()
const selectedShiftId = ref('')

const {
  seats,
  seatAvailability,
  enabledShifts,
  selectedSeat,
  isLoading,
  errorMessage,
} = storeToRefs(seatStore)

const isInitialLoading = computed(() => {
  return isLoading.value && seats.value.length === 0
})

const selectedShift = computed(() => {
  return enabledShifts.value.find((shift) => shift.id === selectedShiftId.value)
})

const selectedShiftName = computed(() => {
  return selectedShift.value?.name || 'selected shift'
})

const selectedShiftTimeRange = computed(() => {
  return formatTimeRange(selectedShift.value?.startTime, selectedShift.value?.endTime)
})

const floorGroups = computed(() => {
  const groups = new Map()

  seats.value.forEach((seat) => {
    const floor = seat.floor || 'Unassigned'
    const id = `floor-${floor}`
    const group = groups.get(id) || {
      id,
      floor,
      label: floor === 'Unassigned' ? 'Unassigned' : `Floor ${floor}`,
      seats: [],
    }

    group.seats.push(seat)
    groups.set(id, group)
  })

  return [...groups.values()]
    .map((group) => ({
      ...group,
      seats: [...group.seats].sort((firstSeat, secondSeat) => {
        return firstSeat.seatNumber.localeCompare(secondSeat.seatNumber)
      }),
    }))
    .sort((firstGroup, secondGroup) => {
      return Number(firstGroup.floor) - Number(secondGroup.floor)
    })
})

const selectedShiftSummary = computed(() => {
  const summary =
    seatAvailability.value?.byShift?.[selectedShiftId.value] ||
    summarizeSeatStatusesForShift(seats.value, selectedShiftId.value)

  return {
    available: summary.availableSeats || 0,
    occupied: summary.occupiedSeats || 0,
    blocked: summary.blockedSeats || 0,
    reserved: summary.reservedSeats || 0,
    maintenance: summary.maintenanceSeats || 0,
  }
})

const selectedShiftAvailability = computed(() => {
  if (!selectedSeat.value) {
    return {
      key: 'available',
      label: 'Available',
      detail: 'Select a seat to view shift availability.',
    }
  }

  return getSeatCardStatus(selectedSeat.value)
})

watch(
  enabledShifts,
  (shifts) => {
    if (selectedShiftId.value && shifts.some((shift) => shift.id === selectedShiftId.value)) {
      return
    }

    selectedShiftId.value = shifts[0]?.id || ''
  },
  { immediate: true },
)

function selectShift(shiftId) {
  selectedShiftId.value = shiftId
}

function getShiftAvailability(seat) {
  return getSeatShiftAvailability(seat, selectedShiftId.value)
}

function getSeatCardStatus(seat) {
  const shiftAvailability = getShiftAvailability(seat)
  const status = getSeatStatusForShift(seat, selectedShiftId.value)

  if (!shiftAvailability) {
    return {
      key: 'maintenance',
      label: 'Unavailable',
      detail: 'Shift not supported',
    }
  }

  if (status === 'blocked' && shiftAvailability.isPartialBlock) {
    const blockingShift = shiftAvailability.blockingAllocation?.shiftName || 'another shift'
    const blockingTime = formatTimeRange(
      shiftAvailability.blockingAllocation?.startTime,
      shiftAvailability.blockingAllocation?.endTime,
    )

    return {
      key: 'blocked',
      label: 'Blocked',
      detail: `${blockingShift} ${blockingTime}`.trim(),
    }
  }

  if (status === 'occupied') {
    return {
      key: 'occupied',
      label: 'Allotted',
      detail: shiftAvailability.assignedStudent?.name || 'Assigned student',
    }
  }

  if (status === 'reserved') {
    return {
      key: 'reserved',
      label: 'Reserved',
      detail: shiftAvailability.assignedStudent?.name || 'Reserved booking',
    }
  }

  if (status === 'maintenance') {
    return {
      key: 'maintenance',
      label: 'Maintenance',
      detail: 'Seat unavailable',
    }
  }

  if (status === 'blocked') {
    return {
      key: 'blocked',
      label: 'Blocked',
      detail: 'Seat blocked by admin',
    }
  }

  return {
    key: 'available',
    label: 'Available',
    detail: formatTimeRange(shiftAvailability.startTime, shiftAvailability.endTime),
  }
}

function getStatusBadgeClass(status) {
  if (status === 'available') return 'badge--success'
  if (status === 'occupied') return 'seat-map-page__badge--occupied'
  if (status === 'blocked') return 'seat-map-page__badge--blocked'
  if (status === 'reserved') return 'seat-map-page__badge--reserved'
  if (status === 'maintenance') return 'badge--warning'

  return 'badge--active'
}

function formatTimeRange(startTime, endTime) {
  if (!startTime || !endTime) return ''

  return `${startTime}-${endTime}`
}

function formatLabel(value) {
  if (!value) return 'Unassigned'

  return String(value)
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())
}

async function handleSeatClick(seat) {
  try {
    await seatStore.selectSeat(seat.id)
  } catch {
    // Store-owned error state is rendered above the map.
  }
}

async function loadSeatMap() {
  try {
    await seatStore.fetchSeats()
  } catch {
    // Store-owned error state is rendered above the map.
  }
}

onMounted(() => {
  loadSeatMap()
})
</script>

<style scoped>
.seat-map-page {
  display: grid;
  gap: var(--space-6);
}

.seat-map-page__header,
.seat-map-page__section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-5);
}

.seat-map-page__eyebrow,
.seat-map-page__title,
.seat-map-page__description {
  margin: 0;
}

.seat-map-page__title {
  margin-top: var(--space-1);
}

.seat-map-page__description {
  margin-top: var(--space-2);
  max-width: 640px;
  color: var(--color-text-muted);
}

.seat-map-page__header-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  justify-content: flex-end;
}

.seat-map-page__loading {
  display: grid;
  min-height: 280px;
  place-items: center;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface-elevated);
}

.seat-map-page__toolbar {
  display: grid;
  gap: var(--space-4);
  padding: var(--space-4);
}

.seat-map-page__shift-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.seat-map-page__shift-tab {
  display: grid;
  gap: var(--space-1);
  min-width: 140px;
  padding: var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-elevated);
  color: var(--color-text-primary);
  text-align: left;
  cursor: pointer;
}

.seat-map-page__shift-tab span {
  color: var(--color-text-muted);
  font-size: var(--font-size-caption);
}

.seat-map-page__shift-tab--active {
  border-color: var(--color-primary);
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.seat-map-page__shift-summary {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.seat-map-page__legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  justify-content: flex-end;
}

.seat-map-page__legend-item {
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

.seat-map-page__legend-indicator {
  width: 10px;
  height: 10px;
  border-radius: var(--radius-pill);
}

.seat-map-page__legend-indicator--available {
  background: var(--color-success);
}

.seat-map-page__legend-indicator--occupied {
  background: var(--color-primary);
}

.seat-map-page__legend-indicator--blocked {
  background: var(--color-danger);
}

.seat-map-page__legend-indicator--reserved {
  background: var(--color-info);
}

.seat-map-page__legend-indicator--maintenance {
  background: var(--color-warning);
}

.seat-map-page__layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(260px, 360px);
  gap: var(--space-5);
  align-items: start;
}

.seat-map-page__groups {
  display: grid;
  gap: var(--space-5);
}

.seat-map-page__group {
  display: grid;
  gap: var(--space-3);
}

.seat-map-page__group-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-4);
}

.seat-map-page__seat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(124px, 1fr));
  gap: var(--space-3);
}

.seat-map-page__seat-card {
  display: grid;
  gap: var(--space-2);
  min-height: 118px;
  padding: var(--space-3);
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

.seat-map-page__seat-card:hover {
  transform: translateY(-2px);
  border-color: var(--color-primary);
  box-shadow: var(--shadow-md);
}

.seat-map-page__seat-card:focus-visible {
  outline: 3px solid var(--color-focus-ring);
  outline-offset: 2px;
}

.seat-map-page__seat-card small {
  color: var(--color-text-muted);
  font-size: var(--font-size-caption);
}

.seat-map-page__seat-card--selected {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-light), var(--shadow-md);
}

.seat-map-page__seat-card--available {
  border-left-color: var(--color-success);
}

.seat-map-page__seat-card--occupied {
  border-left-color: var(--color-primary);
}

.seat-map-page__seat-card--blocked {
  border-left-color: var(--color-danger);
}

.seat-map-page__seat-card--reserved {
  border-left-color: var(--color-info);
}

.seat-map-page__seat-card--maintenance {
  border-left-color: var(--color-warning);
}

.seat-map-page__details {
  position: sticky;
  top: var(--space-5);
}

.seat-map-page__card-header {
  align-items: flex-start;
}

.seat-map-page__details-body,
.seat-map-page__details-empty {
  display: grid;
  gap: var(--space-4);
}

.seat-map-page__detail-row {
  display: grid;
  gap: var(--space-1);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--color-divider);
}

.seat-map-page__detail-row:last-child {
  padding-bottom: 0;
  border-bottom: 0;
}

.seat-map-page__detail-row small {
  color: var(--color-text-muted);
  font-size: var(--font-size-caption);
}

.seat-map-page__badge--occupied {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.seat-map-page__badge--blocked {
  background: var(--color-danger-light);
  color: var(--color-danger);
}

.seat-map-page__badge--reserved {
  background: var(--color-info-light);
  color: var(--color-info);
}

@media (max-width: 1100px) {
  .seat-map-page__layout {
    grid-template-columns: 1fr;
  }

  .seat-map-page__details {
    position: static;
  }
}

@media (max-width: 760px) {
  .seat-map-page__header,
  .seat-map-page__section-header {
    align-items: stretch;
    flex-direction: column;
  }

  .seat-map-page__header-actions {
    justify-content: flex-start;
  }

  .seat-map-page__legend {
    justify-content: flex-start;
  }
}

@media (max-width: 480px) {
  .seat-map-page__seat-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .seat-map-page__shift-tab {
    min-width: 100%;
  }
}
</style>

<!--
src/pages/admin: Dedicated seat availability map.
Cards intentionally render one selected shift at a time so status is calculated
from selectedShift + seatId instead of listing every shift in each card.
-->
