<template>
  <Modal
    :is-open="isOpen"
    title="WhatsApp Fee Reminder"
    title-id="whatsapp-reminder-dialog-title"
    @close="handleClose"
  >
    <form
      class="whatsapp-reminder-dialog"
      novalidate
      @submit.prevent="handleGenerate"
    >
      <section
        v-if="payment"
        class="whatsapp-reminder-dialog__payment card"
      >
        <div>
          <p class="text-label text-muted m-0">Student</p>
          <h3 class="text-h5 m-0">{{ payment.studentName }}</h3>
        </div>

        <span class="badge badge--pending">
          {{ formatStatus(payment.status) }}
        </span>

        <dl class="whatsapp-reminder-dialog__details">
          <div>
            <dt>Payment Month</dt>
            <dd>{{ formatMonth(payment.month) }}</dd>
          </div>

          <div>
            <dt>Pending Amount</dt>
            <dd>{{ formatCurrency(payment.amount) }}</dd>
          </div>

          <div>
            <dt>Phone Number</dt>
            <dd>{{ payment.studentPhone || '—' }}</dd>
          </div>
        </dl>
      </section>

      <div
        class="form-field"
        :class="{ 'form-field--error': messageError }"
      >
        <label class="form-label" for="whatsapp-reminder-message">
          Message Preview
        </label>

        <textarea
          id="whatsapp-reminder-message"
          v-model="message"
          class="form-textarea whatsapp-reminder-dialog__message"
          rows="7"
          :disabled="isSubmitting"
          :aria-invalid="Boolean(messageError)"
        ></textarea>

        <p v-if="messageError" class="form-help">
          {{ messageError }}
        </p>

        <p v-else class="form-help text-muted">
          You can edit the reminder before generating the WhatsApp link.
        </p>
      </div>

      <section
        v-if="reminder"
        class="whatsapp-reminder-dialog__generated alert alert--success"
        aria-live="polite"
      >
        <div>
          <p class="text-label m-0">WhatsApp Link Ready</p>
          <p class="text-small m-0">
            The reminder link has been generated. Open WhatsApp to review and
            send the message.
          </p>
        </div>
      </section>
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
        v-if="!reminder"
        class="btn btn--primary"
        type="button"
        :disabled="isSubmitting || !payment"
        @click="handleGenerate"
      >
        <span
          v-if="isSubmitting"
          class="btn__loader"
          aria-hidden="true"
        ></span>
        <span>
          {{ isSubmitting ? 'Generating' : 'Generate WhatsApp Link' }}
        </span>
      </button>

      <button
        v-else
        class="btn btn--primary"
        type="button"
        @click="handleOpenWhatsApp"
      >
        Open WhatsApp
      </button>
    </template>
  </Modal>
</template>

<script setup>
import { ref, watch } from 'vue'

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
  reminder: {
    type: Object,
    default: null,
  },
  isSubmitting: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close', 'generate', 'open-whatsapp'])

const message = ref('')
const messageError = ref('')

watch(
  () => [props.isOpen, props.payment?.id],
  ([isOpen]) => {
    if (!isOpen) return

    message.value = buildDefaultMessage(props.payment)
    messageError.value = ''
  },
)

function buildDefaultMessage(payment) {
  if (!payment) return ''

  return (
    `Hello ${payment.studentName}, this is a reminder that your library fee ` +
    `of ₹${payment.amount} for ${payment.month} is pending. ` +
    'Please complete the payment at your earliest convenience.'
  )
}

function validateMessage() {
  messageError.value = ''

  if (!message.value.trim()) {
    messageError.value = 'Enter a reminder message.'
  }

  return !messageError.value
}

function handleGenerate() {
  if (!props.payment || props.isSubmitting) return
  if (!validateMessage()) return

  emit('generate', {
    message: message.value.trim(),
  })
}

function handleOpenWhatsApp() {
  if (!props.reminder?.whatsappUrl) return

  emit('open-whatsapp', props.reminder.whatsappUrl)
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

function formatStatus(status) {
  if (!status) return 'Pending'

  return String(status)
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
}

.whatsapp-reminder-dialog__details {
  grid-column: 1 / -1;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
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
}

.whatsapp-reminder-dialog__message {
  min-height: 160px;
  resize: vertical;
}

.whatsapp-reminder-dialog__generated {
  display: grid;
  gap: var(--space-1);
}

.form-field--error .form-help {
  color: var(--color-danger);
}

@media (max-width: 640px) {
  .whatsapp-reminder-dialog__details {
    grid-template-columns: 1fr;
  }
}
</style>

<!--
src/components/payment: Reusable WhatsApp fee reminder preview dialog.

TODO:
- Replace mock WhatsApp link generation with backend-owned reminder delivery
  and audit logging in Milestone 3.
-->
