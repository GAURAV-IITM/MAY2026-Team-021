<template>
  <section class="receipts-page" aria-labelledby="receipts-title">
    <header class="receipts-page__header">
      <div>
        <h1 id="receipts-title" class="text-h2 receipts-page__title">
          Payment Receipts
        </h1>

        <p class="text-body receipts-page__description">
          View and preview receipts for completed library fee payments.
        </p>
      </div>

      <span class="badge badge--success">
        {{ filteredReceipts.length }} Paid
      </span>
    </header>

    <section class="card receipts-page__filters" aria-label="Receipt filters">
      <div class="receipts-page__search">
        <label class="form-label" for="receipt-search">Search receipts</label>
        <input
          id="receipt-search"
          v-model.trim="search"
          class="form-input"
          type="search"
          placeholder="Search by student, receipt, or transaction ID"
        />
      </div>

      <div class="receipts-page__month">
        <label class="form-label" for="receipt-month">Payment month</label>
        <select id="receipt-month" v-model="selectedMonth" class="form-select">
          <option value="">All months</option>
          <option v-for="month in availableMonths" :key="month" :value="month">
            {{ formatMonth(month) }}
          </option>
        </select>
      </div>

      <button
        class="btn btn--secondary receipts-page__clear"
        type="button"
        :disabled="!hasActiveFilters"
        @click="clearFilters"
      >
        Clear Filters
      </button>
    </section>

    <div v-if="errorMessage" class="alert alert--danger" role="alert">
      <span>{{ errorMessage }}</span>

      <button
        class="btn btn--ghost btn--sm"
        type="button"
        :disabled="isLoading"
        @click="loadReceipts"
      >
        Retry
      </button>
    </div>

    <section class="card receipts-page__content">
      <div class="receipts-page__content-header">
        <div>
          <h2 class="text-h4 m-0">Receipt History</h2>
          <p class="text-small text-muted m-0">
            Receipts are available only for payments marked as paid.
          </p>
        </div>

        <span class="text-small text-muted">
          {{ filteredReceipts.length }} records
        </span>
      </div>

      <div v-if="isLoading" class="receipts-page__state" role="status">
        <span class="btn__loader" aria-hidden="true"></span>
        <p class="m-0">Loading receipts...</p>
      </div>

      <div
        v-else-if="filteredReceipts.length === 0"
        class="receipts-page__state"
      >
        <h3 class="text-h5 m-0">No receipts found</h3>
        <p class="text-body text-muted m-0">
          {{ emptyStateDescription }}
        </p>
      </div>

      <div v-else class="table-container">
        <table class="table" aria-label="Payment receipt history">
          <thead>
            <tr>
              <th scope="col">Receipt</th>
              <th scope="col">Student</th>
              <th scope="col">Month</th>
              <th scope="col">Amount</th>
              <th scope="col">Payment Method</th>
              <th scope="col">Payment Date</th>
              <th scope="col">
                <span class="sr-only">Actions</span>
              </th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="receipt in filteredReceipts" :key="receipt.id">
              <td>
                <strong>{{ receipt.receiptNumber || 'Not available' }}</strong>
                <span class="receipts-page__secondary-value">
                  {{ receipt.transactionId || 'No transaction ID' }}
                </span>
              </td>

              <td>
                <strong>{{ receipt.studentName }}</strong>
                <span class="receipts-page__secondary-value">
                  {{ receipt.seatNumber || 'No seat assigned' }}
                </span>
              </td>

              <td>{{ formatMonth(receipt.month) }}</td>
              <td>{{ formatCurrency(receipt.amount) }}</td>
              <td>{{ formatPaymentMethod(receipt.paymentMethod) }}</td>
              <td>{{ formatDate(receipt.paidAt) }}</td>

              <td class="receipts-page__actions">
                <button
                  class="btn btn--secondary btn--sm"
                  type="button"
                  @click="openReceiptPreview(receipt)"
                >
                  Preview
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <ReceiptPreviewDialog
      :is-open="isPreviewOpen"
      :receipt="selectedReceipt"
      @close="closeReceiptPreview"
      @download="handleDownloadPlaceholder"
    />

    <div
      v-if="downloadMessage"
      class="toast-region"
      aria-live="polite"
      aria-atomic="true"
    >
      <div class="toast">
        <div>
          <strong>Download unavailable</strong>
          <p class="text-small text-muted m-0">
            {{ downloadMessage }}
          </p>
        </div>

        <button
          class="btn btn--ghost btn--sm"
          type="button"
          aria-label="Dismiss download message"
          @click="downloadMessage = ''"
        >
          Dismiss
        </button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'

import ReceiptPreviewDialog from '../../components/payment/ReceiptPreviewDialog.vue'
import { usePaymentStore } from '../../stores/paymentStore'

const paymentStore = usePaymentStore()

const {
  receipts,
  isLoading,
  errorMessage,
} = storeToRefs(paymentStore)

const search = ref('')
const selectedMonth = ref('')
const isPreviewOpen = ref(false)
const selectedReceipt = ref(null)
const downloadMessage = ref('')

const availableMonths = computed(() => {
  return [...new Set(receipts.value.map((receipt) => receipt.month))]
    .filter(Boolean)
    .sort((firstMonth, secondMonth) => secondMonth.localeCompare(firstMonth))
})

const filteredReceipts = computed(() => {
  const normalizedSearch = search.value.trim().toLowerCase()

  return receipts.value.filter((receipt) => {
    const matchesSearch =
      !normalizedSearch ||
      [
        receipt.studentName,
        receipt.receiptNumber,
        receipt.transactionId,
      ].some((value) => {
        return String(value || '').toLowerCase().includes(normalizedSearch)
      })

    const matchesMonth =
      !selectedMonth.value || receipt.month === selectedMonth.value

    return matchesSearch && matchesMonth
  })
})

const hasActiveFilters = computed(() => {
  return Boolean(search.value || selectedMonth.value)
})

const emptyStateDescription = computed(() => {
  if (hasActiveFilters.value) {
    return 'No paid payment receipts match the current search and month filter.'
  }

  return 'Receipts will appear here after payments are marked as paid.'
})

onMounted(() => {
  loadReceipts()
})

async function loadReceipts() {
  try {
    await paymentStore.fetchReceipts()
  } catch {
    // Store-owned error state is rendered on the page.
  }
}

function openReceiptPreview(receipt) {
  selectedReceipt.value = receipt
  isPreviewOpen.value = true
}

function closeReceiptPreview() {
  isPreviewOpen.value = false
  selectedReceipt.value = null
}

function clearFilters() {
  search.value = ''
  selectedMonth.value = ''
}

function handleDownloadPlaceholder() {
  downloadMessage.value =
    'Receipt file downloads will be available after backend receipt generation is integrated.'
}

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

function formatDate(value) {
  if (!value) return 'Not available'

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) return value

  return new Intl.DateTimeFormat('en-IN', {
    dateStyle: 'medium',
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
</script>

<style scoped>
.receipts-page {
  display: grid;
  gap: var(--space-6);
}

.receipts-page__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
}

.receipts-page__title {
  margin-bottom: var(--space-2);
}

.receipts-page__description {
  margin: 0;
  color: var(--color-text-secondary);
}

.receipts-page__filters {
  display: grid;
  grid-template-columns: minmax(240px, 2fr) minmax(180px, 1fr) auto;
  align-items: end;
  gap: var(--space-4);
  padding: var(--space-5);
}

.receipts-page__search,
.receipts-page__month {
  min-width: 0;
}

.receipts-page__content {
  min-width: 0;
}

.receipts-page__content-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-5);
  border-bottom: 1px solid var(--color-divider);
}

.receipts-page__state {
  display: grid;
  justify-items: center;
  gap: var(--space-3);
  padding: var(--space-8);
  text-align: center;
}

.receipts-page__secondary-value {
  display: block;
  margin-top: var(--space-1);
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  overflow-wrap: anywhere;
}

.receipts-page__actions {
  text-align: right;
  white-space: nowrap;
}

@media (max-width: 840px) {
  .receipts-page__filters {
    grid-template-columns: 1fr 1fr;
  }

  .receipts-page__clear {
    justify-self: start;
  }
}

@media (max-width: 600px) {
  .receipts-page__header,
  .receipts-page__content-header {
    flex-direction: column;
  }

  .receipts-page__filters {
    grid-template-columns: 1fr;
  }

  .receipts-page__clear {
    width: 100%;
  }
}
</style>

<!--
src/pages/admin: Library owner receipt history and receipt preview page.
TODO:
- Replace client-side receipt filtering and download placeholders with backend receipt APIs in Milestone 3.
-->