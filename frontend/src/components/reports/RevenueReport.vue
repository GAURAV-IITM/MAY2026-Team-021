<template>
  <div class="revenue-report">
    <section class="report-panel revenue-report__trend" aria-labelledby="revenue-trend-title">
      <header class="report-panel__header">
        <div><h2 id="revenue-trend-title">Revenue trend</h2><p>Expected, collected, and pending fees by month.</p></div>
        <span class="badge" :class="revenue.totals.collectionRate >= 85 ? 'badge--success' : 'badge--warning'">
          {{ revenue.totals.collectionRate }}% collected
        </span>
      </header>
      <div class="report-panel__body">
        <AnalyticsChart type="bar" :data="trendData" :options="trendOptions" :height="320" aria-label="Monthly revenue bar chart" />
      </div>
    </section>

    <section class="report-panel" aria-labelledby="payment-method-title">
      <header class="report-panel__header"><div><h2 id="payment-method-title">Payment methods</h2><p>Share of completed payment records.</p></div></header>
      <div class="report-panel__body">
        <div v-if="revenue.paymentMethods.length === 0" class="report-empty">No paid records in this period.</div>
        <AnalyticsChart v-else type="doughnut" :data="methodData" :options="doughnutOptions" :height="260" aria-label="Payment method distribution" />
      </div>
    </section>

    <section class="report-panel revenue-report__table" aria-labelledby="revenue-table-title">
      <header class="report-panel__header"><div><h2 id="revenue-table-title">Monthly collection details</h2><p>Exact values behind the revenue chart.</p></div></header>
      <DataTable :columns="columns" :rows="revenue.series" aria-label="Monthly revenue details">
        <template #cell-expected="{ value }">{{ formatCurrency(value) }}</template>
        <template #cell-collected="{ value }"><strong class="text-success">{{ formatCurrency(value) }}</strong></template>
        <template #cell-pending="{ value }"><strong :class="value ? 'text-warning' : ''">{{ formatCurrency(value) }}</strong></template>
        <template #cell-collectionRate="{ value }">
          <div class="revenue-report__rate"><span><i :style="{ width: `${value}%` }"></i></span><strong>{{ value }}%</strong></div>
        </template>
      </DataTable>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'

import DataTable from '../common/DataTable.vue'
import AnalyticsChart from './AnalyticsChart.vue'

const props = defineProps({ revenue: { type: Object, required: true } })
const currencyFormatter = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })
const columns = [
  { key: 'label', label: 'Month' },
  { key: 'expected', label: 'Expected' },
  { key: 'collected', label: 'Collected' },
  { key: 'pending', label: 'Pending' },
  { key: 'collectionRate', label: 'Collection Rate' },
]

const trendData = computed(() => ({
  labels: props.revenue.series.map((item) => item.label),
  datasets: [
    { label: 'Collected', data: props.revenue.series.map((item) => item.collected), backgroundColor: '#2563eb', borderRadius: 5, maxBarThickness: 44 },
    { label: 'Pending', data: props.revenue.series.map((item) => item.pending), backgroundColor: '#f59e0b', borderRadius: 5, maxBarThickness: 44 },
  ],
}))
const trendOptions = {
  scales: {
    x: { stacked: true, grid: { display: false }, ticks: { color: '#6b7280' } },
    y: { stacked: true, beginAtZero: true, grid: { color: '#e5e7eb' }, ticks: { color: '#6b7280', callback: (value) => `₹${Number(value).toLocaleString('en-IN')}` } },
  },
}
const methodData = computed(() => ({
  labels: props.revenue.paymentMethods.map((item) => item.label),
  datasets: [{ data: props.revenue.paymentMethods.map((item) => item.count), backgroundColor: ['#2563eb', '#16a34a', '#f59e0b', '#0284c7', '#64748b'], borderWidth: 0, hoverOffset: 4 }],
}))
const doughnutOptions = { cutout: '68%', plugins: { legend: { position: 'bottom' } } }
function formatCurrency(value) { return currencyFormatter.format(Number(value) || 0) }
</script>

<style scoped>
.revenue-report { display: grid; grid-template-columns: minmax(0, 1.6fr) minmax(280px, 0.75fr); gap: var(--space-4); align-items: start; }
.report-panel { min-width: 0; overflow: hidden; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-elevated); box-shadow: var(--shadow-sm); }
.report-panel__header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-4); padding: var(--space-5); border-bottom: 1px solid var(--color-divider); }
.report-panel__header h2, .report-panel__header p { margin: 0; }
.report-panel__header h2 { font-size: var(--font-size-h5); }
.report-panel__header p { margin-top: var(--space-1); color: var(--color-text-muted); font-size: var(--font-size-sm); }
.report-panel__body { padding: var(--space-5); }
.revenue-report__table { grid-column: 1 / -1; }
.revenue-report__rate { display: flex; align-items: center; gap: var(--space-3); min-width: 150px; }
.revenue-report__rate > span { width: 90px; height: 7px; overflow: hidden; border-radius: var(--radius-pill); background: var(--color-surface-secondary); }
.revenue-report__rate i { display: block; height: 100%; border-radius: inherit; background: var(--color-success); }
.report-empty { display: grid; min-height: 220px; place-items: center; color: var(--color-text-muted); text-align: center; }
@media (max-width: 900px) { .revenue-report { grid-template-columns: 1fr; } .revenue-report__table { grid-column: auto; } }
@media (max-width: 560px) { .report-panel__header, .report-panel__body { padding: var(--space-4); } }
</style>

