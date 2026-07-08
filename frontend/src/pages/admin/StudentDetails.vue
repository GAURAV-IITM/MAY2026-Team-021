<template>
  <section class="student-details-page" aria-labelledby="student-details-title">
    <header class="student-details-page__header">
      <div>
        <RouterLink
          class="student-details-page__back-link"
          :to="{ name: 'adminStudents' }"
        >
          ← Back to Students
        </RouterLink>

        <h1 id="student-details-title" class="text-h2 student-details-page__title">
          Student Details
        </h1>

        <p class="student-details-page__description">
          View the complete student profile and library information.
        </p>
      </div>

      <div v-if="selectedStudent" class="student-details-page__actions">
  <RouterLink
    class="btn btn--primary"
    :to="{
      name: 'adminEditStudent',
      params: { studentId: selectedStudent.id },
    }"
  >
    Edit Student
  </RouterLink>

  <button
    v-if="selectedStudent.status === 'active'"
    class="btn btn--danger"
    type="button"
    :disabled="isLoading"
    @click="showDeactivateDialog = true"
  >
    Deactivate Student
  </button>
</div>
    </header>

    <div v-if="errorMessage" class="alert alert--danger" role="alert">
  <div>
    <strong>Unable to load student.</strong>
    <p class="m-0">{{ errorMessage }}</p>
  </div>

  <button class="btn btn--secondary btn--sm" type="button" @click="loadStudent">
    Retry
  </button>
</div>

<div
  v-if="successMessage"
  class="alert alert--success"
  role="status"
  aria-live="polite"
>
  <p class="m-0">{{ successMessage }}</p>
</div>

    <div v-if="isLoading && !selectedStudent" class="student-details-page__loading">
      <LoadingSpinner label="Loading student details" />
    </div>

    <template v-else-if="selectedStudent && !errorMessage">
      <section class="student-details-page__profile card" aria-label="Student profile">
        <div class="student-details-page__avatar" aria-hidden="true">
          {{ studentInitials }}
        </div>

        <div class="student-details-page__identity">
          <h2 class="text-h3 m-0">{{ studentFullName }}</h2>
          <p class="text-muted m-0">{{ selectedStudent.email }}</p>

          <div class="student-details-page__badges">
            <span
              class="badge"
              :class="`badge--${selectedStudent.status}`"
            >
              {{ formatLabel(selectedStudent.status) }}
            </span>

            <span class="badge badge--neutral">
              Seat {{ selectedStudent.seatNumber }}
            </span>
          </div>
        </div>
      </section>

      <div class="student-details-page__grid">
        <section class="card student-details-page__section">
          <header class="student-details-page__section-header">
            <h2 class="text-h5 m-0">Personal Information</h2>
          </header>

          <dl class="student-details-page__details">
            <div>
              <dt>First Name</dt>
              <dd>{{ displayValue(selectedStudent.firstName) }}</dd>
            </div>

            <div>
              <dt>Last Name</dt>
              <dd>{{ displayValue(selectedStudent.lastName) }}</dd>
            </div>

            <div>
              <dt>Joining Date</dt>
              <dd>{{ formatDate(selectedStudent.joiningDate) }}</dd>
            </div>

            <div class="student-details-page__full-row">
              <dt>Address</dt>
              <dd>{{ displayValue(selectedStudent.address) }}</dd>
            </div>
          </dl>
        </section>

        <section class="card student-details-page__section">
          <header class="student-details-page__section-header">
            <h2 class="text-h5 m-0">Contact Information</h2>
          </header>

          <dl class="student-details-page__details">
            <div>
              <dt>Email</dt>
              <dd>{{ displayValue(selectedStudent.email) }}</dd>
            </div>

            <div>
              <dt>Phone</dt>
              <dd>{{ displayValue(selectedStudent.phone) }}</dd>
            </div>

            <div>
              <dt>Guardian Name</dt>
              <dd>{{ displayValue(selectedStudent.guardianName) }}</dd>
            </div>

            <div>
              <dt>Guardian Phone</dt>
              <dd>{{ displayValue(selectedStudent.guardianPhone) }}</dd>
            </div>
          </dl>
        </section>

        <section class="card student-details-page__section">
          <header class="student-details-page__section-header">
            <h2 class="text-h5 m-0">Seat & Shift Information</h2>
          </header>

          <dl class="student-details-page__details">
            <div>
              <dt>Seat Number</dt>
              <dd>{{ displayValue(selectedStudent.seatNumber) }}</dd>
            </div>

            <div>
              <dt>Shifts</dt>
              <dd>{{ formatShiftList(selectedStudent) }}</dd>
            </div>
          </dl>
        </section>

        <section class="card student-details-page__section">
          <header class="student-details-page__section-header">
            <h2 class="text-h5 m-0">Payment Summary</h2>
          </header>

          <dl class="student-details-page__details">
            <div>
              <dt>Fee Amount</dt>
              <dd>{{ formatCurrency(selectedStudent.feeAmount) }}</dd>
            </div>

            <div>
              <dt>Fee Status</dt>
              <dd>
                <span
                  class="badge"
                  :class="getFeeStatusClass(selectedStudent.feeStatus)"
                >
                  {{ formatLabel(selectedStudent.feeStatus) }}
                </span>
              </dd>
            </div>

            <div>
              <dt>Fee Due Date</dt>
              <dd>{{ formatDate(selectedStudent.feeDueDate) }}</dd>
            </div>

            <div>
              <dt>Payment History</dt>
              <dd class="text-muted">Payment history will be available in the Payments module.</dd>
            </div>
          </dl>
        </section>
            </div>
          </template>

    <ConfirmDialog
      :is-open="showDeactivateDialog"
      title="Deactivate Student"
      :message="deactivateMessage"
      confirm-label="Deactivate"
      confirming-label="Deactivating"
      :is-confirming="isLoading"
      @confirm="handleDeactivateStudent"
      @cancel="showDeactivateDialog = false"
    />
  </section>
</template>


<script setup>
import { storeToRefs } from 'pinia'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

import ConfirmDialog from '../../components/common/ConfirmDialog.vue'
import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import { useStudentStore } from '../../stores/studentStore'

const route = useRoute()
const studentStore = useStudentStore()

const { selectedStudent, isLoading, errorMessage } = storeToRefs(studentStore)

const studentId = computed(() => String(route.params.studentId))

const showDeactivateDialog = ref(false)
const successMessage = ref('')

const studentFullName = computed(() => {
  if (!selectedStudent.value) return ''

  return `${selectedStudent.value.firstName || ''} ${
    selectedStudent.value.lastName || ''
  }`.trim()
})

const deactivateMessage = computed(() => {
  if (!selectedStudent.value) {
    return 'Are you sure you want to deactivate this student?'
  }

  return `Are you sure you want to deactivate ${studentFullName.value}? The student record will remain available but will be marked as inactive.`
})

const studentInitials = computed(() => {
  if (!selectedStudent.value) return ''

  return [selectedStudent.value.firstName, selectedStudent.value.lastName]
    .filter(Boolean)
    .map((name) => name.charAt(0).toUpperCase())
    .join('')
})

function displayValue(value) {
  return value || '—'
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

  return student?.shift ? [student.shift] : []
}

function formatShiftList(student) {
  const shifts = getStudentShifts(student)

  if (shifts.length === 0) return '—'

  return shifts.map((shift) => formatLabel(shift)).join(', ')
}

function formatDate(value) {
  if (!value) return '—'

  const date = new Date(`${value}T00:00:00`)

  if (Number.isNaN(date.getTime())) return value

  return new Intl.DateTimeFormat('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(date)
}

function formatCurrency(value) {
  const amount = Number(value)

  if (!Number.isFinite(amount)) return '—'

  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount)
}

function getFeeStatusClass(status) {
  if (status === 'paid') return 'badge--paid'
  if (status === 'overdue') return 'badge--inactive'
  return 'badge--pending'
}

async function loadStudent() {
  try {
    await studentStore.fetchStudentById(studentId.value)
  } catch {
    // Store-owned error state is rendered above the details content.
  }
}

async function handleDeactivateStudent() {
  successMessage.value = ''

  try {
    const response = await studentStore.deactivateStudent(studentId.value)

    showDeactivateDialog.value = false
    successMessage.value = response.message
  } catch {
    showDeactivateDialog.value = false
    // Store-owned error state is rendered above the details content.
  }
}

onMounted(loadStudent)

onBeforeUnmount(() => {
  showDeactivateDialog.value = false
  studentStore.clearSelectedStudent()
  studentStore.clearError()
})


</script>

<style scoped>
.student-details-page {
  display: grid;
  gap: var(--space-6);
}

.student-details-page__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-5);
}

.student-details-page__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: var(--space-3);
}

.student-details-page__back-link {
  display: inline-flex;
  margin-bottom: var(--space-3);
  font-weight: var(--font-weight-medium);
}

.student-details-page__title,
.student-details-page__description {
  margin: 0;
}

.student-details-page__description {
  margin-top: var(--space-2);
  color: var(--color-text-muted);
}

.student-details-page__loading {
  display: grid;
  min-height: 280px;
  place-items: center;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface-elevated);
}

.student-details-page__profile {
  display: flex;
  align-items: center;
  gap: var(--space-5);
  padding: var(--space-5);
}

.student-details-page__avatar {
  display: grid;
  flex: 0 0 72px;
  width: 72px;
  height: 72px;
  place-items: center;
  border-radius: 50%;
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-size: var(--font-size-h4);
  font-weight: var(--font-weight-bold);
}

.student-details-page__identity {
  display: grid;
  gap: var(--space-2);
}

.student-details-page__badges {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.student-details-page__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-5);
}

.student-details-page__section {
  padding: var(--space-5);
}

.student-details-page__section-header {
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

.student-details-page__details {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-5);
  margin: var(--space-5) 0 0;
}

.student-details-page__details div {
  min-width: 0;
}

.student-details-page__details dt {
  margin-bottom: var(--space-1);
  color: var(--color-text-muted);
  font-size: var(--font-size-small);
  font-weight: var(--font-weight-medium);
}

.student-details-page__details dd {
  margin: 0;
  overflow-wrap: anywhere;
  color: var(--color-text-primary);
}

.student-details-page__full-row {
  grid-column: 1 / -1;
}

@media (max-width: 900px) {
  .student-details-page__grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .student-details-page__header {
    align-items: stretch;
    flex-direction: column;
  }

    .student-details-page__actions {
    justify-content: stretch;
  }

  .student-details-page__actions .btn {
    width: 100%;
  }

  .student-details-page__profile {
    align-items: flex-start;
    flex-direction: column;
  }

  .student-details-page__details {
    grid-template-columns: 1fr;
  }

  .student-details-page__full-row {
    grid-column: auto;
  }
}
</style>

<!--
src/pages/admin: Complete student profile page.

Responsibilities:
- Load the selected student using the route parameter.
- Display personal, contact, seat, shift, and payment summary information.
- Provide navigation to the Student List and Edit Student pages.
-->
