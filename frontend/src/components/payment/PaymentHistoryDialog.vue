<template>
  <Modal
    :is-open="isOpen"
    title="Transaction History"
    title-id="payment-history-dialog-title"
    @close="$emit('close')"
  >
    <div v-if="payment" class="payment-history">
      <header>
        <div>
          <span class="text-label text-muted">Student</span>
          <strong>{{ payment.studentName }}</strong>
        </div>
        <div>
          <span class="text-label text-muted">Billing Month</span>
          <strong>{{ formatMonth(payment.month) }}</strong>
        </div>
        <div>
          <span class="text-label text-muted">Paid / Total</span>
          <strong>
            {{ formatCurrency(payment.paidAmount) }} /
            {{ formatCurrency(payment.totalAmount) }}
          </strong>
        </div>
      </header>

      <p v-if="!payment.transactions?.length" class="text-muted m-0">
        No transactions have been recorded for this fee.
      </p>

      <ol v-else class="payment-history__list">
        <li
          v-for="transaction in payment.transactions"
          :key="transaction.id"
        >
          <div class="payment-history__amount">
            <strong>{{ formatCurrency(transaction.amount) }}</strong>
            <span class="badge badge--success">
              {{ formatLabel(transaction.method) }}
            </span>
          </div>
          <dl>
            <div>
              <dt>Paid At</dt>
              <dd>{{ formatDateTime(transaction.paidAt) }}</dd>
            </div>
            <div>
              <dt>Reference</dt>
              <dd>{{ transaction.referenceNumber || 'Not provided' }}</dd>
            </div>
            <div>
              <dt>Recorded By</dt>
              <dd>{{ transaction.recordedBy?.name || 'System' }}</dd>
            </div>
            <div v-if="transaction.notes">
              <dt>Notes</dt>
              <dd>{{ transaction.notes }}</dd>
            </div>
          </dl>
        </li>
      </ol>
    </div>

    <template #footer>
      <button class="btn btn--secondary" type="button" @click="$emit('close')">
        Close
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
  payment: {
    type: Object,
    default: null,
  },
})

defineEmits(['close'])

function formatCurrency(amount) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(amount || 0))
}

function formatMonth(month) {
  const [year, monthNumber] = String(month || '').split('-').map(Number)
  if (!year || !monthNumber) return 'Not available'
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
  return String(value || 'Not available')
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())
}
</script>

<style scoped>
.payment-history {
  display: grid;
  gap: var(--space-5);
}

.payment-history > header {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-4);
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-muted);
}

.payment-history > header > div {
  display: grid;
  gap: var(--space-1);
}

.payment-history__list {
  display: grid;
  gap: var(--space-3);
  margin: 0;
  padding: 0;
  list-style: none;
}

.payment-history__list > li {
  display: grid;
  gap: var(--space-3);
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}

.payment-history__amount {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}

.payment-history dl {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-3);
  margin: 0;
}

.payment-history dl > div {
  display: grid;
  gap: var(--space-1);
}

.payment-history dt {
  color: var(--color-text-muted);
  font-size: var(--font-size-caption);
}

.payment-history dd {
  margin: 0;
  overflow-wrap: anywhere;
}

@media (max-width: 640px) {
  .payment-history > header,
  .payment-history dl {
    grid-template-columns: 1fr;
  }
}
</style>
