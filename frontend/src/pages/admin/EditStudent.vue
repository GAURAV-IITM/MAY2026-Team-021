<template>
  <section class="edit-student-page" aria-labelledby="edit-student-title">
    <header class="edit-student-page__header">
      <div>
        <RouterLink
          class="edit-student-page__back-link"
          :to="{ name: 'adminStudents' }"
        >
          <ArrowLeft :size="17" aria-hidden="true" /> Back to Students
        </RouterLink>

        <h1 id="edit-student-title" class="text-h2 edit-student-page__title">
          Edit Student
        </h1>

        <p class="edit-student-page__description">
          Update the student profile, status, and monthly fee.
        </p>
      </div>
    </header>

    <div v-if="errorMessage" class="alert alert--danger" role="alert">
      <div>
        <strong>Unable to process student information.</strong>
        <p class="m-0">{{ errorMessage }}</p>
      </div>

      <button
        class="btn btn--secondary btn--sm"
        type="button"
        @click="studentStore.clearError"
      >
        Dismiss
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

    <div
      v-if="isLoading && !selectedStudent"
      class="edit-student-page__loading"
    >
      <LoadingSpinner label="Loading student information" />
    </div>

    <StudentForm
      v-else-if="selectedStudent"
      :key="studentFormKey"
      :initial-values="selectedStudent"
      :is-submitting="isLoading"
      :enable-seat-assignment="true"
      :shifts="studyShifts"
      :allocation-availability="allocationAvailability"
      :is-availability-loading="isAvailabilityLoading"
      :availability-error="seatAvailabilityError"
      submit-label="Save Changes"
      submitting-label="Saving Changes"
      @availability-request="loadSeatAvailability"
      @availability-clear="seatStore.clearAllocationAvailability"
      @submit="handleUpdateStudent"
      @cancel="handleCancel"
    />
  </section>
</template>

<script setup>
import { ArrowLeft } from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import StudentForm from '../../components/student/StudentForm.vue'
import { useSeatStore } from '../../stores/seatStore'
import { useStudentStore } from '../../stores/studentStore'

const SUCCESS_REDIRECT_DELAY_MS = 700

const route = useRoute()
const router = useRouter()
const studentStore = useStudentStore()
const seatStore = useSeatStore()

const { selectedStudent, isLoading, errorMessage } = storeToRefs(studentStore)
const {
  studyShifts,
  allocationAvailability,
  isAvailabilityLoading,
  availabilityErrorMessage,
  errorMessage: seatErrorMessage,
} = storeToRefs(seatStore)

const successMessage = ref('')
let redirectTimer = null

const studentId = computed(() => String(route.params.studentId))
const studentFormKey = computed(() => {
  return `${selectedStudent.value?.id}:${selectedStudent.value?.updatedAt || ''}`
})
const seatAvailabilityError = computed(() => {
  return availabilityErrorMessage.value || seatErrorMessage.value
})

async function loadStudent() {
  studentStore.clearSelectedStudent()
  try {
    await studentStore.fetchStudentById(studentId.value)
  } catch {
    // Store-owned error state is rendered above the page content.
  }
}

async function loadSeatAvailability(filters) {
  try {
    await seatStore.fetchAllocationAvailability({
      ...filters,
      excludeStudentId: studentId.value,
    })
  } catch {
    // The form renders the seat-store error next to the seat selector.
  }
}

async function handleUpdateStudent(studentData) {
  successMessage.value = ''

  try {
    const response = await studentStore.updateStudent(
      studentId.value,
      studentData,
    )

    const updatedStudent = response.data

    const allocationMessage = studentData.seatAllocationChange
      ? ' The seat allocation was updated and its history was preserved.'
      : ''
    successMessage.value =
      `${updatedStudent.firstName} ${updatedStudent.lastName} was updated successfully.` +
      allocationMessage

    redirectTimer = window.setTimeout(() => {
      router.push({
        name: 'adminStudentDetails',
        params: { studentId: updatedStudent.id },
      })
    }, SUCCESS_REDIRECT_DELAY_MS)
  } catch {
    // Store-owned error state is rendered above the form.
  }
}

function handleCancel() {
  router.push({
    name: 'adminStudentDetails',
    params: { studentId: studentId.value },
  })
}

onMounted(async () => {
  await Promise.allSettled([
    loadStudent(),
    seatStore.fetchShifts(),
  ])
})

onBeforeUnmount(() => {
  if (redirectTimer) {
    window.clearTimeout(redirectTimer)
  }

  studentStore.clearSelectedStudent()
  studentStore.clearError()
  seatStore.clearAllocationAvailability()
  seatStore.clearError()
})
</script>

<style scoped>
.edit-student-page {
  display: grid;
  gap: var(--space-6);
}

.edit-student-page__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-5);
}

.edit-student-page__back-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
  font-weight: var(--font-weight-medium);
}

.edit-student-page__title,
.edit-student-page__description {
  margin: 0;
}

.edit-student-page__description {
  margin-top: var(--space-2);
  color: var(--color-text-muted);
}

.edit-student-page__loading {
  display: grid;
  min-height: 280px;
  place-items: center;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface-elevated);
}
</style>

<!--
src/pages/admin: Student editing page.

Responsibilities:
- Load the existing student using the route parameter.
- Populate the reusable StudentForm with existing student data.
- Validate changes through the shared form component.
- Update the student through the centralized student store.
- Display service errors and successful update feedback.
- Redirect to the updated Student Details page.
-->
