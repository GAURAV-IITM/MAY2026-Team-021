<template>
  <div class="occupancy-report">
    <section class="report-panel occupancy-report__chart" aria-labelledby="occupancy-chart-title">
      <header class="report-panel__header"><div><h2 id="occupancy-chart-title">Availability by shift</h2><p>Current seat status for every shift in the selected scope.</p></div></header>
      <div class="report-panel__body">
        <AnalyticsChart type="bar" :data="shiftChartData" :options="stackedOptions" :height="340" aria-label="Seat availability by shift" />
      </div>
    </section>

    <section class="report-panel" aria-labelledby="floor-utilization-title">
      <header class="report-panel__header"><div><h2 id="floor-utilization-title">Floor utilization</h2><p>Current assigned-seat share by floor.</p></div></header>
      <div class="report-panel__body occupancy-report__floors">
        <div v-if="occupancy.byFloor.length === 0" class="report-empty">No floors match these filters.</div>
        <article v-for="floor in occupancy.byFloor" :key="floor.floor">
          <div><strong>{{ floor.label }}</strong><span>{{ floor.occupied }}/{{ floor.totalSeats }} allotted</span></div>
          <div class="occupancy-report__track"><span :style="{ width: `${floor.occupancyRate}%` }"></span></div>
          <strong>{{ floor.occupancyRate }}%</strong>
        </article>
      </div>
    </section>

    <section class="report-panel occupancy-report__table" aria-labelledby="occupancy-details-title">
      <header class="report-panel__header"><div><h2 id="occupancy-details-title">Shift details</h2><p>Exact availability counts used throughout the seat map and dashboard.</p></div></header>
      <DataTable :columns="columns" :rows="occupancy.byShift" aria-label="Seat occupancy by shift">
        <template #cell-name="{ row }"><div class="occupancy-report__shift"><strong>{{ row.name }}</strong><small>{{ row.timing }}</small></div></template>
        <template #cell-available="{ value }"><span class="status-value status-value--available">{{ value }}</span></template>
        <template #cell-occupied="{ value }"><span class="status-value status-value--occupied">{{ value }}</span></template>
        <template #cell-blocked="{ value }"><span class="status-value status-value--blocked">{{ value }}</span></template>
        <template #cell-reserved="{ value }"><span class="status-value status-value--reserved">{{ value }}</span></template>
        <template #cell-maintenance="{ value }"><span class="status-value status-value--maintenance">{{ value }}</span></template>
        <template #cell-occupancyRate="{ value }"><strong>{{ value }}%</strong></template>
      </DataTable>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'

import DataTable from '../common/DataTable.vue'
import AnalyticsChart from './AnalyticsChart.vue'

const props = defineProps({ occupancy: { type: Object, required: true } })
const columns = [
  { key: 'name', label: 'Shift' },
  { key: 'totalSeats', label: 'Total' },
  { key: 'available', label: 'Available' },
  { key: 'occupied', label: 'Allotted' },
  { key: 'blocked', label: 'Blocked' },
  { key: 'reserved', label: 'Reserved' },
  { key: 'maintenance', label: 'Maintenance' },
  { key: 'occupancyRate', label: 'Occupancy' },
]
const shiftChartData = computed(() => ({
  labels: props.occupancy.byShift.map((shift) => shift.name),
  datasets: [
    { label: 'Available', data: props.occupancy.byShift.map((shift) => shift.available), backgroundColor: '#16a34a' },
    { label: 'Allotted', data: props.occupancy.byShift.map((shift) => shift.occupied), backgroundColor: '#4f46e5' },
    { label: 'Blocked', data: props.occupancy.byShift.map((shift) => shift.blocked), backgroundColor: '#dc2626' },
    { label: 'Reserved', data: props.occupancy.byShift.map((shift) => shift.reserved), backgroundColor: '#0284c7' },
    { label: 'Maintenance', data: props.occupancy.byShift.map((shift) => shift.maintenance), backgroundColor: '#d97706' },
  ],
}))
const stackedOptions = {
  scales: {
    x: { stacked: true, grid: { display: false }, ticks: { color: '#6b7280' } },
    y: { stacked: true, beginAtZero: true, grid: { color: '#e5e7eb' }, ticks: { color: '#6b7280', precision: 0 } },
  },
}
</script>

<style scoped>
.occupancy-report { display: grid; grid-template-columns: minmax(0, 1.55fr) minmax(280px, 0.8fr); gap: var(--space-4); align-items: start; }
.report-panel { min-width: 0; overflow: hidden; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-elevated); box-shadow: var(--shadow-sm); }
.report-panel__header { padding: var(--space-5); border-bottom: 1px solid var(--color-divider); }
.report-panel__header h2, .report-panel__header p { margin: 0; }
.report-panel__header h2 { font-size: var(--font-size-h5); }
.report-panel__header p { margin-top: var(--space-1); color: var(--color-text-muted); font-size: var(--font-size-sm); }
.report-panel__body { padding: var(--space-5); }
.occupancy-report__table { grid-column: 1 / -1; }
.occupancy-report__floors { display: grid; gap: var(--space-5); }
.occupancy-report__floors article { display: grid; grid-template-columns: minmax(90px, 1fr) auto; align-items: center; gap: var(--space-2); }
.occupancy-report__floors article > div:first-child { display: flex; justify-content: space-between; gap: var(--space-2); grid-column: 1 / -1; }
.occupancy-report__floors span { color: var(--color-text-muted); font-size: var(--font-size-sm); }
.occupancy-report__track { height: 9px; overflow: hidden; border-radius: var(--radius-pill); background: var(--color-surface-secondary); }
.occupancy-report__track span { display: block; height: 100%; border-radius: inherit; background: var(--color-info); }
.occupancy-report__shift { display: grid; min-width: 130px; }
.occupancy-report__shift small { color: var(--color-text-muted); }
.status-value { display: inline-grid; min-width: 28px; min-height: 28px; place-items: center; border-radius: var(--radius-sm); font-weight: var(--font-weight-semibold); }
.status-value--available { background: var(--color-success-light); color: var(--color-success); }
.status-value--occupied { background: #eef2ff; color: #4f46e5; }
.status-value--blocked { background: var(--color-danger-light); color: var(--color-danger); }
.status-value--reserved { background: var(--color-info-light); color: var(--color-info); }
.status-value--maintenance { background: var(--color-warning-light); color: var(--color-warning); }
.report-empty { padding: var(--space-6); color: var(--color-text-muted); text-align: center; }
@media (max-width: 900px) { .occupancy-report { grid-template-columns: 1fr; } .occupancy-report__table { grid-column: auto; } }
@media (max-width: 560px) { .report-panel__header, .report-panel__body { padding: var(--space-4); } }
</style>

