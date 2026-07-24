<template>
  <div class="reports-overview">
    <section class="report-panel reports-overview__revenue" aria-labelledby="overview-revenue-title">
      <header class="report-panel__header">
        <div>
          <p class="text-label text-muted m-0">Fee performance</p>
          <h2 id="overview-revenue-title">Revenue trend</h2>
          <p>Expected fees compared with collected revenue.</p>
        </div>
        <strong>{{ formatCurrency(reports.revenue.totals.collected) }}</strong>
      </header>
      <div class="report-panel__body">
        <AnalyticsChart
          type="line"
          :data="revenueChartData"
          :options="currencyChartOptions"
          :height="270"
          aria-label="Expected and collected revenue by month"
        />
      </div>
    </section>

    <section class="report-panel" aria-labelledby="overview-insights-title">
      <header class="report-panel__header">
        <div>
          <p class="text-label text-muted m-0">Decision support</p>
          <h2 id="overview-insights-title">Performance signals</h2>
          <p>Items worth reviewing from the selected scope.</p>
        </div>
      </header>
      <div class="report-panel__body reports-overview__insights">
        <article v-for="insight in reports.insights" :key="insight.id" :class="`reports-overview__insight--${insight.tone}`">
          <span aria-hidden="true"></span>
          <div>
            <strong>{{ insight.title }}</strong>
            <p>{{ insight.detail }}</p>
          </div>
        </article>
      </div>
    </section>

    <section class="report-panel reports-overview__occupancy" aria-labelledby="overview-occupancy-title">
      <header class="report-panel__header">
        <div>
          <p class="text-label text-muted m-0">Current capacity</p>
          <h2 id="overview-occupancy-title">Shift occupancy</h2>
          <p>Current seat usage for each enabled shift.</p>
        </div>
        <strong>{{ reports.occupancy.totals.occupancyRate }}%</strong>
      </header>
      <div class="report-panel__body reports-overview__shift-list">
        <div v-for="shift in reports.occupancy.byShift" :key="shift.shiftId" class="reports-overview__shift">
          <div>
            <strong>{{ shift.name }}</strong>
            <small>{{ shift.timing }}</small>
          </div>
          <div class="reports-overview__track" aria-hidden="true">
            <span :style="{ width: `${shift.occupancyRate}%` }"></span>
          </div>
          <strong>{{ shift.occupied }}/{{ shift.totalSeats }}</strong>
        </div>
      </div>
    </section>

    <section class="report-panel" aria-labelledby="overview-pending-title">
      <header class="report-panel__header">
        <div>
          <p class="text-label text-muted m-0">Follow-up</p>
          <h2 id="overview-pending-title">Largest pending balances</h2>
          <p>Highest unpaid records in this reporting period.</p>
        </div>
        <strong>{{ formatCurrency(reports.pendingPayments.totals.pendingAmount) }}</strong>
      </header>
      <div class="report-panel__body reports-overview__pending-list">
        <div v-if="topPending.length === 0" class="reports-overview__empty">No pending payments in this period.</div>
        <div v-for="payment in topPending" :key="payment.id" class="reports-overview__pending-row">
          <span>{{ getInitials(payment.studentName) }}</span>
          <div><strong>{{ payment.studentName }}</strong><small>{{ payment.monthLabel }} · {{ payment.seatNumber }}</small></div>
          <strong>{{ formatCurrency(payment.amount) }}</strong>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'

import AnalyticsChart from './AnalyticsChart.vue'

const props = defineProps({
  reports: { type: Object, required: true },
})

const currencyFormatter = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 0,
})

const revenueChartData = computed(() => ({
  labels: props.reports.revenue.series.map((item) => item.label),
  datasets: [
    {
      label: 'Expected',
      data: props.reports.revenue.series.map((item) => item.expected),
      borderColor: '#94a3b8',
      backgroundColor: '#94a3b8',
      borderDash: [5, 5],
      borderWidth: 2,
      pointRadius: 3,
      tension: 0.3,
    },
    {
      label: 'Collected',
      data: props.reports.revenue.series.map((item) => item.collected),
      borderColor: '#2563eb',
      backgroundColor: 'rgba(37, 99, 235, 0.12)',
      borderWidth: 3,
      pointRadius: 4,
      pointBackgroundColor: '#2563eb',
      fill: true,
      tension: 0.3,
    },
  ],
}))

const currencyChartOptions = {
  scales: {
    x: { grid: { display: false }, ticks: { color: '#6b7280' } },
    y: {
      beginAtZero: true,
      grid: { color: '#e5e7eb' },
      ticks: {
        color: '#6b7280',
        callback: (value) => `₹${Number(value).toLocaleString('en-IN')}`,
      },
    },
  },
}

const topPending = computed(() => {
  return [...props.reports.pendingPayments.records]
    .sort((first, second) => second.amount - first.amount)
    .slice(0, 4)
})

function formatCurrency(value) {
  return currencyFormatter.format(Number(value) || 0)
}

function getInitials(name) {
  return String(name).split(' ').map((part) => part[0]).slice(0, 2).join('')
}
</script>

<style scoped>
.reports-overview { display: grid; grid-template-columns: minmax(0, 1.55fr) minmax(300px, 0.85fr); gap: var(--space-4); align-items: start; }
.report-panel { min-width: 0; overflow: hidden; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-elevated); box-shadow: var(--shadow-sm); }
.report-panel__header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-4); padding: var(--space-5); border-bottom: 1px solid var(--color-divider); }
.report-panel__header h2, .report-panel__header p { margin: 0; }
.report-panel__header h2 { margin-top: var(--space-1); font-size: var(--font-size-h5); }
.report-panel__header p:not(.text-label) { margin-top: var(--space-1); color: var(--color-text-muted); font-size: var(--font-size-sm); }
.report-panel__header > strong { flex: 0 0 auto; color: var(--color-text-primary); font-size: var(--font-size-h4); }
.report-panel__body { padding: var(--space-5); }
.reports-overview__insights { display: grid; gap: var(--space-4); }
.reports-overview__insights article { display: grid; grid-template-columns: 8px minmax(0, 1fr); gap: var(--space-3); }
.reports-overview__insights article > span { min-height: 54px; border-radius: var(--radius-pill); background: var(--color-info); }
.reports-overview__insights p { margin: var(--space-1) 0 0; color: var(--color-text-muted); font-size: var(--font-size-sm); }
.reports-overview__insight--success > span { background: var(--color-success) !important; }
.reports-overview__insight--warning > span { background: var(--color-warning) !important; }
.reports-overview__insight--neutral > span { background: var(--color-secondary) !important; }
.reports-overview__shift-list { display: grid; gap: var(--space-4); }
.reports-overview__shift { display: grid; grid-template-columns: minmax(110px, 0.65fr) minmax(150px, 1fr) auto; align-items: center; gap: var(--space-4); }
.reports-overview__shift > div:first-child { display: grid; }
.reports-overview__shift small { color: var(--color-text-muted); }
.reports-overview__track { height: 8px; overflow: hidden; border-radius: var(--radius-pill); background: var(--color-surface-secondary); }
.reports-overview__track span { display: block; height: 100%; border-radius: inherit; background: var(--color-info); }
.reports-overview__pending-list { display: grid; gap: var(--space-2); }
.reports-overview__pending-row { display: grid; grid-template-columns: 36px minmax(0, 1fr) auto; align-items: center; gap: var(--space-3); padding-bottom: var(--space-3); border-bottom: 1px solid var(--color-divider); }
.reports-overview__pending-row:last-child { padding-bottom: 0; border-bottom: 0; }
.reports-overview__pending-row > span { display: grid; width: 36px; height: 36px; place-items: center; border-radius: var(--radius-pill); background: var(--color-warning-light); color: var(--color-warning); font-size: var(--font-size-caption); font-weight: var(--font-weight-bold); }
.reports-overview__pending-row > div { display: grid; min-width: 0; }
.reports-overview__pending-row small { color: var(--color-text-muted); }
.reports-overview__empty { padding: var(--space-6); color: var(--color-text-muted); text-align: center; }

@media (max-width: 980px) { .reports-overview { grid-template-columns: 1fr; } }
@media (max-width: 560px) {
  .report-panel__header, .report-panel__body { padding: var(--space-4); }
  .report-panel__header > strong { font-size: var(--font-size-body-lg); }
  .reports-overview__shift { grid-template-columns: minmax(100px, 1fr) auto; gap: var(--space-2); }
  .reports-overview__track { grid-column: 1 / -1; grid-row: 2; }
}
</style>

