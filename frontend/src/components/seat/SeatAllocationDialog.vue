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
              {{ seat.seatNumber }} · {{ seat.availableShiftCount || 0 }} shifts available
            </option>
          </select>
          <p v-if="errors.seatId" class="form-help">{{ errors.seatId }}</p>
        </div>

        <div
          class="form-field seat-allocation-dialog__full-row"
          :class="{ 'form-field--error': errors.activeShifts }"
        >
          <div class="seat-allocation-dialog__field-header">
            <span class="form-label">Shifts</span>
            <div class="seat-allocation-dialog__shift-actions">
              <button
                class="btn btn--ghost btn--sm"
                type="button"
                :disabled="shiftOptions.length === 0"
                @click="selectAllShifts"
              >
                Full Day
              </button>
              <button
                class="btn btn--ghost btn--sm"
                type="button"
                :disabled="form.activeShifts.length === 0"
                @click="clearSelectedShifts"
              >
                Clear
              </button>
            </div>
          </div>

          <div
            class="seat-allocation-dialog__shift-options"
            role="group"
            aria-label="Select one or more shifts"
          >
            <label
              v-for="shift in shiftOptions"
              :key="shift.value"
              class="checkbox seat-allocation-dialog__shift-option"
            >
              <input
                v-model="form.activeShifts"
                type="checkbox"
                :value="shift.value"
              />
              <span>{{ shift.label }}</span>
            </label>

            <p v-if="shiftOptions.length === 0" class="text-small text-muted m-0">
              No enabled shifts are available.
            </p>
          </div>

          <p v-if="errors.activeShifts" class="form-help">
            {{ errors.activeShifts }}
          </p>
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

import { doShiftTimingsOverlap } from '../../utils/timeIntervals'
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
  shifts: {
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

const form = reactive({
  studentId: '',
  seatId: '',
  activeShifts: [],
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

const shiftOptions = computed(() => {
  return props.shifts
    .filter((shift) => shift.isEnabled !== false)
    .map((shift) => ({
      value: shift.id,
      label: shift.name,
    }))
})

const availabilityStatus = computed(() => {
  if (!selectedSeat.value) return 'Select a seat'
  if (selectedSeat.value.physicalStatus === 'maintenance') return 'Maintenance'
  if (form.activeShifts.length === 0) return 'Select shifts'

  return isSeatAvailable(selectedSeat.value) ? 'Available' : 'Unavailable'
})

const availabilityTitle = computed(() => {
  if (!selectedSeat.value) {
    return 'Choose a seat to inspect availability.'
  }

  if (form.activeShifts.length === 0) {
    return 'Select shifts to check this seat.'
  }

  if (isSeatAvailable(selectedSeat.value)) {
    return `${selectedSeat.value.seatNumber} is available for selected shifts.`
  }

  return `${selectedSeat.value.seatNumber} has a conflict in one or more selected shifts.`
})

const availabilityBadgeClass = computed(() => {
  if (!selectedSeat.value) return 'badge--pending'
  if (selectedSeat.value.physicalStatus === 'maintenance') return 'badge--warning'
  if (form.activeShifts.length === 0) return 'badge--pending'
  if (isSeatAvailable(selectedSeat.value)) return 'badge--success'
  if (selectedSeat.value.reservedShiftCount > 0) return 'seat-allocation-dialog__badge--reserved'

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
  form.activeShifts = []
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

  if (form.activeShifts.length === 0) {
    errors.activeShifts = 'Select at least one shift.'
  } else {
    const overlappingShifts = getOverlappingSelectedShifts(form.activeShifts)

    if (overlappingShifts.length > 0) {
      errors.activeShifts = `${overlappingShifts[0].name} overlaps with ${overlappingShifts[1].name}. Select non-overlapping shifts.`
    }
  }

  return Object.keys(errors).length === 0
}

function isSeatAvailable(seat) {
  if (!seat || seat.physicalStatus === 'maintenance') return false

  if (form.activeShifts.length === 0) {
    return Number(seat.availableShiftCount || 0) > 0
  }

  return form.activeShifts.every((shiftId) => {
    const shiftAvailability = seat.shiftAvailability?.find((shift) => {
      return shift.shiftId === shiftId
    })

    return shiftAvailability?.status === 'available'
  })
}

function getStudentName(student) {
  return [student.firstName, student.lastName].filter(Boolean).join(' ')
}

function selectAllShifts() {
  form.activeShifts = shiftOptions.value.map((shift) => shift.value)
}

function clearSelectedShifts() {
  form.activeShifts = []
}

function getOverlappingSelectedShifts(shiftIds = []) {
  const selectedShifts = shiftIds
    .map((shiftId) => props.shifts.find((shift) => shift.id === shiftId))
    .filter(Boolean)

  for (let index = 0; index < selectedShifts.length; index += 1) {
    for (
      let compareIndex = index + 1;
      compareIndex < selectedShifts.length;
      compareIndex += 1
    ) {
      if (
        doShiftTimingsOverlap(selectedShifts[index], selectedShifts[compareIndex])
      ) {
        return [selectedShifts[index], selectedShifts[compareIndex]]
      }
    }
  }

  return []
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
    shift: form.activeShifts[0],
    activeShifts: [...form.activeShifts],
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

.seat-allocation-dialog__field-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.seat-allocation-dialog__shift-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.seat-allocation-dialog__shift-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: var(--space-2);
}

.seat-allocation-dialog__shift-option {
  min-height: 40px;
  padding: 0 var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-elevated);
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

  .seat-allocation-dialog__field-header {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>

<!--
src/components/seat: Reusable dialog for mock seat allocation workflows.
TODO:
- Connect this payload to FastAPI allocation endpoints through seatService in Milestone 3.
-->
