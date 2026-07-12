<template>
  <section class="platform-analytics" aria-labelledby="platform-analytics-title">
    <header class="platform-analytics__header">
      <div>
        <p class="text-label text-muted m-0">Platform Intelligence</p>
        <h1 id="platform-analytics-title" class="text-h2 platform-analytics__title">
          Platform Analytics
        </h1>
        <p class="platform-analytics__description">
          Compare platform growth, regional reach, and library performance.
        </p>
      </div>
      <button class="btn btn--secondary" type="button" :disabled="isLoading" @click="loadAnalytics">
        {{ isLoading && analytics ? 'Refreshing...' : 'Refresh' }}
      </button>
    </header>

    <div v-if="errorMessage" class="alert alert--danger" role="alert">
      <div><strong>Unable to load platform analytics.</strong><p class="m-0">{{ errorMessage }}</p></div>
      <button class="btn btn--secondary btn--sm" type="button" @click="loadAnalytics">Retry</button>
    </div>

    <div v-if="isLoading && !analytics" class="platform-analytics__loading">
      <LoadingSpinner label="Loading platform analytics" />
    </div>

    <template v-else-if="analytics">
      <PlatformMetricCards :items="metricItems" aria-label="Platform analytics summary" />

      <div class="platform-analytics__grid">
        <section class="card analytics-panel platform-analytics__trend" aria-labelledby="analytics-trend-title">
          <header class="analytics-panel__header">
            <div>
              <h2 id="analytics-trend-title" class="analytics-panel__title">Growth Trend</h2>
              <p class="analytics-panel__subtitle">January through July 2026</p>
            </div>
            <div class="platform-analytics__metric-tabs" role="tablist" aria-label="Trend metric">
              <button
                v-for="metric in trendMetrics"
                :key="metric.key"
                class="platform-analytics__metric-tab"
                :class="{ 'platform-analytics__metric-tab--active': selectedMetric === metric.key }"
                type="button"
                role="tab"
                :aria-selected="String(selectedMetric === metric.key)"
                @click="selectedMetric = metric.key"
              >
                {{ metric.label }}
              </button>
            </div>
          </header>
          <div class="analytics-panel__body">
            <div class="platform-analytics__trend-summary">
              <div><span>Current</span><strong>{{ formatNumber(currentTrendValue) }}</strong></div>
              <div><span>Net Growth</span><strong class="text-success">+{{ formatNumber(netGrowth) }}</strong></div>
            </div>
            <PlatformTrend
              :points="analytics.trend"
              :value-key="selectedMetric"
              :aria-label="`${selectedMetricLabel} growth trend`"
            />
          </div>
        </section>

        <section class="card analytics-panel" aria-labelledby="regional-title">
          <header class="analytics-panel__header">
            <div>
              <h2 id="regional-title" class="analytics-panel__title">Regional Reach</h2>
              <p class="analytics-panel__subtitle">Libraries and students by state</p>
            </div>
          </header>
          <div class="analytics-panel__body platform-analytics__regions">
            <div v-for="region in analytics.regionalDistribution" :key="region.state" class="platform-analytics__region">
              <div><strong>{{ region.state }}</strong><span>{{ region.libraryCount }} {{ region.libraryCount === 1 ? 'library' : 'libraries' }}</span></div>
              <strong>{{ formatNumber(region.studentCount) }}</strong>
            </div>
          </div>
        </section>

        <section class="card analytics-panel platform-analytics__performance" aria-labelledby="performance-title">
          <header class="analytics-panel__header">
            <div>
              <h2 id="performance-title" class="analytics-panel__title">Library Performance</h2>
              <p class="analytics-panel__subtitle">Active libraries ordered by occupancy</p>
            </div>
            <span class="text-small text-muted">Generated {{ formatDateTime(analytics.generatedAt) }}</span>
          </header>
          <DataTable
            :columns="performanceColumns"
            :rows="analytics.libraryPerformance"
            aria-label="Library performance analytics"
          >
            <template #cell-name="{ row }">
              <div class="platform-analytics__library-cell"><strong>{{ row.name }}</strong><span>{{ row.city }}, {{ row.state }}</span></div>
            </template>
            <template #cell-studentCount="{ value }">{{ formatNumber(value) }}</template>
            <template #cell-seatCount="{ value }">{{ formatNumber(value) }}</template>
            <template #cell-occupancyRate="{ value }">
              <div class="platform-analytics__occupancy-cell">
                <div aria-hidden="true"><span :style="{ width: `${value}%` }"></span></div>
                <strong>{{ value }}%</strong>
              </div>
            </template>
          </DataTable>
        </section>
      </div>
    </template>
  </section>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { computed, onMounted, ref } from 'vue'

import DataTable from '../../components/common/DataTable.vue'
import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import PlatformMetricCards from '../../components/superadmin/PlatformMetricCards.vue'
import PlatformTrend from '../../components/superadmin/PlatformTrend.vue'
import { useSuperAdminStore } from '../../stores/superAdminStore'

const trendMetrics = Object.freeze([
  { key: 'students', label: 'Students' },
  { key: 'libraries', label: 'Libraries' },
  { key: 'seats', label: 'Seats' },
])
const performanceColumns = Object.freeze([
  { key: 'name', label: 'Library' },
  { key: 'studentCount', label: 'Students' },
  { key: 'seatCount', label: 'Seats' },
  { key: 'occupancyRate', label: 'Occupancy' },
])

const store = useSuperAdminStore()
const { analytics, isLoading, errorMessage } = storeToRefs(store)
const selectedMetric = ref('students')
const numberFormatter = new Intl.NumberFormat('en-IN')

const metricItems = computed(() => {
  const totals = analytics.value?.totals || {}
  return [
    { label: 'Active Libraries', value: formatNumber(totals.activeLibraries), detail: `${totals.totalLibraries || 0} registered`, icon: 'L', tone: 'success' },
    { label: 'Platform Students', value: formatNumber(totals.totalStudents), detail: 'Across active libraries', icon: 'S' },
    { label: 'Configured Seats', value: formatNumber(totals.totalSeats), detail: 'Available platform capacity', icon: 'C', tone: 'info' },
    { label: 'Average Occupancy', value: `${totals.averageOccupancy || 0}%`, detail: 'Across active libraries', icon: '%', tone: 'warning' },
  ]
})
const selectedMetricLabel = computed(() => trendMetrics.find((metric) => metric.key === selectedMetric.value)?.label || 'Platform')
const currentTrendValue = computed(() => analytics.value?.trend?.at(-1)?.[selectedMetric.value] || 0)
const firstTrendValue = computed(() => analytics.value?.trend?.[0]?.[selectedMetric.value] || 0)
const netGrowth = computed(() => currentTrendValue.value - firstTrendValue.value)

function formatNumber(value) { return numberFormatter.format(Number(value) || 0) }
function formatDateTime(value) { return value ? new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' }).format(new Date(value)) : '—' }
async function loadAnalytics() { try { await store.fetchAnalytics() } catch { /* Store-owned errors are rendered above. */ } }
onMounted(loadAnalytics)
</script>

<style scoped>
.platform-analytics { display: grid; gap: var(--space-6); }
.platform-analytics__header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-5); }
.platform-analytics__title { margin: var(--space-1) 0 0; }
.platform-analytics__description { margin: var(--space-2) 0 0; color: var(--color-text-muted); }
.platform-analytics__loading { display: grid; min-height: 420px; place-items: center; border: 1px solid var(--color-border); border-radius: var(--radius-lg); background: var(--color-surface-elevated); }
.platform-analytics__grid { display: grid; grid-template-columns: minmax(0, 1.55fr) minmax(280px, 1fr); align-items: start; gap: var(--space-4); }
.analytics-panel { min-width: 0; overflow: hidden; }
.analytics-panel:hover { box-shadow: var(--shadow-sm); }
.analytics-panel__header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-4); padding: var(--space-5); border-bottom: 1px solid var(--color-divider); }
.analytics-panel__title, .analytics-panel__subtitle { margin: 0; }
.analytics-panel__title { font-size: var(--font-size-h5); }
.analytics-panel__subtitle { margin-top: var(--space-1); color: var(--color-text-muted); font-size: var(--font-size-sm); }
.analytics-panel__body { padding: var(--space-5); }
.platform-analytics__metric-tabs { display: inline-flex; gap: var(--space-1); padding: var(--space-1); border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-secondary); }
.platform-analytics__metric-tab { min-height: 32px; padding: 0 var(--space-3); border: 0; border-radius: var(--radius-sm); background: transparent; color: var(--color-text-secondary); font-size: var(--font-size-sm); }
.platform-analytics__metric-tab--active { background: var(--color-surface-elevated); color: var(--color-primary); box-shadow: var(--shadow-sm); font-weight: var(--font-weight-semibold); }
.platform-analytics__trend-summary { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-4); margin-bottom: var(--space-6); }
.platform-analytics__trend-summary > div { display: grid; padding-bottom: var(--space-3); border-bottom: 1px solid var(--color-divider); }
.platform-analytics__trend-summary span { color: var(--color-text-muted); font-size: var(--font-size-caption); }
.platform-analytics__trend-summary strong { font-size: var(--font-size-h4); }
.platform-analytics__regions { display: grid; gap: var(--space-3); }
.platform-analytics__region { display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); padding-bottom: var(--space-3); border-bottom: 1px solid var(--color-divider); }
.platform-analytics__region:last-child { padding-bottom: 0; border-bottom: 0; }
.platform-analytics__region > div { display: grid; }
.platform-analytics__region span { color: var(--color-text-muted); font-size: var(--font-size-caption); }
.platform-analytics__performance { grid-column: 1 / -1; }
.platform-analytics__performance :deep(.data-table) { border: 0; border-radius: 0; }
.platform-analytics__library-cell { display: grid; min-width: 180px; }
.platform-analytics__library-cell span { color: var(--color-text-muted); font-size: var(--font-size-caption); }
.platform-analytics__occupancy-cell { display: grid; grid-template-columns: minmax(100px, 1fr) auto; align-items: center; gap: var(--space-3); min-width: 170px; }
.platform-analytics__occupancy-cell > div { height: 7px; overflow: hidden; border-radius: var(--radius-pill); background: var(--color-surface-secondary); }
.platform-analytics__occupancy-cell > div span { display: block; height: 100%; border-radius: inherit; background: var(--color-success); }
@media (max-width: 900px) { .platform-analytics__grid { grid-template-columns: 1fr; } .platform-analytics__performance { grid-column: auto; } }
@media (max-width: 680px) { .platform-analytics__header, .analytics-panel__header { flex-direction: column; } .platform-analytics__metric-tabs { width: 100%; } .platform-analytics__metric-tab { min-width: 0; flex: 1; padding: 0 var(--space-2); } }
</style>
