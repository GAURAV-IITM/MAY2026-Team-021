<template>
  <Modal
    :is-open="isOpen"
    title="WhatsApp Fee Reminder"
    title-id="whatsapp-reminder-dialog-title"
    @close="handleClose"
  >
    <form class="whatsapp-reminder-dialog" novalidate @submit.prevent="handleSubmit">
      <section v-if="payment" class="whatsapp-reminder-dialog__payment">
        <div>
          <p class="text-label text-muted m-0">Student</p>
          <h3 class="text-h5 m-0">{{ payment.studentName }}</h3>
        </div>
        <span class="badge badge--pending">{{ formatStatus(payment.status) }}</span>

        <dl class="whatsapp-reminder-dialog__details">
          <div>
            <dt>Billing Month</dt>
            <dd>{{ formatMonth(payment.month) }}</dd>
          </div>
          <div>
            <dt>Outstanding Balance</dt>
            <dd>{{ formatCurrency(payment.balanceAmount) }}</dd>
          </div>
          <div>
            <dt>Due Date</dt>
            <dd>{{ formatDate(payment.dueDate) }}</dd>
          </div>
          <div>
            <dt>Phone Number</dt>
            <dd>{{ payment.studentPhone || 'Not available' }}</dd>
          </div>
        </dl>
      </section>

      <div class="form-field">
        <label class="form-label" for="whatsapp-reminder-message">
          Message Preview
        </label>
        <textarea
          id="whatsapp-reminder-message"
          v-model="message"
          class="form-textarea whatsapp-reminder-dialog__message"
          rows="8"
          maxlength="2000"
          :disabled="isSubmitting"
        ></textarea>
        <p class="form-help text-muted">
          The server rechecks the balance and records the attempt before
          WhatsApp opens.
        </p>
      </div>

      <div v-if="submissionError" class="alert alert--danger" role="alert">
        <div>
          <strong>Unable to create the reminder link.</strong>
          <p class="m-0">{{ submissionError.message }}</p>
          <p v-if="submissionError.requestId" class="text-caption m-0">
            Request ID: {{ submissionError.requestId }}
          </p>
        </div>
      </div>

      <p class="text-small text-muted m-0">
        Opening a WhatsApp link does not mean the message was sent or delivered.
      </p>
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
        :disabled="isSubmitting || !payment || payment.balanceAmount <= 0"
        @click="handleSubmit"
      >
        <span v-if="isSubmitting" class="btn__loader" aria-hidden="true"></span>
        <MessageCircle v-else :size="17" aria-hidden="true" />
        {{ isSubmitting ? 'Recording attempt...' : 'Open WhatsApp' }}
      </button>
    </template>
  </Modal>
</template>

<script setup>
import { MessageCircle } from '@lucide/vue'
import { ref, watch } from 'vue'

import Modal from '../common/Modal.vue'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  payment: { type: Object, default: null },
  isSubmitting: { type: Boolean, default: false },
  submissionError: { type: Object, default: null },
})

const emit = defineEmits(['close', 'submit'])
const message = ref('')
const initialMessage = ref('')

watch(
  () => [props.isOpen, props.payment?.id],
  ([isOpen]) => {
    if (!isOpen) return
    initialMessage.value = buildDefaultMessage(props.payment)
    message.value = initialMessage.value
  },
)

function buildDefaultMessage(payment) {
  if (!payment) return ''
  return (
    `Hello ${payment.studentName},\n\n` +
    `This is a reminder that your library fee for ${formatMonth(payment.month)} ` +
    `has an outstanding balance of ${formatCurrency(payment.balanceAmount)}.\n\n` +
    `Due date: ${formatDate(payment.dueDate)}.\n\n` +
    'Please contact the library if you have already paid or need assistance.'
  )
}

function handleSubmit() {
  if (!props.payment || props.isSubmitting || props.payment.balanceAmount <= 0) return
  const editedMessage = message.value.trim()
  emit('submit', {
    message:
      editedMessage && editedMessage !== initialMessage.value.trim()
        ? editedMessage
        : undefined,
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

function formatDate(value) {
  if (!value) return 'Not available'
  return new Intl.DateTimeFormat('en-IN', {
    dateStyle: 'medium',
  }).format(new Date(`${value}T00:00:00`))
}

function formatStatus(status) {
  return String(status || 'pending')
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())
}
</script>

<style scoped>
.whatsapp-reminder-dialog {
  display: grid;
  gap: var(--space-5);
}

.whatsapp-reminder-dialog__payment {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: var(--space-4);
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-secondary);
}

.whatsapp-reminder-dialog__details {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-3);
  margin: 0;
}

.whatsapp-reminder-dialog__details div {
  display: grid;
  gap: var(--space-1);
}

.whatsapp-reminder-dialog__details dt {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.whatsapp-reminder-dialog__details dd {
  margin: 0;
  font-weight: var(--font-weight-medium);
  overflow-wrap: anywhere;
}

.whatsapp-reminder-dialog__message {
  min-height: 180px;
  resize: vertical;
}

@media (max-width: 640px) {
  .whatsapp-reminder-dialog__details {
    grid-template-columns: 1fr;
  }
}
</style>
