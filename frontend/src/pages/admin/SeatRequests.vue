<template>
  <section class="seat-requests-page" aria-labelledby="seat-requests-title">
    <header class="seat-requests-page__header">
      <div>
        <p class="text-label text-muted m-0">Student Management</p>
        <h1 id="seat-requests-title" class="text-h2 seat-requests-page__title">Seat Change Requests</h1>
        <p class="seat-requests-page__description">Review requests without changing the student’s current allocation.</p>
      </div>
      <button class="btn btn--secondary" type="button" :disabled="isLoading" @click="loadRequests">
        <RefreshCw :size="17" :class="{ 'seat-requests-page__spin': isLoading }" />
        {{ isLoading ? 'Refreshing...' : 'Refresh' }}
      </button>
    </header>

    <Toast v-if="successMessage" type="success">{{ successMessage }}</Toast>

    <section class="seat-request-summary" aria-label="Seat request summary">
      <article v-for="item in summaryItems" :key="item.label" class="stat-card stat-card--dashboard">
        <div class="stat-card__header"><span class="text-label text-muted">{{ item.label }}</span><span class="stat-card__icon"><component :is="item.icon" :size="20" /></span></div>
        <strong class="stat-card__value">{{ item.value }}</strong>
        <span class="text-small text-muted">{{ item.detail }}</span>
      </article>
    </section>

    <section class="card seat-request-filters" aria-label="Seat request filters">
      <SearchBar :model-value="filters.search" placeholder="Search student, enrollment number, seat, or reason" @update:model-value="updateFilter('search', $event)" @clear="updateFilter('search', '')" />
      <label class="seat-request-filters__field">
        <span class="form-label">Status</span>
        <select class="form-select" :value="filters.status" @change="updateFilter('status', $event.target.value)">
          <option value="">All statuses</option>
          <option value="pending">Pending</option>
          <option value="approved">Approved</option>
          <option value="rejected">Rejected</option>
        </select>
      </label>
      <button class="btn btn--secondary" type="button" :disabled="!hasActiveFilters" @click="clearFilters"><RotateCcw :size="16" /> Clear Filters</button>
    </section>

    <div v-if="errorMessage && !selectedRequest" class="alert alert--danger" role="alert">
      <div><strong>Unable to load seat requests.</strong><p class="m-0">{{ errorMessage }}<small v-if="errorRequestId"> Request ID: {{ errorRequestId }}</small></p></div>
      <button class="btn btn--secondary btn--sm" type="button" @click="loadRequests">Retry</button>
    </div>

    <div v-if="isLoading && !hasLoaded" class="seat-requests-page__loading"><LoadingSpinner label="Loading seat requests" /></div>

    <section v-else class="card seat-request-list" aria-labelledby="seat-request-list-title">
      <header class="seat-request-list__header">
        <div><h2 id="seat-request-list-title" class="text-h4 m-0">Requests</h2><p class="text-small text-muted m-0">{{ pagination.totalItems }} matching records</p></div>
        <span v-if="pendingCount" class="badge badge--warning">{{ pendingCount }} Pending</span>
      </header>

      <DataTable class="seat-request-list__table" :columns="columns" :rows="requests" aria-label="Student seat change requests">
        <template #empty>{{ emptyMessage }}</template>
        <template #cell-student="{ row }"><div class="student-cell"><strong>{{ row.studentName }}</strong><span>{{ row.enrollmentNumber }}</span></div></template>
        <template #cell-current="{ row }"><div class="student-cell"><strong>{{ row.currentSeatNumber || 'Not assigned' }}</strong><span>{{ row.currentShiftName || 'No active shift' }}</span></div></template>
        <template #cell-preference="{ row }"><div class="preference-cell"><strong>{{ row.preferredSeatNumber || 'Any seat' }}</strong><span>{{ row.preferredFloorName || 'Any floor' }} · {{ row.preferredShiftName }}</span></div></template>
        <template #cell-submittedAt="{ value }">{{ formatDate(value) }}</template>
        <template #cell-status="{ value }"><span class="badge" :class="statusClass(value)">{{ formatLabel(value) }}</span></template>
        <template #actions="{ row }"><button class="btn btn--secondary btn--sm" type="button" @click="requestStore.selectRequest(row)"><ClipboardCheck v-if="row.status === 'pending'" :size="15" /><Eye v-else :size="15" />{{ row.status === 'pending' ? 'Review' : 'View' }}</button></template>
      </DataTable>

      <div class="seat-request-list__cards">
        <p v-if="requests.length === 0" class="seat-request-list__empty">{{ emptyMessage }}</p>
        <article v-for="request in requests" :key="request.id" class="seat-request-card">
          <header><div><strong>{{ request.studentName }}</strong><span>{{ request.enrollmentNumber }}</span></div><span class="badge" :class="statusClass(request.status)">{{ formatLabel(request.status) }}</span></header>
          <dl><div><dt>Current</dt><dd>{{ request.currentSeatNumber || 'Not assigned' }} · {{ request.currentShiftName || '-' }}</dd></div><div><dt>Preferred</dt><dd>{{ request.preferredSeatNumber || 'Any seat' }} · {{ request.preferredShiftName }}</dd></div><div><dt>Submitted</dt><dd>{{ formatDate(request.submittedAt) }}</dd></div><div><dt>Reviewed by</dt><dd>{{ request.reviewedBy?.name || '-' }}</dd></div></dl>
          <button class="btn btn--secondary" type="button" @click="requestStore.selectRequest(request)"><ClipboardCheck v-if="request.status === 'pending'" :size="16" /><Eye v-else :size="16" />{{ request.status === 'pending' ? 'Review Request' : 'View Details' }}</button>
        </article>
      </div>

      <footer v-if="pagination.totalItems" class="seat-request-list__pagination">
        <span>Showing {{ paginationStart }}–{{ paginationEnd }} of {{ pagination.totalItems }}</span>
        <Pagination :current-page="pagination.page" :total-pages="Math.max(1, pagination.totalPages)" @update:current-page="changePage" />
      </footer>
    </section>

    <SeatRequestReviewModal
      :request="selectedRequest"
      :is-saving="isSaving"
      :server-error="selectedRequest ? errorMessage : ''"
      :error-code="errorCode"
      :request-id="errorRequestId"
      @close="requestStore.clearSelectedRequest"
      @review="handleReview"
    />
  </section>
</template>

<script setup>
import { CircleCheckBig, CircleX, ClipboardCheck, ClipboardList, Clock3, Eye, RefreshCw, RotateCcw } from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import DataTable from '../../components/common/DataTable.vue'
import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import Pagination from '../../components/common/Pagination.vue'
import SearchBar from '../../components/common/SearchBar.vue'
import Toast from '../../components/common/Toast.vue'
import SeatRequestReviewModal from '../../components/student/SeatRequestReviewModal.vue'
import { useSeatRequestStore } from '../../stores/seatRequestStore'

const columns = [{ key: 'student', label: 'Student' }, { key: 'current', label: 'Current Allocation' }, { key: 'preference', label: 'Requested Change' }, { key: 'submittedAt', label: 'Submitted' }, { key: 'status', label: 'Status' }]
const requestStore = useSeatRequestStore()
const { requests, selectedRequest, summary, pagination, filters, isLoading, isSaving, errorMessage, errorRequestId, errorCode, pendingCount, approvedCount, rejectedCount } = storeToRefs(requestStore)
const successMessage = ref('')
const hasLoaded = ref(false)
let filterTimer
let toastTimer

const summaryItems = computed(() => [
  { label: 'Total Requests', value: summary.value.total, detail: 'Complete request history', icon: ClipboardList },
  { label: 'Pending', value: pendingCount.value, detail: 'Awaiting review', icon: Clock3 },
  { label: 'Approved', value: approvedCount.value, detail: 'Decision recorded', icon: CircleCheckBig },
  { label: 'Rejected', value: rejectedCount.value, detail: 'Decision recorded', icon: CircleX },
])
const hasActiveFilters = computed(() => Boolean(filters.value.search || filters.value.status))
const emptyMessage = computed(() => filters.value.status ? `No ${filters.value.status} seat-change requests found.` : filters.value.search ? 'No requests match this search.' : 'No seat-change requests found.')
const paginationStart = computed(() => pagination.value.totalItems ? (pagination.value.page - 1) * pagination.value.pageSize + 1 : 0)
const paginationEnd = computed(() => Math.min(pagination.value.page * pagination.value.pageSize, pagination.value.totalItems))

function formatLabel(value) { return String(value || '-').replace(/[-_]/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase()) }
function formatDate(value) { return value ? new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(value)) : '-' }
function statusClass(status) { return { approved: 'badge--success', pending: 'badge--warning', rejected: 'badge--cancelled', cancelled: 'badge--inactive' }[status] || 'badge--inactive' }
async function loadRequests() { try { await requestStore.fetchRequests(); hasLoaded.value = true } catch { hasLoaded.value = true } }
function updateFilter(key, value) { filters.value = { ...filters.value, [key]: value, page: 1 }; clearTimeout(filterTimer); filterTimer = setTimeout(loadRequests, key === 'search' ? 300 : 0) }
function clearFilters() { requestStore.clearFilters(); loadRequests() }
async function changePage(page) { try { await requestStore.setPage(page) } catch { /* Store error is visible. */ } }
function showSuccess(message) { successMessage.value = message; clearTimeout(toastTimer); toastTimer = setTimeout(() => { successMessage.value = '' }, 4000) }
async function handleReview(payload) {
  if (!selectedRequest.value) return
  try {
    const response = await requestStore.reviewRequest(selectedRequest.value.id, payload)
    requestStore.clearSelectedRequest()
    showSuccess(response.message)
  } catch { /* The dialog keeps the backend error and entered note visible. */ }
}

onMounted(loadRequests)
onBeforeUnmount(() => { clearTimeout(filterTimer); clearTimeout(toastTimer) })
</script>

<style scoped>
.seat-requests-page { display: grid; gap: var(--space-6); }
.seat-requests-page__header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-5); }
.seat-requests-page__title { margin: var(--space-1) 0 0; }
.seat-requests-page__description { margin: var(--space-2) 0 0; color: var(--color-text-muted); }
.seat-request-summary { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: var(--space-4); }
.seat-request-summary .stat-card { display: grid; gap: var(--space-2); }
.seat-request-filters { display: grid; grid-template-columns: minmax(280px, 1fr) minmax(170px, 220px) auto; align-items: end; gap: var(--space-4); padding: var(--space-4); }
.seat-request-filters__field { display: grid; gap: var(--space-2); }
.seat-requests-page__loading { display: grid; min-height: 360px; place-items: center; }
.seat-requests-page__spin { animation: ds-spin var(--transition-slow) linear infinite; }
.seat-request-list { overflow: hidden; }
.seat-request-list__header, .seat-request-list__pagination { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); padding: var(--space-5); border-bottom: 1px solid var(--color-divider); }
.seat-request-list__pagination { border-top: 1px solid var(--color-divider); border-bottom: 0; color: var(--color-text-muted); font-size: var(--font-size-sm); }
.student-cell, .preference-cell { display: grid; gap: var(--space-1); min-width: 0; }
.student-cell span, .preference-cell span { color: var(--color-text-muted); font-size: var(--font-size-xs); overflow-wrap: anywhere; }
.seat-request-list__cards { display: none; }
.seat-request-list__empty { padding: var(--space-6); color: var(--color-text-muted); text-align: center; }
.seat-request-card { display: grid; gap: var(--space-4); padding: var(--space-4); border-bottom: 1px solid var(--color-divider); }
.seat-request-card header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-3); }
.seat-request-card header div { display: grid; gap: var(--space-1); min-width: 0; }
.seat-request-card header div span { color: var(--color-text-muted); font-size: var(--font-size-xs); overflow-wrap: anywhere; }
.seat-request-card dl { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-3); margin: 0; }
.seat-request-card dt { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.seat-request-card dd { margin: 0; font-size: var(--font-size-sm); overflow-wrap: anywhere; }
@media (max-width: 900px) { .seat-request-summary { grid-template-columns: repeat(2, minmax(0, 1fr)); } .seat-request-filters { grid-template-columns: 1fr 1fr; } }
@media (max-width: 720px) { .seat-requests-page__header { flex-direction: column; } .seat-requests-page__header .btn { width: 100%; } .seat-request-filters { grid-template-columns: 1fr; } .seat-request-list__table { display: none; } .seat-request-list__cards { display: grid; } .seat-request-list__pagination { align-items: stretch; flex-direction: column; } }
@media (max-width: 520px) { .seat-request-summary { grid-template-columns: 1fr; } .seat-request-card dl { grid-template-columns: 1fr; } }
</style>
