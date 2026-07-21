<template>
  <section class="student-dashboard" aria-labelledby="student-dashboard-title">
    <header class="student-dashboard__header">
      <div>
        <p class="text-label text-muted m-0">Student Portal</p>
        <h1 id="student-dashboard-title" class="text-h2 student-dashboard__title">
          Welcome back, {{ firstName }}
        </h1>
        <p class="student-dashboard__description">Your seat, fees, requests, and library updates in one place.</p>
      </div>
      <button class="btn btn--secondary" type="button" :disabled="isLoading" @click="loadDashboard">
        <RefreshCw :size="17" :class="{ 'student-dashboard__spin': isLoading }" aria-hidden="true" />
        {{ isLoading && dashboard ? 'Refreshing...' : 'Refresh' }}
      </button>
    </header>

    <div v-if="errorMessage" class="alert alert--danger" role="alert">
      <div><strong>Unable to load your dashboard.</strong><p class="m-0">{{ errorMessage }}</p></div>
      <button class="btn btn--secondary btn--sm" type="button" @click="loadDashboard">Retry</button>
    </div>

    <div v-if="isLoading && !dashboard" class="student-dashboard__loading">
      <LoadingSpinner label="Loading your dashboard" />
    </div>

    <template v-else-if="dashboard">
      <StudentSummaryCards :items="summaryItems" aria-label="Student portal summary" />

      <nav class="student-dashboard__quick-actions" aria-label="Student quick actions">
        <RouterLink v-for="action in quickActions" :key="action.routeName" class="student-dashboard__quick-action" :to="{ name: action.routeName }">
          <span aria-hidden="true"><component :is="action.icon" :size="18" /></span><strong>{{ action.label }}</strong>
        </RouterLink>
      </nav>

      <div class="student-dashboard__grid">
        <section class="student-dashboard__seat-panel" aria-labelledby="dashboard-seat-title">
          <header class="student-panel__header">
            <div><h2 id="dashboard-seat-title">My Seat</h2><p>Current active allocation</p></div>
            <RouterLink :to="{ name: 'studentMySeat' }">View details</RouterLink>
          </header>
          <SeatAllocationCard :seat="dashboard.seat" :allocations="dashboard.allocations" compact />
        </section>

        <section class="card student-panel" aria-labelledby="dashboard-fee-title">
          <header class="student-panel__header">
            <div><h2 id="dashboard-fee-title">Fee Status</h2><p>{{ formatMonth(dashboard.feeSummary.currentPayment?.month) }}</p></div>
            <RouterLink :to="{ name: 'studentFees' }">View fees</RouterLink>
          </header>
          <div class="student-panel__body student-dashboard__fee-status">
            <span class="badge" :class="getPaymentStatusClass(dashboard.feeSummary.currentPayment?.status)">
              {{ formatLabel(dashboard.feeSummary.currentPayment?.status || 'not generated') }}
            </span>
            <strong>{{ formatCurrency(dashboard.feeSummary.currentPayment?.amount) }}</strong>
            <p v-if="dashboard.feeSummary.currentPayment?.status === 'paid'" class="m-0 text-small text-muted">
              Paid {{ formatDate(dashboard.feeSummary.currentPayment.paidAt) }}
            </p>
            <p v-else class="m-0 text-small text-muted">Due by {{ formatDate(dashboard.feeSummary.nextDueDate) }}</p>
          </div>
        </section>

        <section class="card student-panel" aria-labelledby="dashboard-announcements-title">
          <header class="student-panel__header">
            <div><h2 id="dashboard-announcements-title">Recent Announcements</h2><p>{{ dashboard.unreadAnnouncementCount }} unread</p></div>
            <RouterLink :to="{ name: 'studentAnnouncements' }">View all</RouterLink>
          </header>
          <div class="student-dashboard__announcement-list">
            <article v-for="announcement in dashboard.recentAnnouncements" :key="announcement.id" :class="{ 'student-dashboard__announcement--unread': !announcement.isRead }">
              <span class="student-dashboard__announcement-indicator" aria-hidden="true"></span>
              <div><strong>{{ announcement.title }}</strong><span>{{ formatDate(announcement.publishedAt) }}</span></div>
              <span v-if="announcement.priority === 'important'" class="badge badge--pending">Important</span>
            </article>
          </div>
        </section>

        <section class="card student-panel" aria-labelledby="dashboard-request-title">
          <header class="student-panel__header"><div><h2 id="dashboard-request-title">Seat Request</h2><p>Change request status</p></div></header>
          <div class="student-panel__body student-dashboard__request">
            <template v-if="dashboard.activeRequest">
              <span class="badge badge--pending">Pending</span>
              <strong>{{ dashboard.activeRequest.preferredSeatNumber || 'Any available seat' }}</strong>
              <p class="m-0 text-small text-muted">Submitted {{ formatDate(dashboard.activeRequest.submittedAt) }}</p>
            </template>
            <template v-else>
              <span class="student-dashboard__request-icon" aria-hidden="true"><ClipboardPlus :size="20" /></span>
              <strong>No pending request</strong>
              <p class="m-0 text-small text-muted">You can request a different seat or shift.</p>
            </template>
            <RouterLink class="btn btn--secondary btn--sm" :to="{ name: 'studentRequests' }">Manage Requests</RouterLink>
          </div>
        </section>
      </div>
    </template>
  </section>
</template>

<script setup>
import {
  Armchair,
  BellRing,
  ClipboardList,
  ClipboardPlus,
  Clock3,
  IndianRupee,
  ReceiptText,
  RefreshCw,
  UserRound,
} from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'

import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import SeatAllocationCard from '../../components/student/SeatAllocationCard.vue'
import StudentSummaryCards from '../../components/student/StudentSummaryCards.vue'
import { useAuthStore } from '../../stores/authStore'
import { useStudentPortalStore } from '../../stores/studentPortalStore'

const quickActions = Object.freeze([
  { label: 'My Seat', routeName: 'studentMySeat', icon: Armchair },
  { label: 'Fee Receipts', routeName: 'studentReceipts', icon: ReceiptText },
  { label: 'Request Change', routeName: 'studentRequests', icon: ClipboardList },
  { label: 'My Profile', routeName: 'studentProfile', icon: UserRound },
])

const authStore = useAuthStore()
const portalStore = useStudentPortalStore()
const { currentUser } = storeToRefs(authStore)
const { dashboard, isLoading, errorMessage } = storeToRefs(portalStore)
const studentId = computed(() => currentUser.value?.id || '')
const firstName = computed(() => dashboard.value?.profile?.firstName || currentUser.value?.name?.split(' ')[0] || 'Student')
const summaryItems = computed(() => {
  const data = dashboard.value
  if (!data) return []
  const allocation = data.allocations[0]
  const payment = data.feeSummary.currentPayment
  return [
    { label: 'Allocated Seat', value: data.seat?.seatNumber || '—', detail: data.seat ? `Floor ${data.seat.floor} · ${data.seat.seatType}` : 'Not assigned', icon: Armchair },
    { label: 'Active Shift', value: allocation ? formatLabel(allocation.shiftName) : '—', detail: allocation ? `${allocation.startTime}-${allocation.endTime}` : 'Not assigned', icon: Clock3, tone: 'info' },
    { label: 'Current Fee', value: formatLabel(payment?.status || 'Not generated'), detail: payment ? formatCurrency(payment.amount) : 'No payment record', icon: IndianRupee, tone: payment?.status === 'paid' ? 'success' : 'warning' },
    { label: 'Announcements', value: data.unreadAnnouncementCount, detail: 'Unread library updates', icon: BellRing, tone: data.unreadAnnouncementCount ? 'warning' : 'success' },
  ]
})

function formatCurrency(value) { return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(Number(value) || 0) }
function formatLabel(value) { return String(value || '').replace(/[-_]/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase()) }
function formatDate(value) { return value ? new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(value)) : '—' }
function formatMonth(value) { if (!value) return 'Current month'; const [year, month] = value.split('-').map(Number); return new Intl.DateTimeFormat('en-IN', { month: 'long', year: 'numeric', timeZone: 'UTC' }).format(new Date(Date.UTC(year, month - 1, 1))) }
function getPaymentStatusClass(status) { return status === 'paid' ? 'badge--success' : 'badge--pending' }
async function loadDashboard() { if (!studentId.value) return; try { await portalStore.fetchDashboard(studentId.value) } catch { /* Store-owned errors are rendered above. */ } }
onMounted(loadDashboard)
</script>

<style scoped>
.student-dashboard { display: grid; gap: var(--space-6); }
.student-dashboard__header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-5); }
.student-dashboard__title { margin: var(--space-1) 0 0; }
.student-dashboard__description { margin: var(--space-2) 0 0; color: var(--color-text-muted); }
.student-dashboard__loading { display: grid; min-height: 420px; place-items: center; border: 1px solid var(--color-border); border-radius: var(--radius-lg); background: var(--color-surface-elevated); }
.student-dashboard__spin { animation: ds-spin var(--transition-slow) linear infinite; }
.student-dashboard__quick-actions { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--space-3); }
.student-dashboard__quick-action { display: flex; align-items: center; gap: var(--space-3); min-height: 50px; padding: var(--space-2) var(--space-3); border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-elevated); color: var(--color-text-primary); text-decoration: none; }
.student-dashboard__quick-action:hover { border-color: var(--color-primary); color: var(--color-primary); text-decoration: none; }
.student-dashboard__quick-action span { display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; flex: 0 0 32px; border-radius: var(--radius-md); background: var(--color-primary-light); color: var(--color-primary); font-weight: var(--font-weight-bold); }
.student-dashboard__grid { display: grid; grid-template-columns: minmax(0, 1.5fr) minmax(280px, 1fr); align-items: start; gap: var(--space-4); }
.student-dashboard__seat-panel { min-width: 0; }
.student-panel { min-width: 0; overflow: hidden; }
.student-panel:hover { box-shadow: var(--shadow-sm); }
.student-panel__header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-4); padding: var(--space-4) var(--space-5); border: 1px solid var(--color-border); border-bottom: 0; border-radius: var(--radius-lg) var(--radius-lg) 0 0; background: var(--color-surface-elevated); }
.student-panel > .student-panel__header { border: 0; border-bottom: 1px solid var(--color-divider); border-radius: 0; }
.student-panel__header h2, .student-panel__header p { margin: 0; }
.student-panel__header h2 { font-size: var(--font-size-h5); }
.student-panel__header p { margin-top: var(--space-1); color: var(--color-text-muted); font-size: var(--font-size-sm); }
.student-panel__header a { font-size: var(--font-size-sm); font-weight: var(--font-weight-semibold); }
.student-dashboard__seat-panel :deep(.seat-allocation-card) { border-radius: 0 0 var(--radius-lg) var(--radius-lg); }
.student-panel__body { padding: var(--space-5); }
.student-dashboard__fee-status, .student-dashboard__request { display: grid; justify-items: start; gap: var(--space-3); }
.student-dashboard__fee-status > strong { font-size: var(--font-size-h3); }
.student-dashboard__announcement-list { display: grid; }
.student-dashboard__announcement-list article { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: center; gap: var(--space-3); min-height: 64px; padding: var(--space-3) var(--space-5); border-bottom: 1px solid var(--color-divider); }
.student-dashboard__announcement-list article:last-child { border-bottom: 0; }
.student-dashboard__announcement-list article > div { display: grid; }
.student-dashboard__announcement-list article > div span { color: var(--color-text-muted); font-size: var(--font-size-caption); }
.student-dashboard__announcement-indicator { width: 8px; height: 8px; border-radius: var(--radius-pill); background: var(--color-disabled); }
.student-dashboard__announcement--unread .student-dashboard__announcement-indicator { background: var(--color-primary); }
.student-dashboard__request-icon { display: inline-flex; align-items: center; justify-content: center; width: 44px; height: 44px; border-radius: var(--radius-md); background: var(--color-primary-light); color: var(--color-primary); font-weight: var(--font-weight-bold); }
@media (max-width: 960px) { .student-dashboard__grid { grid-template-columns: 1fr; } .student-dashboard__quick-actions { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 600px) { .student-dashboard__header { flex-direction: column; } .student-dashboard__quick-actions { grid-template-columns: 1fr; } .student-dashboard__announcement-list article { grid-template-columns: auto minmax(0, 1fr); } .student-dashboard__announcement-list .badge { grid-column: 2; justify-self: start; } }
</style>
