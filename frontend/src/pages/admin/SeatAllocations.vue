<template>
  <section class="allocations-page" aria-labelledby="allocations-title">
    <header class="allocations-page__header">
      <div>
        <p class="text-label text-muted m-0">Seat Operations</p>
        <h1 id="allocations-title" class="text-h2 allocations-page__title">
          Allocation History
        </h1>
        <p class="text-body text-muted m-0">
          Review current and historical seat assignments without deleting records.
        </p>
      </div>
      <div class="allocations-page__actions">
        <RouterLink class="btn btn--primary" :to="{ name: 'adminSeatMap' }">
          <Plus :size="17" aria-hidden="true" /> New Allocation
        </RouterLink>
        <button class="btn btn--secondary" type="button" :disabled="isAllocationLoading" @click="load">
          <RefreshCw :size="17" aria-hidden="true" /> Refresh
        </button>
      </div>
    </header>

    <Toast v-if="toastMessage" :type="toastType">{{ toastMessage }}</Toast>

    <div v-if="allocationErrorMessage" class="alert alert--danger" role="alert">
      <div>
        <strong>Unable to complete the allocation request.</strong>
        <p class="m-0">{{ allocationErrorMessage }}</p>
      </div>
      <button class="btn btn--secondary btn--sm" type="button" @click="load">Retry</button>
    </div>

    <section class="card allocations-page__filters" aria-label="Allocation filters">
      <div class="form-field allocations-page__search">
        <label class="form-label" for="allocation-search">Search</label>
        <input
          id="allocation-search"
          v-model.trim="filters.search"
          class="form-input"
          type="search"
          placeholder="Student, enrollment, seat, or shift"
          @keyup.enter="applyFilters"
        />
      </div>
      <div class="form-field">
        <label class="form-label" for="allocation-status">Status</label>
        <select id="allocation-status" v-model="filters.status" class="form-select">
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>
      <div class="form-field">
        <label class="form-label" for="allocation-shift">Shift</label>
        <select id="allocation-shift" v-model="filters.shiftId" class="form-select">
          <option value="">All shifts</option>
          <option v-for="shift in enabledShifts" :key="shift.id" :value="shift.id">
            {{ shift.name }}
          </option>
        </select>
      </div>
      <div class="form-field">
        <label class="form-label" for="allocation-student">Student</label>
        <select id="allocation-student" v-model="filters.studentId" class="form-select">
          <option value="">All students</option>
          <option v-for="student in students" :key="student.id" :value="student.id">
            {{ studentName(student) }}
          </option>
        </select>
      </div>
      <div class="form-field">
        <label class="form-label" for="allocation-from">Overlaps from</label>
        <input id="allocation-from" v-model="filters.startDate" class="form-input" type="date" />
      </div>
      <div class="form-field">
        <label class="form-label" for="allocation-to">Overlaps through</label>
        <input
          id="allocation-to"
          v-model="filters.endDate"
          class="form-input"
          type="date"
          :min="filters.startDate"
        />
      </div>
      <div class="allocations-page__filter-actions">
        <button class="btn btn--primary" type="button" @click="applyFilters">
          <Search :size="17" aria-hidden="true" /> Apply
        </button>
        <button class="btn btn--secondary" type="button" @click="resetFilters">
          <RotateCcw :size="17" aria-hidden="true" /> Reset
        </button>
      </div>
    </section>

    <section class="card allocations-page__table-card">
      <header class="card__header">
        <div>
          <h2 class="text-h4 m-0">Seat Allocations</h2>
          <p class="text-small text-muted m-0">{{ allocationMeta.totalItems }} records</p>
        </div>
      </header>
      <div class="card__body allocations-page__table-body">
        <LoadingSpinner v-if="isAllocationLoading" label="Loading allocations" />
        <template v-else>
          <DataTable
            :columns="columns"
            :rows="allocations"
            aria-label="Seat allocation history"
          >
            <template #cell-seat="{ row }">
              <strong>{{ row.seat.seatNumber }}</strong>
              <small>{{ row.seat.floorName }}</small>
            </template>
            <template #cell-student="{ row }">
              <strong>{{ row.student.name }}</strong>
              <small>{{ row.student.enrollmentNumber }}</small>
            </template>
            <template #cell-shift="{ row }">
              <strong>{{ row.shift.name }}</strong>
              <small>{{ row.shift.startTime }}-{{ row.shift.endTime }}</small>
            </template>
            <template #cell-period="{ row }">
              {{ row.startDate }} to {{ row.endDate }}
            </template>
            <template #cell-status="{ row }">
              <span class="badge" :class="statusClass(row.status)">
                {{ label(row.status) }}
              </span>
            </template>
            <template #cell-actor="{ row }">
              {{ row.allocatedBy?.name || 'System' }}
            </template>
            <template #actions="{ row }">
              <button
                v-if="row.status === 'active'"
                class="btn btn--secondary btn--sm"
                type="button"
                @click="openCloseModal(row)"
              >
                Close
              </button>
              <span v-else class="text-small text-muted">
                {{ row.closeReason || 'Closed' }}
              </span>
            </template>
            <template #empty>No allocation records match these filters.</template>
          </DataTable>
          <Pagination
            :current-page="allocationMeta.page"
            :total-pages="allocationMeta.totalPages"
            @update:current-page="changePage"
          />
        </template>
      </div>
    </section>

    <CloseAllocationModal
      :is-open="Boolean(selectedAllocation)"
      :allocation="selectedAllocation"
      :is-submitting="isAllocationSubmitting"
      @close="selectedAllocation = null"
      @confirm="closeAllocation"
    />
  </section>
</template>

<script setup>
import { Plus, RefreshCw, RotateCcw, Search } from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'

import DataTable from '../../components/common/DataTable.vue'
import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import Pagination from '../../components/common/Pagination.vue'
import Toast from '../../components/common/Toast.vue'
import CloseAllocationModal from '../../components/seat/CloseAllocationModal.vue'
import { useSeatStore } from '../../stores/seatStore'
import { useStudentStore } from '../../stores/studentStore'

const columns = [
  { key: 'seat', label: 'Seat' },
  { key: 'student', label: 'Student' },
  { key: 'shift', label: 'Shift' },
  { key: 'period', label: 'Period' },
  { key: 'status', label: 'Status' },
  { key: 'actor', label: 'Allocated By' },
]
const seatStore = useSeatStore()
const studentStore = useStudentStore()
const filters = reactive({
  page: 1,
  pageSize: 20,
  search: '',
  status: '',
  shiftId: '',
  studentId: '',
  startDate: '',
  endDate: '',
})
const selectedAllocation = ref(null)
const toastMessage = ref('')
const toastType = ref('success')
let toastTimer

const {
  allocations,
  allocationMeta,
  studyShifts,
  isAllocationLoading,
  isAllocationSubmitting,
  allocationErrorMessage,
} = storeToRefs(seatStore)
const { students } = storeToRefs(studentStore)
const enabledShifts = computed(() =>
  studyShifts.value.filter((shift) => shift.isEnabled !== false),
)

async function initialize() {
  try {
    await Promise.all([
      seatStore.fetchShifts(),
      studentStore.fetchStudents(),
    ])
    await load()
  } catch {
    // Store error state is rendered above.
  }
}

async function load() {
  try {
    await seatStore.fetchAllocations({ ...filters })
  } catch {
    // Store error state is rendered above.
  }
}

async function applyFilters() {
  filters.page = 1
  await load()
}

async function resetFilters() {
  Object.assign(filters, {
    page: 1,
    pageSize: 20,
    search: '',
    status: '',
    shiftId: '',
    studentId: '',
    startDate: '',
    endDate: '',
  })
  await load()
}

async function changePage(page) {
  filters.page = page
  await load()
}

function openCloseModal(allocation) {
  seatStore.clearAllocationError()
  selectedAllocation.value = allocation
}

async function closeAllocation(payload) {
  try {
    await seatStore.closeAllocation(selectedAllocation.value.id, payload)
    selectedAllocation.value = null
    showToast(`Allocation ${payload.status}.`)
    await load()
  } catch {
    showToast(allocationErrorMessage.value, 'error')
  }
}

function studentName(student) {
  return [student.firstName, student.lastName].filter(Boolean).join(' ')
}

function label(value) {
  return String(value || '').replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function statusClass(status) {
  if (status === 'active') return 'badge--success'
  if (status === 'cancelled') return 'allocations-page__badge--cancelled'
  return 'badge--inactive'
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
.allocations-page {
  display: grid;
  gap: var(--space-6);
}

.allocations-page__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-5);
}

.allocations-page__title {
  margin: var(--space-1) 0;
}

.allocations-page__actions,
.allocations-page__filter-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.allocations-page__filters {
  display: grid;
  grid-template-columns: minmax(220px, 2fr) repeat(5, minmax(140px, 1fr));
  align-items: end;
  gap: var(--space-3);
  padding: var(--space-4);
}

.allocations-page__filter-actions {
  grid-column: 1 / -1;
  justify-content: flex-end;
}

.allocations-page__table-body {
  display: grid;
  gap: var(--space-4);
}

.data-table strong,
.data-table small {
  display: block;
}

.allocations-page__badge--cancelled {
  background: var(--color-danger-light);
  color: var(--color-danger);
}

.data-table small {
  margin-top: var(--space-1);
  color: var(--color-text-muted);
}

@media (max-width: 1100px) {
  .allocations-page__filters {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .allocations-page__header {
    flex-direction: column;
  }

  .allocations-page__filters {
    grid-template-columns: 1fr;
  }

  .allocations-page__filter-actions {
    grid-column: auto;
    justify-content: flex-start;
  }
}
</style>
