<template>
  <Modal
    :is-open="isOpen"
    title="Change Library Assignment"
    title-id="owner-assignment-title"
    @close="handleClose"
  >
    <form id="owner-assignment-form" class="assignment-form" @submit.prevent="submit">
      <p class="m-0 text-muted">
        {{ owner?.name }} is currently assigned to
        <strong>{{ owner?.libraryName || 'no library' }}</strong>.
      </p>
      <div class="form-group">
        <label class="form-label" for="owner-assignment-library">New Library</label>
        <select
          id="owner-assignment-library"
          v-model="libraryId"
          class="form-select"
          required
        >
          <option value="">Select an unassigned library</option>
          <option v-for="library in libraries" :key="library.id" :value="library.id">
            {{ library.name }} ({{ library.code }})
          </option>
        </select>
        <span v-if="error" class="form-error">{{ error }}</span>
      </div>
      <p class="assignment-form__note">
        The previous assignment will be closed and kept in the owner's history.
      </p>
    </form>

    <template #footer>
      <button class="btn btn--secondary" type="button" :disabled="isSaving" @click="handleClose">
        Cancel
      </button>
      <button class="btn btn--primary" type="submit" form="owner-assignment-form" :disabled="isSaving">
        {{ isSaving ? 'Updating...' : 'Update Assignment' }}
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
  libraries: { type: Array, default: () => [] },
  isSaving: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'save'])
const libraryId = ref('')
const error = ref('')

function submit() {
  error.value = libraryId.value ? '' : 'Select a target library.'
  if (!error.value) emit('save', { libraryId: libraryId.value })
}

function handleClose() {
  if (!props.isSaving) emit('close')
}

watch(() => props.isOpen, (isOpen) => {
  if (isOpen) {
    libraryId.value = ''
    error.value = ''
  }
})
</script>

<style scoped>
.assignment-form { display: grid; gap: var(--space-4); }
.assignment-form__note { margin: 0; padding: var(--space-3); border-left: 3px solid var(--color-info); color: var(--color-text-muted); font-size: var(--font-size-caption); }
</style>
