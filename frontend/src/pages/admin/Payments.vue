<template>
  <section class="payments-page" aria-labelledby="payments-title">
    <header class="payments-page__header">
      <div>
        <p class="text-label text-muted payments-page__eyebrow">
          Payment Management
        </p>

        <h1 id="payments-title" class="text-h2 payments-page__title">
          {{ pageTitle }}
        </h1>

        <p class="text-body payments-page__description">
          {{ pageDescription }}
        </p>
      </div>
    </header>

    <nav class="payments-page__views" aria-label="Payment views">
  <button
    class="btn"
    :class="activeView === 'monthly' ? 'btn--primary' : 'btn--secondary'"
    type="button"
    :aria-pressed="activeView === 'monthly'"
    @click="setActiveView('monthly')"
  >
    Monthly Payments
  </button>

  <button
    class="btn"
    :class="activeView === 'history' ? 'btn--primary' : 'btn--secondary'"
    type="button"
    :aria-pressed="activeView === 'history'"
    @click="setActiveView('history')"
  >
    Payment History
  </button>
</nav>

    <section class="payments-page__summary" aria-label="Payment summary">
      <article class="stat-card stat-card--dashboard">
        <div class="stat-card__header">
          <span class="text-label text-muted">Total Payments</span>
          <span class="stat-card__icon" aria-hidden="true">T</span>
        </div>

        <strong class="stat-card__value">{{ paymentCount }}</strong>
      </article>

      <article class="stat-card stat-card--dashboard">
        <div class="stat-card__header">
          <span class="text-label text-muted">Paid</span>
          <span class="stat-card__icon" aria-hidden="true">P</span>
        </div>

        <strong class="stat-card__value">{{ paidPaymentCount }}</strong>
      </article>

      <article class="stat-card stat-card--dashboard">
        <div class="stat-card__header">
          <span class="text-label text-muted">Unpaid</span>
          <span class="stat-card__icon" aria-hidden="true">U</span>
        </div>

        <strong class="stat-card__value">{{ unpaidPaymentCount }}</strong>
      </article>

      <article class="stat-card stat-card--dashboard">
        <div class="stat-card__header">
          <span class="text-label text-muted">Collected</span>
          <span class="stat-card__icon" aria-hidden="true">₹</span>
        </div>

        <strong class="stat-card__value">
          {{ formatCurrency(totalCollectedAmount) }}
        </strong>
      </article>
    </section>

    <PaymentFilters
      :search="paymentFilters.search"
      :month="paymentFilters.month"
      :status="paymentFilters.status"
      :months="availableMonths"
      :has-active-filters="hasActivePaymentFilters"
      @update:search="updateFilter('search', $event)"
      @update:month="updateFilter('month', $event)"
      @update:status="updateFilter('status', $event)"
      @clear="clearFilters"
    />

    <div v-if="errorMessage" class="alert alert--danger" role="alert">
      <div>
        <strong>Unable to load payments.</strong>
        <p class="m-0">{{ errorMessage }}</p>
      </div>

      <button
        class="btn btn--secondary btn--sm"
        type="button"
        @click="loadPayments"
      >
        Retry
      </button>
    </div>

    <div
      v-if="isLoading && payments.length === 0"
      class="payments-page__loading"
    >
      <LoadingSpinner label="Loading payments" />
    </div>

    <template v-else-if="!errorMessage">
      <EmptyState
        v-if="payments.length === 0"
        title="No payments found"
        :description="emptyStateDescription"
      >
        <template #primary-action>
          <button
            v-if="hasActivePaymentFilters"
            class="btn btn--primary"
            type="button"
            @click="clearFilters"
          >
            Clear Filters
          </button>

          <span v-else></span>
        </template>

        <template #secondary-action>
          <span></span>
        </template>
      </EmptyState>

      <template v-else>
        <DataTable
          :columns="columns"
          :rows="paginatedPayments"
          :aria-label="tableAriaLabel"
        >
          <template #cell-studentName="{ row }">
            <div class="payments-page__student">
              <strong>{{ row.studentName }}</strong>
              <span class="text-caption text-muted">
                {{ row.studentEmail }}
              </span>
            </div>
          </template>

          <template #cell-month="{ value }">
            {{ formatMonth(value) }}
          </template>

          <template #cell-amount="{ value }">
            {{ formatCurrency(value) }}
          </template>

          <template #cell-status="{ value }">
            <span class="badge" :class="getStatusBadgeClass(value)">
              {{ formatLabel(value) }}
            </span>
          </template>

          <template #cell-paymentMethod="{ value }">
            {{ formatLabel(value) }}
          </template>

          <template #actions="{ row }">
            <button
              class="btn btn--secondary btn--sm"
              type="button"
              @click="openStatusDialog(row)"
            >
              Update Status
            </button>
          </template>
        </DataTable>

        <footer class="payments-page__pagination">
          <p class="text-small text-muted m-0">
            Showing {{ paginationStart }}–{{ paginationEnd }} of
            {{ payments.length }} payments
          </p>

          <Pagination
            v-model:current-page="currentPage"
            :total-pages="totalPages"
          />
        </footer>
      </template>
    </template>

    <PaymentStatusDialog
      :is-open="isStatusDialogOpen"
      :payment="selectedPayment"
      :is-submitting="isUpdatingStatus"
      @close="closeStatusDialog"
      @confirm="handleStatusUpdate"
    />
  </section>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { computed, onMounted, ref, watch } from 'vue'

import DataTable from '../../components/common/DataTable.vue'
import EmptyState from '../../components/common/EmptyState.vue'
import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import Pagination from '../../components/common/Pagination.vue'
import PaymentFilters from '../../components/payment/PaymentFilters.vue'
import PaymentStatusDialog from '../../components/payment/PaymentStatusDialog.vue'
import { usePaymentStore } from '../../stores/paymentStore'

const PAGE_SIZE = 5

const columns = Object.freeze([
  { key: 'studentName', label: 'Student' },
  { key: 'month', label: 'Month' },
  { key: 'amount', label: 'Amount' },
  { key: 'status', label: 'Status' },
  { key: 'paymentMethod', label: 'Payment Method' },
])

const paymentStore = usePaymentStore()

const {
  payments,
  selectedPayment,
  paymentFilters,
  isLoading,
  errorMessage,
  paymentCount,
  paidPaymentCount,
  unpaidPaymentCount,
  totalCollectedAmount,
  availableMonths,
  hasActivePaymentFilters,
} = storeToRefs(paymentStore)

const currentPage = ref(1)
const activeView = ref('monthly')
const isStatusDialogOpen = ref(false)
const isUpdatingStatus = ref(false)

const totalPages = computed(() => {
  return Math.max(1, Math.ceil(payments.value.length / PAGE_SIZE))
})

const paginatedPayments = computed(() => {
  const startIndex = (currentPage.value - 1) * PAGE_SIZE

  return payments.value.slice(startIndex, startIndex + PAGE_SIZE)
})

const paginationStart = computed(() => {
  if (payments.value.length === 0) return 0

  return (currentPage.value - 1) * PAGE_SIZE + 1
})

const paginationEnd = computed(() => {
  return Math.min(currentPage.value * PAGE_SIZE, payments.value.length)
})

const emptyStateDescription = computed(() => {
  if (hasActivePaymentFilters.value) {
    return activeView.value === 'history'
      ? 'No payment history records match the current search and filters.'
      : 'No payment records match the current search and filters.'
  }

  return activeView.value === 'history'
    ? 'Previous payment transactions will appear here when they are available.'
    : 'Monthly payment records will appear here when they are available.'
})

const pageTitle = computed(() => {
  return activeView.value === 'history'
    ? 'Payment History'
    : 'Monthly Payments'
})

const pageDescription = computed(() => {
  return activeView.value === 'history'
    ? 'Review previous payment transactions using student, month, and status filters.'
    : 'Track monthly fees, review payment status, and manage student payments.'
})

const tableAriaLabel = computed(() => {
  return activeView.value === 'history'
    ? 'Payment history records'
    : 'Monthly payment records'
})

watch(
  () => [
    paymentFilters.value.search,
    paymentFilters.value.month,
    paymentFilters.value.status,
  ],
  () => {
    currentPage.value = 1
    loadPayments()
  },
)

watch(totalPages, (pageCount) => {
  if (currentPage.value > pageCount) {
    currentPage.value = pageCount
  }
})

function setActiveView(view) {
  if (!['monthly', 'history'].includes(view)) return
  if (activeView.value === view) return

  activeView.value = view
  currentPage.value = 1

  loadPayments()
}

function updateFilter(filterName, value) {
  paymentStore.updatePaymentFilter(filterName, value)
}

function clearFilters() {
  paymentStore.resetPaymentFilters()
}

function openStatusDialog(payment) {
  paymentStore.selectedPayment = payment
  isStatusDialogOpen.value = true
}

function closeStatusDialog() {
  if (isUpdatingStatus.value) return

  isStatusDialogOpen.value = false
  paymentStore.clearSelectedPayment()
}

async function handleStatusUpdate(statusPayload) {
  if (!selectedPayment.value) return

  isUpdatingStatus.value = true

  try {
    await paymentStore.updatePaymentStatus(
      selectedPayment.value.id,
      statusPayload,
    )

    isStatusDialogOpen.value = false
    paymentStore.clearSelectedPayment()
  } catch {
    // Store-owned error state is rendered by the page.
  } finally {
    isUpdatingStatus.value = false
  }
}

async function loadPayments() {
  try {
    if (activeView.value === 'history') {
      await paymentStore.fetchPaymentHistory()
      return
    }

    await paymentStore.fetchPayments()
  } catch {
    // Store-owned error state is rendered above the table.
  }
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

onMounted(loadPayments)
</script>

<style scoped>
.payments-page {
  display: grid;
  gap: var(--space-6);
}

.payments-page__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-5);
}

.payments-page__views {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-3);
}

.payments-page__eyebrow,
.payments-page__title,
.payments-page__description {
  margin: 0;
}

.payments-page__title {
  margin-top: var(--space-1);
}

.payments-page__description {
  margin-top: var(--space-2);
  color: var(--color-text-muted);
}

.payments-page__summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-4);
}

.payments-page__loading {
  display: grid;
  min-height: 240px;
  place-items: center;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface-elevated);
}

.payments-page__student {
  display: grid;
  gap: var(--space-1);
  min-width: 180px;
}

.payments-page__pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
}

@media (max-width: 1000px) {
  .payments-page__summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .payments-page__summary {
    grid-template-columns: 1fr;
  }

  .payments-page__pagination {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>

<!--
src/pages/admin: Library owner payment management page.

TODO:
- Add receipt preview and generation workflow.
- Add WhatsApp pending fee reminder workflow.
- Replace mock-backed payment operations with FastAPI integration in Milestone 3.
-->