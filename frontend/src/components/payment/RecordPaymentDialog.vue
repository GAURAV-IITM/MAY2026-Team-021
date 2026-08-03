<template>
  <Modal
    :is-open="isOpen"
    title="Record Payment"
    title-id="record-payment-dialog-title"
    @close="handleClose"
  >
    <form class="record-payment" novalidate @submit.prevent="handleSubmit">
      <div v-if="payment" class="record-payment__summary">
        <div>
          <span class="text-label text-muted">Student</span>
          <strong>{{ payment.studentName }}</strong>
        </div>
        <div>
          <span class="text-label text-muted">Billing Month</span>
          <strong>{{ formatMonth(payment.month) }}</strong>
        </div>
        <div>
          <span class="text-label text-muted">Fee Total</span>
          <strong>{{ formatCurrency(payment.totalAmount) }}</strong>
        </div>
        <div>
          <span class="text-label text-muted">Remaining Balance</span>
          <strong>{{ formatCurrency(payment.balanceAmount) }}</strong>
        </div>
      </div>

      <div
        v-if="submissionError?.message"
        class="alert alert--danger"
        role="alert"
      >
        <div>
          <strong>Payment was not recorded.</strong>
          <p class="m-0">{{ submissionError.message }}</p>
          <p
            v-if="submissionError.remainingBalance"
            class="text-small m-0"
          >
            Current remaining balance:
            {{ formatCurrency(submissionError.remainingBalance) }}
          </p>
          <p v-if="submissionError.requestId" class="text-caption m-0">
            Request ID: {{ submissionError.requestId }}
          </p>
        </div>
      </div>

      <div class="record-payment__grid">
        <div class="form-field" :class="{ 'form-field--error': errors.amount }">
          <label class="form-label" for="payment-amount">Amount</label>
          <input
            id="payment-amount"
            v-model="form.amount"
            class="form-control"
            type="number"
            min="0.01"
            :max="payment?.balanceAmount"
            step="0.01"
            inputmode="decimal"
            :aria-invalid="Boolean(errors.amount)"
          />
          <p v-if="errors.amount" class="form-help">{{ errors.amount }}</p>
          <p
            v-else-if="isPartialPayment"
            class="form-help record-payment__partial"
          >
            This will be recorded as a partial payment.
          </p>
        </div>

        <div class="form-field" :class="{ 'form-field--error': errors.method }">
          <label class="form-label" for="payment-method">Payment Method</label>
          <select
            id="payment-method"
            v-model="form.method"
            class="form-select"
            :aria-invalid="Boolean(errors.method)"
          >
            <option value="">Select method</option>
            <option value="cash">Cash</option>
            <option value="upi">UPI</option>
            <option value="bank_transfer">Bank Transfer</option>
            <option value="card">Card</option>
            <option value="other">Other</option>
          </select>
          <p v-if="errors.method" class="form-help">{{ errors.method }}</p>
        </div>

        <div class="form-field">
          <label class="form-label" for="payment-paid-at">Paid At</label>
          <input
            id="payment-paid-at"
            v-model="form.paidAt"
            class="form-control"
            type="datetime-local"
          />
        </div>

        <div class="form-field">
          <label class="form-label" for="payment-reference">
            Reference Number
          </label>
          <input
            id="payment-reference"
            v-model.trim="form.referenceNumber"
            class="form-control"
            type="text"
            maxlength="120"
            placeholder="Optional UPI or bank reference"
          />
        </div>
      </div>

      <div class="form-field">
        <label class="form-label" for="payment-notes">Notes</label>
        <textarea
          id="payment-notes"
          v-model.trim="form.notes"
          class="form-textarea"
          maxlength="2000"
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
        {{ isSubmitting ? 'Recording...' : 'Record Payment' }}
      </button>
    </template>
  </Modal>
</template>

<script setup>
import { computed, reactive, watch } from 'vue'

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
  submissionError: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['close', 'confirm'])
const form = reactive({
  amount: '',
  method: '',
  paidAt: '',
  referenceNumber: '',
  notes: '',
})
const errors = reactive({})

const isPartialPayment = computed(() => {
  const amount = Number(form.amount)
  const balance = Number(props.payment?.balanceAmount || 0)
  return amount > 0 && amount < balance
})

watch(
  () => [props.isOpen, props.payment?.id],
  ([isOpen]) => {
    if (isOpen) resetForm()
  },
  { immediate: true },
)

function localDateTimeValue() {
  const now = new Date()
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000)
  return local.toISOString().slice(0, 16)
}

function resetForm() {
  form.amount = props.payment?.balanceAmount
    ? Number(props.payment.balanceAmount).toFixed(2)
    : ''
  form.method = ''
  form.paidAt = localDateTimeValue()
  form.referenceNumber = ''
  form.notes = ''
  Object.keys(errors).forEach((key) => delete errors[key])
}

function validate() {
  Object.keys(errors).forEach((key) => delete errors[key])
  const amount = Number(form.amount)
  const balance = Number(props.payment?.balanceAmount || 0)

  if (!Number.isFinite(amount) || amount <= 0) {
    errors.amount = 'Enter an amount greater than zero.'
  } else if (amount > balance) {
    errors.amount = `Amount cannot exceed ${formatCurrency(balance)}.`
  }
  if (!form.method) {
    errors.method = 'Select a payment method.'
  }
  return Object.keys(errors).length === 0
}

function handleSubmit() {
  if (!props.payment || !validate()) return

  emit('confirm', {
    amount: Number(form.amount).toFixed(2),
    method: form.method,
    paidAt: form.paidAt
      ? new Date(form.paidAt).toISOString()
      : undefined,
    referenceNumber: form.referenceNumber,
    notes: form.notes,
  })
}

function handleClose() {
  if (!props.isSubmitting) emit('close')
}

function formatCurrency(amount) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(amount || 0))
}

function formatMonth(month) {
  if (!month) return 'Not available'
  const [year, monthNumber] = month.split('-').map(Number)
  return new Intl.DateTimeFormat('en-IN', {
    month: 'long',
    year: 'numeric',
  }).format(new Date(year, monthNumber - 1, 1))
}
</script>

<style scoped>
.record-payment {
  display: grid;
  gap: var(--space-5);
}

.record-payment__summary,
.record-payment__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
}

.record-payment__summary {
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-muted);
}

.record-payment__summary > div {
  display: grid;
  gap: var(--space-1);
}

.record-payment__partial {
  color: var(--color-warning);
}

@media (max-width: 640px) {
  .record-payment__summary,
  .record-payment__grid {
    grid-template-columns: 1fr;
  }
}
</style>
