<template>
  <Modal
    :is-open="isOpen"
    :title="targetStatus === 'suspended' ? 'Suspend Library' : 'Activate Library'"
    title-id="library-status-title"
    @close="handleClose"
  >
    <form id="library-status-form" class="status-form" @submit.prevent="submit">
      <p class="m-0">
        <template v-if="targetStatus === 'suspended'">
          Suspending <strong>{{ library?.name }}</strong> blocks owner, staff, and student access while preserving all library data.
        </template>
        <template v-else>
          Activate <strong>{{ library?.name }}</strong> and restore access for eligible members?
        </template>
      </p>
      <div v-if="targetStatus === 'suspended'" class="form-group">
        <label class="form-label" for="suspension-reason">Reason</label>
        <textarea
          id="suspension-reason"
          v-model.trim="reason"
          class="form-textarea"
          rows="4"
          maxlength="500"
          required
        ></textarea>
        <span v-if="error" class="form-error">{{ error }}</span>
      </div>
      <div v-if="serverError" class="alert alert--danger" role="alert">{{ serverError }}</div>
    </form>

    <template #footer>
      <button class="btn btn--secondary" type="button" :disabled="isSaving" @click="handleClose">Cancel</button>
      <button
        class="btn"
        :class="targetStatus === 'suspended' ? 'btn--danger' : 'btn--primary'"
        type="submit"
        form="library-status-form"
        :disabled="isSaving"
      >
        {{ isSaving ? 'Updating...' : targetStatus === 'suspended' ? 'Suspend' : 'Activate' }}
      </button>
    </template>
  </Modal>
</template>

<script setup>
import { ref, watch } from 'vue'

import Modal from '../common/Modal.vue'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  library: { type: Object, default: null },
  targetStatus: { type: String, default: 'active' },
  isSaving: { type: Boolean, default: false },
  serverError: { type: String, default: '' },
})
const emit = defineEmits(['close', 'confirm'])
const reason = ref('')
const error = ref('')

function submit() {
  if (props.targetStatus === 'suspended' && reason.value.trim().length < 3) {
    error.value = 'Enter a clear suspension reason.'
    return
  }
  emit('confirm', {
    status: props.targetStatus,
    reason: props.targetStatus === 'suspended' ? reason.value.trim() : null,
    expectedUpdatedAt: props.library?.updatedAt,
  })
}

function handleClose() {
  if (!props.isSaving) emit('close')
}

watch(() => props.isOpen, (isOpen) => {
  if (isOpen) { reason.value = ''; error.value = '' }
})
</script>

<style scoped>
.status-form { display: grid; gap: var(--space-5); }
</style>
