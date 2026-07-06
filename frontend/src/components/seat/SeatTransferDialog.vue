<template>
  <Modal
    :is-open="isOpen"
    :title="dialogTitle"
    title-id="seat-transfer-dialog-title"
    @close="handleClose"
  >
    <form
      v-if="step === 'form'"
      class="seat-transfer-dialog"
      novalidate
      @submit.prevent="handleContinue"
    >
      <section class="seat-transfer-dialog__availability" aria-live="polite">
        <div>
          <p class="text-label text-muted m-0">Transfer Availability</p>
          <h3 class="text-h5 m-0">
            {{ availableTargetSeats.length }} seats available for transfer
          </h3>
        </div>

        <span class="badge badge--success">
          Available Seats
        </span>
      </section>

      <div class="seat-transfer-dialog__grid">
        <div class="form-field" :class="{ 'form-field--error': errors.studentId }">
          <label class="form-label" for="transfer-student">Student</label>
          <select
            id="transfer-student"
            v-model="form.studentId"
            class="form-select"
            :aria-invalid="Boolean(errors.studentId)"
          >
            <option value="">Select student</option>
            <option
              v-for="student in transferableStudents"
              :key="student.id"
              :value="student.id"
            >
              {{ student.name }}
            </option>
          </select>
          <p v-if="errors.studentId" class="form-help">{{ errors.studentId }}</p>
        </div>

        <div class="form-field">
          <span class="form-label">Current Seat</span>
          <div class="seat-transfer-dialog__readonly-panel">
            <strong>{{ currentSeat?.seatNumber || 'Select a student' }}</strong>
            <span class="text-small text-muted">
              {{ currentSeatDescription }}
            </span>
          </div>
        </div>

        <div
          class="form-field seat-transfer-dialog__full-row"
          :class="{ 'form-field--error': errors.targetSeatId }"
        >
          <label class="form-label" for="transfer-new-seat">Choose New Seat</label>
          <select
            id="transfer-new-seat"
            v-model="form.targetSeatId"
            class="form-select"
            :aria-invalid="Boolean(errors.targetSeatId)"
          >
            <option value="">Select new seat</option>
            <option
              v-for="seat in availableTargetSeats"
              :key="seat.id"
              :value="seat.id"
            >
              {{ seat.seatNumber }} - Floor {{ seat.floor }} -
              {{ formatShiftList(seat.activeShifts) }}
            </option>
          </select>
          <p v-if="errors.targetSeatId" class="form-help">
            {{ errors.targetSeatId }}
          </p>
        </div>
      </div>
    </form>

    <section
      v-else
      class="seat-transfer-dialog seat-transfer-dialog__confirmation"
      aria-live="polite"
    >
      <div>
        <p class="text-label text-muted m-0">Transfer Summary</p>
        <h3 class="text-h5 m-0">Confirm this seat transfer</h3>
      </div>

      <div class="seat-transfer-dialog__summary-grid">
        <div class="seat-transfer-dialog__summary-item">
          <span class="text-small text-muted">Student</span>
          <strong>{{ transferSummary.student }}</strong>
        </div>

        <div class="seat-transfer-dialog__summary-item">
          <span class="text-small text-muted">Old Seat</span>
          <strong>{{ transferSummary.oldSeat }}</strong>
        </div>

        <div class="seat-transfer-dialog__summary-item">
          <span class="text-small text-muted">New Seat</span>
          <strong>{{ transferSummary.newSeat }}</strong>
        </div>

        <div class="seat-transfer-dialog__summary-item">
          <span class="text-small text-muted">Shift</span>
          <strong>{{ transferSummary.shift }}</strong>
        </div>
      </div>
    </section>

    <template #footer>
      <button
        class="btn btn--secondary"
        type="button"
        :disabled="isSubmitting"
        @click="handleSecondaryAction"
      >
        {{ step === 'form' ? 'Cancel' : 'Back' }}
      </button>

      <button
        class="btn btn--primary"
        type="button"
        :disabled="isSubmitting"
        @click="step === 'form' ? handleContinue() : handleConfirm()"
      >
        <span v-if="isSubmitting" class="btn__loader" aria-hidden="true"></span>
        <span>{{ primaryActionLabel }}</span>
      </button>
    </template>
  </Modal>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'

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

const step = ref('form')
const form = reactive({
  studentId: '',
  targetSeatId: '',
})
const errors = reactive({})

const occupiedSeats = computed(() => {
  return props.seats.filter((seat) => {
    return seat.status === 'occupied' && seat.assignedStudent
  })
})

const availableTargetSeats = computed(() => {
  return props.seats.filter((seat) => {
    return (
      seat.status === 'available' &&
      !seat.assignedStudent &&
      seat.id !== currentSeat.value?.id
    )
  })
})

const transferableStudents = computed(() => {
  return occupiedSeats.value.map((seat) => ({
    ...seat.assignedStudent,
    currentSeatId: seat.id,
    currentSeatNumber: seat.seatNumber,
  }))
})

const currentSeat = computed(() => {
  return occupiedSeats.value.find((seat) => {
    return seat.assignedStudent?.id === form.studentId
  }) || null
})

const targetSeat = computed(() => {
  return props.seats.find((seat) => seat.id === form.targetSeatId) || null
})

const transferShift = computed(() => {
  return currentSeat.value?.activeShifts?.[0] || ''
})

const dialogTitle = computed(() => {
  return step.value === 'form' ? 'Transfer Seat' : 'Confirm Seat Transfer'
})

const primaryActionLabel = computed(() => {
  if (isConfirmingTransfer.value) return 'Transferring'

  return step.value === 'form' ? 'Review Transfer' : 'Confirm Transfer'
})

const isConfirmingTransfer = computed(() => {
  return props.isSubmitting && step.value === 'confirm'
})

const currentSeatDescription = computed(() => {
  if (!currentSeat.value) return 'Current seat will appear after student selection.'

  return `Floor ${currentSeat.value.floor} - ${formatShiftList(currentSeat.value.activeShifts)}`
})

const transferSummary = computed(() => {
  return {
    student: currentSeat.value?.assignedStudent?.name || 'Selected student',
    oldSeat: currentSeat.value?.seatNumber || 'Current seat',
    newSeat: targetSeat.value?.seatNumber || 'New seat',
    shift: transferShift.value
      ? formatLabel(transferShift.value)
      : 'No active shift',
  }
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
    if (props.isOpen) {
      form.studentId = getInitialStudentId(seatId)
      form.targetSeatId = ''
      clearErrors()
    }
  },
)

watch(
  () => form.studentId,
  () => {
    form.targetSeatId = ''
    clearErrors()
    step.value = 'form'
  },
)

function resetForm() {
  step.value = 'form'
  form.studentId = getInitialStudentId(props.initialSeatId)
  form.targetSeatId = ''
  clearErrors()
}

function getInitialStudentId(seatId) {
  const initialSeat = occupiedSeats.value.find((seat) => seat.id === seatId)

  return initialSeat?.assignedStudent?.id || ''
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
  } else if (!currentSeat.value) {
    errors.studentId = 'Selected student does not have an occupied seat.'
  }

  if (!form.targetSeatId) {
    errors.targetSeatId = 'Select a new seat.'
  } else if (!targetSeat.value) {
    errors.targetSeatId = 'Selected new seat was not found.'
  } else if (!isSeatAvailable(targetSeat.value)) {
    errors.targetSeatId = 'Select an available new seat.'
  } else if (targetSeat.value.id === currentSeat.value?.id) {
    errors.targetSeatId = 'Choose a different seat.'
  }

  return Object.keys(errors).length === 0
}

function isSeatAvailable(seat) {
  return seat?.status === 'available' && !seat.assignedStudent
}

function formatShiftList(shifts = []) {
  if (!Array.isArray(shifts) || shifts.length === 0) return 'No active shifts'

  return shifts.map((shift) => formatLabel(shift)).join(', ')
}

function formatLabel(value) {
  if (!value) return 'Unassigned'

  return String(value)
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())
}

function handleContinue() {
  if (!validateForm()) return

  step.value = 'confirm'
}

function handleConfirm() {
  if (!validateForm()) {
    step.value = 'form'
    return
  }

  emit('confirm', {
    fromSeatId: currentSeat.value.id,
    toSeatId: targetSeat.value.id,
    assignedStudent: currentSeat.value.assignedStudent,
    shift: transferShift.value,
    activeShifts: transferShift.value ? [transferShift.value] : [],
  })
}

function handleSecondaryAction() {
  if (props.isSubmitting) return

  if (step.value === 'confirm') {
    step.value = 'form'
    return
  }

  emit('close')
}

function handleClose() {
  if (props.isSubmitting) return

  emit('close')
}
</script>

<style scoped>
.seat-transfer-dialog {
  display: grid;
  gap: var(--space-5);
}

.seat-transfer-dialog__availability {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.seat-transfer-dialog__grid,
.seat-transfer-dialog__summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
}

.seat-transfer-dialog__full-row {
  grid-column: 1 / -1;
}

.seat-transfer-dialog__readonly-panel,
.seat-transfer-dialog__summary-item {
  display: grid;
  gap: var(--space-1);
  min-height: 40px;
  padding: var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-elevated);
}

.seat-transfer-dialog__confirmation {
  gap: var(--space-4);
}

.form-field--error .form-help {
  color: var(--color-danger);
}

@media (max-width: 680px) {
  .seat-transfer-dialog__availability {
    flex-direction: column;
  }

  .seat-transfer-dialog__grid,
  .seat-transfer-dialog__summary-grid {
    grid-template-columns: 1fr;
  }

  .seat-transfer-dialog__full-row {
    grid-column: auto;
  }
}
</style>

<!--
src/components/seat: Reusable dialog for mock seat transfer workflows.
TODO:
- Connect transfer confirmation to FastAPI transactional seat transfer endpoints in Milestone 3.
-->
