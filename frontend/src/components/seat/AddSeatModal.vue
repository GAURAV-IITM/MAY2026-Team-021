<template>
  <Modal
    :is-open="isOpen"
    title="Add Seat"
    title-id="add-seat-modal-title"
    @close="handleClose"
  >
    <form class="seat-form-modal" novalidate @submit.prevent="handleSubmit">
      <div class="form-field" :class="{ 'form-field--error': errors.seatNumber }">
        <label class="form-label" for="add-seat-number">Seat Number</label>
        <input
          id="add-seat-number"
          v-model.trim="form.seatNumber"
          class="form-control"
          type="text"
          placeholder="Example: A-12"
          :aria-invalid="Boolean(errors.seatNumber)"
        />
        <p v-if="errors.seatNumber" class="form-help">{{ errors.seatNumber }}</p>
      </div>

      <div class="seat-form-modal__grid">
        <div class="form-field" :class="{ 'form-field--error': errors.floorId }">
          <label class="form-label" for="add-seat-floor">Floor</label>
          <select
            id="add-seat-floor"
            v-model="form.floorId"
            class="form-select"
            :aria-invalid="Boolean(errors.floorId)"
          >
            <option value="">Select a floor</option>
            <option v-for="floor in activeFloors" :key="floor.id" :value="floor.id">
              {{ floor.name }} ({{ floor.code }})
            </option>
          </select>
          <p v-if="errors.floorId" class="form-help">{{ errors.floorId }}</p>
        </div>

        <div class="form-field" :class="{ 'form-field--error': errors.seatType }">
          <label class="form-label" for="add-seat-type">Seat Type</label>
          <select
            id="add-seat-type"
            v-model="form.seatType"
            class="form-select"
            :aria-invalid="Boolean(errors.seatType)"
          >
            <option value="standard">Standard</option>
            <option value="premium">Premium</option>
            <option value="cabin">Cabin</option>
            <option value="accessible">Accessible</option>
          </select>
          <p v-if="errors.seatType" class="form-help">{{ errors.seatType }}</p>
        </div>
      </div>

      <div class="form-field">
        <label class="form-label" for="add-seat-status">Status</label>
        <select id="add-seat-status" v-model="form.status" class="form-select">
          <option value="available">Available</option>
          <option value="maintenance">Maintenance</option>
          <option value="blocked">Blocked</option>
        </select>
      </div>

      <div class="form-field">
        <label class="form-label" for="add-seat-notes">Notes</label>
        <textarea
          id="add-seat-notes"
          v-model.trim="form.notes"
          class="form-control"
          rows="3"
          placeholder="Optional physical seat notes"
        ></textarea>
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
        <span>{{ isSubmitting ? 'Creating' : 'Create' }}</span>
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
  floors: {
    type: Array,
    default: () => [],
  },
  isSubmitting: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close', 'create'])

const form = reactive({
  seatNumber: '',
  floorId: '',
  seatType: 'standard',
  status: 'available',
  notes: '',
})
const errors = reactive({})
const activeFloors = computed(() => props.floors.filter((floor) => floor.isActive))

watch(
  () => props.isOpen,
  (isOpen) => {
    if (isOpen) resetForm()
  },
)

function resetForm() {
  form.seatNumber = ''
  form.floorId = activeFloors.value[0]?.id || ''
  form.seatType = 'standard'
  form.status = 'available'
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

  if (!form.seatNumber.trim()) {
    errors.seatNumber = 'Seat number is required.'
  } else if (isDuplicateSeatNumber(form.seatNumber)) {
    errors.seatNumber = 'Seat number must be unique.'
  }

  if (!form.floorId) {
    errors.floorId = 'Select an active floor.'
  }

  if (!form.seatType.trim()) {
    errors.seatType = 'Seat type is required.'
  }

  return Object.keys(errors).length === 0
}

function isDuplicateSeatNumber(seatNumber) {
  const normalizedSeatNumber = seatNumber.trim().toLowerCase()

  return props.seats.some((seat) => {
    return seat.seatNumber.toLowerCase() === normalizedSeatNumber
  })
}

function handleSubmit() {
  if (!validateForm()) return

  emit('create', {
    seatNumber: form.seatNumber.trim(),
    floorId: form.floorId,
    seatType: form.seatType.trim(),
    status: form.status,
    notes: form.notes.trim(),
  })
}

function handleClose() {
  if (props.isSubmitting) return

  emit('close')
}
</script>

<style scoped>
.seat-form-modal {
  display: grid;
  gap: var(--space-5);
}

.seat-form-modal__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
}

.form-field--error .form-help {
  color: var(--color-danger);
}

@media (max-width: 640px) {
  .seat-form-modal__grid {
    grid-template-columns: 1fr;
  }
}
</style>
