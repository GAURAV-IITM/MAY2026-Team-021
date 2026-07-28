<template>
  <Modal
    :is-open="isOpen"
    title="Payment Receipt"
    title-id="receipt-preview-dialog-title"
    @close="handleClose"
  >
    <div v-if="isLoading" class="receipt-preview__state" role="status">
      <LoadingSpinner label="Loading receipt" />
    </div>

    <div v-else-if="errorMessage" class="receipt-preview__state">
      <CircleAlert :size="28" aria-hidden="true" />
      <strong>Unable to load this receipt</strong>
      <p class="text-small text-muted m-0">{{ errorMessage }}</p>
      <p v-if="requestId" class="text-caption text-muted m-0">
        Request ID: {{ requestId }}
      </p>
      <button class="btn btn--secondary btn--sm" type="button" @click="$emit('retry')">
        <RefreshCw :size="15" aria-hidden="true" /> Retry
      </button>
    </div>

    <article v-else-if="receipt" class="receipt-preview">
      <header class="receipt-preview__header">
        <div>
          <p class="text-label text-muted m-0">{{ receipt.library.name }}</p>
          <h3 class="text-h4 m-0">Payment Receipt</h3>
          <p class="text-small text-muted m-0">
            {{ receipt.library.address || receipt.library.email }}
          </p>
        </div>
        <span
          class="badge"
          :class="receipt.status === 'issued' ? 'badge--success' : 'badge--danger'"
        >
          {{ formatLabel(receipt.status) }}
        </span>
      </header>

      <section class="receipt-preview__number" aria-label="Receipt number">
        <span class="text-small text-muted">Receipt Number</span>
        <strong>{{ receipt.receiptNumber }}</strong>
        <span class="text-caption text-muted">
          Issued {{ formatDateTime(receipt.issuedAt) }}
        </span>
      </section>

      <dl class="receipt-preview__details">
        <div class="receipt-preview__detail">
          <dt>Student</dt>
          <dd>{{ receipt.student.name }}</dd>
        </div>
        <div class="receipt-preview__detail">
          <dt>Enrollment Number</dt>
          <dd>{{ receipt.student.enrollmentNumber }}</dd>
        </div>
        <div class="receipt-preview__detail">
          <dt>Billing Month</dt>
          <dd>{{ formatMonth(receipt.fee.billingMonth) }}</dd>
        </div>
        <div class="receipt-preview__detail">
          <dt>Amount Paid</dt>
          <dd>{{ formatCurrency(receipt.payment.amount) }}</dd>
        </div>
        <div class="receipt-preview__detail">
          <dt>Payment Method</dt>
          <dd>{{ formatLabel(receipt.payment.method) }}</dd>
        </div>
        <div class="receipt-preview__detail">
          <dt>Payment Date</dt>
          <dd>{{ formatDateTime(receipt.payment.paidAt) }}</dd>
        </div>
        <div class="receipt-preview__detail">
          <dt>Payment Reference</dt>
          <dd>{{ receipt.payment.referenceNumber || 'Not provided' }}</dd>
        </div>
        <div class="receipt-preview__detail">
          <dt>Remaining Balance</dt>
          <dd>{{ formatCurrency(receipt.fee.remainingBalance) }}</dd>
        </div>
        <div class="receipt-preview__detail">
          <dt>Fee Status</dt>
          <dd>{{ formatLabel(receipt.fee.paymentStatus) }}</dd>
        </div>
        <div class="receipt-preview__detail">
          <dt>Recorded By</dt>
          <dd>{{ receipt.payment.recordedBy?.name || 'System' }}</dd>
        </div>
      </dl>

      <p class="receipt-preview__note text-small text-muted">
        This historical receipt is generated from the immutable snapshot saved
        with the payment transaction.
      </p>
    </article>

    <div v-else class="receipt-preview__state">
      <ReceiptText :size="28" aria-hidden="true" />
      <p class="m-0 text-muted">No receipt selected.</p>
    </div>

    <template #footer>
      <button
        class="btn btn--secondary"
        type="button"
        :disabled="isDownloading"
        @click="handleClose"
      >
        Close
      </button>
      <button
        class="btn btn--primary"
        type="button"
        :disabled="!receipt || isLoading || isDownloading"
        @click="$emit('download')"
      >
        <span v-if="isDownloading" class="btn__loader" aria-hidden="true"></span>
        <Download v-else :size="16" aria-hidden="true" />
        {{ isDownloading ? 'Downloading...' : 'Download PDF' }}
      </button>
    </template>
  </Modal>
</template>

<script setup>
import {
  CircleAlert,
  Download,
  ReceiptText,
  RefreshCw,
} from '@lucide/vue'

import LoadingSpinner from '../common/LoadingSpinner.vue'
import Modal from '../common/Modal.vue'

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  receipt: { type: Object, default: null },
  isLoading: { type: Boolean, default: false },
  isDownloading: { type: Boolean, default: false },
  errorMessage: { type: String, default: '' },
  requestId: { type: String, default: '' },
})

const emit = defineEmits(['close', 'download', 'retry'])

function formatCurrency(amount) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: props.receipt?.currency || 'INR',
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

function formatDateTime(value) {
  if (!value) return 'Not available'
  return new Intl.DateTimeFormat('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function formatLabel(value) {
  if (!value) return 'Not available'
  return String(value)
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())
}

function handleClose() {
  if (!props.isDownloading) emit('close')
}
</script>

<style scoped>
.receipt-preview,
.receipt-preview__state {
  display: grid;
  gap: var(--space-5);
}

.receipt-preview__state {
  justify-items: center;
  padding: var(--space-7) 0;
  text-align: center;
}

.receipt-preview__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
}

.receipt-preview__header > div {
  display: grid;
  gap: var(--space-1);
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

.receipt-preview__detail dt {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.receipt-preview__detail dd {
  margin: 0;
  font-weight: var(--font-weight-medium);
  overflow-wrap: anywhere;
}

.receipt-preview__note {
  margin: 0;
  padding: var(--space-4);
  border-radius: var(--radius-md);
  background: var(--color-surface-secondary);
}

@media (max-width: 560px) {
  .receipt-preview__header {
    flex-direction: column;
  }

  .receipt-preview__details {
    grid-template-columns: 1fr;
  }
}
</style>
