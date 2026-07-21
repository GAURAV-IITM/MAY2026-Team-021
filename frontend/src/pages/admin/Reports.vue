<template>
  <section class="reports-page" aria-labelledby="reports-title">
    <header class="reports-page__header">
      <div>
        <p class="text-label text-muted m-0">Business Intelligence</p>
        <h1 id="reports-title">Reports & Analytics</h1>
        <p>Monitor revenue, seat usage, student growth, and payment collection.</p>
      </div>

      <div class="reports-page__header-actions">
        <span v-if="reports?.generatedAt" class="reports-page__updated">
          Updated {{ formatDateTime(reports.generatedAt) }}
        </span>
        <button class="btn btn--secondary btn--icon" type="button" :disabled="isLoading" title="Refresh reports" aria-label="Refresh reports" @click="refreshReports">
          <RefreshCw :size="18" :class="{ 'reports-page__spin': isLoading }" aria-hidden="true" />
        </button>
        <ReportExportMenu :disabled="!reports || isLoading || isExporting" :exporting="isExporting" @export="downloadReport" @print="printReport" />
      </div>
    </header>

    <div v-if="errorMessage" class="alert alert--danger reports-page__error" role="alert">
      <div><strong>Unable to load reports.</strong><p class="m-0">{{ errorMessage }}</p></div>
      <button class="btn btn--secondary btn--sm" type="button" @click="refreshReports">Retry</button>
    </div>

    <ReportFilters
      v-if="options.months.length"
      :model-value="filters"
      :options="options"
      :loading="isLoading"
      @apply="applyFilters"
      @reset="resetFilters"
    />

    <div v-if="isLoading && !reports" class="reports-page__loading">
      <LoadingSpinner label="Building reports and analytics" />
      <p>Combining payment, student, and seat data...</p>
    </div>

    <template v-else-if="reports">
      <ReportMetricCards :items="metricItems" />

      <nav class="reports-page__tabs" aria-label="Report views">
        <div role="tablist">
          <button
            v-for="tab in reportTabs"
            :id="`report-tab-${tab.id}`"
            :key="tab.id"
            type="button"
            role="tab"
            :aria-selected="String(activeTab === tab.id)"
            :aria-controls="`report-panel-${tab.id}`"
            :class="{ 'reports-page__tab--active': activeTab === tab.id }"
            @click="selectTab(tab.id)"
          >
            <component :is="getTabIcon(tab.id)" :size="17" aria-hidden="true" />
            {{ tab.label }}
          </button>
        </div>
      </nav>

      <div
        :id="`report-panel-${activeTab}`"
        class="reports-page__content"
        role="tabpanel"
        :aria-labelledby="`report-tab-${activeTab}`"
      >
        <ReportsOverview v-if="activeTab === 'overview'" :reports="reports" />
        <RevenueReport v-else-if="activeTab === 'revenue'" :revenue="reports.revenue" />
        <SeatOccupancyReport v-else-if="activeTab === 'occupancy'" :occupancy="reports.occupancy" />
        <StudentStatisticsReport v-else-if="activeTab === 'students'" :students="reports.students" :shift-options="options.shifts" />
        <PendingPaymentsReport v-else :pending="reports.pendingPayments" />
      </div>
    </template>

    <Toast v-if="toastMessage" :type="toastType">{{ toastMessage }}</Toast>
  </section>
</template>

<script setup>
import {
  Armchair,
  BadgeIndianRupee,
  ChartNoAxesCombined,
  CircleDollarSign,
  ClockAlert,
  IndianRupee,
  LayoutDashboard,
  Percent,
  ReceiptIndianRupee,
  RefreshCw,
  TrendingUp,
  UserCheck,
  UserPlus,
  Users,
  WalletCards,
  Wrench,
} from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import Toast from '../../components/common/Toast.vue'
import PendingPaymentsReport from '../../components/reports/PendingPaymentsReport.vue'
import ReportExportMenu from '../../components/reports/ReportExportMenu.vue'
import ReportFilters from '../../components/reports/ReportFilters.vue'
import ReportMetricCards from '../../components/reports/ReportMetricCards.vue'
import ReportsOverview from '../../components/reports/ReportsOverview.vue'
import RevenueReport from '../../components/reports/RevenueReport.vue'
import SeatOccupancyReport from '../../components/reports/SeatOccupancyReport.vue'
import StudentStatisticsReport from '../../components/reports/StudentStatisticsReport.vue'
import { REPORT_TABS } from '../../mocks/analyticsMock.js'
import { useAnalyticsStore } from '../../stores/analyticsStore.js'

const store = useAnalyticsStore()
const { reports, options, filters, isLoading, isExporting, errorMessage } = storeToRefs(store)
const route = useRoute()
const router = useRouter()
const reportTabs = REPORT_TABS
const validTabs = new Set(reportTabs.map((tab) => tab.id))
const activeTab = ref(validTabs.has(route.query.view) ? route.query.view : 'overview')
const toastMessage = ref('')
const toastType = ref('success')
let toastTimer

const currencyFormatter = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })
const numberFormatter = new Intl.NumberFormat('en-IN')
const tabIcons = { overview: LayoutDashboard, revenue: TrendingUp, occupancy: Armchair, students: Users, pending: ClockAlert }

const metricItems = computed(() => {
  if (!reports.value) return []
  const data = reports.value

  if (activeTab.value === 'revenue') {
    return [
      { label: 'Expected Revenue', value: formatCurrency(data.revenue.totals.expected), detail: 'Fees raised in this period', icon: WalletCards, tone: 'info' },
      { label: 'Collected Revenue', value: formatCurrency(data.revenue.totals.collected), detail: 'Successfully received', icon: IndianRupee, tone: 'success', change: data.revenue.totals.revenueChange },
      { label: 'Pending Revenue', value: formatCurrency(data.revenue.totals.pending), detail: `${data.pendingPayments.totals.pendingCount} unpaid records`, icon: ReceiptIndianRupee, tone: 'warning' },
      { label: 'Collection Rate', value: `${data.revenue.totals.collectionRate}%`, detail: 'Collected against expected', icon: Percent, tone: data.revenue.totals.collectionRate >= 85 ? 'success' : 'warning' },
    ]
  }

  if (activeTab.value === 'occupancy') {
    return [
      { label: 'Total Seats', value: formatNumber(data.occupancy.totals.totalSeats), detail: 'Seats in selected floors', icon: Armchair },
      { label: 'Assigned Seats', value: formatNumber(data.occupancy.totals.occupiedSeats), detail: 'Used in at least one shown shift', icon: UserCheck, tone: 'info' },
      { label: 'Available Seats', value: formatNumber(data.occupancy.totals.availableSeats), detail: 'Not currently assigned', icon: ChartNoAxesCombined, tone: 'success' },
      { label: 'Maintenance', value: formatNumber(data.occupancy.totals.maintenanceSeats), detail: 'Physically unavailable seats', icon: Wrench, tone: 'warning' },
    ]
  }

  if (activeTab.value === 'students') {
    return [
      { label: 'Total Students', value: formatNumber(data.students.totals.totalStudents), detail: 'Students in selected scope', icon: Users },
      { label: 'Active Students', value: formatNumber(data.students.totals.activeStudents), detail: `${data.students.totals.activeRate}% active rate`, icon: UserCheck, tone: 'success' },
      { label: 'New Students', value: formatNumber(data.students.totals.newStudents), detail: 'Joined during this period', icon: UserPlus, tone: 'info' },
      { label: 'Inactive Students', value: formatNumber(data.students.totals.inactiveStudents), detail: 'Historical inactive records', icon: Users, tone: 'warning' },
    ]
  }

  if (activeTab.value === 'pending') {
    return [
      { label: 'Pending Amount', value: formatCurrency(data.pendingPayments.totals.pendingAmount), detail: 'Outstanding for this period', icon: ReceiptIndianRupee, tone: 'warning' },
      { label: 'Pending Records', value: formatNumber(data.pendingPayments.totals.pendingCount), detail: 'Monthly fee records', icon: WalletCards },
      { label: 'Overdue Records', value: formatNumber(data.pendingPayments.totals.overdueCount), detail: 'Past their due date', icon: ClockAlert, tone: 'danger' },
      { label: 'Affected Students', value: formatNumber(data.pendingPayments.totals.affectedStudents), detail: 'Unique students to follow up', icon: Users, tone: 'info' },
    ]
  }

  return [
    { label: 'Collected Revenue', value: formatCurrency(data.metrics.collectedRevenue), detail: `${data.metrics.collectionRate}% collection rate`, icon: CircleDollarSign, tone: 'success', change: data.revenue.totals.revenueChange },
    { label: 'Pending Revenue', value: formatCurrency(data.metrics.pendingRevenue), detail: `${data.pendingPayments.totals.pendingCount} payment records`, icon: BadgeIndianRupee, tone: 'warning' },
    { label: 'Active Students', value: formatNumber(data.metrics.activeStudents), detail: `${data.metrics.totalStudents} students in scope`, icon: Users, tone: 'info' },
    { label: 'Seat Occupancy', value: `${data.metrics.occupancyRate}%`, detail: `${data.metrics.occupiedSeats} of ${data.metrics.totalSeats} seats`, icon: Armchair },
  ]
})

function getTabIcon(tabId) { return tabIcons[tabId] || LayoutDashboard }
function formatCurrency(value) { return currencyFormatter.format(Number(value) || 0) }
function formatNumber(value) { return numberFormatter.format(Number(value) || 0) }
function formatDateTime(value) { return new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' }).format(new Date(value)) }

function showToast(message, type = 'success') {
  globalThis.clearTimeout(toastTimer)
  toastMessage.value = message
  toastType.value = type
  toastTimer = globalThis.setTimeout(() => { toastMessage.value = '' }, 3200)
}

async function loadReports(nextFilters) {
  try {
    await store.fetchReports(nextFilters)
  } catch {
    showToast(errorMessage.value, 'error')
  }
}

async function refreshReports() {
  await loadReports(filters.value)
  if (!errorMessage.value) showToast('Reports refreshed with the latest mock data.')
}

async function applyFilters(nextFilters) {
  await loadReports(nextFilters)
  if (!errorMessage.value) showToast('Report filters applied.')
}

async function resetFilters() {
  try {
    await store.resetFilters()
    showToast('Report filters reset.')
  } catch {
    showToast(errorMessage.value, 'error')
  }
}

function selectTab(tabId) {
  activeTab.value = tabId
  router.replace({ query: { ...route.query, view: tabId === 'overview' ? undefined : tabId } })
}

async function downloadReport() {
  try {
    const response = await store.exportCurrentReport(activeTab.value)
    const { content, fileName, mimeType } = response.data
    const url = URL.createObjectURL(new Blob([content], { type: mimeType }))
    const link = document.createElement('a')
    link.href = url
    link.download = fileName
    document.body.append(link)
    link.click()
    link.remove()
    URL.revokeObjectURL(url)
    showToast(`${reportTabs.find((tab) => tab.id === activeTab.value)?.label} report downloaded.`)
  } catch {
    showToast(errorMessage.value, 'error')
  }
}

function printReport() {
  window.print()
}

onMounted(() => loadReports())
onBeforeUnmount(() => globalThis.clearTimeout(toastTimer))
</script>

<style scoped>
.reports-page { display: grid; gap: var(--space-5); }
.reports-page__header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-5); }
.reports-page__header h1 { margin: var(--space-1) 0 0; font-size: var(--font-size-h2); }
.reports-page__header p:not(.text-label) { margin: var(--space-2) 0 0; color: var(--color-text-muted); }
.reports-page__header-actions { display: flex; align-items: center; justify-content: flex-end; gap: var(--space-2); flex-wrap: wrap; }
.reports-page__updated { margin-right: var(--space-2); color: var(--color-text-muted); font-size: var(--font-size-caption); white-space: nowrap; }
.reports-page__error { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); }
.reports-page__loading { display: grid; min-height: 430px; place-items: center; align-content: center; gap: var(--space-4); border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-elevated); }
.reports-page__loading p { margin: 0; color: var(--color-text-muted); }
.reports-page__tabs { overflow-x: auto; border-bottom: 1px solid var(--color-border); scrollbar-width: thin; }
.reports-page__tabs > div { display: flex; min-width: max-content; gap: var(--space-1); }
.reports-page__tabs button { display: inline-flex; align-items: center; gap: var(--space-2); min-height: 44px; padding: 0 var(--space-4); border: 0; border-bottom: 3px solid transparent; background: transparent; color: var(--color-text-secondary); font-weight: var(--font-weight-medium); }
.reports-page__tabs button:hover { background: var(--color-hover); color: var(--color-text-primary); }
.reports-page__tabs .reports-page__tab--active { border-bottom-color: var(--color-primary); color: var(--color-primary); font-weight: var(--font-weight-semibold); }
.reports-page__content { min-width: 0; }
.reports-page__spin { animation: reports-spin 750ms linear infinite; }
@keyframes reports-spin { to { transform: rotate(360deg); } }

@media (max-width: 720px) {
  .reports-page__header { align-items: stretch; flex-direction: column; }
  .reports-page__header-actions { justify-content: flex-start; }
  .reports-page__updated { width: 100%; }
}

@media (max-width: 480px) {
  .reports-page__header h1 { font-size: var(--font-size-h3); }
  .reports-page__header-actions { display: grid; grid-template-columns: 40px auto; justify-content: start; }
  .reports-page__updated { grid-column: 1 / -1; }
  .reports-page__header-actions > .btn--icon { width: 40px; }
  .reports-page__header-actions :deep(.report-export > .btn) { width: auto; min-width: 128px; }
  .reports-page__error { align-items: stretch; flex-direction: column; }
}

@media print {
  :global(.app-navbar), :global(.app-sidebar), :global(.app-footer),
  .reports-page__header-actions, .reports-page__tabs, :deep(.report-filters) { display: none !important; }
  :global(.app-layout__main) { margin: 0 !important; padding: 0 !important; }
  .reports-page { gap: 16px; }
  .reports-page__content { break-inside: avoid; }
}
</style>
