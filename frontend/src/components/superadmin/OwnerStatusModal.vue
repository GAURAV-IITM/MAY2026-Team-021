<template>
  <Modal
    :is-open="isOpen"
    :title="status === 'suspended' ? 'Suspend Owner' : 'Activate Owner'"
    title-id="owner-status-title"
    @close="handleClose"
  >
    <form id="owner-status-form" class="status-form" @submit.prevent="submit">
      <p class="m-0">
        <template v-if="status === 'suspended'">
          Suspend <strong>{{ owner?.name }}</strong>? Active sessions will be revoked and owner access will stop immediately.
        </template>
        <template v-else>
          Activate <strong>{{ owner?.name }}</strong>? The owner must sign in again with a new session.
        </template>
      </p>
      <div v-if="status === 'suspended'" class="form-group">
        <label class="form-label" for="owner-suspension-reason">Reason</label>
        <textarea
          id="owner-suspension-reason"
          v-model.trim="reason"
          class="form-textarea"
          rows="3"
          maxlength="500"
          placeholder="Reason for suspending this owner"
          required
        ></textarea>
        <span v-if="error" class="form-error">{{ error }}</span>
      </div>
    </form>

    <template #footer>
      <button class="btn btn--secondary" type="button" :disabled="isSaving" @click="handleClose">
        Cancel
      </button>
      <button
        class="btn"
        :class="status === 'suspended' ? 'btn--danger' : 'btn--primary'"
        type="submit"
        form="owner-status-form"
        :disabled="isSaving"
      >
        {{ isSaving ? 'Updating...' : status === 'suspended' ? 'Suspend Owner' : 'Activate Owner' }}
      </button>
    </template>
  </Modal>
</template>

<script setup>
import { ref, watch } from 'vue'

import Modal from '../common/Modal.vue'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  owner: { type: Object, default: null },
  status: { type: String, default: 'suspended' },
  isSaving: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'save'])
const reason = ref('')
const error = ref('')

function submit() {
  error.value = props.status === 'suspended' && !reason.value
    ? 'Enter a reason for this suspension.'
    : ''
  if (!error.value) emit('save', { status: props.status, reason: reason.value || null })
}

function handleClose() {
  if (!props.isSaving) emit('close')
}

watch(() => props.isOpen, (isOpen) => {
  if (isOpen) {
    reason.value = ''
    error.value = ''
  }
})
</script>

<style scoped>
.status-form { display: grid; gap: var(--space-4); }
</style>
