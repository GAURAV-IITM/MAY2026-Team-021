<template>
  <section class="student-fees" aria-labelledby="student-fees-title">
    <header class="student-page-header">
      <div>
        <p class="text-label text-muted m-0">Payments</p>
        <h1 id="student-fees-title" class="text-h2 student-page-header__title">Fee Status</h1>
        <p class="student-page-header__description">Review your monthly fees and payment history.</p>
      </div>
      <div class="student-page-header__actions">
        <RouterLink class="btn btn--secondary" :to="{ name: 'studentReceipts' }">View Receipts</RouterLink>
        <button class="btn btn--primary" type="button" :disabled="isLoading" @click="loadFees">
          {{ isLoading ? 'Refreshing...' : 'Refresh' }}
        </button>
      </div>
    </header>

    <div v-if="errorMessage" class="alert alert--danger" role="alert">
      <span>{{ errorMessage }}</span>
      <button class="btn btn--secondary btn--sm" type="button" @click="loadFees">Retry</button>
    </div>

    <LoadingSpinner v-if="isLoading && !feeSummary" label="Loading fee details" />

    <template v-else-if="feeSummary">
      <StudentSummaryCards :items="summaryItems" aria-label="Fee summary" />

      <section class="card current-fee" aria-labelledby="current-fee-title">
        <div>
          <p class="text-label text-muted m-0">Current Month</p>
          <h2 id="current-fee-title" class="text-h4 current-fee__title">
            {{ formatMonth(feeSummary.currentPayment?.month) }}
          </h2>
          <p class="text-small text-muted m-0">Due by {{ formatDate(feeSummary.nextDueDate) }}</p>
        </div>
        <div class="current-fee__amount">
          <strong>{{ formatCurrency(feeSummary.currentPayment?.amount) }}</strong>
          <span class="badge" :class="statusClass(feeSummary.currentPayment?.status)">
            {{ formatLabel(feeSummary.currentPayment?.status || 'not generated') }}
          </span>
        </div>
      </section>

      <section class="card fee-history" aria-labelledby="fee-history-title">
        <header class="fee-history__header">
          <div>
            <h2 id="fee-history-title" class="text-h4 m-0">Payment History</h2>
            <p class="text-small text-muted m-0">Monthly fee records associated with your account.</p>
          </div>
          <span class="text-small text-muted">{{ feeSummary.payments.length }} records</span>
        </header>

        <DataTable
          class="fee-history__table"
          :columns="columns"
          :rows="feeSummary.payments"
          aria-label="Student payment history"
        >
          <template #cell-month="{ value }"><strong>{{ formatMonth(value) }}</strong></template>
          <template #cell-amount="{ value }">{{ formatCurrency(value) }}</template>
          <template #cell-status="{ value }">
            <span class="badge" :class="statusClass(value)">{{ formatLabel(value) }}</span>
          </template>
          <template #cell-paidAt="{ value }">{{ value ? formatDate(value) : 'Not paid' }}</template>
          <template #cell-paymentMethod="{ value }">{{ value ? formatLabel(value) : '-' }}</template>
        </DataTable>

        <div class="fee-history__cards" aria-label="Student payment history">
          <article v-for="payment in feeSummary.payments" :key="payment.id" class="fee-record">
            <div><strong>{{ formatMonth(payment.month) }}</strong><span>{{ formatCurrency(payment.amount) }}</span></div>
            <span class="badge" :class="statusClass(payment.status)">{{ formatLabel(payment.status) }}</span>
            <dl>
              <div><dt>Paid On</dt><dd>{{ payment.paidAt ? formatDate(payment.paidAt) : 'Not paid' }}</dd></div>
              <div><dt>Method</dt><dd>{{ payment.paymentMethod ? formatLabel(payment.paymentMethod) : '-' }}</dd></div>
            </dl>
          </article>
        </div>
      </section>
    </template>
  </section>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'

import DataTable from '../../components/common/DataTable.vue'
import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import StudentSummaryCards from '../../components/student/StudentSummaryCards.vue'
import { useAuthStore } from '../../stores/authStore'
import { useStudentPortalStore } from '../../stores/studentPortalStore'

const authStore = useAuthStore()
const portalStore = useStudentPortalStore()
const { currentUser } = storeToRefs(authStore)
const { feeSummary, isLoading, errorMessage } = storeToRefs(portalStore)

const columns = [
  { key: 'month', label: 'Month' },
  { key: 'amount', label: 'Amount' },
  { key: 'status', label: 'Status' },
  { key: 'paidAt', label: 'Paid On' },
  { key: 'paymentMethod', label: 'Method' },
]

const summaryItems = computed(() => [
  { label: 'Current Status', value: formatLabel(feeSummary.value.currentPayment?.status || 'Pending'), detail: formatMonth(feeSummary.value.currentPayment?.month), icon: 'S', tone: feeSummary.value.currentPayment?.status === 'paid' ? 'success' : 'warning' },
  { label: 'Current Fee', value: formatCurrency(feeSummary.value.currentPayment?.amount), detail: `Due ${formatDate(feeSummary.value.nextDueDate)}`, icon: 'F', tone: 'primary' },
  { label: 'Total Paid', value: formatCurrency(feeSummary.value.totalPaid), detail: `${feeSummary.value.paidCount} completed payments`, icon: 'P', tone: 'success' },
  { label: 'Outstanding', value: formatCurrency(feeSummary.value.totalOutstanding), detail: `${feeSummary.value.unpaidCount} unpaid records`, icon: 'D', tone: feeSummary.value.totalOutstanding ? 'danger' : 'info' },
])

function formatCurrency(value) { return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(Number(value || 0)) }
function formatLabel(value) { return String(value || '').replace(/[-_]/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase()) }
function formatMonth(value) {
  if (!value) return 'Not available'
  const [year, month] = value.split('-').map(Number)
  return new Intl.DateTimeFormat('en-IN', { month: 'long', year: 'numeric' }).format(new Date(year, month - 1, 1))
}
function formatDate(value) { return value ? new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(value)) : 'Not available' }
function statusClass(status) { return status === 'paid' ? 'badge--success' : 'badge--warning' }
async function loadFees() { try { await portalStore.fetchFees(currentUser.value?.id) } catch { /* Store-owned errors are rendered above. */ } }

onMounted(loadFees)
</script>

<style scoped>
.student-fees { display: grid; gap: var(--space-6); }
.student-page-header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-5); }
.student-page-header__title { margin: var(--space-1) 0 0; }
.student-page-header__description { margin: var(--space-2) 0 0; color: var(--color-text-muted); }
.student-page-header__actions { display: flex; gap: var(--space-3); }
.current-fee { display: flex; align-items: center; justify-content: space-between; gap: var(--space-5); padding: var(--space-5); }
.current-fee__title { margin: var(--space-1) 0; }
.current-fee__amount { display: flex; align-items: center; gap: var(--space-4); }
.current-fee__amount strong { font-size: var(--font-size-h3); }
.fee-history { overflow: hidden; }
.fee-history__header { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); padding: var(--space-5); border-bottom: 1px solid var(--color-divider); }
.fee-history__cards { display: none; }
.fee-record { display: grid; gap: var(--space-3); padding: var(--space-4); border-bottom: 1px solid var(--color-divider); }
.fee-record > div { display: flex; justify-content: space-between; gap: var(--space-3); }
.fee-record > .badge { justify-self: start; }
.fee-record dl { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-3); margin: 0; }
.fee-record dl div { display: grid; gap: var(--space-1); }
.fee-record dt { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.fee-record dd { margin: 0; font-size: var(--font-size-sm); }
@media (max-width: 680px) {
  .student-page-header { flex-direction: column; }
  .student-page-header__actions { width: 100%; }
  .student-page-header__actions > * { flex: 1; }
  .current-fee { align-items: flex-start; flex-direction: column; }
  .current-fee__amount { width: 100%; justify-content: space-between; }
  .fee-history__table { display: none; }
  .fee-history__cards { display: grid; }
  .fee-history__header { align-items: flex-start; }
}
</style>
