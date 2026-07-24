<template>
  <Modal
    :is-open="isOpen"
    title="Update Payment Status"
    title-id="payment-status-dialog-title"
    @close="handleClose"
  >
    <form
      class="payment-status-dialog"
      novalidate
      @submit.prevent="handleSubmit"
    >
      <div v-if="payment" class="payment-status-dialog__summary">
        <div>
          <span class="text-label text-muted">Student</span>
          <strong>{{ payment.studentName }}</strong>
        </div>

        <div>
          <span class="text-label text-muted">Month</span>
          <strong>{{ formatMonth(payment.month) }}</strong>
        </div>

        <div>
          <span class="text-label text-muted">Amount</span>
          <strong>{{ formatCurrency(payment.amount) }}</strong>
        </div>

        <div>
          <span class="text-label text-muted">Current Status</span>
          <span class="badge" :class="getStatusBadgeClass(payment.status)">
            {{ formatLabel(payment.status) }}
          </span>
        </div>
      </div>

      <div
        class="form-field"
        :class="{ 'form-field--error': errors.status }"
      >
        <label class="form-label" for="payment-status">New Status</label>

        <select
          id="payment-status"
          v-model="form.status"
          class="form-select"
          :aria-invalid="Boolean(errors.status)"
        >
          <option value="">Select status</option>
          <option value="paid">Paid</option>
          <option value="unpaid">Unpaid</option>
        </select>

        <p v-if="errors.status" class="form-help">
          {{ errors.status }}
        </p>
      </div>

      <template v-if="form.status === 'paid'">
        <div
          class="form-field"
          :class="{ 'form-field--error': errors.paymentMethod }"
        >
          <label class="form-label" for="payment-method">
            Payment Method
          </label>

          <select
            id="payment-method"
            v-model="form.paymentMethod"
            class="form-select"
            :aria-invalid="Boolean(errors.paymentMethod)"
          >
            <option value="">Select payment method</option>
            <option value="cash">Cash</option>
            <option value="upi">UPI</option>
            <option value="card">Card</option>
            <option value="bank_transfer">Bank Transfer</option>
          </select>

          <p v-if="errors.paymentMethod" class="form-help">
            {{ errors.paymentMethod }}
          </p>
        </div>

        <div class="form-field">
          <label class="form-label" for="payment-transaction-id">
            Transaction ID
          </label>

          <input
            id="payment-transaction-id"
            v-model.trim="form.transactionId"
            class="form-control"
            type="text"
            placeholder="Optional transaction reference"
          />
        </div>
      </template>

      <div class="form-field">
        <label class="form-label" for="payment-notes">Notes</label>

        <textarea
          id="payment-notes"
          v-model.trim="form.notes"
          class="form-textarea"
          placeholder="Optional payment note"
        ></textarea>
      </div>
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
        <span
          v-if="isSubmitting"
          class="btn__loader"
          aria-hidden="true"
        ></span>

        <span>
          {{ isSubmitting ? 'Updating' : 'Update Status' }}
        </span>
      </button>
    </template>
  </Modal>
</template>

<script setup>
import { reactive, watch } from 'vue'

import Modal from '../common/Modal.vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false,
  },
  payment: {
    type: Object,
    default: null,
  },
  isSubmitting: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close', 'confirm'])

const form = reactive({
  status: '',
  paymentMethod: '',
  transactionId: '',
  notes: '',
})

const errors = reactive({})

watch(
  () => props.isOpen,
  (isOpen) => {
    if (isOpen) {
      resetForm()
    }
  },
)

function resetForm() {
  form.status = ''
  form.paymentMethod = ''
  form.transactionId = ''
  form.notes = ''
  clearErrors()
}

function clearErrors() {
  Object.keys(errors).forEach((key) => {
    delete errors[key]
  })
}

function validateForm() {
  clearErrors()

  if (!form.status) {
    errors.status = 'Select a payment status.'
  } else if (form.status === props.payment?.status) {
    errors.status = 'Select a different payment status.'
  }

  if (form.status === 'paid' && !form.paymentMethod) {
    errors.paymentMethod = 'Select a payment method.'
  }

  return Object.keys(errors).length === 0
}

function handleSubmit() {
  if (!props.payment || !validateForm()) return

  emit('confirm', {
    status: form.status,
    paymentMethod:
      form.status === 'paid' ? form.paymentMethod : null,
    transactionId:
      form.status === 'paid' ? form.transactionId : '',
    notes: form.notes,
  })
}

function handleClose() {
  if (props.isSubmitting) return

  emit('close')
}

function formatCurrency(amount) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(Number(amount || 0))
}

function formatMonth(month) {
  if (!month) return '—'

  const [year, monthNumber] = month.split('-')
  const date = new Date(Number(year), Number(monthNumber) - 1, 1)

  return new Intl.DateTimeFormat('en-IN', {
    month: 'long',
    year: 'numeric',
  }).format(date)
}

function formatLabel(value) {
  if (!value) return '—'

  return String(value)
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())
}

function getStatusBadgeClass(status) {
  return status === 'paid' ? 'badge--paid' : 'badge--pending'
}
</script>

<style scoped>
.payment-status-dialog {
  display: grid;
  gap: var(--space-5);
}

.payment-status-dialog__summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.payment-status-dialog__summary > div {
  display: grid;
  align-content: start;
  gap: var(--space-1);
}

.form-field--error .form-help {
  color: var(--color-danger);
}

@media (max-width: 560px) {
  .payment-status-dialog__summary {
    grid-template-columns: 1fr;
  }
}
</style>

<!--
src/components/payment: Payment status management dialog backed by paymentStore.

TODO:
- Replace mock payment updates with FastAPI-backed payment status operations in Milestone 3.
-->