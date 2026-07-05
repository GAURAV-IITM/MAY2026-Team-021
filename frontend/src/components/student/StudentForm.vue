<template>
  <form class="student-form" novalidate @submit.prevent="handleSubmit">
    <section class="form-card student-form__section">
      <header class="card__header">
        <h2 class="text-h5 m-0">Personal Information</h2>
      </header>

      <div class="card__body student-form__grid">
        <div class="form-field" :class="{ 'form-field--error': errors.firstName }">
          <label class="form-label" for="student-first-name">First Name</label>
          <input
            id="student-first-name"
            v-model="form.firstName"
            class="form-control"
            type="text"
            autocomplete="given-name"
            :aria-invalid="Boolean(errors.firstName)"
          />
          <p v-if="errors.firstName" class="form-help">{{ errors.firstName }}</p>
        </div>

        <div class="form-field" :class="{ 'form-field--error': errors.lastName }">
          <label class="form-label" for="student-last-name">Last Name</label>
          <input
            id="student-last-name"
            v-model="form.lastName"
            class="form-control"
            type="text"
            autocomplete="family-name"
            :aria-invalid="Boolean(errors.lastName)"
          />
          <p v-if="errors.lastName" class="form-help">{{ errors.lastName }}</p>
        </div>

        <div class="form-field student-form__full-row">
          <label class="form-label" for="student-address">Address</label>
          <textarea
            id="student-address"
            v-model="form.address"
            class="form-textarea"
            autocomplete="street-address"
          ></textarea>
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
          <label class="form-label" for="student-status">Status</label>
          <select id="student-status" v-model="form.status" class="form-select">
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
      </div>
    </section>

    <section class="form-card student-form__section">
      <header class="card__header">
        <h2 class="text-h5 m-0">Contact Information</h2>
      </header>

      <div class="card__body student-form__grid">
        <div class="form-field" :class="{ 'form-field--error': errors.email }">
          <label class="form-label" for="student-email">Email</label>
          <input
            id="student-email"
            v-model="form.email"
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
            v-model="form.phone"
            class="form-control"
            type="tel"
            inputmode="numeric"
            autocomplete="tel"
            :aria-invalid="Boolean(errors.phone)"
          />
          <p v-if="errors.phone" class="form-help">{{ errors.phone }}</p>
        </div>

        <div class="form-field">
          <label class="form-label" for="student-guardian-name">Guardian Name</label>
          <input
            id="student-guardian-name"
            v-model="form.guardianName"
            class="form-control"
            type="text"
          />
        </div>

        <div
          class="form-field"
          :class="{ 'form-field--error': errors.guardianPhone }"
        >
          <label class="form-label" for="student-guardian-phone">Guardian Phone</label>
          <input
            id="student-guardian-phone"
            v-model="form.guardianPhone"
            class="form-control"
            type="tel"
            inputmode="numeric"
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
        <h2 class="text-h5 m-0">Seat & Shift Information</h2>
      </header>

      <div class="card__body student-form__grid">
        <div class="form-field" :class="{ 'form-field--error': errors.seatNumber }">
          <label class="form-label" for="student-seat">Seat Number</label>
          <input
            id="student-seat"
            v-model="form.seatNumber"
            class="form-control"
            type="text"
            placeholder="Example: A-01"
            :aria-invalid="Boolean(errors.seatNumber)"
          />
          <p v-if="errors.seatNumber" class="form-help">{{ errors.seatNumber }}</p>
        </div>

        <div class="form-field" :class="{ 'form-field--error': errors.shift }">
          <label class="form-label" for="student-shift">Shift</label>
          <select
            id="student-shift"
            v-model="form.shift"
            class="form-select"
            :aria-invalid="Boolean(errors.shift)"
          >
            <option value="">Select shift</option>
            <option value="morning">Morning</option>
            <option value="afternoon">Afternoon</option>
            <option value="evening">Evening</option>
          </select>
          <p v-if="errors.shift" class="form-help">{{ errors.shift }}</p>
        </div>
      </div>
    </section>

    <section class="form-card student-form__section">
      <header class="card__header">
        <h2 class="text-h5 m-0">Fee Details</h2>
      </header>

      <div class="card__body student-form__grid">
        <div class="form-field" :class="{ 'form-field--error': errors.feeAmount }">
          <label class="form-label" for="student-fee-amount">Fee Amount</label>
          <input
            id="student-fee-amount"
            v-model="form.feeAmount"
            class="form-control"
            type="number"
            min="0"
            step="1"
            :aria-invalid="Boolean(errors.feeAmount)"
          />
          <p v-if="errors.feeAmount" class="form-help">{{ errors.feeAmount }}</p>
        </div>

        <div class="form-field">
          <label class="form-label" for="student-fee-status">Fee Status</label>
          <select id="student-fee-status" v-model="form.feeStatus" class="form-select">
            <option value="paid">Paid</option>
            <option value="pending">Pending</option>
            <option value="overdue">Overdue</option>
          </select>
        </div>

        <div class="form-field" :class="{ 'form-field--error': errors.feeDueDate }">
          <label class="form-label" for="student-fee-due-date">Fee Due Date</label>
          <input
            id="student-fee-due-date"
            v-model="form.feeDueDate"
            class="form-control"
            type="date"
            :aria-invalid="Boolean(errors.feeDueDate)"
          />
          <p v-if="errors.feeDueDate" class="form-help">{{ errors.feeDueDate }}</p>
        </div>
      </div>
    </section>

    <div class="student-form__actions">
      <button class="btn btn--secondary" type="button" :disabled="isSubmitting" @click="$emit('cancel')">
        Cancel
      </button>

      <button class="btn btn--primary" type="submit" :disabled="isSubmitting">
        <span v-if="isSubmitting" class="btn__loader" aria-hidden="true"></span>
        <span>{{ isSubmitting ? submittingLabel : submitLabel }}</span>
      </button>
    </div>
  </form>
</template>

<script setup>
import { reactive, watch } from 'vue'

import {
  isPositiveNumber,
  isRequired,
  isValidEmail,
  isValidIndianPhone,
} from '../../utils/validators'

const props = defineProps({
  initialValues: {
    type: Object,
    default: () => ({}),
  },
  isSubmitting: {
    type: Boolean,
    default: false,
  },
  submitLabel: {
    type: String,
    default: 'Save Student',
  },
  submittingLabel: {
    type: String,
    default: 'Saving Student',
  },
})

const emit = defineEmits(['submit', 'cancel'])

function createInitialForm(values = {}) {
  return {
    firstName: values.firstName || '',
    lastName: values.lastName || '',
    email: values.email || '',
    phone: values.phone || '',
    address: values.address || '',
    guardianName: values.guardianName || '',
    guardianPhone: values.guardianPhone || '',
    seatNumber: values.seatNumber || '',
    shift: values.shift || '',
    feeAmount: values.feeAmount ?? '',
    feeStatus: values.feeStatus || 'pending',
    feeDueDate: values.feeDueDate || '',
    status: values.status || 'active',
    joiningDate: values.joiningDate || '',
  }
}

const form = reactive(createInitialForm(props.initialValues))
const errors = reactive({})

watch(
  () => props.initialValues,
  (values) => {
    Object.assign(form, createInitialForm(values))
    clearErrors()
  },
  { deep: true },
)

function clearErrors() {
  Object.keys(errors).forEach((key) => {
    delete errors[key]
  })
}

function validateForm() {
  clearErrors()

  if (!isRequired(form.firstName)) {
    errors.firstName = 'First name is required.'
  }

  if (!isRequired(form.lastName)) {
    errors.lastName = 'Last name is required.'
  }

  if (!isValidEmail(form.email)) {
    errors.email = 'Enter a valid email address.'
  }

  if (!isValidIndianPhone(form.phone)) {
    errors.phone = 'Enter a valid 10-digit Indian phone number.'
  }

  if (isRequired(form.guardianPhone) && !isValidIndianPhone(form.guardianPhone)) {
    errors.guardianPhone = 'Enter a valid 10-digit Indian phone number.'
  }

  if (!isRequired(form.seatNumber)) {
    errors.seatNumber = 'Seat selection is required.'
  }

  if (!isRequired(form.shift)) {
    errors.shift = 'Shift selection is required.'
  }

  if (!isPositiveNumber(form.feeAmount)) {
    errors.feeAmount = 'Fee amount must be greater than zero.'
  }

  if (!isRequired(form.feeDueDate)) {
    errors.feeDueDate = 'Fee due date is required.'
  }

  if (!isRequired(form.joiningDate)) {
    errors.joiningDate = 'Joining date is required.'
  }

  return Object.keys(errors).length === 0
}

function handleSubmit() {
  if (!validateForm()) return

  emit('submit', {
    ...form,
    firstName: form.firstName.trim(),
    lastName: form.lastName.trim(),
    email: form.email.trim(),
    phone: form.phone.trim(),
    address: form.address.trim(),
    guardianName: form.guardianName.trim(),
    guardianPhone: form.guardianPhone.trim(),
    seatNumber: form.seatNumber.trim(),
    feeAmount: Number(form.feeAmount),
  })
}
</script>

<style scoped>
.student-form {
  display: grid;
  gap: var(--space-5);
}

.student-form__section {
  overflow: hidden;
}

.student-form__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-5);
}

.student-form__full-row {
  grid-column: 1 / -1;
}

.student-form__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}

.form-field--error .form-help {
  color: var(--color-danger);
}

@media (max-width: 700px) {
  .student-form__grid {
    grid-template-columns: 1fr;
  }

  .student-form__full-row {
    grid-column: auto;
  }
}

@media (max-width: 480px) {
  .student-form__actions {
    flex-direction: column-reverse;
  }
}
</style>