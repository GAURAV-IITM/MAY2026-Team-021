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
          <p class="text-label text-muted m-0">Selected Seat</p>
          <h3 class="text-h5 m-0">
            {{ selectedSeat?.seatNumber || 'Choose a seat' }}
          </h3>
          <p class="text-small text-muted m-0">
            Availability is verified again by the server when you confirm.
          </p>
        </div>
        <span class="badge" :class="availabilityBadgeClass">
          {{ availabilityStatus }}
        </span>
      </section>

      <div v-if="submissionError" class="alert alert--danger" role="alert">
        <div>
          <strong>Allocation could not be created.</strong>
          <p class="m-0">{{ submissionError.message }}</p>
          <p v-if="submissionError.requestId" class="text-small m-0">
            Request ID: {{ submissionError.requestId }}
          </p>
        </div>
      </div>

      <div class="seat-allocation-dialog__grid">
        <div class="form-field" :class="{ 'form-field--error': errors.studentId }">
          <label class="form-label" for="allocation-student">Student</label>
          <select
            id="allocation-student"
            v-model="form.studentId"
            class="form-select"
            :aria-invalid="Boolean(errors.studentId)"
          >
            <option value="">Select active student</option>
            <option
              v-for="student in activeStudents"
              :key="student.id"
              :value="student.id"
            >
              {{ getStudentName(student) }}
              <template v-if="student.enrollmentNumber">
                ({{ student.enrollmentNumber }})
              </template>
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
            <option value="">Select available seat</option>
            <option
              v-for="seat in selectableSeats"
              :key="seat.id"
              :value="seat.id"
            >
              {{ seat.seatNumber }} · {{ seat.floorName }}
            </option>
          </select>
          <p v-if="errors.seatId" class="form-help">{{ errors.seatId }}</p>
        </div>

        <div class="form-field" :class="{ 'form-field--error': errors.startDate }">
          <label class="form-label" for="allocation-start-date">Start Date</label>
          <input
            id="allocation-start-date"
            v-model="form.startDate"
            class="form-input"
            type="date"
            :aria-invalid="Boolean(errors.startDate)"
          />
          <p v-if="errors.startDate" class="form-help">{{ errors.startDate }}</p>
        </div>

        <div class="form-field" :class="{ 'form-field--error': errors.endDate }">
          <label class="form-label" for="allocation-end-date">End Date</label>
          <input
            id="allocation-end-date"
            v-model="form.endDate"
            class="form-input"
            type="date"
            :min="form.startDate"
            :aria-invalid="Boolean(errors.endDate)"
          />
          <p v-if="errors.endDate" class="form-help">{{ errors.endDate }}</p>
        </div>

        <div
          class="form-field seat-allocation-dialog__full-row"
          :class="{ 'form-field--error': errors.shiftIds }"
        >
          <div class="seat-allocation-dialog__field-header">
            <span class="form-label">Shifts</span>
            <button
              class="btn btn--ghost btn--sm"
              type="button"
              :disabled="form.shiftIds.length === 0"
              @click="form.shiftIds = []"
            >
              Clear
            </button>
          </div>

          <div
            class="seat-allocation-dialog__shift-options"
            role="group"
            aria-label="Select one or more non-overlapping shifts"
          >
            <label
              v-for="shift in enabledShifts"
              :key="shift.id"
              class="checkbox seat-allocation-dialog__shift-option"
            >
              <input
                v-model="form.shiftIds"
                type="checkbox"
                :value="shift.id"
              />
              <span>
                <strong>{{ shift.name }}</strong>
                <small>{{ shift.startTime }}-{{ shift.endTime }}</small>
              </span>
            </label>
          </div>
          <p v-if="errors.shiftIds" class="form-help">{{ errors.shiftIds }}</p>
        </div>

        <div class="form-field seat-allocation-dialog__full-row">
          <label class="form-label" for="allocation-notes">Notes</label>
          <textarea
            id="allocation-notes"
            v-model.trim="form.notes"
            class="form-textarea"
            maxlength="2000"
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
        {{ isSubmitting ? 'Allocating' : 'Confirm Allocation' }}
      </button>
    </template>
  </Modal>
</template>

<script setup>
import { computed, reactive, watch } from 'vue'

import { doShiftTimingsOverlap } from '../../utils/timeIntervals'
import Modal from '../common/Modal.vue'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  seats: { type: Array, default: () => [] },
  students: { type: Array, default: () => [] },
  shifts: { type: Array, default: () => [] },
  initialSeatId: { type: String, default: '' },
  initialShiftIds: { type: Array, default: () => [] },
  initialStartDate: { type: String, default: '' },
  initialEndDate: { type: String, default: '' },
  isSubmitting: { type: Boolean, default: false },
  submissionError: { type: Object, default: null },
})

const emit = defineEmits(['close', 'confirm'])

const form = reactive({
  studentId: '',
  seatId: '',
  shiftIds: [],
  startDate: '',
  endDate: '',
  notes: '',
})
const errors = reactive({})

const activeStudents = computed(() =>
  props.students.filter((student) => student.status === 'active'),
)
const enabledShifts = computed(() =>
  props.shifts.filter((shift) => shift.isEnabled !== false),
)
const selectableSeats = computed(() =>
  props.seats.filter(
    (seat) => seat.isAvailable || seat.id === form.seatId,
  ),
)
const selectedSeat = computed(
  () => props.seats.find((seat) => seat.id === form.seatId) || null,
)
const selectedStudent = computed(
  () => props.students.find((student) => student.id === form.studentId) || null,
)
const availabilityStatus = computed(() => {
  if (!selectedSeat.value) return 'Not selected'
  return selectedSeat.value.isAvailable ? 'Available' : formatLabel(selectedSeat.value.status)
})
const availabilityBadgeClass = computed(() =>
  selectedSeat.value?.isAvailable ? 'badge--success' : 'badge--warning',
)

watch(
  () => props.isOpen,
  (isOpen, wasOpen) => {
    if (isOpen && !wasOpen) resetForm()
  },
  { immediate: true },
)

function resetForm() {
  const today = new Date().toISOString().slice(0, 10)
  form.studentId = ''
  form.seatId = props.initialSeatId || ''
  form.shiftIds = [...props.initialShiftIds]
  form.startDate = props.initialStartDate || today
  form.endDate = props.initialEndDate || form.startDate
  form.notes = ''
  clearErrors()
}

function clearErrors() {
  Object.keys(errors).forEach((key) => delete errors[key])
}

function validateForm() {
  clearErrors()
  if (!form.studentId || !selectedStudent.value) {
    errors.studentId = 'Select an active student.'
  } else if (selectedStudent.value.status !== 'active') {
    errors.studentId = 'Only active students can receive a seat.'
  }
  if (!form.seatId || !selectedSeat.value) {
    errors.seatId = 'Select a seat.'
  } else if (!selectedSeat.value.isAvailable) {
    errors.seatId = 'This seat is not available for the selected map window.'
  }
  if (!form.startDate) errors.startDate = 'Select a start date.'
  if (!form.endDate) {
    errors.endDate = 'Select an end date.'
  } else if (form.startDate && form.endDate < form.startDate) {
    errors.endDate = 'End date cannot be earlier than start date.'
  }
  if (form.shiftIds.length === 0) {
    errors.shiftIds = 'Select at least one shift.'
  } else {
    const overlap = findShiftOverlap(form.shiftIds)
    if (overlap) {
      errors.shiftIds = `${overlap[0].name} overlaps with ${overlap[1].name}. Select non-overlapping shifts.`
    }
  }
  return Object.keys(errors).length === 0
}

function findShiftOverlap(shiftIds) {
  const selected = shiftIds
    .map((id) => props.shifts.find((shift) => shift.id === id))
    .filter(Boolean)
  for (let index = 0; index < selected.length; index += 1) {
    for (let other = index + 1; other < selected.length; other += 1) {
      if (doShiftTimingsOverlap(selected[index], selected[other])) {
        return [selected[index], selected[other]]
      }
    }
  }
  return null
}

function getStudentName(student) {
  return [student.firstName, student.lastName].filter(Boolean).join(' ')
}

function formatLabel(value) {
  return String(value || 'Unavailable')
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())
}

function handleSubmit() {
  if (!validateForm()) return
  emit('confirm', {
    studentId: form.studentId,
    seatId: form.seatId,
    shiftIds: [...form.shiftIds],
    startDate: form.startDate,
    endDate: form.endDate,
    notes: form.notes || null,
  })
}

function handleClose() {
  if (!props.isSubmitting) emit('close')
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

.seat-allocation-dialog__field-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.seat-allocation-dialog__shift-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: var(--space-2);
}

.seat-allocation-dialog__shift-option {
  min-height: 48px;
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-elevated);
}

.seat-allocation-dialog__shift-option span {
  display: grid;
}

.seat-allocation-dialog__shift-option small {
  color: var(--color-text-muted);
}

.form-field--error .form-help {
  color: var(--color-danger);
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
