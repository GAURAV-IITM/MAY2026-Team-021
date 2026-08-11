<template>
  <Modal
    :is-open="isOpen"
    :title="mode === 'edit' ? 'Edit Library' : 'Add Library'"
    title-id="library-form-title"
    @close="handleClose"
  >
    <form id="library-form" class="super-admin-form" @submit.prevent="handleSubmit">
      <div v-if="serverError" class="alert alert--danger super-admin-form__full" role="alert">
        {{ serverError }}
      </div>

      <div class="form-group super-admin-form__full">
        <label class="form-label" for="library-name">Library Name</label>
        <input
          id="library-name"
          v-model.trim="form.name"
          class="form-input"
          type="text"
          autocomplete="organization"
          maxlength="180"
          required
        />
        <span v-if="errors.name" class="form-error">{{ errors.name }}</span>
      </div>

      <div class="form-group">
        <label class="form-label" for="library-code">Library Code</label>
        <input
          id="library-code"
          v-model.trim="form.code"
          class="form-input"
          type="text"
          maxlength="32"
          :disabled="mode === 'edit'"
          required
          @input="form.code = form.code.toUpperCase()"
        />
        <span v-if="errors.code" class="form-error">{{ errors.code }}</span>
        <span v-else-if="mode === 'edit'" class="form-help">Library codes cannot be changed.</span>
      </div>

      <div class="form-group">
        <label class="form-label" for="library-timezone">Timezone</label>
        <select id="library-timezone" v-model="form.timezone" class="form-select" required>
          <option value="Asia/Kolkata">Asia/Kolkata</option>
          <option value="Asia/Dubai">Asia/Dubai</option>
          <option value="Asia/Singapore">Asia/Singapore</option>
          <option value="Europe/London">Europe/London</option>
          <option value="America/New_York">America/New_York</option>
        </select>
      </div>

      <div class="form-group super-admin-form__full">
        <label class="form-label" for="library-email">Contact Email</label>
        <input
          id="library-email"
          v-model.trim="form.contactEmail"
          class="form-input"
          type="email"
          autocomplete="email"
          maxlength="320"
          required
        />
        <span v-if="errors.contactEmail" class="form-error">{{ errors.contactEmail }}</span>
      </div>

      <div class="form-group">
        <label class="form-label" for="library-phone">Contact Phone</label>
        <input
          id="library-phone"
          v-model.trim="form.contactPhone"
          class="form-input"
          type="tel"
          autocomplete="tel"
          maxlength="32"
        />
        <span v-if="errors.contactPhone" class="form-error">{{ errors.contactPhone }}</span>
      </div>

      <div class="form-group">
        <label class="form-label" for="library-postal-code">Postal Code</label>
        <input
          id="library-postal-code"
          v-model.trim="form.postalCode"
          class="form-input"
          type="text"
          autocomplete="postal-code"
          maxlength="20"
        />
      </div>

      <div class="form-group super-admin-form__full">
        <label class="form-label" for="library-address">Address</label>
        <input
          id="library-address"
          v-model.trim="form.addressLine"
          class="form-input"
          type="text"
          autocomplete="street-address"
          maxlength="255"
        />
      </div>

      <div class="form-group">
        <label class="form-label" for="library-city">City</label>
        <input id="library-city" v-model.trim="form.city" class="form-input" maxlength="100" />
      </div>

      <div class="form-group">
        <label class="form-label" for="library-state">State</label>
        <input id="library-state" v-model.trim="form.state" class="form-input" maxlength="100" />
      </div>

      <div v-if="mode === 'create'" class="form-group super-admin-form__full">
        <label class="form-label" for="library-owner">Existing Owner (Optional)</label>
        <select id="library-owner" v-model="form.ownerId" class="form-select">
          <option value="">Assign later</option>
          <option v-for="owner in owners" :key="owner.id" :value="owner.id">
            {{ owner.name }} - {{ owner.email }}
          </option>
        </select>
        <span class="form-help">Only active, unassigned owner accounts are listed.</span>
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
  serverError: { type: String, default: '' },
})

const emit = defineEmits(['close', 'save'])

const form = reactive({
  name: '',
  code: '',
  contactEmail: '',
  contactPhone: '',
  addressLine: '',
  city: '',
  state: '',
  postalCode: '',
  timezone: 'Asia/Kolkata',
  ownerId: '',
})
const errors = reactive({ name: '', code: '', contactEmail: '', contactPhone: '' })

function resetForm() {
  Object.assign(form, {
    name: props.library?.name || '',
    code: props.library?.code || '',
    contactEmail: props.library?.contactEmail || '',
    contactPhone: props.library?.contactPhone || '',
    addressLine: props.library?.addressLine || '',
    city: props.library?.city || '',
    state: props.library?.state || '',
    postalCode: props.library?.postalCode || '',
    timezone: props.library?.timezone || 'Asia/Kolkata',
    ownerId: '',
  })
  Object.keys(errors).forEach((field) => { errors[field] = '' })
}

function validate() {
  errors.name = form.name.trim().length >= 2 ? '' : 'Enter a library name.'
  errors.code = /^[A-Z0-9_-]{2,32}$/.test(form.code)
    ? ''
    : 'Use 2-32 letters, numbers, hyphens, or underscores.'
  errors.contactEmail = /^\S+@\S+\.\S+$/.test(form.contactEmail)
    ? ''
    : 'Enter a valid contact email.'
  const digits = form.contactPhone.replace(/\D/g, '')
  errors.contactPhone = !form.contactPhone || (digits.length >= 7 && digits.length <= 15)
    ? ''
    : 'Enter a valid phone number.'
  return Object.values(errors).every((message) => !message)
}

function handleSubmit() {
  if (!validate()) return
  const payload = { ...form }
  if (props.mode === 'edit') {
    delete payload.code
    delete payload.ownerId
    payload.expectedUpdatedAt = props.library?.updatedAt
  }
  emit('save', payload)
}

function handleClose() {
  if (!props.isSaving) emit('close')
}

watch(
  () => [props.isOpen, props.library],
  () => { if (props.isOpen) resetForm() },
  { immediate: true },
)
</script>

<style scoped>
.super-admin-form { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-4); }
.super-admin-form__full { grid-column: 1 / -1; }
.form-help { color: var(--color-text-muted); font-size: var(--font-size-caption); }

@media (max-width: 560px) {
  .super-admin-form { grid-template-columns: 1fr; }
  .super-admin-form__full { grid-column: auto; }
}
</style>
