<template>
  <Modal
    :is-open="isOpen"
    :title="mode === 'edit' ? 'Edit Library' : 'Add Library'"
    title-id="library-form-title"
    @close="handleClose"
  >
    <form id="library-form" class="super-admin-form" @submit.prevent="handleSubmit">
      <div class="form-group super-admin-form__full">
        <label class="form-label" for="library-name">Library Name</label>
        <input
          id="library-name"
          v-model.trim="form.name"
          class="form-input"
          type="text"
          autocomplete="organization"
          required
        />
        <span v-if="errors.name" class="form-error">{{ errors.name }}</span>
      </div>

      <div class="form-group">
        <label class="form-label" for="library-city">City</label>
        <input id="library-city" v-model.trim="form.city" class="form-input" required />
      </div>

      <div class="form-group">
        <label class="form-label" for="library-state">State</label>
        <input id="library-state" v-model.trim="form.state" class="form-input" required />
      </div>

      <div class="form-group super-admin-form__full">
        <label class="form-label" for="library-email">Contact Email</label>
        <input
          id="library-email"
          v-model.trim="form.contactEmail"
          class="form-input"
          type="email"
          autocomplete="email"
          required
        />
        <span v-if="errors.contactEmail" class="form-error">
          {{ errors.contactEmail }}
        </span>
      </div>

      <div class="form-group">
        <label class="form-label" for="library-phone">Contact Phone</label>
        <input
          id="library-phone"
          v-model.trim="form.contactPhone"
          class="form-input"
          type="tel"
          autocomplete="tel"
        />
      </div>

      <div class="form-group">
        <label class="form-label" for="library-seats">Seat Capacity</label>
        <input
          id="library-seats"
          v-model.number="form.seatCount"
          class="form-input"
          type="number"
          min="0"
          step="1"
          required
        />
      </div>

      <div class="form-group">
        <label class="form-label" for="library-status">Status</label>
        <select id="library-status" v-model="form.status" class="form-select">
          <option value="pending">Pending</option>
          <option value="active">Active</option>
          <option value="suspended">Suspended</option>
        </select>
      </div>

      <div class="form-group">
        <label class="form-label" for="library-owner">Library Owner</label>
        <select
          id="library-owner"
          v-model="form.ownerId"
          class="form-select"
          :disabled="Boolean(library?.ownerId)"
        >
          <option value="">Not assigned</option>
          <option v-for="owner in owners" :key="owner.id" :value="owner.id">
            {{ owner.name }}
          </option>
        </select>
        <span v-if="library?.ownerId" class="form-help">
          Owner assignment can be changed from Owner Management.
        </span>
      </div>
    </form>

    <template #footer>
      <button class="btn btn--secondary" type="button" :disabled="isSaving" @click="handleClose">
        Cancel
      </button>
      <button class="btn btn--primary" type="submit" form="library-form" :disabled="isSaving">
        {{ isSaving ? 'Saving...' : mode === 'edit' ? 'Save Changes' : 'Create Library' }}
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
  library: { type: Object, default: null },
  owners: { type: Array, default: () => [] },
  isSaving: { type: Boolean, default: false },
})

const emit = defineEmits(['close', 'save'])

const form = reactive({
  name: '',
  city: '',
  state: '',
  contactEmail: '',
  contactPhone: '',
  seatCount: 0,
  status: 'pending',
  ownerId: '',
})
const errors = reactive({ name: '', contactEmail: '' })

function resetForm() {
  Object.assign(form, {
    name: props.library?.name || '',
    city: props.library?.city || '',
    state: props.library?.state || '',
    contactEmail: props.library?.contactEmail || '',
    contactPhone: props.library?.contactPhone || '',
    seatCount: props.library?.seatCount || 0,
    status: props.library?.status || 'pending',
    ownerId: props.library?.ownerId || '',
  })
  errors.name = ''
  errors.contactEmail = ''
}

function validate() {
  errors.name = form.name ? '' : 'Library name is required.'
  errors.contactEmail = /^\S+@\S+\.\S+$/.test(form.contactEmail)
    ? ''
    : 'Enter a valid contact email.'

  return !errors.name && !errors.contactEmail
}

function handleSubmit() {
  if (!validate()) return

  emit('save', { ...form })
}

function handleClose() {
  if (props.isSaving) return
  emit('close')
}

watch(
  () => [props.isOpen, props.library],
  () => {
    if (props.isOpen) resetForm()
  },
  { immediate: true },
)
</script>

<style scoped>
.super-admin-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
}

.super-admin-form__full {
  grid-column: 1 / -1;
}

.form-help {
  color: var(--color-text-muted);
  font-size: var(--font-size-caption);
}

@media (max-width: 560px) {
  .super-admin-form {
    grid-template-columns: 1fr;
  }

  .super-admin-form__full {
    grid-column: auto;
  }
}
</style>
