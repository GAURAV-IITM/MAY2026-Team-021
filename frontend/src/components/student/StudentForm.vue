<template>
  <form class="student-form" novalidate @submit.prevent="handleSubmit">
    <section class="form-card student-form__section">
      <header class="card__header">
        <div>
          <h2 class="text-h5 m-0">Student Profile</h2>
          <p class="text-small text-muted m-0">Identity and enrollment details.</p>
        </div>
      </header>

      <div class="card__body student-form__grid">
        <div class="form-field">
          <label class="form-label" for="student-enrollment">Enrollment Number</label>
          <input
            id="student-enrollment"
            v-model.trim="form.enrollmentNumber"
            class="form-control"
            placeholder="Generated automatically when left empty"
          />
        </div>

        <div class="form-field" :class="{ 'form-field--error': errors.status }">
          <label class="form-label" for="student-status">Status</label>
          <select id="student-status" v-model="form.status" class="form-select">
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="suspended">Suspended</option>
            <option value="left">Left</option>
          </select>
        </div>

        <div class="form-field" :class="{ 'form-field--error': errors.firstName }">
          <label class="form-label" for="student-first-name">First Name</label>
          <input
            id="student-first-name"
            v-model.trim="form.firstName"
            class="form-control"
            autocomplete="given-name"
            :aria-invalid="Boolean(errors.firstName)"
          />
          <p v-if="errors.firstName" class="form-help">{{ errors.firstName }}</p>
        </div>

        <div class="form-field" :class="{ 'form-field--error': errors.lastName }">
          <label class="form-label" for="student-last-name">Last Name</label>
          <input
            id="student-last-name"
            v-model.trim="form.lastName"
            class="form-control"
            autocomplete="family-name"
            :aria-invalid="Boolean(errors.lastName)"
          />
          <p v-if="errors.lastName" class="form-help">{{ errors.lastName }}</p>
        </div>

        <div class="form-field" :class="{ 'form-field--error': errors.joiningDate }">
          <label class="form-label" for="student-joining-date">Joining Date</label>
          <input
            id="student-joining-date"
            v-model="form.joiningDate"
            class="form-control"
            type="date"
            :aria-invalid="Boolean(errors.joiningDate)"
          />
          <p v-if="errors.joiningDate" class="form-help">{{ errors.joiningDate }}</p>
        </div>

        <div class="form-field">
          <label class="form-label" for="student-date-of-birth">Date of Birth</label>
          <input
            id="student-date-of-birth"
            v-model="form.dateOfBirth"
            class="form-control"
            type="date"
          />
        </div>

        <div class="form-field student-form__full-row">
          <label class="form-label" for="student-address">Address</label>
          <textarea
            id="student-address"
            v-model.trim="form.address"
            class="form-textarea"
            autocomplete="street-address"
          ></textarea>
        </div>
      </div>
    </section>

    <section class="form-card student-form__section">
      <header class="card__header">
        <div>
          <h2 class="text-h5 m-0">Contact Information</h2>
          <p class="text-small text-muted m-0">Used for account access and notices.</p>
        </div>
      </header>

      <div class="card__body student-form__grid">
        <div class="form-field" :class="{ 'form-field--error': errors.email }">
          <label class="form-label" for="student-email">Email</label>
          <input
            id="student-email"
            v-model.trim="form.email"
            class="form-control"
            type="email"
            autocomplete="email"
            :aria-invalid="Boolean(errors.email)"
          />
          <p v-if="errors.email" class="form-help">{{ errors.email }}</p>
        </div>

        <div class="form-field" :class="{ 'form-field--error': errors.phone }">
          <label class="form-label" for="student-phone">Phone</label>
          <input
            id="student-phone"
            v-model.trim="form.phone"
            class="form-control"
            type="tel"
            autocomplete="tel"
            :aria-invalid="Boolean(errors.phone)"
          />
          <p v-if="errors.phone" class="form-help">{{ errors.phone }}</p>
        </div>

        <div class="form-field">
          <label class="form-label" for="student-guardian-name">Guardian Name</label>
          <input
            id="student-guardian-name"
            v-model.trim="form.guardianName"
            class="form-control"
          />
        </div>

        <div class="form-field" :class="{ 'form-field--error': errors.guardianPhone }">
          <label class="form-label" for="student-guardian-phone">Guardian Phone</label>
          <input
            id="student-guardian-phone"
            v-model.trim="form.guardianPhone"
            class="form-control"
            type="tel"
            :aria-invalid="Boolean(errors.guardianPhone)"
          />
          <p v-if="errors.guardianPhone" class="form-help">
            {{ errors.guardianPhone }}
          </p>
        </div>
      </div>
    </section>

    <section class="form-card student-form__section">
      <header class="card__header">
        <div>
          <h2 class="text-h5 m-0">Library Preferences</h2>
          <p class="text-small text-muted m-0">Fee default and administrative notes.</p>
        </div>
      </header>

      <div class="card__body student-form__grid">
        <div class="form-field" :class="{ 'form-field--error': errors.feeAmount }">
          <label class="form-label" for="student-fee-amount">Monthly Fee</label>
          <input
            id="student-fee-amount"
            v-model.number="form.feeAmount"
            class="form-control"
            type="number"
            min="0"
            step="1"
            :aria-invalid="Boolean(errors.feeAmount)"
          />
          <p v-if="errors.feeAmount" class="form-help">{{ errors.feeAmount }}</p>
        </div>

        <div class="form-field">
          <label class="form-label" for="student-language">Preferred Language</label>
          <select id="student-language" v-model="form.preferredLanguage" class="form-select">
            <option value="en">English</option>
            <option value="hi">Hindi</option>
          </select>
        </div>

        <div class="form-field student-form__full-row">
          <label class="form-label" for="student-notes">Notes</label>
          <textarea
            id="student-notes"
            v-model.trim="form.notes"
            class="form-textarea"
            placeholder="Optional internal notes"
          ></textarea>
        </div>

        <label v-if="!isEditMode" class="checkbox student-form__invitation">
          <input v-model="form.sendInvitation" type="checkbox" />
          <span>
            <strong>Create student portal invitation</strong>
            <small>A password setup link will be created after registration.</small>
          </span>
        </label>
      </div>
    </section>

    <div class="student-form__actions">
      <button class="btn btn--secondary" type="button" :disabled="isSubmitting" @click="$emit('cancel')">
        Cancel
      </button>
      <button class="btn btn--primary" type="submit" :disabled="isSubmitting">
        <span v-if="isSubmitting" class="btn__loader" aria-hidden="true"></span>
        {{ isSubmitting ? submittingLabel : submitLabel }}
      </button>
    </div>
  </form>
</template>

<script setup>
import { computed, reactive } from 'vue'

import {
  isNonNegativeNumber,
  isRequired,
  isValidEmail,
  isValidIndianPhone,
} from '../../utils/validators'

const props = defineProps({
  initialValues: { type: Object, default: () => ({}) },
  isSubmitting: { type: Boolean, default: false },
  submitLabel: { type: String, default: 'Save Student' },
  submittingLabel: { type: String, default: 'Saving Student' },
})

const emit = defineEmits(['submit', 'cancel'])
const isEditMode = computed(() => Boolean(props.initialValues?.id))
const today = new Date().toISOString().slice(0, 10)
const form = reactive({
  enrollmentNumber: props.initialValues.enrollmentNumber || '',
  firstName: props.initialValues.firstName || '',
  lastName: props.initialValues.lastName || '',
  email: props.initialValues.email || '',
  phone: props.initialValues.phone || '',
  address: props.initialValues.address || '',
  guardianName: props.initialValues.guardianName || '',
  guardianPhone: props.initialValues.guardianPhone || '',
  dateOfBirth: props.initialValues.dateOfBirth || '',
  preferredLanguage: props.initialValues.preferredLanguage || 'en',
  joiningDate: props.initialValues.joiningDate || today,
  feeAmount: Number(props.initialValues.feeAmount ?? 0),
  status: props.initialValues.status || 'active',
  notes: props.initialValues.notes || '',
  sendInvitation: true,
})
const errors = reactive({})

function clearErrors() {
  Object.keys(errors).forEach((key) => delete errors[key])
}

function validate() {
  clearErrors()
  if (!isRequired(form.firstName)) errors.firstName = 'First name is required.'
  if (!isRequired(form.lastName)) errors.lastName = 'Last name is required.'
  if (!isValidEmail(form.email)) errors.email = 'Enter a valid email address.'
  if (!isValidIndianPhone(form.phone)) errors.phone = 'Enter a valid 10-digit phone number.'
  if (form.guardianPhone && !isValidIndianPhone(form.guardianPhone)) {
    errors.guardianPhone = 'Enter a valid 10-digit phone number.'
  }
  if (!form.joiningDate) errors.joiningDate = 'Joining date is required.'
  if (!isNonNegativeNumber(form.feeAmount)) {
    errors.feeAmount = 'Monthly fee cannot be negative.'
  }
  return Object.keys(errors).length === 0
}

function handleSubmit() {
  if (!validate()) {
    requestAnimationFrame(() => {
      document.querySelector('.form-field--error input')?.focus()
    })
    return
  }
  const payload = {
    enrollmentNumber: form.enrollmentNumber || undefined,
    firstName: form.firstName,
    lastName: form.lastName,
    email: form.email.toLowerCase(),
    phone: form.phone,
    address: form.address || null,
    guardianName: form.guardianName || null,
    guardianPhone: form.guardianPhone || null,
    dateOfBirth: form.dateOfBirth || null,
    preferredLanguage: form.preferredLanguage,
    joiningDate: form.joiningDate,
    feeAmount: Number(form.feeAmount),
    status: form.status,
    notes: form.notes || null,
  }
  if (!isEditMode.value) payload.sendInvitation = form.sendInvitation
  emit('submit', payload)
}
</script>

<style scoped>
.student-form { display: grid; gap: var(--space-5); }
.student-form__section { overflow: hidden; }
.student-form__section .card__header > div { display: grid; gap: var(--space-1); }
.student-form__grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-4); }
.student-form__full-row { grid-column: 1 / -1; }
.student-form__actions { display: flex; justify-content: flex-end; gap: var(--space-3); }
.student-form__invitation { grid-column: 1 / -1; align-items: flex-start; padding: var(--space-4); border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-muted); }
.student-form__invitation span { display: grid; gap: var(--space-1); }
.student-form__invitation small { color: var(--color-text-muted); }
.form-field--error .form-help { color: var(--color-danger); }
@media (max-width: 680px) {
  .student-form__grid { grid-template-columns: 1fr; }
  .student-form__full-row, .student-form__invitation { grid-column: auto; }
  .student-form__actions { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
</style>
