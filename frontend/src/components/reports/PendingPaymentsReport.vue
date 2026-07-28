<template>
  <div class="pending-report">
    <section class="report-panel" aria-labelledby="pending-ageing-title">
      <header class="report-panel__header"><div><h2 id="pending-ageing-title">Pending fee ageing</h2><p>How long payment records have remained unpaid.</p></div></header>
      <div class="report-panel__body">
        <AnalyticsChart type="bar" :data="ageingData" :options="ageingOptions" :height="260" aria-label="Pending payment ageing chart" />
      </div>
    </section>

    <section class="report-panel pending-report__attention" aria-labelledby="pending-attention-title">
      <header class="report-panel__header"><div><h2 id="pending-attention-title">Collection attention</h2><p>Prioritize older payment records first.</p></div></header>
      <div class="report-panel__body pending-report__summary">
        <div><span>Overdue records</span><strong>{{ pending.totals.overdueCount }}</strong></div>
        <div><span>Affected students</span><strong>{{ pending.totals.affectedStudents }}</strong></div>
        <div><span>Total outstanding</span><strong>{{ formatCurrency(pending.totals.pendingAmount) }}</strong></div>
      </div>
    </section>

    <section class="report-panel pending-report__records" aria-labelledby="pending-records-title">
      <header class="report-panel__header"><div><h2 id="pending-records-title">Pending payment records</h2><p>Unpaid monthly fee records within the selected period.</p></div><span class="badge badge--warning">{{ pending.totals.pendingCount }} records</span></header>

      <div class="pending-report__desktop">
        <DataTable :columns="columns" :rows="pending.records" aria-label="Pending payment records">
          <template #cell-studentName="{ row }"><div class="pending-report__student"><strong>{{ row.studentName }}</strong><small>{{ row.phone }}</small></div></template>
          <template #cell-amount="{ value }"><strong>{{ formatCurrency(value) }}</strong></template>
          <template #cell-dueDate="{ value }">{{ formatDate(value) }}</template>
          <template #cell-ageing="{ row }"><span class="badge" :class="row.daysOverdue ? 'pending-report__overdue' : 'badge--warning'">{{ row.ageing }}</span></template>
          <template #empty>No pending payment records match the selected filters.</template>
        </DataTable>
      </div>

      <div class="pending-report__mobile">
        <p v-if="pending.records.length === 0" class="report-empty">No pending payment records match the selected filters.</p>
        <article v-for="record in pending.records" :key="record.id">
          <header><div><strong>{{ record.studentName }}</strong><small>{{ record.phone }}</small></div><strong>{{ formatCurrency(record.amount) }}</strong></header>
          <dl>
            <div><dt>Fee month</dt><dd>{{ record.monthLabel }}</dd></div>
            <div><dt>Seat</dt><dd>{{ record.seatNumber }}</dd></div>
            <div><dt>Due date</dt><dd>{{ formatDate(record.dueDate) }}</dd></div>
            <div><dt>Status</dt><dd :class="{ 'text-danger': record.daysOverdue }">{{ record.ageing }}</dd></div>
          </dl>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'

import DataTable from '../common/DataTable.vue'
import AnalyticsChart from './AnalyticsChart.vue'

const props = defineProps({ pending: { type: Object, required: true } })
const currencyFormatter = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 })
const dateFormatter = new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
const columns = [
  { key: 'studentName', label: 'Student' },
  { key: 'seatNumber', label: 'Seat' },
  { key: 'monthLabel', label: 'Fee Month' },
  { key: 'amount', label: 'Amount' },
  { key: 'dueDate', label: 'Due Date' },
  { key: 'ageing', label: 'Ageing' },
]
const ageingData = computed(() => ({
  labels: props.pending.ageing.map((item) => item.label),
  datasets: [{ label: 'Payment records', data: props.pending.ageing.map((item) => item.count), backgroundColor: ['#0284c7', '#f59e0b', '#f97316', '#dc2626', '#991b1b'], borderRadius: 5, maxBarThickness: 54 }],
}))
const ageingOptions = { plugins: { legend: { display: false } } }
function formatCurrency(value) { return currencyFormatter.format(Number(value) || 0) }
function formatDate(value) { return value ? dateFormatter.format(new Date(`${String(value).slice(0, 10)}T00:00:00`)) : 'Not set' }
</script>

<style scoped>
.pending-report { display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(280px, 0.75fr); gap: var(--space-4); align-items: start; }
.report-panel { min-width: 0; overflow: hidden; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-elevated); box-shadow: var(--shadow-sm); }
.report-panel__header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-4); padding: var(--space-5); border-bottom: 1px solid var(--color-divider); }
.report-panel__header h2, .report-panel__header p { margin: 0; }
.report-panel__header h2 { font-size: var(--font-size-h5); }
.report-panel__header p { margin-top: var(--space-1); color: var(--color-text-muted); font-size: var(--font-size-sm); }
.report-panel__body { padding: var(--space-5); }
.pending-report__summary { display: grid; gap: var(--space-4); }
.pending-report__summary div { display: flex; align-items: baseline; justify-content: space-between; gap: var(--space-3); padding-bottom: var(--space-3); border-bottom: 1px solid var(--color-divider); }
.pending-report__summary div:last-child { padding-bottom: 0; border-bottom: 0; }
.pending-report__summary span { color: var(--color-text-muted); }
.pending-report__summary strong { font-size: var(--font-size-h5); }
.pending-report__records { grid-column: 1 / -1; }
.pending-report__student { display: grid; min-width: 150px; }
.pending-report__student small { color: var(--color-text-muted); }
.pending-report__overdue { background: var(--color-danger-light); color: var(--color-danger); }
.pending-report__mobile { display: none; }
.report-empty { padding: var(--space-6); color: var(--color-text-muted); text-align: center; }
@media (max-width: 900px) { .pending-report { grid-template-columns: 1fr; } .pending-report__records { grid-column: auto; } }
@media (max-width: 680px) {
  .report-panel__header, .report-panel__body { padding: var(--space-4); }
  .pending-report__desktop { display: none; }
  .pending-report__mobile { display: grid; gap: var(--space-3); padding: var(--space-4); }
  .pending-report__mobile article { padding: var(--space-4); border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface); }
  .pending-report__mobile header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-3); margin-bottom: var(--space-4); }
  .pending-report__mobile header div { display: grid; }
  .pending-report__mobile small { color: var(--color-text-muted); }
  .pending-report__mobile dl { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-3); margin: 0; }
  .pending-report__mobile dl div { min-width: 0; }
  .pending-report__mobile dt { color: var(--color-text-muted); font-size: var(--font-size-caption); }
  .pending-report__mobile dd { margin: var(--space-1) 0 0; font-weight: var(--font-weight-medium); overflow-wrap: anywhere; }
}
</style>
