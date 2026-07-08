<template>
  <section class="students-page" aria-labelledby="students-title">
    <header class="students-page__header">
      <div>
        <p class="text-label text-muted students-page__eyebrow">Student Management</p>
        <h1 id="students-title" class="text-h2 students-page__title">Students</h1>
        <p class="text-body students-page__description">
          View, search, filter, and manage registered students.
        </p>
      </div>

      <RouterLink class="btn btn--primary students-page__add-button" :to="{ name: 'adminAddStudent' }">
        Add Student
      </RouterLink>
    </header>

    <section class="students-page__summary" aria-label="Student summary">
      <article class="stat-card stat-card--dashboard">
        <div class="stat-card__header">
          <span class="text-label text-muted">Total Students</span>
          <span class="stat-card__icon" aria-hidden="true">T</span>
        </div>
        <strong class="stat-card__value">{{ studentCount }}</strong>
      </article>

      <article class="stat-card stat-card--dashboard">
        <div class="stat-card__header">
          <span class="text-label text-muted">Active Students</span>
          <span class="stat-card__icon" aria-hidden="true">A</span>
        </div>
        <strong class="stat-card__value">{{ activeStudentCount }}</strong>
      </article>

      <article class="stat-card stat-card--dashboard">
        <div class="stat-card__header">
          <span class="text-label text-muted">Inactive Students</span>
          <span class="stat-card__icon" aria-hidden="true">I</span>
        </div>
        <strong class="stat-card__value">{{ inactiveStudentCount }}</strong>
      </article>
    </section>

    <section class="students-page__filters card" aria-label="Student filters">
      <div class="students-page__search">
        <SearchBar
          v-model="searchQuery"
          placeholder="Search by student name or seat number"
          @clear="clearSearch"
        />
      </div>

      <div class="students-page__filter">
        <label class="form-label" for="status-filter">Status</label>
        <select id="status-filter" v-model="statusFilter" class="form-select">
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
      </div>

      <div class="students-page__filter">
        <label class="form-label" for="shift-filter">Shift</label>
        <select id="shift-filter" v-model="shiftFilter" class="form-select">
          <option value="">All shifts</option>
          <option
            v-for="shift in shiftOptions"
            :key="shift.value"
            :value="shift.value"
          >
            {{ shift.label }}
          </option>
        </select>
      </div>

      <button
        class="btn btn--secondary students-page__clear-button"
        type="button"
        :disabled="!hasActiveFilters"
        @click="clearFilters"
      >
        Clear Filters
      </button>
    </section>

    <div v-if="errorMessage" class="alert alert--danger" role="alert">
      <div>
        <strong>Unable to load students.</strong>
        <p class="m-0">{{ errorMessage }}</p>
      </div>

      <button class="btn btn--secondary btn--sm" type="button" @click="loadStudents">
        Retry
      </button>
    </div>

    <div v-if="isLoading && students.length === 0" class="students-page__loading">
      <LoadingSpinner label="Loading students" />
    </div>

    <template v-else-if="!errorMessage">
      <EmptyState
        v-if="filteredStudents.length === 0"
        title="No students found"
        :description="emptyStateDescription"
      >
        <template #primary-action>
          <button
            v-if="hasActiveFilters"
            class="btn btn--primary"
            type="button"
            @click="clearFilters"
          >
            Clear Filters
          </button>

          <RouterLink v-else class="btn btn--primary" :to="{ name: 'adminAddStudent' }">
            Add Student
          </RouterLink>
        </template>

        <template #secondary-action>
          <span></span>
        </template>
      </EmptyState>

      <template v-else>
        <DataTable
          :columns="columns"
          :rows="paginatedStudents"
          aria-label="Registered students"
        >
          <template #cell-name="{ row }">
            <div class="students-page__student">
              <strong>{{ getStudentFullName(row) }}</strong>
              <span class="text-caption text-muted">{{ row.email }}</span>
            </div>
          </template>

          <template #cell-shift="{ row }">
            {{ formatShiftList(row) }}
          </template>

          <template #cell-status="{ value }">
            <span class="badge" :class="`badge--${value}`">
              {{ formatLabel(value) }}
            </span>
          </template>

          <template #cell-feeStatus="{ value }">
            <span class="badge" :class="getFeeStatusClass(value)">
              {{ formatLabel(value) }}
            </span>
          </template>

          <template #actions="{ row }">
            <div class="students-page__row-actions">
              <RouterLink
                class="btn btn--secondary btn--sm"
                :to="{ name: 'adminStudentDetails', params: { studentId: row.id } }"
              >
                View
              </RouterLink>

              <RouterLink
                class="btn btn--outline btn--sm"
                :to="{ name: 'adminEditStudent', params: { studentId: row.id } }"
              >
                Edit
              </RouterLink>
            </div>
          </template>
        </DataTable>

        <footer class="students-page__pagination">
          <p class="text-small text-muted m-0">
            Showing {{ paginationStart }}–{{ paginationEnd }} of
            {{ filteredStudents.length }} students
          </p>

          <Pagination
            v-model:current-page="currentPage"
            :total-pages="totalPages"
          />
        </footer>
      </template>
    </template>
  </section>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'

import DataTable from '../../components/common/DataTable.vue'
import EmptyState from '../../components/common/EmptyState.vue'
import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import Pagination from '../../components/common/Pagination.vue'
import SearchBar from '../../components/common/SearchBar.vue'
import { shiftMock } from '../../mocks/seatMock'
import { useStudentStore } from '../../stores/studentStore'

const PAGE_SIZE = 5

const columns = Object.freeze([
  { key: 'name', label: 'Student' },
  { key: 'seatNumber', label: 'Seat' },
  { key: 'shift', label: 'Shift' },
  { key: 'status', label: 'Status' },
  { key: 'feeStatus', label: 'Fee Status' },
])

const studentStore = useStudentStore()

const {
  students,
  isLoading,
  errorMessage,
  studentCount,
  activeStudentCount,
  inactiveStudentCount,
} = storeToRefs(studentStore)

const searchQuery = ref('')
const statusFilter = ref('')
const shiftFilter = ref('')
const currentPage = ref(1)

const shiftOptions = computed(() => {
  return shiftMock
    .filter((shift) => shift.isEnabled !== false)
    .map((shift) => ({
      value: shift.id,
      label: shift.name,
    }))
})

const hasActiveFilters = computed(() => {
  return Boolean(searchQuery.value.trim() || statusFilter.value || shiftFilter.value)
})

const filteredStudents = computed(() => {
  const normalizedQuery = searchQuery.value.trim().toLowerCase()

  return students.value.filter((student) => {
    const fullName = getStudentFullName(student).toLowerCase()
    const seatNumber = String(student.seatNumber || '').toLowerCase()

    const matchesSearch =
      !normalizedQuery ||
      fullName.includes(normalizedQuery) ||
      seatNumber.includes(normalizedQuery)

    const matchesStatus = !statusFilter.value || student.status === statusFilter.value
    const matchesShift =
      !shiftFilter.value || getStudentShifts(student).includes(shiftFilter.value)

    return matchesSearch && matchesStatus && matchesShift
  })
})

const totalPages = computed(() => {
  return Math.max(1, Math.ceil(filteredStudents.value.length / PAGE_SIZE))
})

const paginatedStudents = computed(() => {
  const startIndex = (currentPage.value - 1) * PAGE_SIZE

  return filteredStudents.value.slice(startIndex, startIndex + PAGE_SIZE)
})

const paginationStart = computed(() => {
  if (filteredStudents.value.length === 0) return 0
  return (currentPage.value - 1) * PAGE_SIZE + 1
})

const paginationEnd = computed(() => {
  return Math.min(currentPage.value * PAGE_SIZE, filteredStudents.value.length)
})

const emptyStateDescription = computed(() => {
  if (hasActiveFilters.value) {
    return 'No student records match the current search and filters.'
  }

  return 'Registered students will appear here after they are added.'
})

watch([searchQuery, statusFilter, shiftFilter], () => {
  currentPage.value = 1
})

watch(totalPages, (pageCount) => {
  if (currentPage.value > pageCount) {
    currentPage.value = pageCount
  }
})

function getStudentFullName(student) {
  return `${student.firstName || ''} ${student.lastName || ''}`.trim()
}

function formatLabel(value) {
  if (!value) return '—'

  return String(value)
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())
}

function getStudentShifts(student) {
  if (Array.isArray(student.activeShifts) && student.activeShifts.length > 0) {
    return student.activeShifts
  }

  return student.shift ? [student.shift] : []
}

function formatShiftList(student) {
  const shifts = getStudentShifts(student)

  if (shifts.length === 0) return '—'

  return shifts.map((shift) => formatLabel(shift)).join(', ')
}

function getFeeStatusClass(status) {
  if (status === 'paid') return 'badge--paid'
  if (status === 'overdue') return 'badge--inactive'
  return 'badge--pending'
}

function clearSearch() {
  searchQuery.value = ''
}

function clearFilters() {
  searchQuery.value = ''
  statusFilter.value = ''
  shiftFilter.value = ''
}

async function loadStudents() {
  try {
    await studentStore.fetchStudents()
  } catch {
    // Store-owned error state is rendered above the table.
  }
}

onMounted(loadStudents)
</script>

<style scoped>
.students-page {
  display: grid;
  gap: var(--space-6);
}

.students-page__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-5);
}

.students-page__eyebrow,
.students-page__title,
.students-page__description {
  margin: 0;
}

.students-page__title {
  margin-top: var(--space-1);
}

.students-page__description {
  margin-top: var(--space-2);
  color: var(--color-text-muted);
}

.students-page__summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-4);
}

.students-page__filters {
  display: grid;
  grid-template-columns: minmax(240px, 1fr) minmax(150px, 200px) minmax(150px, 200px) auto;
  align-items: end;
  gap: var(--space-4);
  padding: var(--space-4);
}

.students-page__search {
  align-self: end;
}

.students-page__search :deep(.search-bar) {
  max-width: none;
}

.students-page__filter {
  display: grid;
  gap: var(--space-2);
}

.students-page__clear-button {
  white-space: nowrap;
}

.students-page__loading {
  display: grid;
  min-height: 240px;
  place-items: center;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface-elevated);
}

.students-page__student {
  display: grid;
  gap: var(--space-1);
  min-width: 180px;
}

.students-page__row-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.students-page__pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
}

@media (max-width: 1000px) {
  .students-page__filters {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .students-page__search {
    grid-column: 1 / -1;
  }
}

@media (max-width: 768px) {
  .students-page__header,
  .students-page__pagination {
    align-items: stretch;
    flex-direction: column;
  }

  .students-page__summary {
    grid-template-columns: 1fr;
  }

  .students-page__add-button {
    align-self: flex-start;
  }
}

@media (max-width: 480px) {
  .students-page__filters {
    grid-template-columns: 1fr;
  }

  .students-page__search {
    grid-column: auto;
  }

  .students-page__row-actions .btn {
    width: auto;
  }

  .students-page__pagination :deep(.pagination) {
    justify-content: space-between;
  }
}
</style>

<!--
src/pages/admin: Student listing and management entry page.

Responsibilities:
- Fetch student records through the centralized student store.
- Search students by name and seat number.
- Filter students by status and shift.
- Paginate filtered student records.
- Navigate to Add, View, and Edit Student pages.

Milestone 3:
- Search, filtering, and pagination can move to backend query parameters without requiring major UI changes.
-->
