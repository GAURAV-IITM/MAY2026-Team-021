<template>
  <section class="seat-requests-page" aria-labelledby="seat-requests-title">
    <header class="seat-requests-page__header">
      <div>
        <p class="text-label text-muted m-0">Student Management</p>
        <h1 id="seat-requests-title" class="text-h2 seat-requests-page__title">Seat Change Requests</h1>
        <p class="seat-requests-page__description">Review student requests for a different seat, floor, or shift.</p>
      </div>
      <button class="btn btn--secondary" type="button" :disabled="isLoading" @click="loadRequests">
        {{ isLoading ? 'Refreshing...' : 'Refresh' }}
      </button>
    </header>

    <Toast v-if="successMessage" type="success">{{ successMessage }}</Toast>

    <section class="seat-request-summary" aria-label="Seat request summary">
      <article v-for="item in summaryItems" :key="item.label" class="stat-card stat-card--dashboard">
        <div class="stat-card__header"><span class="text-label text-muted">{{ item.label }}</span><span class="stat-card__icon" aria-hidden="true">{{ item.icon }}</span></div>
        <strong class="stat-card__value">{{ item.value }}</strong>
        <span class="text-small text-muted">{{ item.detail }}</span>
      </article>
    </section>

    <section class="card seat-request-filters" aria-label="Seat request filters">
      <div class="seat-request-filters__search">
        <SearchBar v-model="searchQuery" placeholder="Search student, seat, or email" @clear="searchQuery = ''" />
      </div>
      <div class="seat-request-filters__field">
        <label class="form-label" for="request-status-filter">Status</label>
        <select id="request-status-filter" v-model="statusFilter" class="form-select">
          <option value="">All statuses</option><option value="pending">Pending</option><option value="approved">Approved</option><option value="rejected">Rejected</option><option value="cancelled">Cancelled</option>
        </select>
      </div>
      <div class="seat-request-filters__field">
        <label class="form-label" for="request-shift-filter">Preferred Shift</label>
        <select id="request-shift-filter" v-model="shiftFilter" class="form-select">
          <option value="">All shifts</option><option v-for="shift in shiftOptions" :key="shift.value" :value="shift.value">{{ shift.label }}</option>
        </select>
      </div>
      <button class="btn btn--secondary" type="button" :disabled="!hasActiveFilters" @click="clearFilters">Clear Filters</button>
    </section>

    <div v-if="errorMessage" class="alert alert--danger" role="alert">
      <div><strong>Unable to load seat requests.</strong><p class="m-0">{{ errorMessage }}</p></div>
      <button class="btn btn--secondary btn--sm" type="button" @click="loadRequests">Retry</button>
    </div>

    <div v-if="isLoading && requests.length === 0" class="seat-requests-page__loading"><LoadingSpinner label="Loading seat requests" /></div>

    <section v-else class="card seat-request-list" aria-labelledby="seat-request-list-title">
      <header class="seat-request-list__header">
        <div><h2 id="seat-request-list-title" class="text-h4 m-0">Requests</h2><p class="text-small text-muted m-0">{{ filteredRequests.length }} matching records</p></div>
        <span v-if="pendingCount" class="badge badge--warning">{{ pendingCount }} Pending</span>
      </header>

      <DataTable class="seat-request-list__table" :columns="columns" :rows="filteredRequests" aria-label="Student seat change requests">
        <template #empty>No seat change requests match the current filters.</template>
        <template #cell-student="{ row }"><div class="student-cell"><strong>{{ row.studentName }}</strong><span>{{ row.studentEmail }}</span></div></template>
        <template #cell-preference="{ row }"><div class="preference-cell"><strong>{{ row.preferredSeatNumber || 'Any seat' }}</strong><span>{{ row.preferredFloor ? `Floor ${row.preferredFloor}` : 'Any floor' }}</span></div></template>
        <template #cell-preferredShiftName="{ value }">{{ formatLabel(value) }}</template>
        <template #cell-submittedAt="{ value }">{{ formatDate(value) }}</template>
        <template #cell-status="{ value }"><span class="badge" :class="statusClass(value)">{{ formatLabel(value) }}</span></template>
        <template #actions="{ row }"><button class="btn btn--secondary btn--sm" type="button" @click="requestStore.selectRequest(row)">{{ row.status === 'pending' ? 'Review' : 'View' }}</button></template>
      </DataTable>

      <div class="seat-request-list__cards">
        <p v-if="filteredRequests.length === 0" class="seat-request-list__empty">No seat change requests match the current filters.</p>
        <article v-for="request in filteredRequests" :key="request.id" class="seat-request-card">
          <header><div><strong>{{ request.studentName }}</strong><span>{{ request.studentEmail }}</span></div><span class="badge" :class="statusClass(request.status)">{{ formatLabel(request.status) }}</span></header>
          <dl><div><dt>Current Seat</dt><dd>{{ request.currentSeatNumber || '-' }}</dd></div><div><dt>Preferred</dt><dd>{{ request.preferredSeatNumber || 'Any seat' }}</dd></div><div><dt>Shift</dt><dd>{{ formatLabel(request.preferredShiftName) }}</dd></div><div><dt>Submitted</dt><dd>{{ formatDate(request.submittedAt) }}</dd></div></dl>
          <button class="btn btn--secondary" type="button" @click="requestStore.selectRequest(request)">{{ request.status === 'pending' ? 'Review Request' : 'View Details' }}</button>
        </article>
      </div>
    </section>

    <SeatRequestReviewModal :request="selectedRequest" :is-saving="isSaving" @close="requestStore.clearSelectedRequest" @review="handleReview" />
  </section>
</template>

<script setup>
import { storeToRefs } from 'pinia'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import DataTable from '../../components/common/DataTable.vue'
import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import SearchBar from '../../components/common/SearchBar.vue'
import Toast from '../../components/common/Toast.vue'
import SeatRequestReviewModal from '../../components/student/SeatRequestReviewModal.vue'
import { useAuthStore } from '../../stores/authStore'
import { useSeatRequestStore } from '../../stores/seatRequestStore'

const columns = [{ key: 'student', label: 'Student' }, { key: 'currentSeatNumber', label: 'Current Seat' }, { key: 'preference', label: 'Preference' }, { key: 'preferredShiftName', label: 'Shift' }, { key: 'submittedAt', label: 'Submitted' }, { key: 'status', label: 'Status' }]
const authStore = useAuthStore()
const requestStore = useSeatRequestStore()
const { currentUser } = storeToRefs(authStore)
const { requests, selectedRequest, isLoading, isSaving, errorMessage, pendingCount, approvedCount, rejectedCount } = storeToRefs(requestStore)
const searchQuery = ref('')
const statusFilter = ref('')
const shiftFilter = ref('')
const successMessage = ref('')
let toastTimer = null

const adminIdentity = computed(() => ({ id: currentUser.value?.id, name: currentUser.value?.name, libraryName: currentUser.value?.libraryName }))
const summaryItems = computed(() => [
  { label: 'Total Requests', value: requests.value.length, detail: 'All student requests', icon: 'T' },
  { label: 'Pending', value: pendingCount.value, detail: 'Awaiting review', icon: 'P' },
  { label: 'Approved', value: approvedCount.value, detail: 'Approved requests', icon: 'A' },
  { label: 'Rejected', value: rejectedCount.value, detail: 'Rejected requests', icon: 'R' },
])
const shiftOptions = computed(() => [...new Map(requests.value.map((request) => [request.preferredShiftId, { value: request.preferredShiftId, label: formatLabel(request.preferredShiftName) }])).values()])
const hasActiveFilters = computed(() => Boolean(searchQuery.value.trim() || statusFilter.value || shiftFilter.value))
const filteredRequests = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  return requests.value.filter((request) => {
    const searchable = [request.studentName, request.studentEmail, request.currentSeatNumber, request.preferredSeatNumber].join(' ').toLowerCase()
    return (!query || searchable.includes(query)) && (!statusFilter.value || request.status === statusFilter.value) && (!shiftFilter.value || request.preferredShiftId === shiftFilter.value)
  })
})

function formatLabel(value) { return String(value || '-').replace(/[-_]/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase()) }
function formatDate(value) { return value ? new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(value)) : '-' }
function statusClass(status) { return { approved: 'badge--success', pending: 'badge--warning', rejected: 'badge--cancelled', cancelled: 'badge--inactive' }[status] || 'badge--inactive' }
function clearFilters() { searchQuery.value = ''; statusFilter.value = ''; shiftFilter.value = '' }
function showSuccess(message) { successMessage.value = message; window.clearTimeout(toastTimer); toastTimer = window.setTimeout(() => { successMessage.value = '' }, 4000) }
async function loadRequests() { try { await requestStore.fetchRequests(adminIdentity.value) } catch { /* Store-owned errors are rendered above. */ } }
async function handleReview(payload) { if (!selectedRequest.value) return; try { const decision = payload.decision; await requestStore.reviewRequest(adminIdentity.value, selectedRequest.value.id, payload); requestStore.clearSelectedRequest(); showSuccess(`Seat request ${decision}. The student's allocation was not changed.`) } catch { /* Store-owned errors are rendered above. */ } }

onMounted(loadRequests)
onBeforeUnmount(() => window.clearTimeout(toastTimer))
</script>

<style scoped>
.seat-requests-page { display: grid; gap: var(--space-6); }
.seat-requests-page__header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-5); }
.seat-requests-page__title { margin: var(--space-1) 0 0; }
.seat-requests-page__description { margin: var(--space-2) 0 0; color: var(--color-text-muted); }
.seat-request-summary { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--space-4); }
.seat-request-summary .stat-card { display: grid; gap: var(--space-2); }
.seat-request-filters { display: grid; grid-template-columns: minmax(280px, 1.4fr) repeat(2, minmax(170px, .7fr)) auto; align-items: end; gap: var(--space-4); padding: var(--space-4); }
.seat-request-filters__field { display: grid; gap: var(--space-2); }
.seat-requests-page__loading { display: grid; min-height: 360px; place-items: center; }
.seat-request-list { overflow: hidden; }
.seat-request-list__header { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); padding: var(--space-5); border-bottom: 1px solid var(--color-divider); }
.student-cell, .preference-cell { display: grid; gap: var(--space-1); min-width: 0; }
.student-cell span, .preference-cell span { color: var(--color-text-muted); font-size: var(--font-size-xs); overflow-wrap: anywhere; }
.seat-request-list__cards { display: none; }
.seat-request-list__empty { padding: var(--space-6); color: var(--color-text-muted); text-align: center; }
.seat-request-card { display: grid; gap: var(--space-4); padding: var(--space-4); border-bottom: 1px solid var(--color-divider); }
.seat-request-card header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-3); }
.seat-request-card header div { display: grid; gap: var(--space-1); min-width: 0; }
.seat-request-card header div span { color: var(--color-text-muted); font-size: var(--font-size-xs); overflow-wrap: anywhere; }
.seat-request-card dl { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-3); margin: 0; }
.seat-request-card dl div { display: grid; gap: var(--space-1); }
.seat-request-card dt { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.seat-request-card dd { margin: 0; font-size: var(--font-size-sm); overflow-wrap: anywhere; }
@media (max-width: 1050px) { .seat-request-summary { grid-template-columns: repeat(2, minmax(0, 1fr)); } .seat-request-filters { grid-template-columns: repeat(2, minmax(0, 1fr)); } .seat-request-filters__search { grid-column: 1 / -1; } }
@media (max-width: 720px) { .seat-requests-page__header { flex-direction: column; } .seat-requests-page__header .btn { width: 100%; } .seat-request-filters { grid-template-columns: 1fr; } .seat-request-filters__search { grid-column: auto; } .seat-request-list__table { display: none; } .seat-request-list__cards { display: grid; } }
@media (max-width: 520px) { .seat-request-summary { grid-template-columns: 1fr; } }
</style>
