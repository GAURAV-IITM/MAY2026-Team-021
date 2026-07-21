<template>
  <section class="payments-page" aria-labelledby="payments-title">
    <header class="payments-page__header">
      <div>
        <p class="text-label text-muted payments-page__eyebrow">Payment Management</p>

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
        <CalendarDays :size="17" aria-hidden="true" /> Monthly Payments
      </button>

      <button
        class="btn"
        :class="activeView === 'history' ? 'btn--primary' : 'btn--secondary'"
        type="button"
        :aria-pressed="activeView === 'history'"
        @click="setActiveView('history')"
      >
        <History :size="17" aria-hidden="true" /> Payment History
      </button>

      <button
        class="btn"
        :class="activeView === 'reminders' ? 'btn--primary' : 'btn--secondary'"
        type="button"
        :aria-pressed="activeView === 'reminders'"
        @click="setActiveView('reminders')"
      >
        <MessageCircleMore :size="17" aria-hidden="true" /> Fee Reminders
      </button>
    </nav>

    <div v-if="activeView === 'monthly'" class="payments-page__generation">
      <button
        class="btn btn--primary"
        type="button"
        :disabled="!paymentFilters.month || isGeneratingMonthlyPayments || isLoading"
        @click="handleGenerateMonthlyPayments"
      >
        <FilePlus2 :size="17" aria-hidden="true" />
        {{ isGeneratingMonthlyPayments ? 'Generating Payments...' : 'Generate Monthly Payments' }}
      </button>

      <p class="text-small text-muted m-0">
        Generate unpaid payment records for active students for
        {{ formatMonth(paymentFilters.month) }}.
      </p>
    </div>
    <div
      v-if="activeView === 'monthly' && generationResult"
      class="alert alert--info"
      role="status"
    >
      <div>
        <strong>Monthly payment generation completed.</strong>

        <p class="m-0">
          {{ generationResult.createdCount }} created, {{ generationResult.skippedCount }} skipped
          from {{ generationResult.activeStudentCount }} active students for
          {{ formatMonth(generationResult.month) }}.
        </p>
      </div>
    </div>

    <section
      class="payments-page__summary"
      :aria-label="activeView === 'reminders' ? 'Fee reminder summary' : 'Payment summary'"
    >
      <article class="stat-card stat-card--dashboard">
        <div class="stat-card__header">
          <span class="text-label text-muted">
            {{ activeView === 'reminders' ? 'Pending Payments' : 'Total Payments' }}
          </span>

          <span class="stat-card__icon" aria-hidden="true">
            <ClockAlert v-if="activeView === 'reminders'" :size="20" />
            <CreditCard v-else :size="20" />
          </span>
        </div>

        <strong class="stat-card__value">
          {{ activeView === 'reminders' ? reminderPaymentCount : paymentCount }}
        </strong>
      </article>

      <article class="stat-card stat-card--dashboard">
        <div class="stat-card__header">
          <span class="text-label text-muted">
            {{ activeView === 'reminders' ? 'Students Pending' : 'Paid' }}
          </span>

          <span class="stat-card__icon" aria-hidden="true">
            <UsersRound v-if="activeView === 'reminders'" :size="20" />
            <CircleCheckBig v-else :size="20" />
          </span>
        </div>

        <strong class="stat-card__value">
          {{ activeView === 'reminders' ? reminderStudentCount : paidPaymentCount }}
        </strong>
      </article>

      <article class="stat-card stat-card--dashboard">
        <div class="stat-card__header">
          <span class="text-label text-muted">
            {{ activeView === 'reminders' ? 'Months Pending' : 'Unpaid' }}
          </span>

          <span class="stat-card__icon" aria-hidden="true">
            <CalendarClock v-if="activeView === 'reminders'" :size="20" />
            <CircleAlert v-else :size="20" />
          </span>
        </div>

        <strong class="stat-card__value">
          {{ activeView === 'reminders' ? reminderMonthCount : unpaidPaymentCount }}
        </strong>
      </article>

      <article class="stat-card stat-card--dashboard">
        <div class="stat-card__header">
          <span class="text-label text-muted">
            {{ activeView === 'reminders' ? 'Total Due' : 'Collected' }}
          </span>

          <span class="stat-card__icon" aria-hidden="true"><IndianRupee :size="20" /></span>
        </div>

        <strong class="stat-card__value">
          {{
            formatCurrency(
              activeView === 'reminders' ? reminderTotalDueAmount : totalCollectedAmount,
            )
          }}
        </strong>
      </article>
    </section>

    <PaymentFilters
      :search="paymentFilters.search"
      :month="paymentFilters.month"
      :status="paymentFilters.status"
      :months="availableMonths"
      :has-active-filters="hasActivePaymentFilters"
      :hide-status="activeView === 'reminders' || activeView === 'history'"
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

      <button class="btn btn--secondary btn--sm" type="button" @click="loadPayments">Retry</button>
    </div>

    <div v-if="isLoading && activePayments.length === 0" class="payments-page__loading">
      <LoadingSpinner label="Loading payments" />
    </div>

    <template v-else-if="!errorMessage">
      <EmptyState
        v-if="activePayments.length === 0"
        title="No payments found"
        :description="emptyStateDescription"
      >
        <template #icon><WalletCards :size="26" /></template>
        <template #primary-action>
          <button
            v-if="hasActivePaymentFilters"
            class="btn btn--primary"
            type="button"
            @click="clearFilters"
          >
            <RotateCcw :size="16" aria-hidden="true" /> Clear Filters
          </button>

          <span v-else></span>
        </template>

        <template #secondary-action>
          <span></span>
        </template>
      </EmptyState>

      <template v-else>
        <DataTable :columns="columns" :rows="paginatedPayments" :aria-label="tableAriaLabel">
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

          <template #cell-transactionId="{ value }">
            {{ value || '—' }}
          </template>

          <template #cell-paidAt="{ value }">
            {{ formatDateTime(value) }}
          </template>

          <template #actions="{ row }">
            <div class="payments-page__actions">
              <button
                v-if="activeView === 'monthly'"
                class="btn btn--secondary btn--sm"
                type="button"
                @click="openStatusDialog(row)"
              >
                <CircleCheckBig :size="15" aria-hidden="true" /> Update Status
              </button>

              <button
                v-if="activeView !== 'reminders' && row.status === 'paid'"
                class="btn btn--secondary btn--sm"
                type="button"
                :disabled="isLoadingReceipt"
                @click="openReceiptDialog(row)"
              >
                <ReceiptText :size="15" aria-hidden="true" /> View Receipt
              </button>

              <button
                v-if="activeView === 'reminders'"
                class="btn btn--primary btn--sm"
                type="button"
                @click="openReminderDialog(row)"
              >
                <MessageCircleMore :size="15" aria-hidden="true" /> Send Reminder
              </button>
            </div>
          </template>
        </DataTable>

        <footer class="payments-page__pagination">
          <p class="text-small text-muted m-0">
            Showing {{ paginationStart }}–{{ paginationEnd }} of
            {{ activePayments.length }} payments
          </p>

          <Pagination v-model:current-page="currentPage" :total-pages="totalPages" />
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
    <ReceiptPreviewDialog
      :is-open="isReceiptDialogOpen"
      :receipt="selectedReceipt"
      @close="closeReceiptDialog"
      @download="handleReceiptDownload"
    />
    <WhatsAppReminderDialog
      :is-open="isReminderDialogOpen"
      :payment="selectedPayment"
      :reminder="selectedReminder"
      :is-submitting="isGeneratingReminder"
      @close="closeReminderDialog"
      @generate="handleGenerateReminder"
      @open-whatsapp="handleOpenWhatsApp"
    />
  </section>
</template>

<script setup>
import {
  CalendarClock,
  CalendarDays,
  CircleAlert,
  CircleCheckBig,
  ClockAlert,
  CreditCard,
  FilePlus2,
  History,
  IndianRupee,
  MessageCircleMore,
  ReceiptText,
  RotateCcw,
  UsersRound,
  WalletCards,
} from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onMounted, ref, watch } from 'vue'

import DataTable from '../../components/common/DataTable.vue'
import EmptyState from '../../components/common/EmptyState.vue'
import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import Pagination from '../../components/common/Pagination.vue'
import PaymentFilters from '../../components/payment/PaymentFilters.vue'
import PaymentStatusDialog from '../../components/payment/PaymentStatusDialog.vue'
import ReceiptPreviewDialog from '../../components/payment/ReceiptPreviewDialog.vue'
import WhatsAppReminderDialog from '../../components/payment/WhatsAppReminderDialog.vue'
import { usePaymentStore } from '../../stores/paymentStore'
import { useStudentStore } from '../../stores/studentStore'

const PAGE_SIZE = 5

function getCurrentMonth() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')

  return `${year}-${month}`
}

const columns = computed(() => {
  if (activeView.value === 'history') {
    return [
      { key: 'studentName', label: 'Student' },
      { key: 'month', label: 'Month' },
      { key: 'amount', label: 'Amount' },
      { key: 'paymentMethod', label: 'Payment Method' },
      { key: 'transactionId', label: 'Transaction ID' },
      { key: 'paidAt', label: 'Paid Date' },
    ]
  }

  return [
    { key: 'studentName', label: 'Student' },
    { key: 'month', label: 'Month' },
    { key: 'amount', label: 'Amount' },
    { key: 'status', label: 'Status' },
    { key: 'paymentMethod', label: 'Payment Method' },
  ]
})

const paymentStore = usePaymentStore()
const studentStore = useStudentStore()

const {
  payments,
  pendingPayments,
  selectedPayment,
  selectedReceipt,
  selectedReminder,
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

const { students } = storeToRefs(studentStore)

const currentPage = ref(1)
const isGeneratingMonthlyPayments = ref(false)
const generationResult = ref(null)
const activeView = ref('monthly')

paymentStore.updatePaymentFilter('month', getCurrentMonth())

const isStatusDialogOpen = ref(false)
const isUpdatingStatus = ref(false)
const isReceiptDialogOpen = ref(false)
const isLoadingReceipt = ref(false)
const isReminderDialogOpen = ref(false)
const isGeneratingReminder = ref(false)

const activePayments = computed(() => {
  return activeView.value === 'reminders' ? pendingPayments.value : payments.value
})

const reminderPaymentCount = computed(() => {
  return pendingPayments.value.length
})

const reminderTotalDueAmount = computed(() => {
  return pendingPayments.value.reduce((total, payment) => {
    return total + Number(payment.amount || 0)
  }, 0)
})

const reminderStudentCount = computed(() => {
  return new Set(pendingPayments.value.map((payment) => payment.studentId)).size
})

const reminderMonthCount = computed(() => {
  return new Set(pendingPayments.value.map((payment) => payment.month)).size
})

const totalPages = computed(() => {
  return Math.max(1, Math.ceil(activePayments.value.length / PAGE_SIZE))
})

const paginatedPayments = computed(() => {
  const startIndex = (currentPage.value - 1) * PAGE_SIZE

  return activePayments.value.slice(startIndex, startIndex + PAGE_SIZE)
})

const paginationStart = computed(() => {
  if (activePayments.value.length === 0) return 0

  return (currentPage.value - 1) * PAGE_SIZE + 1
})

const paginationEnd = computed(() => {
  return Math.min(currentPage.value * PAGE_SIZE, activePayments.value.length)
})

const emptyStateDescription = computed(() => {
  if (hasActivePaymentFilters.value) {
    if (activeView.value === 'history') {
      return 'No payment history records match the current search and filters.'
    }

    if (activeView.value === 'reminders') {
      return 'No pending payments match the current search and filters.'
    }

    return 'No payment records match the current search and filters.'
  }

  if (activeView.value === 'history') {
    return 'Previous payment transactions will appear here when they are available.'
  }

  if (activeView.value === 'reminders') {
    return 'Students with pending fees will appear here when reminders are needed.'
  }

  return 'Monthly payment records will appear here when they are available.'
})

const pageTitle = computed(() => {
  if (activeView.value === 'history') return 'Payment History'
  if (activeView.value === 'reminders') return 'Fee Reminders'

  return 'Monthly Payments'
})

const pageDescription = computed(() => {
  if (activeView.value === 'history') {
    return 'Review previous payment transactions using student, month, and status filters.'
  }

  if (activeView.value === 'reminders') {
    return 'Review pending student fees, preview reminder messages, and open WhatsApp reminders.'
  }

  return 'Track monthly fees, review payment status, and manage student payments.'
})

const tableAriaLabel = computed(() => {
  if (activeView.value === 'history') return 'Payment history records'
  if (activeView.value === 'reminders') {
    return 'Pending payment reminder records'
  }

  return 'Monthly payment records'
})

watch(
  () => [paymentFilters.value.search, paymentFilters.value.month, paymentFilters.value.status],
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
  if (!['monthly', 'history', 'reminders'].includes(view)) return
  if (activeView.value === view) return

  activeView.value = view
  currentPage.value = 1

  if (view === 'monthly') {
    paymentStore.setPaymentFilters({
      month: getCurrentMonth(),
      status: '',
    })
    return
  }

  if (view === 'history') {
    paymentStore.setPaymentFilters({
      month: '',
      status: '',
    })
    return
  }

  if (view === 'reminders') {
    paymentStore.setPaymentFilters({
      month: '',
      status: '',
    })
  }
}

function updateFilter(filterName, value) {
  paymentStore.updatePaymentFilter(filterName, value)
}

function clearFilters() {
  paymentStore.resetPaymentFilters()
}

async function handleGenerateMonthlyPayments() {
  const month = paymentFilters.value.month

  if (!month || isGeneratingMonthlyPayments.value) return

  isGeneratingMonthlyPayments.value = true
  generationResult.value = null

  try {
    await studentStore.fetchStudents()

    const response = await paymentStore.generateMonthlyPayments(month, students.value)

    generationResult.value = {
      month,
      createdCount: response.meta?.createdCount || 0,
      skippedCount: response.meta?.skippedCount || 0,
      activeStudentCount: response.meta?.activeStudentCount || 0,
    }

    currentPage.value = 1
    await paymentStore.fetchPayments()
  } catch {
    // Store-owned error state is rendered by the page.
  } finally {
    isGeneratingMonthlyPayments.value = false
  }
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

async function openReceiptDialog(payment) {
  if (!payment || payment.status !== 'paid' || isLoadingReceipt.value) return

  paymentStore.clearSelectedReceipt()
  isLoadingReceipt.value = true

  try {
    await paymentStore.generateReceipt(payment.id)
    isReceiptDialogOpen.value = true
  } catch {
    // Store-owned error state is rendered by the page.
  } finally {
    isLoadingReceipt.value = false
  }
}

function closeReceiptDialog() {
  isReceiptDialogOpen.value = false
  paymentStore.clearSelectedReceipt()
}

function handleReceiptDownload(receipt) {
  if (!receipt) return

  // Milestone 2 placeholder until backend receipt download is available.
}

function openReminderDialog(payment) {
  paymentStore.selectedPayment = payment
  paymentStore.clearSelectedReminder()
  isReminderDialogOpen.value = true
}

function closeReminderDialog() {
  if (isGeneratingReminder.value) return

  isReminderDialogOpen.value = false
  paymentStore.clearSelectedPayment()
  paymentStore.clearSelectedReminder()
}

async function handleGenerateReminder(reminderPayload) {
  if (!selectedPayment.value) return

  isGeneratingReminder.value = true

  try {
    await paymentStore.generateWhatsAppReminder(selectedPayment.value.id, reminderPayload)
  } catch {
    // Store-owned error state is rendered by the page.
  } finally {
    isGeneratingReminder.value = false
  }
}

function handleOpenWhatsApp(whatsappUrl) {
  if (!whatsappUrl) return

  window.open(whatsappUrl, '_blank', 'noopener,noreferrer')
}

async function handleStatusUpdate(statusPayload) {
  if (!selectedPayment.value) return

  isUpdatingStatus.value = true

  try {
    await paymentStore.updatePaymentStatus(selectedPayment.value.id, statusPayload)

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

    if (activeView.value === 'reminders') {
      await paymentStore.fetchPendingPayments({
        search: paymentFilters.value.search,
        month: paymentFilters.value.month,
      })
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

function formatDateTime(value) {
  if (!value) return '—'

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) return value

  return new Intl.DateTimeFormat('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
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

.payments-page__generation {
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

.payments-page__actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-2);
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
