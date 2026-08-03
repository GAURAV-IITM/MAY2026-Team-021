<template>
  <div class="student-report">
    <section class="report-panel student-report__trend" aria-labelledby="student-trend-title">
      <header class="report-panel__header"><div><h2 id="student-trend-title">Student joining trend</h2><p>New registrations during the selected period.</p></div><strong>{{ students.totals.newStudents }} joined</strong></header>
      <div class="report-panel__body">
        <AnalyticsChart type="line" :data="joiningData" :options="joiningOptions" :height="300" aria-label="New students by month" />
      </div>
    </section>

    <section class="report-panel" aria-labelledby="student-status-title">
      <header class="report-panel__header"><div><h2 id="student-status-title">Student status</h2><p>Active and inactive student records.</p></div></header>
      <div class="report-panel__body">
        <AnalyticsChart type="doughnut" :data="statusData" :options="doughnutOptions" :height="240" aria-label="Student status distribution" />
      </div>
    </section>

    <section class="report-panel" aria-labelledby="fee-status-title">
      <header class="report-panel__header"><div><h2 id="fee-status-title">Fee status</h2><p>Current student-level payment standing.</p></div></header>
      <div class="report-panel__body student-report__breakdown">
        <article v-for="item in students.feeStatus" :key="item.status">
          <span :class="`student-report__dot--${item.status}`"></span>
          <div><strong>{{ item.label }}</strong><small>{{ getShare(item.count) }}% of students</small></div>
          <strong>{{ item.count }}</strong>
        </article>
      </div>
    </section>

    <section class="report-panel student-report__shifts" aria-labelledby="student-shifts-title">
      <header class="report-panel__header"><div><h2 id="student-shifts-title">Students by shift</h2><p>A student with multiple shifts is counted in each selected shift.</p></div></header>
      <div class="report-panel__body student-report__shift-list">
        <article v-for="shift in shiftRows" :key="shift.shiftId">
          <div><strong>{{ shift.label }}</strong><small>{{ shift.timing }}</small></div>
          <div class="student-report__track"><span :style="{ width: `${shift.share}%` }"></span></div>
          <strong>{{ shift.count }}</strong>
        </article>
        <div v-if="shiftRows.length === 0" class="report-empty">No student shift assignments match these filters.</div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'

import AnalyticsChart from './AnalyticsChart.vue'

const props = defineProps({
  students: { type: Object, required: true },
  shiftOptions: { type: Array, default: () => [] },
})

const joiningData = computed(() => ({
  labels: props.students.joiningTrend.map((item) => item.label),
  datasets: [{ label: 'New students', data: props.students.joiningTrend.map((item) => item.joined), borderColor: '#0284c7', backgroundColor: 'rgba(2, 132, 199, 0.13)', borderWidth: 3, pointRadius: 4, pointBackgroundColor: '#0284c7', fill: true, tension: 0.3 }],
}))
const joiningOptions = { plugins: { legend: { display: false } } }
const statusData = computed(() => ({
  labels: props.students.statusDistribution.map((item) => item.label),
  datasets: [{ data: props.students.statusDistribution.map((item) => item.count), backgroundColor: ['#16a34a', '#94a3b8', '#dc2626', '#d97706'], borderWidth: 0, hoverOffset: 4 }],
}))
const doughnutOptions = { cutout: '68%' }
const shiftRows = computed(() => {
  const optionsById = new Map(props.shiftOptions.map((shift) => [shift.value, shift]))
  const maximum = Math.max(1, ...props.students.shiftDistribution.map((shift) => shift.count))

  return props.students.shiftDistribution
    .map((shift) => ({ ...shift, label: optionsById.get(shift.shiftId)?.label || shift.shiftId, timing: optionsById.get(shift.shiftId)?.timing || '', share: Math.round((shift.count / maximum) * 100) }))
    .sort((first, second) => second.count - first.count)
})
function getShare(count) { return props.students.totals.totalStudents ? Math.round((count / props.students.totals.totalStudents) * 100) : 0 }
</script>

<style scoped>
.student-report { display: grid; grid-template-columns: minmax(0, 1.45fr) minmax(260px, 0.75fr); gap: var(--space-4); align-items: start; }
.report-panel { min-width: 0; overflow: hidden; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-elevated); box-shadow: var(--shadow-sm); }
.report-panel__header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-4); padding: var(--space-5); border-bottom: 1px solid var(--color-divider); }
.report-panel__header h2, .report-panel__header p { margin: 0; }
.report-panel__header h2 { font-size: var(--font-size-h5); }
.report-panel__header p { margin-top: var(--space-1); color: var(--color-text-muted); font-size: var(--font-size-sm); }
.report-panel__header > strong { flex: 0 0 auto; color: var(--color-info); }
.report-panel__body { padding: var(--space-5); }
.student-report__breakdown, .student-report__shift-list { display: grid; gap: var(--space-4); }
.student-report__breakdown article { display: grid; grid-template-columns: 10px minmax(0, 1fr) auto; align-items: center; gap: var(--space-3); padding-bottom: var(--space-3); border-bottom: 1px solid var(--color-divider); }
.student-report__breakdown article:last-child { padding-bottom: 0; border-bottom: 0; }
.student-report__breakdown span { width: 10px; height: 10px; border-radius: var(--radius-pill); background: var(--color-text-muted); }
.student-report__dot--paid { background: var(--color-success) !important; }
.student-report__dot--pending { background: var(--color-warning) !important; }
.student-report__dot--overdue { background: var(--color-danger) !important; }
.student-report__breakdown article > div, .student-report__shift-list article > div:first-child { display: grid; }
.student-report__breakdown small, .student-report__shift-list small { color: var(--color-text-muted); }
.student-report__shifts { grid-column: 1 / -1; }
.student-report__shift-list { grid-template-columns: repeat(2, minmax(0, 1fr)); column-gap: var(--space-8); }
.student-report__shift-list article { display: grid; grid-template-columns: minmax(120px, 0.7fr) minmax(120px, 1fr) auto; align-items: center; gap: var(--space-3); }
.student-report__track { height: 8px; overflow: hidden; border-radius: var(--radius-pill); background: var(--color-surface-secondary); }
.student-report__track span { display: block; height: 100%; border-radius: inherit; background: var(--color-info); }
.report-empty { padding: var(--space-6); color: var(--color-text-muted); text-align: center; }
@media (max-width: 900px) { .student-report { grid-template-columns: 1fr; } .student-report__shifts { grid-column: auto; } .student-report__shift-list { grid-template-columns: 1fr; } }
@media (max-width: 560px) { .report-panel__header, .report-panel__body { padding: var(--space-4); } .student-report__shift-list article { grid-template-columns: minmax(100px, 1fr) auto; } .student-report__track { grid-column: 1 / -1; grid-row: 2; } }
</style>
