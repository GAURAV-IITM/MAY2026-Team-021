<template>
  <Modal is-open title="Request Seat Change" title-id="seat-request-title" @close="handleClose">
    <form id="seat-request-form" class="seat-request-form" @submit.prevent="handleSubmit">
      <div class="seat-request-form__current">
        <span class="text-small text-muted">Current Seat</span>
        <strong>{{ currentSeatNumber || 'Not assigned' }}</strong>
      </div>

      <div class="form-group">
        <label class="form-label" for="request-shift">Preferred Shift</label>
        <select id="request-shift" v-model="form.preferredShiftId" class="form-select" required>
          <option value="">Select a shift</option>
          <option v-for="shift in shifts" :key="shift.id" :value="shift.id">
            {{ formatLabel(shift.name) }} ({{ shift.startTime }}-{{ shift.endTime }})
          </option>
        </select>
        <span v-if="errors.shift" class="form-error">{{ errors.shift }}</span>
      </div>

      <div class="seat-request-form__grid">
        <div class="form-group">
          <label class="form-label" for="request-seat">Preferred Seat</label>
          <input id="request-seat" v-model.trim="form.preferredSeatNumber" class="form-input" placeholder="Example: B-02" />
        </div>
        <div class="form-group">
          <label class="form-label" for="request-floor">Preferred Floor</label>
          <select id="request-floor" v-model="form.preferredFloor" class="form-select">
            <option value="">No preference</option>
            <option value="1">Floor 1</option>
            <option value="2">Floor 2</option>
            <option value="3">Floor 3</option>
          </select>
        </div>
      </div>

      <div class="form-group">
        <label class="form-label" for="request-reason">Reason</label>
        <textarea id="request-reason" v-model.trim="form.reason" class="form-textarea" rows="4" placeholder="Explain why you need a seat or shift change" required></textarea>
        <span v-if="errors.reason" class="form-error">{{ errors.reason }}</span>
      </div>
    </form>

    <template #footer>
      <button class="btn btn--secondary" type="button" :disabled="isSaving" @click="handleClose">Cancel</button>
      <button class="btn btn--primary" type="submit" form="seat-request-form" :disabled="isSaving">
        {{ isSaving ? 'Submitting...' : 'Submit Request' }}
      </button>
    </template>
  </Modal>
</template>

<script setup>
import { reactive } from 'vue'

import Modal from '../common/Modal.vue'

const props = defineProps({
  currentSeatNumber: { type: String, default: '' },
  shifts: { type: Array, default: () => [] },
  isSaving: { type: Boolean, default: false },
})
const emit = defineEmits(['close', 'submit'])
const form = reactive({ preferredShiftId: '', preferredSeatNumber: '', preferredFloor: '', reason: '' })
const errors = reactive({ shift: '', reason: '' })

function formatLabel(value) { return String(value || '').replace(/[-_]/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase()) }
function handleClose() { if (!props.isSaving) emit('close') }
function handleSubmit() {
  errors.shift = form.preferredShiftId ? '' : 'Select a preferred shift.'
  errors.reason = form.reason.length >= 15 ? '' : 'Provide at least 15 characters.'
  if (errors.shift || errors.reason) return
  emit('submit', { ...form, preferredFloor: form.preferredFloor ? Number(form.preferredFloor) : null })
}
</script>

<style scoped>
.seat-request-form { display: grid; gap: var(--space-4); }
.seat-request-form__current { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); padding: var(--space-3); border-radius: var(--radius-md); background: var(--color-surface-secondary); }
.seat-request-form__grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-4); }
@media (max-width: 560px) { .seat-request-form__grid { grid-template-columns: 1fr; } }
</style>
