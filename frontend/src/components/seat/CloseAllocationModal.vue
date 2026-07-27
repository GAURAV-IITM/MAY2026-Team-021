<template>
  <Modal
    :is-open="isOpen"
    title="Close Allocation"
    title-id="close-allocation-title"
    @close="handleClose"
  >
    <form class="close-allocation" novalidate @submit.prevent="submit">
      <div v-if="allocation" class="close-allocation__summary">
        <strong>{{ allocation.seat.seatNumber }} · {{ allocation.shift.name }}</strong>
        <span>{{ allocation.student.name }}</span>
        <small>{{ allocation.startDate }} to {{ allocation.endDate }}</small>
      </div>

      <div class="form-field">
        <span class="form-label">Outcome</span>
        <div class="close-allocation__status-options">
          <label class="checkbox">
            <input v-model="form.status" type="radio" value="completed" />
            <span>Completed</span>
          </label>
          <label class="checkbox">
            <input v-model="form.status" type="radio" value="cancelled" />
            <span>Cancelled</span>
          </label>
        </div>
      </div>

      <div class="form-field" :class="{ 'form-field--error': errors.effectiveEndDate }">
        <label class="form-label" for="effective-end-date">Effective end date</label>
        <input
          id="effective-end-date"
          v-model="form.effectiveEndDate"
          class="form-input"
          type="date"
          :min="allocation?.startDate"
          :max="allocation?.endDate"
        />
        <p class="text-small text-muted m-0">
          Leave empty to keep the current end date when cancelling.
        </p>
        <p v-if="errors.effectiveEndDate" class="form-help">
          {{ errors.effectiveEndDate }}
        </p>
      </div>

      <div class="form-field" :class="{ 'form-field--error': errors.closeReason }">
        <label class="form-label" for="close-reason">Reason</label>
        <textarea
          id="close-reason"
          v-model.trim="form.closeReason"
          class="form-textarea"
          maxlength="2000"
          placeholder="Why is this allocation being closed?"
        ></textarea>
        <p v-if="errors.closeReason" class="form-help">{{ errors.closeReason }}</p>
      </div>
    </form>

    <template #footer>
      <button class="btn btn--secondary" type="button" :disabled="isSubmitting" @click="handleClose">
        Cancel
      </button>
      <button class="btn btn--primary" type="button" :disabled="isSubmitting" @click="submit">
        <span v-if="isSubmitting" class="btn__loader" aria-hidden="true"></span>
        {{ isSubmitting ? 'Closing' : 'Close Allocation' }}
      </button>
    </template>
  </Modal>
</template>

<script setup>
import { reactive, watch } from 'vue'

import Modal from '../common/Modal.vue'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  allocation: { type: Object, default: null },
  isSubmitting: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'confirm'])
const form = reactive({
  status: 'completed',
  effectiveEndDate: '',
  closeReason: '',
})
const errors = reactive({})

watch(
  () => props.isOpen,
  (isOpen, wasOpen) => {
    if (isOpen && !wasOpen) {
      form.status = 'completed'
      form.effectiveEndDate = ''
      form.closeReason = ''
      clearErrors()
    }
  },
  { immediate: true },
)

function clearErrors() {
  Object.keys(errors).forEach((key) => delete errors[key])
}

function submit() {
  clearErrors()
  if (!form.closeReason) errors.closeReason = 'Enter a reason.'
  if (
    form.effectiveEndDate &&
    (form.effectiveEndDate < props.allocation.startDate ||
      form.effectiveEndDate > props.allocation.endDate)
  ) {
    errors.effectiveEndDate = 'Choose a date within the allocation period.'
  }
  if (Object.keys(errors).length) return

  emit('confirm', {
    status: form.status,
    effectiveEndDate: form.effectiveEndDate || null,
    closeReason: form.closeReason,
  })
}

function handleClose() {
  if (!props.isSubmitting) emit('close')
}
</script>

<style scoped>
.close-allocation,
.close-allocation__summary {
  display: grid;
  gap: var(--space-4);
}

.close-allocation__summary {
  gap: var(--space-1);
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.close-allocation__summary small,
.close-allocation__summary span {
  color: var(--color-text-muted);
}

.close-allocation__status-options {
  display: flex;
  gap: var(--space-5);
}

.form-field--error .form-help {
  color: var(--color-danger);
}
</style>
