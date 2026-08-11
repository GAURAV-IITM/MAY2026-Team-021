<template>
  <Modal
    :is-open="isOpen"
    :title="mode === 'edit' ? 'Edit Library Owner' : 'Invite Library Owner'"
    title-id="owner-form-title"
    @close="handleClose"
  >
    <form id="owner-form" class="owner-form" @submit.prevent="handleSubmit">
      <div class="form-group owner-form__full">
        <label class="form-label" for="owner-name">Full Name</label>
        <input
          id="owner-name"
          v-model.trim="form.name"
          class="form-input"
          type="text"
          autocomplete="name"
          required
        />
        <span v-if="errors.name" class="form-error">{{ errors.name }}</span>
      </div>

      <div class="form-group owner-form__full">
        <label class="form-label" for="owner-email">Email</label>
        <input
          id="owner-email"
          v-model.trim="form.email"
          class="form-input"
          type="email"
          autocomplete="email"
          :readonly="mode === 'edit'"
          required
        />
        <span v-if="mode === 'edit'" class="form-help">
          Email changes require a separate verified account workflow.
        </span>
        <span v-if="errors.email" class="form-error">{{ errors.email }}</span>
      </div>

      <div class="form-group">
        <label class="form-label" for="owner-phone">Phone</label>
        <input
          id="owner-phone"
          v-model.trim="form.phone"
          class="form-input"
          type="tel"
          autocomplete="tel"
        />
      </div>

      <div v-if="mode !== 'edit'" class="form-group owner-form__full">
        <label class="form-label" for="owner-library">Assigned Library</label>
        <select id="owner-library" v-model="form.libraryId" class="form-select" required>
          <option value="">Select a library</option>
          <option v-for="library in libraries" :key="library.id" :value="library.id">
            {{ library.name }}
          </option>
        </select>
        <span v-if="errors.libraryId" class="form-error">{{ errors.libraryId }}</span>
      </div>
    </form>

    <template #footer>
      <button class="btn btn--secondary" type="button" :disabled="isSaving" @click="handleClose">
        Cancel
      </button>
      <button class="btn btn--primary" type="submit" form="owner-form" :disabled="isSaving">
        {{ isSaving ? 'Saving...' : mode === 'edit' ? 'Save Changes' : 'Send Invitation' }}
      </button>
    </template>
  </Modal>
</template>

<script setup>
import { reactive, watch } from 'vue'

import Modal from '../common/Modal.vue'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  mode: { type: String, default: 'create' },
  owner: { type: Object, default: null },
  libraries: { type: Array, default: () => [] },
  isSaving: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'save'])
const form = reactive({ name: '', email: '', phone: '', libraryId: '' })
const errors = reactive({ name: '', email: '', libraryId: '' })

function resetForm() {
  Object.assign(form, {
    name: props.owner?.name || '',
    email: props.owner?.email || '',
    phone: props.owner?.phone || '',
    libraryId: props.owner?.libraryId || '',
  })
  errors.name = ''
  errors.email = ''
  errors.libraryId = ''
}

function validate() {
  errors.name = form.name ? '' : 'Owner name is required.'
  errors.email = /^\S+@\S+\.\S+$/.test(form.email) ? '' : 'Enter a valid email.'
  errors.libraryId = props.mode === 'edit' || form.libraryId
    ? ''
    : 'Select a library for this owner.'
  return !errors.name && !errors.email && !errors.libraryId
}

function handleSubmit() {
  if (!validate()) return
  emit('save', props.mode === 'edit'
    ? { name: form.name, phone: form.phone }
    : { ...form })
}

function handleClose() {
  if (!props.isSaving) emit('close')
}

watch(
  () => [props.isOpen, props.owner],
  () => {
    if (props.isOpen) resetForm()
  },
  { immediate: true },
)
</script>

<style scoped>
.owner-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
}

.owner-form__full {
  grid-column: 1 / -1;
}

@media (max-width: 560px) {
  .owner-form {
    grid-template-columns: 1fr;
  }

  .owner-form__full {
    grid-column: auto;
  }
}
</style>
