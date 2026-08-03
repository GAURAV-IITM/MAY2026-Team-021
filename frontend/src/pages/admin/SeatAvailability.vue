<template>
  <section class="seat-map-page" aria-labelledby="seat-map-title">
    <header class="seat-map-page__header">
      <div>
        <p class="text-label text-muted m-0">Seat Availability</p>
        <h1 id="seat-map-title" class="text-h2 seat-map-page__title">Seat Map</h1>
        <p class="text-body seat-map-page__description">
          Availability is calculated by the server for the selected shift and date range.
        </p>
      </div>
      <div class="seat-map-page__header-actions">
        <RouterLink class="btn btn--secondary" :to="{ name: 'adminSeatAllocations' }">
          <History :size="17" aria-hidden="true" /> Allocation History
        </RouterLink>
        <RouterLink class="btn btn--secondary" :to="{ name: 'adminSeatManagement' }">
          <ArrowLeft :size="17" aria-hidden="true" /> Seat Management
        </RouterLink>
        <button
          class="btn btn--secondary"
          type="button"
          :disabled="isAvailabilityLoading"
          @click="loadAvailability"
        >
          <RefreshCw
            :size="17"
            :class="{ 'seat-map-page__spin': isAvailabilityLoading }"
            aria-hidden="true"
          />
          Refresh
        </button>
      </div>
    </header>

    <Toast v-if="toastMessage" :type="toastType">{{ toastMessage }}</Toast>

    <div v-if="pageError" class="alert alert--danger" role="alert">
      <div>
        <strong>Unable to load seat availability.</strong>
        <p class="m-0">{{ pageError }}</p>
      </div>
      <button class="btn btn--secondary btn--sm" type="button" @click="initialize">
        Retry
      </button>
    </div>

    <section class="card seat-map-page__controls" aria-label="Availability criteria">
      <div class="seat-map-page__date-controls">
        <div class="form-field">
          <label class="form-label" for="map-start-date">Start date</label>
          <input id="map-start-date" v-model="filters.startDate" class="form-input" type="date" />
        </div>
        <div class="form-field">
          <label class="form-label" for="map-end-date">End date</label>
          <input
            id="map-end-date"
            v-model="filters.endDate"
            class="form-input"
            type="date"
            :min="filters.startDate"
          />
        </div>
        <div class="form-field">
          <label class="form-label" for="map-floor">Floor</label>
          <select id="map-floor" v-model="filters.floorId" class="form-select">
            <option value="">All floors</option>
            <option v-for="floor in floors" :key="floor.id" :value="floor.id">
              {{ floor.name }}
            </option>
          </select>
        </div>
        <button
          class="btn btn--primary seat-map-page__apply"
          type="button"
          :disabled="!criteriaAreValid || isAvailabilityLoading"
          @click="loadAvailability"
        >
          <Search :size="17" aria-hidden="true" /> Check Availability
        </button>
      </div>

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
          <span>{{ shift.startTime }}-{{ shift.endTime }}</span>
        </button>
      </div>

      <div class="seat-map-page__summary" aria-live="polite">
        <span class="badge badge--success">{{ summary.available }} Available</span>
        <span class="badge seat-map-page__badge--allotted">{{ summary.allotted }} Allotted</span>
        <span class="badge seat-map-page__badge--blocked">
          {{ summary.blocked + summary.physicallyBlocked }} Blocked
        </span>
        <span class="badge seat-map-page__badge--reserved">{{ summary.reserved }} Reserved</span>
        <span class="badge badge--warning">{{ summary.maintenance }} Maintenance</span>
      </div>
    </section>

    <div v-if="isInitialLoading" class="seat-map-page__loading">
      <LoadingSpinner label="Loading seat availability map" />
    </div>

    <template v-else-if="!pageError">
      <section class="seat-map-page__section-header">
        <div>
          <h2 class="text-h4 m-0">{{ selectedShift?.name || 'Seat Availability' }}</h2>
          <p class="text-small text-muted m-0">
            {{ formatDateRange(filters.startDate, filters.endDate) }}
          </p>
        </div>
        <div class="seat-map-page__legend" aria-label="Seat status legend">
          <span v-for="item in legendItems" :key="item.status" class="seat-map-page__legend-item">
            <span :class="`seat-map-page__dot seat-map-page__dot--${item.status}`"></span>
            {{ item.label }}
          </span>
        </div>
      </section>

      <div class="seat-map-page__layout">
        <div class="seat-map-page__groups">
          <div v-if="floorGroups.length === 0" class="card seat-map-page__empty">
            <Armchair :size="28" aria-hidden="true" />
            <strong>No seats match these criteria.</strong>
          </div>

          <section
            v-for="group in floorGroups"
            :key="group.id"
            class="seat-map-page__group"
            :aria-labelledby="`${group.id}-title`"
          >
            <header>
              <h3 :id="`${group.id}-title`" class="text-h4 m-0">{{ group.label }}</h3>
              <p class="text-small text-muted m-0">{{ group.seats.length }} seats</p>
            </header>
            <div class="seat-map-page__seat-grid" role="list">
              <button
                v-for="seat in group.seats"
                :key="seat.id"
                class="seat-map-page__seat-card"
                :class="[
                  `seat-map-page__seat-card--${visualStatus(seat.status)}`,
                  { 'seat-map-page__seat-card--selected': selectedSeat?.id === seat.id },
                ]"
                type="button"
                role="listitem"
                :aria-pressed="String(selectedSeat?.id === seat.id)"
                @click="selectedSeat = seat"
              >
                <strong>{{ seat.seatNumber }}</strong>
                <span class="badge" :class="badgeClass(seat.status)">
                  {{ statusLabel(seat.status) }}
                </span>
                <small>{{ seatDetail(seat) }}</small>
              </button>
            </div>
          </section>
        </div>

        <aside class="card seat-map-page__details" aria-label="Selected seat details">
          <template v-if="selectedSeat">
            <header class="card__header">
              <div>
                <p class="text-label text-muted m-0">Selected Seat</p>
                <h3 class="text-h4 m-0">{{ selectedSeat.seatNumber }}</h3>
              </div>
              <span class="badge" :class="badgeClass(selectedSeat.status)">
                {{ statusLabel(selectedSeat.status) }}
              </span>
            </header>
            <div class="card__body seat-map-page__details-body">
              <div class="seat-map-page__detail-row">
                <span class="text-small text-muted">Floor</span>
                <strong>{{ selectedSeat.floorName }}</strong>
              </div>
              <div class="seat-map-page__detail-row">
                <span class="text-small text-muted">Physical status</span>
                <strong>{{ statusLabel(selectedSeat.physicalStatus) }}</strong>
                <small v-if="selectedSeat.statusNote">{{ selectedSeat.statusNote }}</small>
              </div>
              <div v-if="selectedSeat.blockers.length" class="seat-map-page__detail-row">
                <span class="text-small text-muted">Blocking allocation</span>
                <strong>{{ selectedSeat.blockers[0].studentName }}</strong>
                <small>
                  {{ selectedSeat.blockers[0].shiftName }}
                  {{ selectedSeat.blockers[0].shiftStartTime }}-{{ selectedSeat.blockers[0].shiftEndTime }}
                </small>
                <small>
                  {{ selectedSeat.blockers[0].startDate }} to {{ selectedSeat.blockers[0].endDate }}
                </small>
              </div>
              <button
                v-if="selectedSeat.isAvailable"
                class="btn btn--primary"
                type="button"
                @click="openAllocationDialog"
              >
                <UserPlus :size="17" aria-hidden="true" /> Allocate This Seat
              </button>
            </div>
          </template>
          <div v-else class="card__body seat-map-page__details-empty">
            <Armchair :size="24" aria-hidden="true" />
            <h3 class="text-h4 m-0">No seat selected</h3>
            <p class="text-small text-muted m-0">Choose a seat to inspect its current status.</p>
          </div>
        </aside>
      </div>
    </template>

    <SeatAllocationDialog
      :is-open="isAllocationDialogOpen"
      :seats="availabilitySeats"
      :students="students"
      :shifts="studyShifts"
      :initial-seat-id="selectedSeat?.id || ''"
      :initial-shift-ids="selectedShiftId ? [selectedShiftId] : []"
      :initial-start-date="filters.startDate"
      :initial-end-date="filters.endDate"
      :is-submitting="isAllocationSubmitting"
      :submission-error="submissionError"
      @close="closeAllocationDialog"
      @confirm="createAllocation"
    />
  </section>
</template>

<script setup>
import {
  Armchair,
  ArrowLeft,
  History,
  RefreshCw,
  Search,
  UserPlus,
} from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'

import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import Toast from '../../components/common/Toast.vue'
import SeatAllocationDialog from '../../components/seat/SeatAllocationDialog.vue'
import { useSeatStore } from '../../stores/seatStore'
import { useStudentStore } from '../../stores/studentStore'

const legendItems = Object.freeze([
  { status: 'available', label: 'Available' },
  { status: 'allotted', label: 'Allotted' },
  { status: 'blocked', label: 'Blocked' },
  { status: 'reserved', label: 'Reserved' },
  { status: 'maintenance', label: 'Maintenance' },
])

const seatStore = useSeatStore()
const studentStore = useStudentStore()
const selectedShiftId = ref('')
const selectedSeat = ref(null)
const isAllocationDialogOpen = ref(false)
const toastMessage = ref('')
const toastType = ref('success')
let toastTimer

const today = localDateString(new Date())
const filters = reactive({
  startDate: today,
  endDate: today,
  floorId: '',
})

const {
  studyShifts,
  floors,
  allocationAvailability,
  isLoading,
  isAvailabilityLoading,
  isAllocationSubmitting,
  errorMessage,
  availabilityErrorMessage,
  allocationError,
} = storeToRefs(seatStore)
const { students } = storeToRefs(studentStore)

const enabledShifts = computed(() =>
  studyShifts.value.filter((shift) => shift.isEnabled !== false),
)
const selectedShift = computed(() =>
  enabledShifts.value.find((shift) => shift.id === selectedShiftId.value),
)
const criteriaAreValid = computed(
  () =>
    Boolean(selectedShiftId.value && filters.startDate && filters.endDate) &&
    filters.endDate >= filters.startDate,
)
const pageError = computed(
  () => availabilityErrorMessage.value || errorMessage.value,
)
const isInitialLoading = computed(
  () =>
    (isLoading.value || isAvailabilityLoading.value) &&
    !allocationAvailability.value,
)
const availabilitySeats = computed(() =>
  (allocationAvailability.value?.seats || []).map((seat) => ({
    ...seat,
    id: seat.seatId,
  })),
)
const summary = computed(() => {
  const values = allocationAvailability.value?.summary || {}
  return {
    available: values.available || 0,
    allotted: values.allotted || 0,
    blocked: values.blocked || 0,
    reserved: values.reserved || 0,
    maintenance: values.maintenance || 0,
    physicallyBlocked: values.physicallyBlocked || 0,
  }
})
const floorGroups = computed(() => {
  const groups = new Map()
  availabilitySeats.value.forEach((seat) => {
    const group = groups.get(seat.floorId) || {
      id: `floor-${seat.floorId}`,
      label: seat.floorName,
      seats: [],
    }
    group.seats.push(seat)
    groups.set(seat.floorId, group)
  })
  return [...groups.values()].map((group) => ({
    ...group,
    seats: group.seats.sort((first, second) =>
      first.seatNumber.localeCompare(second.seatNumber),
    ),
  }))
})
const submissionError = computed(() => {
  if (!allocationError.value) return null
  return {
    message:
      allocationError.value.response?.data?.error?.message ||
      allocationError.value.message,
    requestId: allocationError.value.response?.data?.requestId || '',
  }
})

async function initialize() {
  try {
    await Promise.all([
      seatStore.fetchShifts(),
      seatStore.fetchFloors(),
      studentStore.fetchStudents(),
    ])
    if (!selectedShiftId.value) {
      selectedShiftId.value = enabledShifts.value[0]?.id || ''
    }
    if (selectedShiftId.value) await loadAvailability()
  } catch {
    // Store error state is rendered above.
  }
}

async function loadAvailability() {
  if (!criteriaAreValid.value) return
  try {
    const response = await seatStore.fetchAllocationAvailability({
      shiftIds: [selectedShiftId.value],
      startDate: filters.startDate,
      endDate: filters.endDate,
      floorId: filters.floorId || undefined,
    })
    const selectedId = selectedSeat.value?.id
    selectedSeat.value =
      response.data.seats
        .map((seat) => ({ ...seat, id: seat.seatId }))
        .find((seat) => seat.id === selectedId) || null
  } catch {
    selectedSeat.value = null
  }
}

async function selectShift(shiftId) {
  selectedShiftId.value = shiftId
  selectedSeat.value = null
  await loadAvailability()
}

function openAllocationDialog() {
  seatStore.clearAllocationError()
  isAllocationDialogOpen.value = true
}

function closeAllocationDialog() {
  isAllocationDialogOpen.value = false
  seatStore.clearAllocationError()
}

async function createAllocation(payload) {
  try {
    const response = await seatStore.allocateSeat(payload)
    isAllocationDialogOpen.value = false
    showToast(
      `${response.data.allocationCount} allocation${response.data.allocationCount === 1 ? '' : 's'} created.`,
    )
    await loadAvailability()
  } catch {
    // Keep the dialog and values open; submissionError shows the server response.
  }
}

function visualStatus(status) {
  return status === 'physically_blocked' ? 'blocked' : status
}

function statusLabel(status) {
  const labels = {
    available: 'Available',
    allotted: 'Allotted',
    reserved: 'Reserved',
    blocked: 'Blocked',
    physically_blocked: 'Blocked',
    maintenance: 'Maintenance',
  }
  return labels[status] || 'Unavailable'
}

function badgeClass(status) {
  const visual = visualStatus(status)
  if (visual === 'available') return 'badge--success'
  if (visual === 'maintenance') return 'badge--warning'
  return `seat-map-page__badge--${visual}`
}

function seatDetail(seat) {
  if (seat.blockers.length) {
    return `${seat.blockers[0].shiftName} · ${seat.blockers[0].studentName}`
  }
  if (seat.statusNote) return seat.statusNote
  return seat.floorName
}

function formatDateRange(startDate, endDate) {
  if (!startDate || !endDate) return ''
  return startDate === endDate ? startDate : `${startDate} to ${endDate}`
}

function localDateString(value) {
  const offset = value.getTimezoneOffset() * 60_000
  return new Date(value.getTime() - offset).toISOString().slice(0, 10)
}

function showToast(message, type = 'success') {
  globalThis.clearTimeout(toastTimer)
  toastMessage.value = message
  toastType.value = type
  toastTimer = globalThis.setTimeout(() => {
    toastMessage.value = ''
  }, 3500)
}

onMounted(initialize)
onBeforeUnmount(() => globalThis.clearTimeout(toastTimer))
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

.seat-map-page__title {
  margin: var(--space-1) 0 0;
}

.seat-map-page__description {
  margin: var(--space-2) 0 0;
  color: var(--color-text-muted);
}

.seat-map-page__header-actions,
.seat-map-page__summary,
.seat-map-page__legend {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.seat-map-page__controls {
  display: grid;
  gap: var(--space-4);
  padding: var(--space-4);
}

.seat-map-page__date-controls {
  display: grid;
  grid-template-columns: repeat(3, minmax(150px, 220px)) auto;
  align-items: end;
  gap: var(--space-3);
}

.seat-map-page__apply {
  margin-bottom: 1px;
}

.seat-map-page__shift-tabs {
  display: flex;
  gap: var(--space-2);
  overflow-x: auto;
  padding-bottom: var(--space-1);
}

.seat-map-page__shift-tab {
  display: grid;
  flex: 0 0 140px;
  gap: var(--space-1);
  min-height: 64px;
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

.seat-map-page__loading,
.seat-map-page__empty {
  display: grid;
  min-height: 240px;
  place-items: center;
}

.seat-map-page__spin {
  animation: ds-spin var(--transition-slow) linear infinite;
}

.seat-map-page__legend {
  justify-content: flex-end;
}

.seat-map-page__legend-item {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-caption);
  font-weight: var(--font-weight-semibold);
}

.seat-map-page__dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
}

.seat-map-page__dot--available { background: var(--color-success); }
.seat-map-page__dot--allotted { background: var(--color-primary); }
.seat-map-page__dot--blocked { background: var(--color-danger); }
.seat-map-page__dot--reserved { background: var(--color-info); }
.seat-map-page__dot--maintenance { background: var(--color-warning); }

.seat-map-page__layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(280px, 350px);
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

.seat-map-page__seat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: var(--space-3);
}

.seat-map-page__seat-card {
  display: grid;
  gap: var(--space-2);
  min-height: 116px;
  padding: var(--space-3);
  border: 1px solid var(--color-border);
  border-left-width: 4px;
  border-radius: var(--radius-md);
  background: var(--color-surface-elevated);
  color: var(--color-text-primary);
  text-align: left;
  cursor: pointer;
}

.seat-map-page__seat-card:hover,
.seat-map-page__seat-card--selected {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-md);
}

.seat-map-page__seat-card small {
  color: var(--color-text-muted);
}

.seat-map-page__seat-card--available { border-left-color: var(--color-success); }
.seat-map-page__seat-card--allotted { border-left-color: var(--color-primary); }
.seat-map-page__seat-card--blocked { border-left-color: var(--color-danger); }
.seat-map-page__seat-card--reserved { border-left-color: var(--color-info); }
.seat-map-page__seat-card--maintenance { border-left-color: var(--color-warning); }

.seat-map-page__details {
  position: sticky;
  top: var(--space-5);
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

.seat-map-page__badge--allotted {
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

@media (max-width: 1000px) {
  .seat-map-page__date-controls {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .seat-map-page__layout {
    grid-template-columns: 1fr;
  }

  .seat-map-page__details {
    position: static;
  }
}

@media (max-width: 680px) {
  .seat-map-page__header,
  .seat-map-page__section-header {
    flex-direction: column;
  }

  .seat-map-page__date-controls {
    grid-template-columns: 1fr;
  }

  .seat-map-page__seat-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
