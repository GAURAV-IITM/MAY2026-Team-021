<template>
  <section class="add-student-page" aria-labelledby="add-student-title">
    <header class="add-student-page__header">
      <div>
        <RouterLink
          class="add-student-page__back-link"
          :to="{ name: 'adminStudents' }"
        >
          <ArrowLeft :size="17" aria-hidden="true" /> Back to Students
        </RouterLink>

        <h1 id="add-student-title" class="text-h2 add-student-page__title">
          Add Student
        </h1>

        <p class="add-student-page__description">
          Register a student and create their portal invitation.
        </p>
      </div>
    </header>

    <div v-if="errorMessage" class="alert alert--danger" role="alert">
      <div>
        <strong>Unable to add student.</strong>
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

    <StudentForm
      :is-submitting="isLoading"
      submit-label="Add Student"
      submitting-label="Adding Student"
      @submit="handleCreateStudent"
      @cancel="handleCancel"
    />
  </section>
</template>

<script setup>
import { ArrowLeft } from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { onBeforeUnmount, ref } from 'vue'
import { RouterLink, useRouter } from 'vue-router'

import StudentForm from '../../components/student/StudentForm.vue'
import { useStudentStore } from '../../stores/studentStore'

const SUCCESS_REDIRECT_DELAY_MS = 700

const router = useRouter()
const studentStore = useStudentStore()

const { isLoading, errorMessage } = storeToRefs(studentStore)

const successMessage = ref('')
let redirectTimer = null

async function handleCreateStudent(studentData) {
  successMessage.value = ''

  try {
    const response = await studentStore.createStudent(studentData)
    const createdStudent = response.data

    successMessage.value = `${createdStudent.firstName} ${createdStudent.lastName} was added successfully.`

    redirectTimer = window.setTimeout(() => {
      router.push({
        name: 'adminStudentDetails',
        params: { studentId: createdStudent.id },
        state: { setupLink: createdStudent.invitationSetupUrl || '' },
      })
    }, SUCCESS_REDIRECT_DELAY_MS)
  } catch {
    // Store-owned error state is rendered above the form.
  }
}

function handleCancel() {
  router.push({ name: 'adminStudents' })
}

onBeforeUnmount(() => {
  if (redirectTimer) {
    window.clearTimeout(redirectTimer)
  }

  studentStore.clearError()
})
</script>

<style scoped>
.add-student-page {
  display: grid;
  gap: var(--space-6);
}

.add-student-page__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-5);
}

.add-student-page__back-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
  font-weight: var(--font-weight-medium);
}

.add-student-page__title,
.add-student-page__description {
  margin: 0;
}

.add-student-page__description {
  margin-top: var(--space-2);
  color: var(--color-text-muted);
}
</style>

<!--
src/pages/admin: Student registration page.

Responsibilities:
- Render the reusable StudentForm.
- Create student records through the centralized student store.
- Display service errors and successful creation feedback.
- Redirect to the newly created Student Details page.
-->
