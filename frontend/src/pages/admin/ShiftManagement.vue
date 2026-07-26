<template>
  <section class="shift-management-page" aria-labelledby="shift-management-title">
    <header class="shift-management-page__header">
      <div>
        <p class="text-label text-muted shift-management-page__eyebrow">
          Seat Operations
        </p>
        <h1 id="shift-management-title" class="text-h2 shift-management-page__title">
          Shift Management
        </h1>
        <p class="text-body shift-management-page__description">
          Manage study shifts, timings, availability status, and shift-level seat usage.
        </p>
      </div>

      <button class="btn btn--primary" type="button" @click="openCreateShiftModal">
        <Plus :size="18" aria-hidden="true" /> Add Shift
      </button>
    </header>

    <Toast v-if="successToastMessage" type="success">
      {{ successToastMessage }}
    </Toast>

    <div v-if="errorMessage" class="alert alert--danger" role="alert">
      <div>
        <strong>Unable to load shifts.</strong>
        <p class="m-0">{{ errorMessage }}</p>
      </div>

      <button
        class="btn btn--secondary btn--sm"
        type="button"
        @click="loadShiftManagement"
      >
        Retry
      </button>
    </div>

    <div v-if="isInitialLoading" class="shift-management-page__loading">
      <LoadingSpinner label="Loading shift management" />
    </div>

    <template v-else-if="!errorMessage">
      <section class="shift-management-page__summary" aria-label="Shift summary">
        <StatCard
          title="Total Shifts"
          :value="String(shiftRows.length)"
          :icon="Clock3"
          trend="Default and custom shifts"
        >
          <template #footer>
            {{ enabledShiftCount }} enabled
          </template>
        </StatCard>

        <StatCard
          title="Occupied Seats"
          :value="String(totalOccupiedAcrossShifts)"
          :icon="Armchair"
          trend="Counted by active shift"
        >
          <template #footer>
            {{ unassignedOccupiedSeats.length }} occupied without shift
          </template>
        </StatCard>

        <StatCard
          title="Available Seats"
          :value="String(totalAvailableAcrossShifts)"
          :icon="CircleCheckBig"
          trend="Available by shift"
        >
          <template #footer>
            Recomputed after shift changes
          </template>
        </StatCard>
      </section>

      <section class="card shift-management-page__table-card" aria-labelledby="shift-list-title">
        <header class="card__header shift-management-page__card-header">
          <div>
            <h2 id="shift-list-title" class="text-h4 m-0">Shift List</h2>
            <p class="text-small text-muted m-0">
              Default shifts can be adjusted, and custom shifts can be added as the library grows.
            </p>
          </div>
        </header>

        <div class="card__body">
          <DataTable
            :columns="shiftColumns"
            :rows="shiftRows"
            aria-label="Study shifts"
          >
            <template #cell-name="{ row }">
              <div class="shift-management-page__shift-name">
                <strong>{{ row.name }}</strong>
                <span v-if="row.isDefault" class="badge badge--pending">Default</span>
              </div>
            </template>

            <template #cell-timing="{ row }">
              {{ formatTimeRange(row) }}
            </template>

            <template #cell-isEnabled="{ value }">
              <span class="badge" :class="value ? 'badge--success' : 'badge--pending'">
                {{ value ? 'Enabled' : 'Disabled' }}
              </span>
            </template>

            <template #cell-occupiedSeatCount="{ value }">
              <strong>{{ value }}</strong>
            </template>

            <template #cell-availableSeatCount="{ value }">
              {{ value }}
            </template>

            <template #actions="{ row }">
              <div class="shift-management-page__row-actions">
                <button
                  class="btn btn--outline btn--sm"
                  type="button"
                  @click="openEditShiftModal(row)"
                >
                  <Pencil :size="15" aria-hidden="true" /> Edit
                </button>

                <button
                  class="btn btn--secondary btn--sm"
                  type="button"
                  @click="handleToggleShift(row)"
                >
                  <Power :size="15" aria-hidden="true" />
                  {{ row.isEnabled ? 'Disable' : 'Enable' }}
                </button>

                <button
                  class="btn btn--danger btn--sm"
                  type="button"
                  @click="openDeleteConfirm(row)"
                >
                  <Trash2 :size="15" aria-hidden="true" /> Delete
                </button>
              </div>
            </template>

            <template #empty>
              Shifts will appear after they are created.
            </template>
          </DataTable>
        </div>
      </section>
    </template>

    <ShiftFormModal
      :is-open="isShiftModalOpen"
      :mode="shiftModalMode"
      :shift="selectedShift"
      :is-submitting="isLoading"
      @close="closeShiftModal"
      @save="handleSaveShift"
    />

    <ConfirmDialog
      :is-open="Boolean(shiftPendingDelete)"
      title="Delete Shift"
      :message="deleteShiftMessage"
      confirm-label="Delete Shift"
      confirming-label="Deleting"
      :is-confirming="isLoading"
      @cancel="closeDeleteConfirm"
      @confirm="handleDeleteShift"
    />
  </section>
</template>

<script setup>
import { Armchair, CircleCheckBig, Clock3, Pencil, Plus, Power, Trash2 } from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import ConfirmDialog from '../../components/common/ConfirmDialog.vue'
import DataTable from '../../components/common/DataTable.vue'
import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import Toast from '../../components/common/Toast.vue'
import StatCard from '../../components/dashboard/StatCard.vue'
import ShiftFormModal from '../../components/seat/ShiftFormModal.vue'
import { useSeatStore } from '../../stores/seatStore'

const shiftColumns = Object.freeze([
  { key: 'name', label: 'Shift' },
  { key: 'timing', label: 'Timing' },
  { key: 'isEnabled', label: 'Status' },
  { key: 'occupiedSeatCount', label: 'Occupied Seats' },
  { key: 'availableSeatCount', label: 'Available Seats' },
])

const seatStore = useSeatStore()
const isShiftModalOpen = ref(false)
const shiftModalMode = ref('create')
const selectedShift = ref(null)
const shiftPendingDelete = ref(null)
const successToastMessage = ref('')
const isPageLoading = ref(false)
let successToastTimer = null

const {
  seats,
  shiftRows,
  isLoading,
  errorMessage,
} = storeToRefs(seatStore)

const isInitialLoading = computed(() => {
  return isPageLoading.value && shiftRows.value.length === 0
})

const enabledShiftCount = computed(() => {
  return shiftRows.value.filter((shift) => shift.isEnabled !== false).length
})

const totalOccupiedAcrossShifts = computed(() => {
  return shiftRows.value.reduce((total, shift) => {
    return total + shift.occupiedSeatCount
  }, 0)
})

const totalAvailableAcrossShifts = computed(() => {
  return shiftRows.value.reduce((total, shift) => {
    return total + shift.availableSeatCount
  }, 0)
})

const unassignedOccupiedSeats = computed(() => {
  return seats.value.filter((seat) => {
    const hasActiveShift =
      Array.isArray(seat.activeShifts) && seat.activeShifts.length > 0

    return Number(seat.occupiedShiftCount || 0) > 0 && !hasActiveShift
  })
})

const deleteShiftMessage = computed(() => {
  if (!shiftPendingDelete.value) {
    return 'This shift will be removed.'
  }

  return `Delete ${shiftPendingDelete.value.name}? Seats using this shift will have availability recalculated.`
})

function formatTimeRange(shift) {
  return `${shift.startTime || '--:--'} - ${shift.endTime || '--:--'}`
}

function openCreateShiftModal() {
  shiftModalMode.value = 'create'
  selectedShift.value = null
  isShiftModalOpen.value = true
}

function openEditShiftModal(shift) {
  shiftModalMode.value = 'edit'
  selectedShift.value = shift
  isShiftModalOpen.value = true
}

function closeShiftModal() {
  if (isLoading.value) return

  isShiftModalOpen.value = false
}

function openDeleteConfirm(shift) {
  shiftPendingDelete.value = shift
}

function closeDeleteConfirm() {
  if (isLoading.value) return

  shiftPendingDelete.value = null
}

function showSuccessToast(message) {
  successToastMessage.value = message

  window.clearTimeout(successToastTimer)
  successToastTimer = window.setTimeout(() => {
    successToastMessage.value = ''
  }, 4000)
}

async function handleSaveShift(shiftPayload) {
  try {
    if (shiftModalMode.value === 'edit' && selectedShift.value) {
      await seatStore.updateStudyShift(selectedShift.value.id, shiftPayload)
      showSuccessToast(`${shiftPayload.name} updated successfully.`)
    } else {
      await seatStore.createShift(shiftPayload)
      showSuccessToast(`${shiftPayload.name} created successfully.`)
    }

    closeShiftModal()
  } catch {
    // Store-owned error state is rendered above the page.
  }
}

async function handleToggleShift(shift) {
  try {
    await seatStore.toggleStudyShift(shift.id, !shift.isEnabled)
    showSuccessToast(
      `${shift.name} ${shift.isEnabled ? 'disabled' : 'enabled'} successfully.`,
    )
  } catch {
    // Store-owned error state is rendered above the page.
  }
}

async function handleDeleteShift() {
  if (!shiftPendingDelete.value) return

  const shiftName = shiftPendingDelete.value.name

  try {
    await seatStore.deleteStudyShift(shiftPendingDelete.value.id)
    closeDeleteConfirm()
    showSuccessToast(`${shiftName} deleted successfully.`)
  } catch {
    // Store-owned error state is rendered above the page.
  }
}

async function loadShiftManagement() {
  isPageLoading.value = true

  try {
    await seatStore.fetchSeats()
    await seatStore.fetchShifts()
  } catch {
    // Store-owned error state is rendered above the page.
  } finally {
    isPageLoading.value = false
  }
}

onMounted(loadShiftManagement)

onBeforeUnmount(() => {
  window.clearTimeout(successToastTimer)
})
</script>

<style scoped>
.shift-management-page {
  display: grid;
  gap: var(--space-6);
}

.shift-management-page__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-5);
}

.shift-management-page__eyebrow,
.shift-management-page__title,
.shift-management-page__description {
  margin: 0;
}

.shift-management-page__title {
  margin-top: var(--space-1);
}

.shift-management-page__description {
  margin-top: var(--space-2);
  max-width: 680px;
  color: var(--color-text-muted);
}

.shift-management-page__summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-4);
}

.shift-management-page__loading {
  display: grid;
  min-height: 280px;
  place-items: center;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface-elevated);
}

.shift-management-page__card-header {
  align-items: flex-start;
}

.shift-management-page__shift-name {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-2);
  min-width: 160px;
}

.shift-management-page__row-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-2);
}

@media (max-width: 1100px) {
  .shift-management-page__summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .shift-management-page__header {
    align-items: stretch;
    flex-direction: column;
  }

  .shift-management-page__header .btn {
    align-self: flex-start;
  }

  .shift-management-page__summary {
    grid-template-columns: 1fr;
  }
}
</style>

<!--
src/pages/admin: Shift management page for library owners and admins.

Responsibilities:
- Display tenant-defined study shifts from seatStore.
- Coordinate create, edit, delete, enable, and disable workflows through seatStore.
- Keep shift availability calculated from mock seat data until FastAPI is available.

Milestone 3:
- Replace mock shift operations with FastAPI endpoints and tenant-level shift policies.
-->
