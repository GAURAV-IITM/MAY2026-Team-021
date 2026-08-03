<template>
  <section class="admin-dashboard" aria-labelledby="admin-dashboard-title">
    <header class="admin-dashboard__header">
      <div>
        <p class="text-label text-muted admin-dashboard__eyebrow">Library Overview</p>
        <h1 id="admin-dashboard-title" class="text-h2 admin-dashboard__title">
          {{ greeting }}, {{ ownerName }}
        </h1>
        <p class="text-body admin-dashboard__description">
          Here is what is happening at {{ libraryName }} today.
        </p>
      </div>

      <div class="admin-dashboard__header-actions">
        <div class="admin-dashboard__updated" aria-live="polite">
          <span>{{ dashboardDate }}</span>
          <small v-if="summary?.lastUpdated">
            Updated {{ formatTime(summary.lastUpdated) }}
          </small>
        </div>
        <button
          class="btn btn--secondary"
          type="button"
          :disabled="isLoading"
          :aria-busy="isLoading"
          @click="loadDashboard"
        >
          <RefreshCw :size="17" :class="{ 'admin-dashboard__spin': isLoading }" aria-hidden="true" />
          {{ isLoading && hasSummary ? 'Refreshing...' : 'Refresh' }}
        </button>
      </div>
    </header>

    <div v-if="errorMessage" class="alert alert--danger" role="alert">
      <div>
        <strong>Unable to load the dashboard.</strong>
        <p class="m-0">{{ errorMessage }}</p>
        <small v-if="requestId">Request ID: {{ requestId }}</small>
      </div>
      <button class="btn btn--secondary btn--sm" type="button" @click="loadDashboard">
        Retry
      </button>
    </div>

    <div v-if="isLoading && !hasSummary" class="admin-dashboard__loading">
      <LoadingSpinner label="Loading dashboard" />
    </div>

    <EmptyState
      v-else-if="!hasSummary && !errorMessage"
      title="Dashboard data is not available"
      description="Refresh the dashboard to load the latest library overview."
    >
      <template #icon><LayoutDashboard :size="26" /></template>
      <template #primary-action>
        <button class="btn btn--primary" type="button" @click="loadDashboard">
          Refresh Dashboard
        </button>
      </template>
      <template #secondary-action><span></span></template>
    </EmptyState>

    <template v-else-if="hasSummary">
      <section class="admin-dashboard__metrics" aria-label="Library summary">
        <StatCard
          class="admin-dashboard__metric admin-dashboard__metric--students"
          title="Active Students"
          :value="String(metrics.activeStudents || 0)"
          :icon="UsersRound"
          trend="Currently enrolled"
        >
          <template #footer>
            {{ metrics.totalStudents || 0 }} total · {{ metrics.inactiveStudents || 0 }} inactive
          </template>
        </StatCard>

        <StatCard
          class="admin-dashboard__metric admin-dashboard__metric--seats"
          title="Occupied Seats"
          :value="String(metrics.occupiedSeats || 0)"
          :icon="Armchair"
          trend="Seats currently in use"
        >
          <template #footer>
            {{ metrics.availableSeats || 0 }} available of {{ metrics.totalSeats || 0 }}
          </template>
        </StatCard>

        <StatCard
          class="admin-dashboard__metric admin-dashboard__metric--collection"
          title="Monthly Collection"
          :value="formatCurrency(metrics.collectedAmount)"
          :icon="IndianRupee"
          :trend="`${metrics.collectionRate || 0}% collected`"
        >
          <template #footer>
            {{ formatMonth(summary.currentMonth) }} · {{ metrics.paidPaymentCount || 0 }} paid
          </template>
        </StatCard>

        <StatCard
          class="admin-dashboard__metric admin-dashboard__metric--dues"
          title="Pending Dues"
          :value="formatCurrency(metrics.pendingAmount)"
          :icon="CircleAlert"
          trend="Requires follow-up"
        >
          <template #footer>
            {{ metrics.unpaidPaymentCount || 0 }} unpaid payment records
          </template>
        </StatCard>
      </section>

      <div class="admin-dashboard__content-grid">
        <section class="card dashboard-panel" aria-labelledby="collection-title">
          <header class="dashboard-panel__header">
            <div>
              <h2 id="collection-title" class="dashboard-panel__title">Fee Collection</h2>
              <p class="dashboard-panel__subtitle">
                {{ formatMonth(summary.currentMonth) }} payment progress
              </p>
            </div>
            <RouterLink class="dashboard-panel__link" :to="{ name: 'adminPayments' }">
              View payments
            </RouterLink>
          </header>

          <div class="dashboard-panel__body">
            <div class="admin-dashboard__collection-total">
              <div>
                <span class="text-small text-muted">Collected</span>
                <strong>{{ formatCurrency(metrics.collectedAmount) }}</strong>
              </div>
              <p class="m-0">
                of <strong>{{ formatCurrency(metrics.expectedAmount) }}</strong>
              </p>
            </div>

            <div
              class="admin-dashboard__progress"
              role="progressbar"
              aria-label="Current month fee collection"
              aria-valuemin="0"
              aria-valuemax="100"
              :aria-valuenow="metrics.collectionRate || 0"
            >
              <span :style="{ width: `${metrics.collectionRate || 0}%` }"></span>
            </div>

            <div class="admin-dashboard__collection-history" aria-label="Collection history">
              <div
                v-for="month in monthlyCollection"
                :key="month.month"
                class="admin-dashboard__collection-row"
              >
                <span>{{ formatShortMonth(month.month) }}</span>
                <div class="admin-dashboard__mini-progress" aria-hidden="true">
                  <span :style="{ width: `${month.collectionRate}%` }"></span>
                </div>
                <strong>{{ month.collectionRate }}%</strong>
                <small>{{ formatCurrency(month.collectedAmount) }}</small>
              </div>
            </div>
          </div>
        </section>

        <section class="card dashboard-panel" aria-labelledby="quick-actions-title">
          <header class="dashboard-panel__header">
            <div>
              <h2 id="quick-actions-title" class="dashboard-panel__title">Quick Actions</h2>
              <p class="dashboard-panel__subtitle">Common admin tasks</p>
            </div>
          </header>

          <nav class="admin-dashboard__quick-actions" aria-label="Dashboard quick actions">
            <RouterLink
              v-for="action in quickActions"
              :key="action.routeName"
              class="admin-dashboard__quick-action"
              :to="{ name: action.routeName }"
            >
              <span class="admin-dashboard__action-icon" aria-hidden="true">
                <component :is="action.icon" :size="19" />
              </span>
              <span>
                <strong>{{ action.label }}</strong>
                <small>{{ action.description }}</small>
              </span>
              <ChevronRight class="admin-dashboard__action-arrow" :size="18" aria-hidden="true" />
            </RouterLink>
          </nav>
        </section>

        <section class="card dashboard-panel" aria-labelledby="shift-occupancy-title">
          <header class="dashboard-panel__header">
            <div>
              <h2 id="shift-occupancy-title" class="dashboard-panel__title">
                Shift Availability
              </h2>
              <p class="dashboard-panel__subtitle">
                Live seat status across enabled shifts
              </p>
            </div>
            <RouterLink class="dashboard-panel__link" :to="{ name: 'adminSeatMap' }">
              Open seat map
            </RouterLink>
          </header>

          <ShiftAvailabilitySummary :shifts="shiftAvailability" />
        </section>

        <section class="card dashboard-panel" aria-labelledby="seat-status-title">
          <header class="dashboard-panel__header">
            <div>
              <h2 id="seat-status-title" class="dashboard-panel__title">Seat Status</h2>
              <p class="dashboard-panel__subtitle">Physical seat overview</p>
            </div>
            <RouterLink
              class="dashboard-panel__link"
              :to="{ name: 'adminSeatManagement' }"
            >
              Manage seats
            </RouterLink>
          </header>

          <div class="dashboard-panel__body">
            <div class="admin-dashboard__seat-total">
              <strong>{{ metrics.totalSeats || 0 }}</strong>
              <span class="text-small text-muted">configured seats</span>
            </div>

            <div class="admin-dashboard__seat-bar" aria-hidden="true">
              <span
                v-for="status in seatStatus"
                :key="status.status"
                :class="`admin-dashboard__seat-bar-segment--${status.status}`"
                :style="{ width: getSeatStatusWidth(status.count) }"
              ></span>
            </div>

            <ul class="admin-dashboard__seat-legend">
              <li v-for="status in seatStatus" :key="status.status">
                <span
                  class="admin-dashboard__status-dot"
                  :class="`admin-dashboard__status-dot--${status.status}`"
                  aria-hidden="true"
                ></span>
                <span>{{ status.label }}</span>
                <strong>{{ status.count }}</strong>
              </li>
            </ul>
          </div>
        </section>

        <section class="card dashboard-panel" aria-labelledby="recent-activity-title">
          <header class="dashboard-panel__header">
            <div>
              <h2 id="recent-activity-title" class="dashboard-panel__title">
                Recent Activity
              </h2>
              <p class="dashboard-panel__subtitle">Latest payments and registrations</p>
            </div>
          </header>

          <div class="admin-dashboard__activity-list">
            <p v-if="recentActivity.length === 0" class="dashboard-panel__empty">
              No recent activity has been recorded yet.
            </p>
            <article
              v-for="activity in recentActivity"
              :key="activity.id"
              class="admin-dashboard__activity-row"
            >
              <span
                class="admin-dashboard__activity-icon"
                :class="`admin-dashboard__activity-icon--${activity.type}`"
                aria-hidden="true"
              >
                <IndianRupee v-if="activity.type === 'payment'" :size="18" />
                <UserPlus v-else :size="18" />
              </span>
              <div class="admin-dashboard__activity-copy">
                <strong>{{ activity.title }}</strong>
                <span>{{ formatLabel(activity.detail) }}</span>
              </div>
              <div class="admin-dashboard__activity-meta">
                <strong v-if="activity.amount">{{ formatCurrency(activity.amount) }}</strong>
                <time :datetime="activity.occurredAt">
                  {{ formatDateTime(activity.occurredAt) }}
                </time>
              </div>
            </article>
          </div>
        </section>

        <section class="card dashboard-panel" aria-labelledby="attention-title">
          <header class="dashboard-panel__header">
            <div>
              <h2 id="attention-title" class="dashboard-panel__title">Needs Attention</h2>
              <p class="dashboard-panel__subtitle">Items that may need action</p>
            </div>
          </header>

          <div class="admin-dashboard__attention-list">
            <p
              v-if="studentsRequiringAttention.length === 0"
              class="dashboard-panel__empty"
            >
              No students need attention right now.
            </p>
            <RouterLink
              v-for="item in studentsRequiringAttention"
              :key="item.id"
              class="admin-dashboard__attention-item"
              :to="{
                name: item.routeName,
                params: { studentId: item.studentId },
              }"
            >
              <span
                class="admin-dashboard__attention-value"
                :class="`admin-dashboard__attention-value--${item.severity}`"
              >
                {{ getInitials(item.studentName) }}
              </span>
              <span class="admin-dashboard__attention-copy">
                <strong>{{ item.studentName }}</strong>
                <small>{{ item.message }}</small>
              </span>
              <ChevronRight class="admin-dashboard__action-arrow" :size="18" aria-hidden="true" />
            </RouterLink>
          </div>
        </section>
      </div>
    </template>
  </section>
</template>

<script setup>
import {
  Armchair,
  ChevronRight,
  CircleAlert,
  CreditCard,
  IndianRupee,
  LayoutDashboard,
  Map,
  RefreshCw,
  UserPlus,
  UsersRound,
} from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'

import EmptyState from '../../components/common/EmptyState.vue'
import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import ShiftAvailabilitySummary from '../../components/dashboard/ShiftAvailabilitySummary.vue'
import StatCard from '../../components/dashboard/StatCard.vue'
import { useAuthStore } from '../../stores/authStore'
import { useDashboardStore } from '../../stores/dashboardStore'

const quickActions = Object.freeze([
  {
    label: 'Add Student',
    description: 'Register a new library member',
    icon: UserPlus,
    routeName: 'adminAddStudent',
  },
  {
    label: 'View Seat Map',
    description: 'Check shift-wise seat availability',
    icon: Map,
    routeName: 'adminSeatMap',
  },
  {
    label: 'Manage Payments',
    description: 'Update fees and send reminders',
    icon: CreditCard,
    routeName: 'adminPayments',
  },
  {
    label: 'Manage Seats',
    description: 'Update physical seat records',
    icon: Armchair,
    routeName: 'adminSeatManagement',
  },
])

const currencyFormatter = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
})

const authStore = useAuthStore()
const dashboardStore = useDashboardStore()

const { currentUser } = storeToRefs(authStore)
const {
  summary,
  isLoading,
  hasSummary,
  metrics,
  seatStatus,
  monthlyCollection,
  shiftAvailability,
  studentsRequiringAttention,
  recentActivity,
  errorMessage,
  requestId,
} = storeToRefs(dashboardStore)

const ownerName = computed(() => currentUser.value?.name || 'Library Owner')
const libraryName = computed(
  () => currentUser.value?.libraryName || 'your library',
)
const greeting = computed(() => {
  const currentHour = new Date().getHours()

  if (currentHour < 12) return 'Good morning'
  if (currentHour < 17) return 'Good afternoon'
  return 'Good evening'
})
const dashboardDate = computed(() => {
  return new Intl.DateTimeFormat('en-IN', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(new Date())
})

function formatCurrency(value = 0) {
  return currencyFormatter.format(Number(value) || 0)
}

function formatMonth(value) {
  if (!value) return 'Current month'

  const [year, month] = value.split('-').map(Number)

  return new Intl.DateTimeFormat('en-IN', {
    month: 'long',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(new Date(Date.UTC(year, month - 1, 1)))
}

function formatShortMonth(value) {
  if (!value) return '—'

  const [year, month] = value.split('-').map(Number)

  return new Intl.DateTimeFormat('en-IN', {
    month: 'short',
    timeZone: 'UTC',
  }).format(new Date(Date.UTC(year, month - 1, 1)))
}

function formatTime(value) {
  if (!value) return '—'

  return new Intl.DateTimeFormat('en-IN', {
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(value))
}

function formatDateTime(value) {
  if (!value) return '—'

  return new Intl.DateTimeFormat('en-IN', {
    day: 'numeric',
    month: 'short',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(value))
}

function formatLabel(value) {
  return String(value || '')
    .replace(/[_-]/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())
}

function getInitials(name) {
  return String(name || '')
    .split(' ')
    .filter(Boolean)
    .map((part) => part[0])
    .slice(0, 2)
    .join('')
}

function getSeatStatusWidth(count) {
  if (!metrics.value.totalSeats) return '0%'

  return `${(count / metrics.value.totalSeats) * 100}%`
}

async function loadDashboard() {
  try {
    await dashboardStore.fetchDashboardSummary()
  } catch {
    // The store-owned error state is rendered above the dashboard.
  }
}

onMounted(loadDashboard)
</script>

<style scoped>
.admin-dashboard {
  display: grid;
  gap: var(--space-6);
}

.admin-dashboard__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-6);
}

.admin-dashboard__eyebrow,
.admin-dashboard__title,
.admin-dashboard__description {
  margin: 0;
}

.admin-dashboard__title {
  margin-top: var(--space-1);
}

.admin-dashboard__description {
  margin-top: var(--space-2);
  color: var(--color-text-muted);
}

.admin-dashboard__header-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-4);
}

.admin-dashboard__updated {
  display: grid;
  justify-items: end;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.admin-dashboard__updated small {
  color: var(--color-text-muted);
}

.admin-dashboard__loading {
  display: grid;
  min-height: 420px;
  place-items: center;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface-elevated);
}

.admin-dashboard__metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-4);
}

.admin-dashboard__metric {
  min-width: 0;
  border-top-width: 3px;
}

.admin-dashboard__metric--students {
  border-top-color: var(--color-primary);
}

.admin-dashboard__metric--seats {
  border-top-color: var(--color-info);
}

.admin-dashboard__metric--collection {
  border-top-color: var(--color-success);
}

.admin-dashboard__metric--dues {
  border-top-color: var(--color-warning);
}

.admin-dashboard__content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(300px, 1fr);
  align-items: start;
  gap: var(--space-4);
}

.dashboard-panel {
  min-width: 0;
  overflow: hidden;
}

.dashboard-panel:hover {
  box-shadow: var(--shadow-sm);
}

.dashboard-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-5);
  border-bottom: 1px solid var(--color-divider);
}

.dashboard-panel__title,
.dashboard-panel__subtitle {
  margin: 0;
}

.dashboard-panel__title {
  font-size: var(--font-size-h5);
}

.dashboard-panel__subtitle {
  margin-top: var(--space-1);
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.dashboard-panel__link {
  flex: 0 0 auto;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.dashboard-panel__body {
  padding: var(--space-5);
}

.dashboard-panel__empty {
  padding: var(--space-6);
  margin: 0;
  color: var(--color-text-muted);
  text-align: center;
}

.admin-dashboard__collection-total {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-4);
}

.admin-dashboard__collection-total > div {
  display: grid;
  gap: var(--space-1);
}

.admin-dashboard__collection-total > div strong {
  font-size: var(--font-size-h3);
}

.admin-dashboard__collection-total > p {
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.admin-dashboard__progress,
.admin-dashboard__mini-progress,
.admin-dashboard__shift-progress,
.admin-dashboard__seat-bar {
  overflow: hidden;
  border-radius: var(--radius-pill);
  background: var(--color-surface-secondary);
}

.admin-dashboard__progress {
  height: 10px;
  margin-top: var(--space-4);
}

.admin-dashboard__progress > span,
.admin-dashboard__mini-progress > span,
.admin-dashboard__shift-progress > span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--color-success);
}

.admin-dashboard__collection-history {
  display: grid;
  gap: var(--space-3);
  margin-top: var(--space-6);
}

.admin-dashboard__collection-row {
  display: grid;
  grid-template-columns: 36px minmax(90px, 1fr) 40px 76px;
  align-items: center;
  gap: var(--space-3);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.admin-dashboard__collection-row strong,
.admin-dashboard__collection-row small {
  text-align: right;
}

.admin-dashboard__collection-row small {
  color: var(--color-text-muted);
}

.admin-dashboard__mini-progress {
  height: 7px;
}

.admin-dashboard__quick-actions,
.admin-dashboard__attention-list,
.admin-dashboard__activity-list {
  display: grid;
}

.admin-dashboard__quick-action,
.admin-dashboard__attention-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--space-3);
  min-height: 66px;
  padding: var(--space-3) var(--space-5);
  border-bottom: 1px solid var(--color-divider);
  color: var(--color-text-primary);
  text-decoration: none;
}

.admin-dashboard__quick-action:last-child,
.admin-dashboard__attention-item:last-child,
.admin-dashboard__activity-row:last-child {
  border-bottom: 0;
}

.admin-dashboard__quick-action:hover,
.admin-dashboard__attention-item:hover {
  background: var(--color-hover);
  color: var(--color-text-primary);
  text-decoration: none;
}

.admin-dashboard__quick-action > span:nth-child(2),
.admin-dashboard__attention-copy {
  display: grid;
  min-width: 0;
}

.admin-dashboard__quick-action small,
.admin-dashboard__attention-copy small {
  overflow: hidden;
  color: var(--color-text-muted);
  font-size: var(--font-size-caption);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.admin-dashboard__action-icon,
.admin-dashboard__activity-icon,
.admin-dashboard__attention-value {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  flex: 0 0 38px;
  border-radius: var(--radius-md);
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-weight: var(--font-weight-bold);
}

.admin-dashboard__action-arrow {
  color: var(--color-text-muted);
  font-size: var(--font-size-h4);
}

.admin-dashboard__seat-total {
  display: flex;
  align-items: baseline;
  gap: var(--space-2);
}

.admin-dashboard__seat-total strong {
  font-size: var(--font-size-h3);
}

.admin-dashboard__seat-bar {
  display: flex;
  height: 10px;
  margin: var(--space-4) 0 var(--space-5);
}

.admin-dashboard__seat-bar > span {
  display: block;
  height: 100%;
}

.admin-dashboard__seat-bar-segment--available,
.admin-dashboard__status-dot--available {
  background: var(--color-success);
}

.admin-dashboard__seat-bar-segment--occupied,
.admin-dashboard__status-dot--occupied {
  background: var(--color-primary);
}

.admin-dashboard__seat-bar-segment--reserved,
.admin-dashboard__status-dot--reserved {
  background: var(--color-info);
}

.admin-dashboard__seat-bar-segment--maintenance,
.admin-dashboard__status-dot--maintenance {
  background: var(--color-warning);
}

.admin-dashboard__seat-bar-segment--blocked,
.admin-dashboard__status-dot--blocked {
  background: var(--color-danger);
}

.admin-dashboard__seat-legend {
  display: grid;
  gap: var(--space-3);
  padding: 0;
  margin: 0;
  list-style: none;
}

.admin-dashboard__seat-legend li {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: var(--space-2);
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

.admin-dashboard__status-dot {
  width: 9px;
  height: 9px;
  border-radius: var(--radius-pill);
}

.admin-dashboard__activity-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--space-3);
  min-height: 68px;
  padding: var(--space-3) var(--space-5);
  border-bottom: 1px solid var(--color-divider);
}

.admin-dashboard__activity-icon--payment {
  background: var(--color-success-light);
  color: var(--color-success);
}

.admin-dashboard__activity-copy,
.admin-dashboard__activity-meta {
  display: grid;
  min-width: 0;
}

.admin-dashboard__activity-copy span,
.admin-dashboard__activity-meta time {
  color: var(--color-text-muted);
  font-size: var(--font-size-caption);
}

.admin-dashboard__activity-copy span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.admin-dashboard__activity-meta {
  justify-items: end;
}

.admin-dashboard__attention-value--warning {
  background: var(--color-warning-light);
  color: var(--color-warning);
}

.admin-dashboard__attention-value--danger {
  background: var(--color-danger-light);
  color: var(--color-danger);
}

.admin-dashboard__attention-value--info {
  background: var(--color-info-light);
  color: var(--color-info);
}

.admin-dashboard__attention-value--critical,
.admin-dashboard__attention-value--high {
  background: var(--color-danger-light);
  color: var(--color-danger);
}

.admin-dashboard__attention-value--medium {
  background: var(--color-warning-light);
  color: var(--color-warning);
}

.admin-dashboard__attention-value--low {
  background: var(--color-info-light);
  color: var(--color-info);
}

@media (max-width: 1100px) {
  .admin-dashboard__metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .admin-dashboard__content-grid {
    grid-template-columns: minmax(0, 1fr) minmax(280px, 0.8fr);
  }
}

@media (max-width: 860px) {
  .admin-dashboard__header {
    flex-direction: column;
  }

  .admin-dashboard__header-actions {
    width: 100%;
    justify-content: space-between;
  }

  .admin-dashboard__updated {
    justify-items: start;
  }

  .admin-dashboard__content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 580px) {
  .admin-dashboard__metrics {
    grid-template-columns: 1fr;
  }

  .admin-dashboard__header-actions,
  .admin-dashboard__collection-total {
    align-items: stretch;
    flex-direction: column;
  }

  .admin-dashboard__header-actions .btn {
    width: 100%;
  }

  .dashboard-panel__header {
    flex-direction: column;
  }

  .admin-dashboard__collection-row {
    grid-template-columns: 34px minmax(70px, 1fr) 38px;
  }

  .admin-dashboard__collection-row small {
    display: none;
  }

  .admin-dashboard__activity-row {
    grid-template-columns: auto minmax(0, 1fr);
  }

  .admin-dashboard__activity-meta {
    grid-column: 2;
    grid-auto-flow: column;
    justify-content: space-between;
    justify-items: start;
    gap: var(--space-3);
  }
}
</style>
