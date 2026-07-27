<template>
  <section class="payments-page" aria-labelledby="payments-title">
    <header class="payments-page__header">
      <div>
        <p class="text-label text-muted payments-page__eyebrow">
          Payment Management
        </p>
        <h1 id="payments-title" class="text-h2 payments-page__title">
          {{ activeView === 'monthly' ? 'Monthly Payments' : 'Payment History' }}
        </h1>
        <p class="text-body payments-page__description">
          Generate monthly fees and record full or partial payments.
        </p>
      </div>
    </header>

    <Toast v-if="successMessage" type="success">
      {{ successMessage }}
    </Toast>

    <nav class="payments-page__views" aria-label="Payment views">
      <button
        class="btn"
        :class="activeView === 'monthly' ? 'btn--primary' : 'btn--secondary'"
        type="button"
        :aria-pressed="activeView === 'monthly'"
        @click="setActiveView('monthly')"
      >
        <CalendarDays :size="17" aria-hidden="true" />
        Monthly Payments
      </button>
      <button
        class="btn"
        :class="activeView === 'history' ? 'btn--primary' : 'btn--secondary'"
        type="button"
        :aria-pressed="activeView === 'history'"
        @click="setActiveView('history')"
      >
        <History :size="17" aria-hidden="true" />
        Payment History
      </button>
    </nav>

    <section
      v-if="activeView === 'monthly'"
      class="payments-page__generation card"
      aria-label="Monthly fee generation"
    >
      <div>
        <strong>{{ formatMonth(paymentFilters.month) }}</strong>
        <p class="text-small text-muted m-0">
          Creates one fee record for each eligible active student. Existing
          records are kept unchanged.
        </p>
      </div>
      <button
        class="btn btn--primary"
        type="button"
        :disabled="!paymentFilters.month || isGenerating || isLoading"
        @click="handleGenerate"
      >
        <FilePlus2 :size="17" aria-hidden="true" />
        {{ isGenerating ? 'Generating...' : 'Generate Monthly Fees' }}
      </button>
    </section>

    <section
      v-if="generationResult"
      class="generation-result"
      aria-label="Generation result"
    >
      <div>
        <span class="text-label text-muted">Created</span>
        <strong>{{ generationResult.createdCount }}</strong>
      </div>
      <div>
        <span class="text-label text-muted">Already Existed</span>
        <strong>{{ generationResult.existingCount }}</strong>
      </div>
      <div>
        <span class="text-label text-muted">Skipped</span>
        <strong>{{ generationResult.skippedCount }}</strong>
      </div>
      <div>
        <span class="text-label text-muted">Eligible Students</span>
        <strong>{{ generationResult.eligibleStudentCount }}</strong>
      </div>
      <details
        v-if="generationResult.skippedStudents?.length"
        class="generation-result__details"
      >
        <summary>Why students were skipped</summary>
        <p
          v-for="student in generationResult.skippedStudents"
          :key="student.studentId"
          class="text-small m-0"
        >
          <strong>{{ student.studentName }}:</strong> {{ student.message }}
        </p>
      </details>
    </section>

    <section class="payments-page__summary" aria-label="Payment summary">
      <article class="stat-card stat-card--dashboard">
        <div class="stat-card__header">
          <span class="text-label text-muted">Fee Records</span>
          <CreditCard :size="20" aria-hidden="true" />
        </div>
        <strong class="stat-card__value">{{ paymentCount }}</strong>
        <span class="text-caption text-muted">
          {{ paidPaymentCount }} paid ·
          {{ partiallyPaidPaymentCount }} partial ·
          {{ unpaidPaymentCount }} unpaid
        </span>
      </article>
      <article class="stat-card stat-card--dashboard">
        <div class="stat-card__header">
          <span class="text-label text-muted">Total Billed</span>
          <ReceiptIndianRupee :size="20" aria-hidden="true" />
        </div>
        <strong class="stat-card__value">
          {{ formatCurrency(totalBilledAmount) }}
        </strong>
      </article>
      <article class="stat-card stat-card--dashboard">
        <div class="stat-card__header">
          <span class="text-label text-muted">Collected</span>
          <CircleCheckBig :size="20" aria-hidden="true" />
        </div>
        <strong class="stat-card__value">
          {{ formatCurrency(totalCollectedAmount) }}
        </strong>
      </article>
      <article class="stat-card stat-card--dashboard">
        <div class="stat-card__header">
          <span class="text-label text-muted">Pending</span>
          <ClockAlert :size="20" aria-hidden="true" />
        </div>
        <strong class="stat-card__value">
          {{ formatCurrency(totalPendingAmount) }}
        </strong>
      </article>
    </section>

    <PaymentFilters
      :search="paymentFilters.search"
      :month="paymentFilters.month"
      :status="paymentFilters.status"
      :has-active-filters="pageHasActiveFilters"
      @update:search="updateFilter('search', $event)"
      @update:month="updateFilter('month', $event)"
      @update:status="updateFilter('status', $event)"
      @clear="clearFilters"
    />

    <div v-if="errorMessage" class="alert alert--danger" role="alert">
      <div>
        <strong>Unable to complete the payment request.</strong>
        <p class="m-0">{{ errorMessage }}</p>
        <p v-if="errorRequestId" class="text-caption m-0">
          Request ID: {{ errorRequestId }}
        </p>
      </div>
      <button class="btn btn--secondary btn--sm" type="button" @click="loadPayments">
        Retry
      </button>
    </div>

    <div v-if="isLoading && payments.length === 0" class="payments-page__loading">
      <LoadingSpinner label="Loading payments" />
    </div>

    <template v-else-if="!errorMessage">
      <EmptyState
        v-if="payments.length === 0"
        title="No payment records found"
        :description="emptyStateDescription"
      >
        <template #icon><WalletCards :size="26" /></template>
        <template #primary-action>
          <button
            v-if="activeView === 'monthly' && paymentFilters.month"
            class="btn btn--primary"
            type="button"
            @click="handleGenerate"
          >
            <FilePlus2 :size="16" aria-hidden="true" />
            Generate Monthly Fees
          </button>
          <span v-else></span>
        </template>
        <template #secondary-action><span></span></template>
      </EmptyState>

      <template v-else>
        <DataTable
          class="payments-page__table"
          :columns="columns"
          :rows="payments"
          :aria-label="activeView === 'monthly' ? 'Monthly fee records' : 'Payment history'"
        >
          <template #cell-studentName="{ row }">
            <div class="payments-page__student">
              <strong>{{ row.studentName }}</strong>
              <span class="text-caption text-muted">
                {{ row.enrollmentNumber }} · {{ row.studentEmail }}
              </span>
            </div>
          </template>
          <template #cell-month="{ value }">{{ formatMonth(value) }}</template>
          <template #cell-dueDate="{ value }">{{ formatDate(value) }}</template>
          <template #cell-totalAmount="{ value }">
            {{ formatCurrency(value) }}
          </template>
          <template #cell-paidAmount="{ value }">
            {{ formatCurrency(value) }}
          </template>
          <template #cell-balanceAmount="{ value }">
            {{ formatCurrency(value) }}
          </template>
          <template #cell-status="{ value }">
            <span class="badge" :class="statusClass(value)">
              {{ formatLabel(value) }}
            </span>
          </template>
          <template #cell-paymentMethod="{ value }">
            {{ formatLabel(value) }}
          </template>
          <template #cell-transactionId="{ value }">{{ value || '—' }}</template>
          <template #cell-paidAt="{ value }">{{ formatDateTime(value) }}</template>
          <template #actions="{ row }">
            <div class="payments-page__actions">
              <button
                v-if="row.balanceAmount > 0"
                class="btn btn--primary btn--sm"
                type="button"
                @click="openRecordDialog(row)"
              >
                <CircleDollarSign :size="15" aria-hidden="true" />
                Record Payment
              </button>
              <button
                v-if="row.balanceAmount > 0"
                class="btn btn--secondary btn--sm"
                type="button"
                @click="openReminderDialog(row)"
              >
                <MessageCircle :size="15" aria-hidden="true" />
                Remind
              </button>
              <button
                v-if="row.transactions.length"
                class="btn btn--secondary btn--sm"
                type="button"
                @click="openHistoryDialog(row)"
              >
                <History :size="15" aria-hidden="true" />
                History
              </button>
            </div>
          </template>
        </DataTable>

        <div class="payments-page__mobile-list">
          <article
            v-for="payment in payments"
            :key="payment.id"
            class="payment-card"
          >
            <header>
              <div>
                <strong>{{ payment.studentName }}</strong>
                <span class="text-caption text-muted">
                  {{ formatMonth(payment.month) }}
                </span>
              </div>
              <span class="badge" :class="statusClass(payment.status)">
                {{ formatLabel(payment.status) }}
              </span>
            </header>
            <dl>
              <div><dt>Total</dt><dd>{{ formatCurrency(payment.totalAmount) }}</dd></div>
              <div><dt>Paid</dt><dd>{{ formatCurrency(payment.paidAmount) }}</dd></div>
              <div><dt>Balance</dt><dd>{{ formatCurrency(payment.balanceAmount) }}</dd></div>
              <div><dt>Due</dt><dd>{{ formatDate(payment.dueDate) }}</dd></div>
            </dl>
            <button
              v-if="payment.balanceAmount > 0"
              class="btn btn--primary"
              type="button"
              @click="openRecordDialog(payment)"
            >
              <CircleDollarSign :size="16" aria-hidden="true" />
              Record Payment
            </button>
            <button
              v-if="payment.balanceAmount > 0"
              class="btn btn--secondary"
              type="button"
              @click="openReminderDialog(payment)"
            >
              <MessageCircle :size="16" aria-hidden="true" />
              WhatsApp Reminder
            </button>
            <button
              v-if="payment.transactions.length"
              class="btn btn--secondary"
              type="button"
              @click="openHistoryDialog(payment)"
            >
              <History :size="16" aria-hidden="true" />
              Transaction History
            </button>
          </article>
        </div>

        <footer class="payments-page__pagination">
          <p class="text-small text-muted m-0">
            Showing {{ paginationStart }}–{{ paginationEnd }} of
            {{ pagination.totalItems }} records
          </p>
          <Pagination
            :current-page="pagination.page"
            :total-pages="Math.max(1, pagination.totalPages)"
            @update:current-page="changePage"
          />
        </footer>
      </template>
    </template>

    <RecordPaymentDialog
      :is-open="isRecordDialogOpen"
      :payment="selectedPayment"
      :is-submitting="isRecording"
      :submission-error="paymentSubmissionError"
      @close="closeRecordDialog"
      @confirm="handleRecordPayment"
    />
    <PaymentHistoryDialog
      :is-open="isHistoryDialogOpen"
      :payment="historyPayment"
      @close="closeHistoryDialog"
    />
    <WhatsAppReminderDialog
      :is-open="isReminderDialogOpen"
      :payment="reminderPayment"
      :is-submitting="isReminderSubmitting"
      :submission-error="reminderSubmissionError"
      @close="closeReminderDialog"
      @submit="handleReminder"
    />
    <ReceiptPreviewDialog
      :is-open="isReceiptPreviewOpen"
      :receipt="selectedReceipt"
      :is-loading="isReceiptPreviewLoading"
      :is-downloading="isReceiptDownloading"
      :error-message="isReceiptPreviewOpen ? receiptErrorMessage : ''"
      :request-id="receiptRequestId"
      @close="closeReceiptPreview"
      @retry="loadRecordedReceipt"
      @download="downloadRecordedReceipt"
    />
  </section>
</template>

<script setup>
import {
  CalendarDays,
  CircleCheckBig,
  CircleDollarSign,
  ClockAlert,
  CreditCard,
  FilePlus2,
  History,
  MessageCircle,
  ReceiptIndianRupee,
  WalletCards,
} from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import DataTable from '../../components/common/DataTable.vue'
import EmptyState from '../../components/common/EmptyState.vue'
import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import Pagination from '../../components/common/Pagination.vue'
import Toast from '../../components/common/Toast.vue'
import PaymentFilters from '../../components/payment/PaymentFilters.vue'
import PaymentHistoryDialog from '../../components/payment/PaymentHistoryDialog.vue'
import ReceiptPreviewDialog from '../../components/payment/ReceiptPreviewDialog.vue'
import RecordPaymentDialog from '../../components/payment/RecordPaymentDialog.vue'
import WhatsAppReminderDialog from '../../components/payment/WhatsAppReminderDialog.vue'
import { usePaymentStore } from '../../stores/paymentStore'

const paymentStore = usePaymentStore()
const {
  payments,
  selectedPayment,
  selectedReceipt,
  pagination,
  paymentFilters,
  isLoading,
  error,
  errorMessage,
  isReminderSubmitting,
  reminderError,
  isReceiptPreviewLoading,
  isReceiptDownloading,
  receiptError,
  receiptErrorMessage,
  paymentCount,
  paidPaymentCount,
  unpaidPaymentCount,
  partiallyPaidPaymentCount,
  totalCollectedAmount,
  totalPendingAmount,
  totalBilledAmount,
} = storeToRefs(paymentStore)

const activeView = ref('monthly')
const isGenerating = ref(false)
const generationResult = ref(null)
const isRecordDialogOpen = ref(false)
const isRecording = ref(false)
const isHistoryDialogOpen = ref(false)
const historyPayment = ref(null)
const isReminderDialogOpen = ref(false)
const reminderPayment = ref(null)
const isReceiptPreviewOpen = ref(false)
const recordedReceiptId = ref(null)
const successMessage = ref('')
let filterTimer = null
let toastTimer = null

const columns = computed(() => {
  if (activeView.value === 'history') {
    return [
      { key: 'studentName', label: 'Student' },
      { key: 'month', label: 'Month' },
      { key: 'paidAmount', label: 'Paid' },
      { key: 'paymentMethod', label: 'Latest Method' },
      { key: 'transactionId', label: 'Latest Reference' },
      { key: 'paidAt', label: 'Latest Payment' },
      { key: 'status', label: 'Status' },
    ]
  }
  return [
    { key: 'studentName', label: 'Student' },
    { key: 'month', label: 'Month' },
    { key: 'dueDate', label: 'Due Date' },
    { key: 'totalAmount', label: 'Total' },
    { key: 'paidAmount', label: 'Paid' },
    { key: 'balanceAmount', label: 'Balance' },
    { key: 'status', label: 'Status' },
  ]
})

const paginationStart = computed(() => {
  if (!pagination.value.totalItems) return 0
  return (pagination.value.page - 1) * pagination.value.pageSize + 1
})
const paginationEnd = computed(() =>
  Math.min(
    pagination.value.page * pagination.value.pageSize,
    pagination.value.totalItems,
  ),
)
const emptyStateDescription = computed(() => {
  if (pageHasActiveFilters.value) {
    return 'No fee records match the selected month, status, or student.'
  }
  return activeView.value === 'monthly'
    ? 'Generate fee records for the selected month to begin collecting payments.'
    : 'Recorded payment transactions will appear here.'
})
const pageHasActiveFilters = computed(() => {
  return Boolean(
    paymentFilters.value.search ||
    paymentFilters.value.status ||
    (
      activeView.value === 'monthly'
        ? paymentFilters.value.month !== getCurrentMonth()
        : paymentFilters.value.month
    ),
  )
})
const errorRequestId = computed(
  () => error.value?.response?.data?.requestId || '',
)
const paymentSubmissionError = computed(() => {
  if (!isRecordDialogOpen.value || !error.value) return null
  const response = error.value.response?.data
  return {
    message: response?.error?.message || error.value.message,
    requestId: response?.requestId,
    remainingBalance: response?.error?.details?.remainingBalance,
  }
})
const reminderSubmissionError = computed(() => {
  if (!isReminderDialogOpen.value || !reminderError.value) return null
  const response = reminderError.value.response?.data
  return {
    message:
      response?.error?.message ||
      reminderError.value.message ||
      'Unable to create the WhatsApp reminder link.',
    requestId: response?.requestId,
  }
})
const receiptRequestId = computed(
  () => receiptError.value?.response?.data?.requestId || '',
)

watch(
  () => [
    paymentFilters.value.search,
    paymentFilters.value.month,
    paymentFilters.value.status,
  ],
  () => {
    window.clearTimeout(filterTimer)
    filterTimer = window.setTimeout(loadPayments, 250)
  },
)

onMounted(loadPayments)
onBeforeUnmount(() => {
  window.clearTimeout(filterTimer)
  window.clearTimeout(toastTimer)
})

function setActiveView(view) {
  if (activeView.value === view) return
  activeView.value = view
  generationResult.value = null
  paymentStore.setPaymentFilters({
    month: view === 'monthly' ? getCurrentMonth() : '',
    status: '',
    page: 1,
  })
}

function getCurrentMonth() {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
}

function updateFilter(name, value) {
  paymentStore.updatePaymentFilter(name, value)
}

function clearFilters() {
  paymentStore.setPaymentFilters({
    search: '',
    month: activeView.value === 'monthly' ? getCurrentMonth() : '',
    status: '',
    page: 1,
  })
}

function changePage(page) {
  paymentStore.updatePaymentFilter('page', page)
  loadPayments()
}

async function loadPayments() {
  try {
    if (activeView.value === 'history') {
      await paymentStore.fetchPaymentHistory()
      return
    }
    await paymentStore.fetchPayments()
  } catch {
    // Store-owned errors are rendered above the table.
  }
}

async function handleGenerate() {
  if (!paymentFilters.value.month || isGenerating.value) return
  isGenerating.value = true
  generationResult.value = null
  try {
    const response = await paymentStore.generateMonthlyPayments(
      paymentFilters.value.month,
    )
    generationResult.value = response.data
    showSuccess(
      `${response.data.createdCount} fee records created; ` +
        `${response.data.existingCount} already existed.`,
    )
  } catch {
    // Store-owned errors are rendered above the table.
  } finally {
    isGenerating.value = false
  }
}

function openRecordDialog(payment) {
  paymentStore.clearError()
  paymentStore.selectedPayment = payment
  isRecordDialogOpen.value = true
}

function closeRecordDialog() {
  if (isRecording.value) return
  isRecordDialogOpen.value = false
  paymentStore.clearSelectedPayment()
  paymentStore.clearError()
}

function openHistoryDialog(payment) {
  historyPayment.value = payment
  isHistoryDialogOpen.value = true
}

function closeHistoryDialog() {
  isHistoryDialogOpen.value = false
  historyPayment.value = null
}

function openReminderDialog(payment) {
  paymentStore.clearSelectedReminder()
  reminderPayment.value = payment
  isReminderDialogOpen.value = true
}

function closeReminderDialog() {
  if (isReminderSubmitting.value) return
  isReminderDialogOpen.value = false
  reminderPayment.value = null
  paymentStore.clearSelectedReminder()
}

async function handleRecordPayment(payload) {
  if (!selectedPayment.value || isRecording.value) return
  isRecording.value = true
  try {
    const response = await paymentStore.recordPayment(
      selectedPayment.value.id,
      payload,
    )
    isRecordDialogOpen.value = false
    paymentStore.clearSelectedPayment()
    showSuccess(
      `${formatCurrency(response.data.transaction.amount)} recorded. Receipt ` +
        `${response.data.receipt.receiptNumber} is ready.`,
    )
    recordedReceiptId.value = response.data.receipt.id
    isReceiptPreviewOpen.value = true
    await loadRecordedReceipt()
  } catch {
    // The dialog remains open so the administrator can correct the input.
  } finally {
    isRecording.value = false
  }
}

async function loadRecordedReceipt() {
  if (!recordedReceiptId.value) return
  try {
    await paymentStore.fetchReceiptDetail(recordedReceiptId.value)
  } catch {
    // Receipt dialog renders the structured API error and retry action.
  }
}

function closeReceiptPreview() {
  isReceiptPreviewOpen.value = false
  recordedReceiptId.value = null
  paymentStore.clearSelectedReceipt()
}

async function downloadRecordedReceipt() {
  if (!recordedReceiptId.value || isReceiptDownloading.value) return
  try {
    const { blob, filename } = await paymentStore.downloadReceipt(
      recordedReceiptId.value,
    )
    const objectUrl = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = objectUrl
    link.download = filename
    document.body.appendChild(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(objectUrl)
    showSuccess('Receipt PDF downloaded.')
  } catch {
    // Receipt dialog displays the download error and request ID.
  }
}

async function handleReminder(payload) {
  if (!reminderPayment.value || isReminderSubmitting.value) return
  const pendingTab = window.open('about:blank', '_blank')
  if (pendingTab) {
    pendingTab.opener = null
  }
  try {
    const response = await paymentStore.createWhatsAppReminder(
      reminderPayment.value.id,
      payload,
    )
    const whatsappUrl = response.data.whatsappUrl
    if (pendingTab) {
      pendingTab.location.replace(whatsappUrl)
      showSuccess('Reminder attempt recorded and WhatsApp link opened.')
    } else {
      showSuccess(
        'Reminder attempt recorded. Allow popups to open the WhatsApp link.',
      )
    }
    isReminderDialogOpen.value = false
    reminderPayment.value = null
  } catch {
    pendingTab?.close()
    // The dialog stays open with the server's actionable error.
  }
}

function showSuccess(message) {
  successMessage.value = message
  window.clearTimeout(toastTimer)
  toastTimer = window.setTimeout(() => {
    successMessage.value = ''
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
  if (!month) return 'All months'
  const [year, monthNumber] = month.split('-').map(Number)
  return new Intl.DateTimeFormat('en-IN', {
    month: 'long',
    year: 'numeric',
  }).format(new Date(year, monthNumber - 1, 1))
}

function formatDate(value) {
  if (!value) return '—'
  return new Intl.DateTimeFormat('en-IN', {
    dateStyle: 'medium',
  }).format(new Date(`${value}T00:00:00`))
}

function formatDateTime(value) {
  if (!value) return '—'
  return new Intl.DateTimeFormat('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function formatLabel(value) {
  if (!value) return '—'
  return String(value)
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())
}

function statusClass(status) {
  return {
    paid: 'badge--paid',
    partially_paid: 'badge--warning',
    unpaid: 'badge--pending',
  }[status]
}
</script>

<style scoped>
.payments-page {
  display: grid;
  gap: var(--space-6);
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

.payments-page__views,
.payments-page__generation,
.payments-page__pagination {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.payments-page__views {
  flex-wrap: wrap;
}

.payments-page__generation {
  justify-content: space-between;
  padding: var(--space-4);
}

.generation-result {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-3);
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-elevated);
}

.generation-result > div {
  display: grid;
  gap: var(--space-1);
}

.generation-result__details {
  grid-column: 1 / -1;
}

.generation-result__details p {
  margin-top: var(--space-2);
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
  min-width: 190px;
}

.payments-page__actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.payments-page__pagination {
  justify-content: space-between;
}

.payments-page__mobile-list {
  display: none;
}

.payment-card {
  display: grid;
  gap: var(--space-4);
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-elevated);
}

.payment-card header,
.payment-card header > div {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
}

.payment-card header > div {
  flex-direction: column;
  gap: var(--space-1);
}

.payment-card dl {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--space-3);
  margin: 0;
}

.payment-card dl > div {
  display: grid;
  gap: var(--space-1);
}

.payment-card dt {
  color: var(--color-text-muted);
  font-size: var(--font-size-caption);
}

.payment-card dd {
  margin: 0;
  font-weight: var(--font-weight-semibold);
}

@media (max-width: 1000px) {
  .payments-page__summary,
  .generation-result {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .payments-page__generation,
  .payments-page__pagination {
    align-items: stretch;
    flex-direction: column;
  }

  .payments-page__generation .btn {
    width: 100%;
  }

  .payments-page__table {
    display: none;
  }

  .payments-page__mobile-list {
    display: grid;
    gap: var(--space-3);
  }
}

@media (max-width: 560px) {
  .payments-page__summary,
  .generation-result {
    grid-template-columns: 1fr;
  }
}
</style>
