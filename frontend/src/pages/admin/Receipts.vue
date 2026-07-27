<template>
  <section class="receipts-page" aria-labelledby="receipts-title">
    <header class="receipts-page__header">
      <div>
        <p class="text-label text-muted m-0">Payment Management</p>
        <h1 id="receipts-title" class="text-h2 receipts-page__title">
          Payment Receipts
        </h1>
        <p class="text-body receipts-page__description">
          Preview and download immutable receipts for recorded payments.
        </p>
      </div>
      <span class="badge badge--success">
        <ReceiptText :size="14" aria-hidden="true" />
        {{ receiptPagination.totalItems }} receipts
      </span>
    </header>

    <section class="card receipts-page__filters" aria-label="Receipt filters">
      <div class="receipts-page__search">
        <label class="form-label" for="receipt-search">Search</label>
        <SearchBar
          id="receipt-search"
          :model-value="receiptFilters.search"
          placeholder="Receipt, student, enrollment, or reference"
          @update:model-value="updateFilter('search', $event)"
          @clear="updateFilter('search', '')"
        />
      </div>
      <div>
        <label class="form-label" for="receipt-month">Billing month</label>
        <input
          id="receipt-month"
          class="form-input"
          type="month"
          :value="receiptFilters.billingMonth"
          @input="updateFilter('billingMonth', $event.target.value)"
        />
      </div>
      <div>
        <label class="form-label" for="receipt-method">Payment method</label>
        <select
          id="receipt-method"
          class="form-select"
          :value="receiptFilters.paymentMethod"
          @change="updateFilter('paymentMethod', $event.target.value)"
        >
          <option value="">All methods</option>
          <option value="cash">Cash</option>
          <option value="upi">UPI</option>
          <option value="bank_transfer">Bank transfer</option>
          <option value="card">Card</option>
          <option value="other">Other</option>
        </select>
      </div>
      <div>
        <label class="form-label" for="receipt-status">Status</label>
        <select
          id="receipt-status"
          class="form-select"
          :value="receiptFilters.status"
          @change="updateFilter('status', $event.target.value)"
        >
          <option value="">All statuses</option>
          <option value="issued">Issued</option>
          <option value="voided">Voided</option>
        </select>
      </div>
      <div>
        <label class="form-label" for="receipt-sort">Sort</label>
        <select
          id="receipt-sort"
          class="form-select"
          :value="sortValue"
          @change="updateSort($event.target.value)"
        >
          <option value="issuedAt:desc">Newest issued</option>
          <option value="issuedAt:asc">Oldest issued</option>
          <option value="amount:desc">Highest amount</option>
          <option value="amount:asc">Lowest amount</option>
          <option value="receiptNumber:asc">Receipt number</option>
        </select>
      </div>
      <button
        class="btn btn--secondary receipts-page__clear"
        type="button"
        :disabled="!hasActiveFilters"
        @click="clearFilters"
      >
        <RotateCcw :size="16" aria-hidden="true" /> Clear
      </button>
    </section>

    <Toast v-if="toast.message" :type="toast.type">{{ toast.message }}</Toast>

    <div
      v-if="receiptErrorMessage && !isPreviewOpen"
      class="alert alert--danger"
      role="alert"
    >
      <div>
        <strong>Unable to load receipts.</strong>
        <p class="m-0">{{ receiptErrorMessage }}</p>
        <p v-if="receiptRequestId" class="text-caption m-0">
          Request ID: {{ receiptRequestId }}
        </p>
      </div>
      <button
        class="btn btn--secondary btn--sm"
        type="button"
        :disabled="isReceiptLoading"
        @click="loadReceipts"
      >
        <RefreshCw :size="16" aria-hidden="true" /> Retry
      </button>
    </div>

    <section class="card receipts-page__content">
      <div class="receipts-page__content-header">
        <div>
          <h2 class="text-h4 m-0">Receipt History</h2>
          <p class="text-small text-muted m-0">
            One receipt is stored for every completed payment transaction.
          </p>
        </div>
        <span class="text-small text-muted">
          {{ paginationStart }}–{{ paginationEnd }} of
          {{ receiptPagination.totalItems }}
        </span>
      </div>

      <div v-if="isReceiptLoading" class="receipts-page__state" role="status">
        <LoadingSpinner label="Loading receipts" />
      </div>

      <EmptyState
        v-else-if="receipts.length === 0 && !receiptErrorMessage"
        :title="hasActiveFilters ? 'No matching receipts' : 'No receipts yet'"
        :description="emptyStateDescription"
      >
        <template #icon><ReceiptText :size="27" /></template>
      </EmptyState>

      <template v-else-if="!receiptErrorMessage">
        <div class="table-container receipts-page__table">
          <table class="table" aria-label="Payment receipt history">
            <thead>
              <tr>
                <th scope="col">Receipt</th>
                <th scope="col">Student</th>
                <th scope="col">Month</th>
                <th scope="col">Amount</th>
                <th scope="col">Method</th>
                <th scope="col">Payment Date</th>
                <th scope="col">Status</th>
                <th scope="col"><span class="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="receipt in receipts" :key="receipt.id">
                <td>
                  <strong>{{ receipt.receiptNumber }}</strong>
                  <span class="receipts-page__secondary-value">
                    {{ receipt.paymentReference || 'No reference' }}
                  </span>
                </td>
                <td>
                  <strong>{{ receipt.studentName }}</strong>
                  <span class="receipts-page__secondary-value">
                    {{ receipt.enrollmentNumber }}
                  </span>
                </td>
                <td>{{ formatMonth(receipt.month) }}</td>
                <td>{{ formatCurrency(receipt.amount) }}</td>
                <td>{{ formatLabel(receipt.paymentMethod) }}</td>
                <td>{{ formatDate(receipt.paidAt) }}</td>
                <td>
                  <span
                    class="badge"
                    :class="receipt.status === 'issued' ? 'badge--success' : 'badge--danger'"
                  >
                    {{ formatLabel(receipt.status) }}
                  </span>
                </td>
                <td>
                  <div class="receipts-page__actions">
                    <button
                      class="btn btn--secondary btn--sm"
                      type="button"
                      @click="openReceiptPreview(receipt.id)"
                    >
                      <Eye :size="15" aria-hidden="true" /> Preview
                    </button>
                    <button
                      class="btn btn--ghost btn--icon"
                      type="button"
                      :disabled="isReceiptDownloading"
                      :aria-label="`Download ${receipt.receiptNumber}`"
                      title="Download receipt"
                      @click="handleDownload(receipt.id)"
                    >
                      <Download :size="16" aria-hidden="true" />
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="receipts-page__mobile-list">
          <article v-for="receipt in receipts" :key="receipt.id" class="receipt-card">
            <header>
              <div>
                <strong>{{ receipt.receiptNumber }}</strong>
                <span class="text-caption text-muted">{{ receipt.studentName }}</span>
              </div>
              <span class="badge badge--success">{{ formatLabel(receipt.status) }}</span>
            </header>
            <dl>
              <div><dt>Month</dt><dd>{{ formatMonth(receipt.month) }}</dd></div>
              <div><dt>Amount</dt><dd>{{ formatCurrency(receipt.amount) }}</dd></div>
              <div><dt>Method</dt><dd>{{ formatLabel(receipt.paymentMethod) }}</dd></div>
              <div><dt>Paid</dt><dd>{{ formatDate(receipt.paidAt) }}</dd></div>
            </dl>
            <div class="receipt-card__actions">
              <button class="btn btn--secondary" type="button" @click="openReceiptPreview(receipt.id)">
                <Eye :size="16" aria-hidden="true" /> Preview
              </button>
              <button class="btn btn--secondary" type="button" @click="handleDownload(receipt.id)">
                <Download :size="16" aria-hidden="true" /> Download
              </button>
            </div>
          </article>
        </div>

        <footer class="receipts-page__pagination">
          <Pagination
            :current-page="receiptPagination.page"
            :total-pages="Math.max(1, receiptPagination.totalPages)"
            @update:current-page="changePage"
          />
        </footer>
      </template>
    </section>

    <ReceiptPreviewDialog
      :is-open="isPreviewOpen"
      :receipt="selectedReceipt"
      :is-loading="isReceiptPreviewLoading"
      :is-downloading="isReceiptDownloading"
      :error-message="isPreviewOpen ? receiptErrorMessage : ''"
      :request-id="receiptRequestId"
      @close="closeReceiptPreview"
      @retry="retryReceiptPreview"
      @download="handleDownload(selectedReceiptId)"
    />
  </section>
</template>

<script setup>
import {
  Download,
  Eye,
  ReceiptText,
  RefreshCw,
  RotateCcw,
} from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'

import EmptyState from '../../components/common/EmptyState.vue'
import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import Pagination from '../../components/common/Pagination.vue'
import SearchBar from '../../components/common/SearchBar.vue'
import Toast from '../../components/common/Toast.vue'
import ReceiptPreviewDialog from '../../components/payment/ReceiptPreviewDialog.vue'
import { usePaymentStore } from '../../stores/paymentStore'

const paymentStore = usePaymentStore()
const {
  receipts,
  selectedReceipt,
  receiptPagination,
  receiptFilters,
  isReceiptLoading,
  isReceiptPreviewLoading,
  isReceiptDownloading,
  receiptError,
  receiptErrorMessage,
} = storeToRefs(paymentStore)

const isPreviewOpen = ref(false)
const selectedReceiptId = ref(null)
const toast = reactive({ type: 'success', message: '' })
let filterTimer = null
let toastTimer = null

const hasActiveFilters = computed(() =>
  Boolean(
    receiptFilters.value.search ||
      receiptFilters.value.billingMonth ||
      receiptFilters.value.paymentMethod ||
      receiptFilters.value.status,
  ),
)
const sortValue = computed(
  () => `${receiptFilters.value.sortBy}:${receiptFilters.value.sortOrder}`,
)
const receiptRequestId = computed(
  () => receiptError.value?.response?.data?.requestId || '',
)
const paginationStart = computed(() => {
  if (!receiptPagination.value.totalItems) return 0
  return (
    (receiptPagination.value.page - 1) * receiptPagination.value.pageSize + 1
  )
})
const paginationEnd = computed(() =>
  Math.min(
    receiptPagination.value.page * receiptPagination.value.pageSize,
    receiptPagination.value.totalItems,
  ),
)
const emptyStateDescription = computed(() =>
  hasActiveFilters.value
    ? 'Try clearing or changing the receipt filters.'
    : 'Receipts appear automatically after a payment is recorded.',
)

watch(
  () => [
    receiptFilters.value.search,
    receiptFilters.value.billingMonth,
    receiptFilters.value.paymentMethod,
    receiptFilters.value.status,
    receiptFilters.value.sortBy,
    receiptFilters.value.sortOrder,
  ],
  () => {
    window.clearTimeout(filterTimer)
    filterTimer = window.setTimeout(loadReceipts, 250)
  },
)

onMounted(loadReceipts)
onBeforeUnmount(() => {
  window.clearTimeout(filterTimer)
  window.clearTimeout(toastTimer)
})

async function loadReceipts() {
  try {
    await paymentStore.fetchReceipts()
  } catch {
    // Store-owned structured error is rendered above.
  }
}

function updateFilter(name, value) {
  paymentStore.updateReceiptFilter(name, value)
}

function updateSort(value) {
  const [sortBy, sortOrder] = value.split(':')
  paymentStore.setReceiptFilters({ sortBy, sortOrder, page: 1 })
}

function clearFilters() {
  paymentStore.resetReceiptFilters()
}

function changePage(page) {
  paymentStore.updateReceiptFilter('page', page)
  loadReceipts()
}

async function openReceiptPreview(receiptId) {
  selectedReceiptId.value = receiptId
  isPreviewOpen.value = true
  try {
    await paymentStore.fetchReceiptDetail(receiptId)
  } catch {
    // The dialog owns its loading and structured error state.
  }
}

function closeReceiptPreview() {
  isPreviewOpen.value = false
  selectedReceiptId.value = null
  paymentStore.clearSelectedReceipt()
}

function retryReceiptPreview() {
  if (selectedReceiptId.value) {
    openReceiptPreview(selectedReceiptId.value)
  }
}

async function handleDownload(receiptId) {
  if (!receiptId || isReceiptDownloading.value) return
  try {
    const { blob, filename } = await paymentStore.downloadReceipt(receiptId)
    const objectUrl = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = objectUrl
    link.download = filename
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(objectUrl)
    showToast('success', 'Receipt PDF downloaded.')
  } catch {
    showToast('error', receiptErrorMessage.value || 'Unable to download receipt.')
  }
}

function showToast(type, message) {
  toast.type = type
  toast.message = message
  window.clearTimeout(toastTimer)
  toastTimer = window.setTimeout(() => {
    toast.message = ''
  }, 4000)
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
    month: 'short',
    year: 'numeric',
  }).format(new Date(year, monthNumber - 1, 1))
}

function formatDate(value) {
  if (!value) return 'Not available'
  return new Intl.DateTimeFormat('en-IN', {
    dateStyle: 'medium',
  }).format(new Date(value))
}

function formatLabel(value) {
  if (!value) return 'Not available'
  return String(value)
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())
}
</script>

<style scoped>
.receipts-page {
  display: grid;
  gap: var(--space-6);
}

.receipts-page__header,
.receipts-page__content-header,
.receipts-page__pagination {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
}

.receipts-page__title {
  margin: var(--space-1) 0 0;
}

.receipts-page__description {
  margin: var(--space-2) 0 0;
  color: var(--color-text-secondary);
}

.receipts-page__filters {
  display: grid;
  grid-template-columns: minmax(220px, 2fr) repeat(4, minmax(150px, 1fr)) auto;
  align-items: end;
  gap: var(--space-3);
  padding: var(--space-4);
}

.receipts-page__filters > div {
  min-width: 0;
}

.receipts-page__content {
  min-width: 0;
}

.receipts-page__content-header {
  padding: var(--space-5);
  border-bottom: 1px solid var(--color-divider);
}

.receipts-page__content-header > div {
  display: grid;
  gap: var(--space-1);
}

.receipts-page__state {
  display: grid;
  min-height: 260px;
  place-items: center;
}

.receipts-page__secondary-value {
  display: block;
  margin-top: var(--space-1);
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
  overflow-wrap: anywhere;
}

.receipts-page__actions,
.receipt-card__actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-2);
  white-space: nowrap;
}

.receipts-page__pagination {
  justify-content: flex-end;
  padding: var(--space-4);
  border-top: 1px solid var(--color-divider);
}

.receipts-page__mobile-list {
  display: none;
}

.receipt-card {
  display: grid;
  gap: var(--space-4);
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-elevated);
}

.receipt-card header,
.receipt-card header > div {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
}

.receipt-card header > div {
  flex-direction: column;
  gap: var(--space-1);
}

.receipt-card dl {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-3);
  margin: 0;
}

.receipt-card dl > div {
  display: grid;
  gap: var(--space-1);
}

.receipt-card dt {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.receipt-card dd {
  margin: 0;
  font-weight: var(--font-weight-medium);
}

@media (max-width: 1260px) {
  .receipts-page__filters {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
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

  .receipts-page__table {
    display: none;
  }

  .receipts-page__mobile-list {
    display: grid;
    gap: var(--space-3);
    padding: var(--space-3);
  }

  .receipt-card__actions {
    align-items: stretch;
    flex-direction: column;
  }

  .receipts-page__pagination {
    justify-content: center;
  }
}
</style>
