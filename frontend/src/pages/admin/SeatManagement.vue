<template>
  <section class="seat-management-page" aria-labelledby="seat-management-title">
    <header class="seat-management-page__header">
      <div>
        <p class="text-label text-muted seat-management-page__eyebrow">
          Seat Operations
        </p>
        <h1 id="seat-management-title" class="text-h2 seat-management-page__title">
          Seat Management
        </h1>
        <p class="text-body seat-management-page__description">
          Create, update, and maintain the seats available in the library.
        </p>
      </div>

      <div class="seat-management-page__actions">
        <button class="btn btn--secondary" type="button" @click="isFloorModalOpen = true">
          <Layers3 :size="17" aria-hidden="true" /> Manage Floors
        </button>
        <button class="btn btn--primary" type="button" @click="openAddSeatModal">
          <Plus :size="18" aria-hidden="true" /> Add Seat
        </button>
        <button
          class="btn btn--secondary"
          type="button"
          :disabled="isLoading"
          @click="loadSeats"
        >
          <RefreshCw :size="17" :class="{ 'seat-management-page__spin': isLoading }" aria-hidden="true" />
          {{ isLoading ? 'Refreshing' : 'Refresh' }}
        </button>
        <BulkActionMenu
          :selected-count="selectedSeatIds.length"
          :disabled="selectedSeatIds.length === 0 || isLoading"
          @action="handleBulkAction"
        />
      </div>
    </header>

    <Toast v-if="successToastMessage" type="success">
      {{ successToastMessage }}
    </Toast>

    <div v-if="errorMessage" class="alert alert--danger" role="alert">
      <div>
        <strong>Unable to load seats.</strong>
        <p class="m-0">{{ errorMessage }}</p>
      </div>

      <button class="btn btn--secondary btn--sm" type="button" @click="loadSeats">
        Retry
      </button>
    </div>

    <div v-if="isInitialLoading" class="seat-management-page__loading">
      <LoadingSpinner label="Loading physical seats" />
    </div>

    <template v-else-if="!errorMessage">
      <SeatSummaryCards :summary="summaryCards" />

      <SeatFilters
        :filters="seatFilters"
        :floors="availableFloors"
        :has-active-filters="hasActiveSeatFilters"
        @update="seatStore.updateSeatFilter"
        @reset="seatStore.resetSeatFilters"
      />

      <EmptyState
        v-if="seats.length === 0"
        title="No seats created yet."
        description="Create seats before managing availability or viewing the seat map."
      >
        <template #icon>
          <Armchair :size="28" />
        </template>
        <template #primary-action>
          <button class="btn btn--primary" type="button" @click="openAddSeatModal">
            Add Seat
          </button>
        </template>
        <template #secondary-action>
          <span></span>
        </template>
      </EmptyState>

      <section
        v-else
        class="card seat-management-page__table-card"
        aria-labelledby="seat-table-title"
      >
        <header class="card__header seat-management-page__card-header">
          <div>
            <h2 id="seat-table-title" class="text-h4 m-0">Seat List</h2>
            <p class="text-small text-muted m-0">
              Manage seat records, status, floor, type, and notes.
            </p>
          </div>

          <label class="checkbox seat-management-page__select-all">
            <input
              type="checkbox"
              :checked="areVisibleSeatsSelected"
              :disabled="filteredSeats.length === 0"
              @change="toggleAllVisibleSeats"
            />
            <span>Select visible</span>
          </label>
        </header>

        <div class="card__body">
          <SeatTable
            :seats="filteredSeats"
            :selected-seat-ids="selectedSeatIds"
            @toggle-seat="toggleSeatSelection"
            @edit="openEditSeatModal"
            @delete="openDeleteSeatConfirm"
            @change-status="handleSeatStatusChange"
            @view-map="handleViewSeatMap"
          />
        </div>
      </section>
    </template>

    <AddSeatModal
      :is-open="isAddSeatModalOpen"
      :seats="seats"
      :floors="floors"
      :is-submitting="isLoading"
      @close="closeAddSeatModal"
      @create="handleCreateSeat"
    />

    <EditSeatModal
      :is-open="isEditSeatModalOpen"
      :seat="selectedSeatForEdit"
      :seats="seats"
      :floors="floors"
      :is-submitting="isLoading"
      @close="closeEditSeatModal"
      @save="handleUpdateSeat"
    />

    <FloorManagementModal
      :is-open="isFloorModalOpen"
      :floors="floors"
      :is-submitting="isLoading"
      @close="isFloorModalOpen = false"
      @create="handleCreateFloor"
      @update="handleUpdateFloor"
      @delete="handleDeleteFloor"
    />

    <ConfirmDialog
      :is-open="Boolean(deleteTarget)"
      :title="deleteConfirmTitle"
      :message="deleteConfirmMessage"
      confirm-label="Delete"
      confirming-label="Deleting"
      :is-confirming="isLoading"
      @cancel="closeDeleteConfirm"
      @confirm="handleDeleteConfirm"
    />
  </section>
</template>

<script setup>
import { Armchair, Layers3, Plus, RefreshCw } from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import ConfirmDialog from '../../components/common/ConfirmDialog.vue'
import EmptyState from '../../components/common/EmptyState.vue'
import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import Toast from '../../components/common/Toast.vue'
import AddSeatModal from '../../components/seat/AddSeatModal.vue'
import BulkActionMenu from '../../components/seat/BulkActionMenu.vue'
import EditSeatModal from '../../components/seat/EditSeatModal.vue'
import FloorManagementModal from '../../components/seat/FloorManagementModal.vue'
import SeatFilters from '../../components/seat/SeatFilters.vue'
import SeatSummaryCards from '../../components/seat/SeatSummaryCards.vue'
import SeatTable from '../../components/seat/SeatTable.vue'
import { useSeatStore } from '../../stores/seatStore'

const router = useRouter()
const seatStore = useSeatStore()
const isAddSeatModalOpen = ref(false)
const isEditSeatModalOpen = ref(false)
const isFloorModalOpen = ref(false)
const selectedSeatForEdit = ref(null)
const selectedSeatIds = ref([])
const deleteTarget = ref(null)
const successToastMessage = ref('')
let successToastTimer = null

const {
  seats,
  floors,
  availableSeats,
  occupiedSeats,
  totalSeats,
  availableFloors,
  filteredSeats,
  seatFilters,
  hasActiveSeatFilters,
  isLoading,
  errorMessage,
} = storeToRefs(seatStore)

const isInitialLoading = computed(() => {
  return isLoading.value && seats.value.length === 0
})

const maintenanceSeats = computed(() => {
  return seats.value.filter((seat) => seat.physicalStatus === 'maintenance')
})

const summaryCards = computed(() => ({
  total: totalSeats.value,
  available: availableSeats.value.length,
  occupied: occupiedSeats.value.length,
  maintenance: maintenanceSeats.value.length,
}))

const areVisibleSeatsSelected = computed(() => {
  if (filteredSeats.value.length === 0) return false

  return filteredSeats.value.every((seat) => selectedSeatIds.value.includes(seat.id))
})

const deleteConfirmTitle = computed(() => {
  if (!deleteTarget.value) return 'Delete Seat'

  if (deleteTarget.value.type === 'bulk') {
    return `Delete ${deleteTarget.value.seatIds.length} selected seats?`
  }

  return `Delete Seat ${deleteTarget.value.seat.seatNumber}?`
})

const deleteConfirmMessage = computed(() => {
  return 'This action cannot be undone.'
})

function openAddSeatModal() {
  isAddSeatModalOpen.value = true
}

function closeAddSeatModal() {
  if (isLoading.value) return

  isAddSeatModalOpen.value = false
}

function openEditSeatModal(seat) {
  selectedSeatForEdit.value = seat
  isEditSeatModalOpen.value = true
}

function closeEditSeatModal() {
  if (isLoading.value) return

  isEditSeatModalOpen.value = false
  selectedSeatForEdit.value = null
}

function openDeleteSeatConfirm(seat) {
  deleteTarget.value = {
    type: 'single',
    seat,
  }
}

function openBulkDeleteConfirm() {
  deleteTarget.value = {
    type: 'bulk',
    seatIds: [...selectedSeatIds.value],
  }
}

function closeDeleteConfirm() {
  if (isLoading.value) return

  deleteTarget.value = null
}

function toggleSeatSelection(seatId) {
  if (selectedSeatIds.value.includes(seatId)) {
    selectedSeatIds.value = selectedSeatIds.value.filter((id) => id !== seatId)
    return
  }

  selectedSeatIds.value = [...selectedSeatIds.value, seatId]
}

function toggleAllVisibleSeats() {
  const visibleSeatIds = filteredSeats.value.map((seat) => seat.id)

  if (areVisibleSeatsSelected.value) {
    selectedSeatIds.value = selectedSeatIds.value.filter((seatId) => {
      return !visibleSeatIds.includes(seatId)
    })
    return
  }

  selectedSeatIds.value = [...new Set([...selectedSeatIds.value, ...visibleSeatIds])]
}

function clearDeletedSelections(deletedSeatIds = []) {
  selectedSeatIds.value = selectedSeatIds.value.filter((seatId) => {
    return !deletedSeatIds.includes(seatId)
  })
}

function handleBulkAction(action) {
  if (selectedSeatIds.value.length === 0) return

  if (action === 'delete') {
    openBulkDeleteConfirm()
    return
  }

  handleBulkStatusChange(action)
}

function showSuccessToast(message) {
  successToastMessage.value = message

  window.clearTimeout(successToastTimer)
  successToastTimer = window.setTimeout(() => {
    successToastMessage.value = ''
  }, 4000)
}

async function handleCreateSeat(seatPayload) {
  try {
    await seatStore.createSeat(seatPayload)
    closeAddSeatModal()
    showSuccessToast(`${seatPayload.seatNumber} created successfully.`)
  } catch {
    // Store-owned error state is rendered above the page.
  }
}

async function handleCreateFloor(_unused, payload) {
  try {
    await seatStore.createFloor(payload)
    showSuccessToast(`${payload.name} created successfully.`)
  } catch {
    // Store-owned error state is rendered above the page.
  }
}

async function handleUpdateFloor(floorId, payload) {
  try {
    await seatStore.updateFloor(floorId, payload)
    await seatStore.fetchSeats()
    showSuccessToast(`${payload.name} updated successfully.`)
  } catch {
    // Store-owned error state is rendered above the page.
  }
}

async function handleDeleteFloor(floorId) {
  try {
    await seatStore.deleteFloor(floorId)
    showSuccessToast('Floor deleted successfully.')
  } catch {
    // Store-owned error state is rendered above the page.
  }
}

async function handleUpdateSeat(seatPayload) {
  if (!selectedSeatForEdit.value) return

  try {
    await seatStore.updateSeat(selectedSeatForEdit.value.id, seatPayload)
    closeEditSeatModal()
    showSuccessToast(`${seatPayload.seatNumber} updated successfully.`)
  } catch {
    // Store-owned error state is rendered above the page.
  }
}

async function handleSeatStatusChange(seat, status) {
  if (seat.physicalStatus === status) {
    showSuccessToast(`${seat.seatNumber} is already ${formatLabel(status)}.`)
    return
  }

  try {
    await seatStore.updateSeatStatus(seat.id, { status })
    showSuccessToast(`${seat.seatNumber} marked ${formatLabel(status)}.`)
  } catch {
    // Store-owned error state is rendered above the page.
  }
}

async function handleBulkStatusChange(status) {
  try {
    await seatStore.bulkUpdateSeatStatus(selectedSeatIds.value, { status })
    showSuccessToast(
      `${selectedSeatIds.value.length} seats marked ${formatLabel(status)}.`,
    )
  } catch {
    // Store-owned error state is rendered above the page.
  }
}

async function handleDeleteConfirm() {
  if (!deleteTarget.value) return

  try {
    if (deleteTarget.value.type === 'bulk') {
      const seatIds = [...deleteTarget.value.seatIds]

      await seatStore.bulkDeleteSeats(seatIds)
      clearDeletedSelections(seatIds)
      showSuccessToast(`${seatIds.length} seats deleted successfully.`)
    } else {
      const seat = deleteTarget.value.seat

      await seatStore.deleteSeat(seat.id)
      clearDeletedSelections([seat.id])
      showSuccessToast(`${seat.seatNumber} deleted successfully.`)
    }

    closeDeleteConfirm()
  } catch {
    // Store-owned error state is rendered above the page.
  }
}

function handleViewSeatMap() {
  router.push({ name: 'adminSeatMap' })
}

function formatLabel(value) {
  if (!value) return 'Unassigned'

  return String(value)
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())
}

async function loadSeats() {
  try {
    await Promise.all([seatStore.fetchSeats(), seatStore.fetchFloors()])
  } catch {
    // Store-owned error state is rendered above the page.
  }
}

onMounted(loadSeats)

onBeforeUnmount(() => {
  window.clearTimeout(successToastTimer)
})
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

.seat-management-page__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  justify-content: flex-end;
}

.seat-management-page__loading {
  display: grid;
  min-height: 280px;
  place-items: center;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface-elevated);
}

.seat-management-page__spin {
  animation: ds-spin var(--transition-slow) linear infinite;
}

.seat-management-page__table-card {
  overflow: visible;
}

.seat-management-page__card-header {
  align-items: flex-start;
}

.seat-management-page__select-all {
  white-space: nowrap;
}

@media (max-width: 760px) {
  .seat-management-page__header {
    align-items: stretch;
    flex-direction: column;
  }

  .seat-management-page__actions {
    justify-content: flex-start;
  }
}
</style>

<!--
src/pages/admin: Physical seat CRUD page for library owners.
Allocation, transfer, student assignment, shift management, and seat-map workflows
live in their own modules.
-->
