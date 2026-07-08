<template>
  <Modal
    :is-open="isOpen"
    title="Payment Receipt"
    title-id="receipt-preview-dialog-title"
    @close="handleClose"
  >
    <article v-if="receipt" class="receipt-preview">
      <header class="receipt-preview__header">
        <div>
          <p class="text-label text-muted m-0">Smart Library App</p>
          <h3 class="text-h4 m-0">Payment Receipt</h3>
        </div>

        <span class="badge badge--success">Paid</span>
      </header>

      <section class="receipt-preview__number" aria-label="Receipt number">
        <span class="text-small text-muted">Receipt Number</span>
        <strong>{{ receipt.receiptNumber || 'Not available' }}</strong>
      </section>

      <dl class="receipt-preview__details">
        <div class="receipt-preview__detail">
          <dt>Student</dt>
          <dd>{{ receipt.studentName || 'Not available' }}</dd>
        </div>

        <div class="receipt-preview__detail">
          <dt>Seat Number</dt>
          <dd>{{ receipt.seatNumber || 'Not assigned' }}</dd>
        </div>

        <div class="receipt-preview__detail">
          <dt>Payment Month</dt>
          <dd>{{ formatMonth(receipt.month) }}</dd>
        </div>

        <div class="receipt-preview__detail">
          <dt>Amount Paid</dt>
          <dd>{{ formatCurrency(receipt.amount) }}</dd>
        </div>

        <div class="receipt-preview__detail">
          <dt>Payment Method</dt>
          <dd>{{ formatPaymentMethod(receipt.paymentMethod) }}</dd>
        </div>

        <div class="receipt-preview__detail">
          <dt>Payment Date</dt>
          <dd>{{ formatDateTime(receipt.paidAt) }}</dd>
        </div>

        <div class="receipt-preview__detail receipt-preview__detail--full">
          <dt>Transaction ID</dt>
          <dd class="receipt-preview__transaction">
            {{ receipt.transactionId || 'Not available' }}
          </dd>
        </div>
      </dl>

      <p class="receipt-preview__note text-small text-muted">
        This receipt preview is generated from the current mock payment service.
        File download will be connected when the receipt API is available.
      </p>
    </article>

    <div v-else class="receipt-preview__empty">
      <p class="m-0 text-muted">No receipt selected.</p>
    </div>

    <template #footer>
      <button class="btn btn--secondary" type="button" @click="handleClose">
        Close
      </button>

      <button
        class="btn btn--primary"
        type="button"
        :disabled="!receipt"
        @click="handleDownload"
      >
        Download Receipt
      </button>
    </template>
  </Modal>
</template>

<script setup>
import Modal from '../common/Modal.vue'

defineProps({
  isOpen: {
    type: Boolean,
    default: false,
  },
  receipt: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['close', 'download'])

function formatCurrency(amount) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(Number(amount || 0))
}

function formatMonth(month) {
  if (!month) return 'Not available'

  const [year, monthNumber] = month.split('-').map(Number)

  if (!year || !monthNumber) return month

  return new Intl.DateTimeFormat('en-IN', {
    month: 'long',
    year: 'numeric',
  }).format(new Date(year, monthNumber - 1, 1))
}

function formatDateTime(value) {
  if (!value) return 'Not available'

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) return value

  return new Intl.DateTimeFormat('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

function formatPaymentMethod(method) {
  if (!method) return 'Not available'

  return String(method)
    .split(/[-_]/)
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function handleClose() {
  emit('close')
}

function handleDownload() {
  emit('download')
}
</script>

<style scoped>
.receipt-preview {
  display: grid;
  gap: var(--space-5);
}

.receipt-preview__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
}

.receipt-preview__number {
  display: grid;
  gap: var(--space-1);
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.receipt-preview__details {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-4);
  margin: 0;
}

.receipt-preview__detail {
  display: grid;
  gap: var(--space-1);
  min-width: 0;
}

.receipt-preview__detail--full {
  grid-column: 1 / -1;
}

.receipt-preview__detail dt {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.receipt-preview__detail dd {
  margin: 0;
  font-weight: var(--font-weight-medium);
  overflow-wrap: anywhere;
}

.receipt-preview__transaction {
  font-family: var(--font-family-mono);
  font-size: var(--font-size-sm);
}

.receipt-preview__note {
  margin: 0;
  padding: var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-surface-secondary);
}

.receipt-preview__empty {
  padding: var(--space-6) 0;
  text-align: center;
}

@media (max-width: 560px) {
  .receipt-preview__header {
    flex-direction: column;
  }

  .receipt-preview__details {
    grid-template-columns: 1fr;
  }

  .receipt-preview__detail--full {
    grid-column: auto;
  }
}
</style>

<!--
src/components/payment: Reusable payment receipt preview dialog.
TODO:
- Replace the download placeholder with backend-generated receipt files in Milestone 3.
-->