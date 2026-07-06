<template>
  <Modal
    :is-open="isOpen"
    title="Allocate Seat"
    title-id="seat-allocation-dialog-title"
    @close="handleClose"
  >
    <form class="seat-allocation-dialog" novalidate @submit.prevent="handleSubmit">
      <section class="seat-allocation-dialog__availability" aria-live="polite">
        <div>
          <p class="text-label text-muted m-0">Seat Availability</p>
          <h3 class="text-h5 m-0">{{ availabilityTitle }}</h3>
        </div>

        <span class="badge" :class="availabilityBadgeClass">
          {{ availabilityStatus }}
        </span>
      </section>

      <div class="seat-allocation-dialog__grid">
        <div class="form-field" :class="{ 'form-field--error': errors.studentId }">
          <label class="form-label" for="allocation-student">Student</label>
          <select
            id="allocation-student"
            v-model="form.studentId"
            class="form-select"
            :aria-invalid="Boolean(errors.studentId)"
          >
            <option value="">Select student</option>
            <option
              v-for="student in activeStudents"
              :key="student.id"
              :value="student.id"
            >
              {{ getStudentName(student) }}
            </option>
          </select>
          <p v-if="errors.studentId" class="form-help">{{ errors.studentId }}</p>
        </div>

        <div class="form-field" :class="{ 'form-field--error': errors.seatId }">
          <label class="form-label" for="allocation-seat">Seat</label>
          <select
            id="allocation-seat"
            v-model="form.seatId"
            class="form-select"
            :aria-invalid="Boolean(errors.seatId)"
          >
            <option value="">Select seat</option>
            <option v-for="seat in seats" :key="seat.id" :value="seat.id">
              {{ seat.seatNumber }} · {{ formatLabel(seat.status) }}
            </option>
          </select>
          <p v-if="errors.seatId" class="form-help">{{ errors.seatId }}</p>
        </div>

        <div class="form-field" :class="{ 'form-field--error': errors.shift }">
          <label class="form-label" for="allocation-shift">Shift</label>
          <select
            id="allocation-shift"
            v-model="form.shift"
            class="form-select"
            :aria-invalid="Boolean(errors.shift)"
          >
            <option value="">Select shift</option>
            <option
              v-for="shift in shiftOptions"
              :key="shift.value"
              :value="shift.value"
            >
              {{ shift.label }}
            </option>
          </select>
          <p v-if="errors.shift" class="form-help">{{ errors.shift }}</p>
        </div>

        <div class="form-field seat-allocation-dialog__full-row">
          <label class="form-label" for="allocation-notes">Notes</label>
          <textarea
            id="allocation-notes"
            v-model.trim="form.notes"
            class="form-textarea"
            placeholder="Optional allocation note"
          ></textarea>
        </div>
      </div>
    </form>

    <template #footer>
      <button
        class="btn btn--secondary"
        type="button"
        :disabled="isSubmitting"
        @click="handleClose"
      >
        Cancel
      </button>

      <button
        class="btn btn--primary"
        type="button"
        :disabled="isSubmitting"
        @click="handleSubmit"
      >
        <span v-if="isSubmitting" class="btn__loader" aria-hidden="true"></span>
        <span>{{ isSubmitting ? 'Allocating' : 'Confirm Allocation' }}</span>
      </button>
    </template>
  </Modal>
</template>

<script setup>
import { computed, reactive, watch } from 'vue'

import Modal from '../common/Modal.vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false,
  },
  seats: {
    type: Array,
    default: () => [],
  },
  students: {
    type: Array,
    default: () => [],
  },
  initialSeatId: {
    type: String,
    default: '',
  },
  isSubmitting: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close', 'confirm'])

const shiftOptions = Object.freeze([
  { value: 'morning', label: 'Morning' },
  { value: 'afternoon', label: 'Afternoon' },
  { value: 'evening', label: 'Evening' },
])

const form = reactive({
  studentId: '',
  seatId: '',
  shift: '',
  notes: '',
})

const errors = reactive({})

const selectedSeat = computed(() => {
  return props.seats.find((seat) => seat.id === form.seatId) || null
})

const selectedStudent = computed(() => {
  return props.students.find((student) => student.id === form.studentId) || null
})

const activeStudents = computed(() => {
  return props.students.filter((student) => student.status !== 'inactive')
})

const availabilityStatus = computed(() => {
  if (!selectedSeat.value) return 'Select a seat'

  return formatLabel(selectedSeat.value.status)
})

const availabilityTitle = computed(() => {
  if (!selectedSeat.value) {
    return 'Choose a seat to inspect availability.'
  }

  if (isSeatAvailable(selectedSeat.value)) {
    return `${selectedSeat.value.seatNumber} is available for allocation.`
  }

  return `${selectedSeat.value.seatNumber} cannot be allocated right now.`
})

const availabilityBadgeClass = computed(() => {
  if (!selectedSeat.value) return 'badge--pending'
  if (selectedSeat.value.status === 'available') return 'badge--success'
  if (selectedSeat.value.status === 'maintenance') return 'badge--warning'
  if (selectedSeat.value.status === 'reserved') return 'seat-allocation-dialog__badge--reserved'

  return 'seat-allocation-dialog__badge--occupied'
})

watch(
  () => props.isOpen,
  (isOpen) => {
    if (isOpen) {
      resetForm()
    }
  },
)

watch(
  () => props.initialSeatId,
  (seatId) => {
    if (props.isOpen && seatId) {
      form.seatId = seatId
    }
  },
)

function resetForm() {
  form.studentId = ''
  form.seatId = props.initialSeatId || ''
  form.shift = ''
  form.notes = ''
  clearErrors()
}

function clearErrors() {
  Object.keys(errors).forEach((key) => {
    delete errors[key]
  })
}

function validateForm() {
  clearErrors()

  if (!form.studentId) {
    errors.studentId = 'Select a student.'
  } else if (!selectedStudent.value) {
    errors.studentId = 'Selected student was not found.'
  }

  if (!form.seatId) {
    errors.seatId = 'Select a seat.'
  } else if (!selectedSeat.value) {
    errors.seatId = 'Selected seat was not found.'
  } else if (!isSeatAvailable(selectedSeat.value)) {
    errors.seatId = 'Select an available seat.'
  }

  if (!form.shift) {
    errors.shift = 'Select a shift.'
  }

  return Object.keys(errors).length === 0
}

function isSeatAvailable(seat) {
  return seat?.status === 'available' && !seat.assignedStudent
}

function getStudentName(student) {
  return [student.firstName, student.lastName].filter(Boolean).join(' ')
}

function formatLabel(value) {
  if (!value) return 'Not selected'

  return String(value)
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())
}

function handleSubmit() {
  if (!validateForm()) return

  emit('confirm', {
    seatId: form.seatId,
    assignedStudent: {
      id: selectedStudent.value.id,
      name: getStudentName(selectedStudent.value),
      email: selectedStudent.value.email,
    },
    shift: form.shift,
    notes: form.notes,
  })
}

function handleClose() {
  if (props.isSubmitting) return

  emit('close')
}
</script>

<style scoped>
.seat-allocation-dialog {
  display: grid;
  gap: var(--space-5);
}

.seat-allocation-dialog__availability {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.seat-allocation-dialog__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
}

.seat-allocation-dialog__full-row {
  grid-column: 1 / -1;
}

.form-field--error .form-help {
  color: var(--color-danger);
}

.seat-allocation-dialog__badge--occupied {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.seat-allocation-dialog__badge--reserved {
  background: var(--color-info-light);
  color: var(--color-info);
}

@media (max-width: 680px) {
  .seat-allocation-dialog__availability {
    flex-direction: column;
  }

  .seat-allocation-dialog__grid {
    grid-template-columns: 1fr;
  }

  .seat-allocation-dialog__full-row {
    grid-column: auto;
  }
}
</style>

<!--
src/components/seat: Reusable dialog for mock seat allocation workflows.
TODO:
- Connect this payload to FastAPI allocation endpoints through seatService in Milestone 3.
-->
