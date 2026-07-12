<template>
  <section class="platform-dashboard" aria-labelledby="platform-dashboard-title">
    <header class="platform-dashboard__header">
      <div>
        <p class="text-label text-muted m-0">Platform Overview</p>
        <h1 id="platform-dashboard-title" class="text-h2 platform-dashboard__title">
          Super Admin Dashboard
        </h1>
        <p class="platform-dashboard__description">
          Monitor library growth, owner access, and platform activity.
        </p>
      </div>

      <div class="platform-dashboard__header-actions">
        <span v-if="dashboard?.lastUpdated" class="text-small text-muted">
          Updated {{ formatDateTime(dashboard.lastUpdated) }}
        </span>
        <button
          class="btn btn--secondary"
          type="button"
          :disabled="isLoading"
          @click="loadDashboard"
        >
          {{ isLoading && dashboard ? 'Refreshing...' : 'Refresh' }}
        </button>
      </div>
    </header>

    <div v-if="errorMessage" class="alert alert--danger" role="alert">
      <div>
        <strong>Unable to load the platform dashboard.</strong>
        <p class="m-0">{{ errorMessage }}</p>
      </div>
      <button class="btn btn--secondary btn--sm" type="button" @click="loadDashboard">
        Retry
      </button>
    </div>

    <div v-if="isLoading && !dashboard" class="platform-dashboard__loading">
      <LoadingSpinner label="Loading platform dashboard" />
    </div>

    <template v-else-if="dashboard">
      <PlatformMetricCards :items="metricItems" aria-label="Platform summary" />

      <nav class="platform-dashboard__quick-actions" aria-label="Super Admin quick actions">
        <RouterLink
          v-for="action in quickActions"
          :key="action.routeName"
          class="platform-dashboard__quick-action"
          :to="{ name: action.routeName }"
        >
          <span aria-hidden="true">{{ action.icon }}</span>
          <strong>{{ action.label }}</strong>
        </RouterLink>
      </nav>

      <div class="platform-dashboard__grid">
        <section class="card platform-panel" aria-labelledby="growth-title">
          <header class="platform-panel__header">
            <div>
              <h2 id="growth-title" class="platform-panel__title">Student Growth</h2>
              <p class="platform-panel__subtitle">Registered students across the platform</p>
            </div>
            <RouterLink class="platform-panel__link" :to="{ name: 'superAdminAnalytics' }">
              View analytics
            </RouterLink>
          </header>
          <div class="platform-panel__body">
            <PlatformTrend
              :points="dashboard.trend"
              value-key="students"
              aria-label="Monthly platform student growth"
            />
          </div>
        </section>

        <section class="card platform-panel" aria-labelledby="library-status-title">
          <header class="platform-panel__header">
            <div>
              <h2 id="library-status-title" class="platform-panel__title">Library Status</h2>
              <p class="platform-panel__subtitle">Registration lifecycle</p>
            </div>
            <RouterLink class="platform-panel__link" :to="{ name: 'superAdminLibraries' }">
              Manage
            </RouterLink>
          </header>
          <div class="platform-panel__body">
            <StatusDistribution :items="dashboard.libraryStatus" />
          </div>
        </section>

        <section class="card platform-panel" aria-labelledby="top-libraries-title">
          <header class="platform-panel__header">
            <div>
              <h2 id="top-libraries-title" class="platform-panel__title">Top Libraries</h2>
              <p class="platform-panel__subtitle">Active libraries by student count</p>
            </div>
          </header>
          <div class="platform-panel__table">
            <DataTable
              :columns="topLibraryColumns"
              :rows="dashboard.topLibraries"
              aria-label="Top performing libraries"
            >
              <template #cell-name="{ row }">
                <div class="platform-dashboard__library-name">
                  <strong>{{ row.name }}</strong>
                  <span>{{ row.city }}, {{ row.state }}</span>
                </div>
              </template>
              <template #cell-studentCount="{ value }">
                {{ formatNumber(value) }}
              </template>
              <template #cell-occupancyRate="{ value }">
                <strong>{{ value }}%</strong>
              </template>
            </DataTable>
          </div>
        </section>

        <section class="card platform-panel" aria-labelledby="attention-title">
          <header class="platform-panel__header">
            <div>
              <h2 id="attention-title" class="platform-panel__title">Needs Attention</h2>
              <p class="platform-panel__subtitle">Items awaiting platform action</p>
            </div>
          </header>
          <div class="platform-dashboard__attention-list">
            <RouterLink
              v-for="item in dashboard.attention"
              :key="item.id"
              class="platform-dashboard__attention-item"
              :to="{ name: item.routeName }"
            >
              <span
                class="platform-dashboard__attention-value"
                :class="`platform-dashboard__attention-value--${item.tone}`"
              >
                {{ item.value }}
              </span>
              <strong>{{ item.label }}</strong>
              <span class="platform-dashboard__arrow" aria-hidden="true">›</span>
            </RouterLink>
          </div>
        </section>

        <section
          class="card platform-panel platform-dashboard__activity-panel"
          aria-labelledby="activity-title"
        >
          <header class="platform-panel__header">
            <div>
              <h2 id="activity-title" class="platform-panel__title">Recent Activity</h2>
              <p class="platform-panel__subtitle">Latest platform administration events</p>
            </div>
          </header>
          <div class="platform-dashboard__activity-list">
            <article
              v-for="item in dashboard.recentActivity"
              :key="item.id"
              class="platform-dashboard__activity-item"
            >
              <span
                class="platform-dashboard__activity-icon"
                :class="`platform-dashboard__activity-icon--${item.type}`"
                aria-hidden="true"
              >
                {{ getActivityIcon(item.type) }}
              </span>
              <div>
                <strong>{{ item.title }}</strong>
                <span>{{ item.detail }}</span>
              </div>
              <time :datetime="item.occurredAt">{{ formatDateTime(item.occurredAt) }}</time>
            </article>
          </div>
        </section>
      </div>
    </template>
  </section>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'

import DataTable from '../../components/common/DataTable.vue'
import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import PlatformMetricCards from '../../components/superadmin/PlatformMetricCards.vue'
import PlatformTrend from '../../components/superadmin/PlatformTrend.vue'
import StatusDistribution from '../../components/superadmin/StatusDistribution.vue'
import { useSuperAdminStore } from '../../stores/superAdminStore'

const topLibraryColumns = Object.freeze([
  { key: 'name', label: 'Library' },
  { key: 'studentCount', label: 'Students' },
  { key: 'seatCount', label: 'Seats' },
  { key: 'occupancyRate', label: 'Occupancy' },
])

const quickActions = Object.freeze([
  { label: 'Manage Libraries', routeName: 'superAdminLibraries', icon: 'L' },
  { label: 'Manage Owners', routeName: 'superAdminOwners', icon: 'O' },
  { label: 'View Analytics', routeName: 'superAdminAnalytics', icon: 'A' },
  { label: 'Platform Settings', routeName: 'superAdminSettings', icon: 'S' },
])

const store = useSuperAdminStore()
const { dashboard, isLoading, errorMessage } = storeToRefs(store)
const numberFormatter = new Intl.NumberFormat('en-IN')

const metricItems = computed(() => {
  const totals = dashboard.value?.totals || {}

  return [
    {
      label: 'Registered Libraries',
      value: formatNumber(totals.totalLibraries),
      detail: `${totals.pendingLibraries || 0} awaiting approval`,
      icon: 'L',
      tone: 'primary',
    },
    {
      label: 'Active Libraries',
      value: formatNumber(totals.activeLibraries),
      detail: `${totals.averageOccupancy || 0}% average occupancy`,
      icon: 'A',
      tone: 'success',
    },
    {
      label: 'Library Owners',
      value: formatNumber(totals.totalOwners),
      detail: `${totals.activeOwners || 0} active accounts`,
      icon: 'O',
      tone: 'info',
    },
    {
      label: 'Platform Students',
      value: formatNumber(totals.totalStudents),
      detail: `${formatNumber(totals.totalSeats)} seats configured`,
      icon: 'S',
      tone: 'warning',
    },
  ]
})

function formatNumber(value) {
  return numberFormatter.format(Number(value) || 0)
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

function getActivityIcon(type) {
  const icons = {
    library: 'L',
    owner: 'O',
    status: '!',
    growth: 'G',
    settings: 'S',
  }

  return icons[type] || 'A'
}

async function loadDashboard() {
  try {
    await store.fetchDashboard()
  } catch {
    // Store-owned errors are rendered above the page.
  }
}

onMounted(loadDashboard)
</script>

<style scoped>
.platform-dashboard {
  display: grid;
  gap: var(--space-6);
}

.platform-dashboard__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-5);
}

.platform-dashboard__title {
  margin: var(--space-1) 0 0;
}

.platform-dashboard__description {
  margin: var(--space-2) 0 0;
  color: var(--color-text-muted);
}

.platform-dashboard__header-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--space-3);
}

.platform-dashboard__loading {
  display: grid;
  min-height: 420px;
  place-items: center;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface-elevated);
}

.platform-dashboard__quick-actions {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-3);
}

.platform-dashboard__quick-action {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  min-height: 50px;
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface-elevated);
  color: var(--color-text-primary);
  text-decoration: none;
}

.platform-dashboard__quick-action:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  text-decoration: none;
}

.platform-dashboard__quick-action > span {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  flex: 0 0 32px;
  border-radius: var(--radius-md);
  background: var(--color-primary-light);
  color: var(--color-primary);
  font-weight: var(--font-weight-bold);
}

.platform-dashboard__grid {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(280px, 1fr);
  align-items: start;
  gap: var(--space-4);
}

.platform-panel {
  min-width: 0;
  overflow: hidden;
}

.platform-panel:hover {
  box-shadow: var(--shadow-sm);
}

.platform-panel__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-4);
  padding: var(--space-5);
  border-bottom: 1px solid var(--color-divider);
}

.platform-panel__title,
.platform-panel__subtitle {
  margin: 0;
}

.platform-panel__title {
  font-size: var(--font-size-h5);
}

.platform-panel__subtitle {
  margin-top: var(--space-1);
  color: var(--color-text-muted);
  font-size: var(--font-size-sm);
}

.platform-panel__body {
  padding: var(--space-5);
}

.platform-panel__link {
  flex: 0 0 auto;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.platform-panel__table :deep(.data-table) {
  border: 0;
  border-radius: 0;
}

.platform-dashboard__library-name {
  display: grid;
  min-width: 180px;
}

.platform-dashboard__library-name span {
  color: var(--color-text-muted);
  font-size: var(--font-size-caption);
}

.platform-dashboard__attention-list,
.platform-dashboard__activity-list {
  display: grid;
}

.platform-dashboard__attention-item {
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

.platform-dashboard__attention-item:last-child,
.platform-dashboard__activity-item:last-child {
  border-bottom: 0;
}

.platform-dashboard__attention-item:hover {
  background: var(--color-hover);
  color: var(--color-text-primary);
  text-decoration: none;
}

.platform-dashboard__attention-value,
.platform-dashboard__activity-icon {
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

.platform-dashboard__attention-value--warning {
  background: var(--color-warning-light);
  color: var(--color-warning);
}

.platform-dashboard__attention-value--info {
  background: var(--color-info-light);
  color: var(--color-info);
}

.platform-dashboard__attention-value--danger,
.platform-dashboard__activity-icon--status {
  background: var(--color-danger-light);
  color: var(--color-danger);
}

.platform-dashboard__arrow {
  color: var(--color-text-muted);
  font-size: var(--font-size-h4);
}

.platform-dashboard__activity-panel {
  grid-column: 1 / -1;
}

.platform-dashboard__activity-item {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--space-3);
  min-height: 66px;
  padding: var(--space-3) var(--space-5);
  border-bottom: 1px solid var(--color-divider);
}

.platform-dashboard__activity-item > div {
  display: grid;
  min-width: 0;
}

.platform-dashboard__activity-item > div span,
.platform-dashboard__activity-item time {
  color: var(--color-text-muted);
  font-size: var(--font-size-caption);
}

.platform-dashboard__activity-item time {
  white-space: nowrap;
}

@media (max-width: 980px) {
  .platform-dashboard__quick-actions {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .platform-dashboard__grid {
    grid-template-columns: 1fr;
  }

  .platform-dashboard__activity-panel {
    grid-column: auto;
  }
}

@media (max-width: 680px) {
  .platform-dashboard__header,
  .platform-dashboard__header-actions {
    align-items: stretch;
    flex-direction: column;
  }

  .platform-dashboard__quick-actions {
    grid-template-columns: 1fr;
  }

  .platform-dashboard__activity-item {
    grid-template-columns: auto minmax(0, 1fr);
  }

  .platform-dashboard__activity-item time {
    grid-column: 2;
  }
}
</style>
