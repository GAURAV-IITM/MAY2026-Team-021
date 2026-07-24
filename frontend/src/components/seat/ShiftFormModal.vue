<template>
  <Modal
    :is-open="isOpen"
    :title="modalTitle"
    title-id="shift-form-modal-title"
    @close="handleClose"
  >
    <form class="shift-form-modal" novalidate @submit.prevent="handleSubmit">
      <div class="form-field" :class="{ 'form-field--error': errors.name }">
        <label class="form-label" for="shift-name">Shift Name</label>
        <input
          id="shift-name"
          v-model.trim="form.name"
          class="form-control"
          type="text"
          placeholder="Example: Late Night"
          :aria-invalid="Boolean(errors.name)"
        />
        <p v-if="errors.name" class="form-help">{{ errors.name }}</p>
      </div>

      <div class="shift-form-modal__grid">
        <div class="form-field" :class="{ 'form-field--error': errors.startTime }">
          <label class="form-label" for="shift-start-time">Start Time</label>
          <input
            id="shift-start-time"
            v-model="form.startTime"
            class="form-control"
            type="time"
            :aria-invalid="Boolean(errors.startTime)"
          />
          <p v-if="errors.startTime" class="form-help">{{ errors.startTime }}</p>
        </div>

        <div class="form-field" :class="{ 'form-field--error': errors.endTime }">
          <label class="form-label" for="shift-end-time">End Time</label>
          <input
            id="shift-end-time"
            v-model="form.endTime"
            class="form-control"
            type="time"
            :aria-invalid="Boolean(errors.endTime)"
          />
          <p v-if="errors.endTime" class="form-help">{{ errors.endTime }}</p>
        </div>
      </div>

      <label class="checkbox shift-form-modal__toggle">
        <input v-model="form.isEnabled" type="checkbox" />
        <span>Enable this shift</span>
      </label>
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
        <span>{{ isSubmitting ? 'Saving' : submitLabel }}</span>
      </button>
    </template>
  </Modal>
</template>

<script setup>
import { computed, reactive, watch } from 'vue'

import { isSameDayTimeRange } from '../../utils/timeIntervals'
import Modal from '../common/Modal.vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false,
  },
  mode: {
    type: String,
    default: 'create',
  },
  shift: {
    type: Object,
    default: null,
  },
  isSubmitting: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close', 'save'])

const form = reactive({
  name: '',
  startTime: '',
  endTime: '',
  isEnabled: true,
})

const errors = reactive({})

const modalTitle = computed(() => {
  return props.mode === 'edit' ? 'Edit Shift' : 'Add Shift'
})

const submitLabel = computed(() => {
  return props.mode === 'edit' ? 'Update Shift' : 'Create Shift'
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
  () => props.shift,
  () => {
    if (props.isOpen) {
      resetForm()
    }
  },
)

function resetForm() {
  form.name = props.shift?.name || ''
  form.startTime = props.shift?.startTime || ''
  form.endTime = props.shift?.endTime || ''
  form.isEnabled = props.shift?.isEnabled !== false
  clearErrors()
}

function clearErrors() {
  Object.keys(errors).forEach((key) => {
    delete errors[key]
  })
}

function validateForm() {
  clearErrors()

  if (!form.name.trim()) {
    errors.name = 'Shift name is required.'
  }

  if (!form.startTime) {
    errors.startTime = 'Start time is required.'
  }

  if (!form.endTime) {
    errors.endTime = 'End time is required.'
  } else if (form.startTime && !isSameDayTimeRange(form.startTime, form.endTime)) {
    errors.endTime = 'End time must be later than start time.'
  }

  return Object.keys(errors).length === 0
}

function handleSubmit() {
  if (!validateForm()) return

  emit('save', {
    name: form.name.trim(),
    startTime: form.startTime,
    endTime: form.endTime,
    isEnabled: form.isEnabled,
  })
}

function handleClose() {
  if (props.isSubmitting) return

  emit('close')
}
</script>

<style scoped>
.shift-form-modal {
  display: grid;
  gap: var(--space-5);
}

.shift-form-modal__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
}

.shift-form-modal__toggle {
  justify-self: start;
}

.form-field--error .form-help {
  color: var(--color-danger);
}

@media (max-width: 640px) {
  .shift-form-modal__grid {
    grid-template-columns: 1fr;
  }
}
</style>

<!--
src/components/seat: Reusable create/edit modal for tenant-defined study shifts.
TODO:
- Replace frontend-only validation with FastAPI-backed validation errors in Milestone 3.
-->
