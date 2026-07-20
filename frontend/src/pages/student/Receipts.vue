<template>
  <section class="student-receipts" aria-labelledby="student-receipts-title">
    <header class="receipts-header">
      <div>
        <p class="text-label text-muted m-0">Payments</p>
        <h1 id="student-receipts-title" class="text-h2 receipts-header__title">Fee Receipts</h1>
        <p class="receipts-header__description">View receipts issued for your completed payments.</p>
      </div>
      <button class="btn btn--primary" type="button" :disabled="isLoading" @click="loadReceipts">
        {{ isLoading ? 'Refreshing...' : 'Refresh' }}
      </button>
    </header>

    <Toast v-if="notice" type="info">{{ notice }}</Toast>
    <div v-if="errorMessage" class="alert alert--danger" role="alert">
      <span>{{ errorMessage }}</span>
      <button class="btn btn--secondary btn--sm" type="button" @click="loadReceipts">Retry</button>
    </div>
    <LoadingSpinner v-if="isLoading && receipts.length === 0" label="Loading receipts" />

    <template v-else>
      <StudentSummaryCards :items="summaryItems" aria-label="Receipt summary" />

      <section class="card receipt-list" aria-labelledby="receipt-list-title">
        <header class="receipt-list__header">
          <div><h2 id="receipt-list-title" class="text-h4 m-0">Receipt History</h2><p class="text-small text-muted m-0">Only paid fees produce a receipt.</p></div>
          <span class="text-small text-muted">{{ receipts.length }} receipts</span>
        </header>

        <DataTable :columns="columns" :rows="receipts" aria-label="Student fee receipts">
          <template #empty>No receipts are available yet.</template>
          <template #cell-receiptNumber="{ value }"><strong>{{ value }}</strong></template>
          <template #cell-month="{ value }">{{ formatMonth(value) }}</template>
          <template #cell-amount="{ value }">{{ formatCurrency(value) }}</template>
          <template #cell-paidAt="{ value }">{{ formatDate(value) }}</template>
          <template #cell-paymentMethod="{ value }">{{ formatLabel(value) }}</template>
          <template #actions="{ row }"><button class="btn btn--secondary btn--sm" type="button" @click="portalStore.selectReceipt(row)">View</button></template>
        </DataTable>

        <div class="receipt-list__cards">
          <p v-if="receipts.length === 0" class="receipt-list__empty">No receipts are available yet.</p>
          <article v-for="receipt in receipts" :key="receipt.id" class="receipt-card">
            <div><div><span class="text-small text-muted">{{ formatMonth(receipt.month) }}</span><strong>{{ receipt.receiptNumber }}</strong></div><span class="badge badge--success">Paid</span></div>
            <dl><div><dt>Amount</dt><dd>{{ formatCurrency(receipt.amount) }}</dd></div><div><dt>Paid On</dt><dd>{{ formatDate(receipt.paidAt) }}</dd></div><div><dt>Method</dt><dd>{{ formatLabel(receipt.paymentMethod) }}</dd></div></dl>
            <button class="btn btn--secondary" type="button" @click="portalStore.selectReceipt(receipt)">View Receipt</button>
          </article>
        </div>
      </section>
    </template>

    <ReceiptPreviewDialog :is-open="Boolean(selectedReceipt)" :receipt="selectedReceipt" @close="portalStore.clearSelectedReceipt" @download="handleDownload" />
  </section>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import DataTable from '../../components/common/DataTable.vue'
import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import Toast from '../../components/common/Toast.vue'
import ReceiptPreviewDialog from '../../components/payment/ReceiptPreviewDialog.vue'
import StudentSummaryCards from '../../components/student/StudentSummaryCards.vue'
import { useAuthStore } from '../../stores/authStore'
import { useStudentPortalStore } from '../../stores/studentPortalStore'

const authStore = useAuthStore()
const portalStore = useStudentPortalStore()
const { currentUser } = storeToRefs(authStore)
const { receipts, selectedReceipt, isLoading, errorMessage } = storeToRefs(portalStore)
const notice = ref('')
let noticeTimer = null
const columns = [{ key: 'receiptNumber', label: 'Receipt' }, { key: 'month', label: 'Month' }, { key: 'amount', label: 'Amount' }, { key: 'paidAt', label: 'Paid On' }, { key: 'paymentMethod', label: 'Method' }]
const summaryItems = computed(() => [
  { label: 'Total Receipts', value: receipts.value.length, detail: 'Completed payments', icon: 'R', tone: 'primary' },
  { label: 'Total Paid', value: formatCurrency(receipts.value.reduce((total, item) => total + item.amount, 0)), detail: 'Across all receipts', icon: 'P', tone: 'success' },
  { label: 'Latest Receipt', value: receipts.value[0]?.receiptNumber || '-', detail: formatMonth(receipts.value[0]?.month), icon: 'L', tone: 'info' },
  { label: 'Latest Payment', value: formatDate(receipts.value[0]?.paidAt), detail: receipts.value[0] ? formatCurrency(receipts.value[0].amount) : 'No payment', icon: 'D', tone: 'success' },
])

function formatCurrency(value) { return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(Number(value || 0)) }
function formatLabel(value) { return String(value || '-').replace(/[-_]/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase()) }
function formatMonth(value) { if (!value) return 'Not available'; const [year, month] = value.split('-').map(Number); return new Intl.DateTimeFormat('en-IN', { month: 'long', year: 'numeric' }).format(new Date(year, month - 1, 1)) }
function formatDate(value) { return value ? new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(value)) : 'Not available' }
async function loadReceipts() { try { await portalStore.fetchReceipts(currentUser.value?.id) } catch { /* Store-owned errors are rendered above. */ } }
function handleDownload() { notice.value = 'Receipt downloads will be enabled when the backend receipt API is connected.'; window.clearTimeout(noticeTimer); noticeTimer = window.setTimeout(() => { notice.value = '' }, 4000) }

onMounted(loadReceipts)
onBeforeUnmount(() => { window.clearTimeout(noticeTimer); portalStore.clearSelectedReceipt() })
</script>

<style scoped>
.student-receipts { display: grid; gap: var(--space-6); }
.receipts-header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-5); }
.receipts-header__title { margin: var(--space-1) 0 0; }
.receipts-header__description { margin: var(--space-2) 0 0; color: var(--color-text-muted); }
.receipt-list { overflow: hidden; }
.receipt-list__header { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); padding: var(--space-5); border-bottom: 1px solid var(--color-divider); }
.receipt-list__cards { display: none; }
.receipt-list__empty { margin: 0; padding: var(--space-6); text-align: center; color: var(--color-text-muted); }
.receipt-card { display: grid; gap: var(--space-4); padding: var(--space-4); border-bottom: 1px solid var(--color-divider); }
.receipt-card > div { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-3); }
.receipt-card > div > div { display: grid; gap: var(--space-1); }
.receipt-card dl { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--space-3); margin: 0; }
.receipt-card dl div { display: grid; gap: var(--space-1); }
.receipt-card dt { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.receipt-card dd { margin: 0; font-size: var(--font-size-sm); overflow-wrap: anywhere; }
@media (max-width: 680px) {
  .receipts-header { flex-direction: column; }
  .receipts-header .btn { width: 100%; }
  .receipt-list :deep(.data-table) { display: none; }
  .receipt-list__cards { display: grid; }
  .receipt-list__header { align-items: flex-start; }
  .receipt-card dl { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
</style>
