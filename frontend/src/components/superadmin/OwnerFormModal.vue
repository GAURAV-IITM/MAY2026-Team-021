<template>
  <Modal
    :is-open="isOpen"
    :title="mode === 'edit' ? 'Edit Library Owner' : 'Add Library Owner'"
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
          required
        />
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

      <div class="form-group">
        <label class="form-label" for="owner-status">Status</label>
        <select id="owner-status" v-model="form.status" class="form-select">
          <option value="invited">Invited</option>
          <option value="active">Active</option>
          <option value="suspended">Suspended</option>
        </select>
      </div>

      <div class="form-group owner-form__full">
        <label class="form-label" for="owner-library">Assigned Library</label>
        <select id="owner-library" v-model="form.libraryId" class="form-select">
          <option value="">Not assigned</option>
          <option v-for="library in libraries" :key="library.id" :value="library.id">
            {{ library.name }}
          </option>
        </select>
      </div>
    </form>

    <template #footer>
      <button class="btn btn--secondary" type="button" :disabled="isSaving" @click="handleClose">
        Cancel
      </button>
      <button class="btn btn--primary" type="submit" form="owner-form" :disabled="isSaving">
        {{ isSaving ? 'Saving...' : mode === 'edit' ? 'Save Changes' : 'Create Owner' }}
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
const form = reactive({ name: '', email: '', phone: '', libraryId: '', status: 'invited' })
const errors = reactive({ name: '', email: '' })

function resetForm() {
  Object.assign(form, {
    name: props.owner?.name || '',
    email: props.owner?.email || '',
    phone: props.owner?.phone || '',
    libraryId: props.owner?.libraryId || '',
    status: props.owner?.status || 'invited',
  })
  errors.name = ''
  errors.email = ''
}

function validate() {
  errors.name = form.name ? '' : 'Owner name is required.'
  errors.email = /^\S+@\S+\.\S+$/.test(form.email) ? '' : 'Enter a valid email.'
  return !errors.name && !errors.email
}

function handleSubmit() {
  if (validate()) emit('save', { ...form })
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
