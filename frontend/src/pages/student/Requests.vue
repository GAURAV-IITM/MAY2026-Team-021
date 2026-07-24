<template>
  <section class="student-requests" aria-labelledby="student-requests-title">
    <header class="requests-header">
      <div><p class="text-label text-muted m-0">Seat Services</p><h1 id="student-requests-title" class="text-h2 requests-header__title">Seat Change Requests</h1><p class="requests-header__description">Ask the library team to review a different seat or shift.</p></div>
      <button class="btn btn--primary" type="button" :disabled="Boolean(pendingRequest) || isLoading" @click="isRequestModalOpen = true"><ClipboardPlus :size="18" aria-hidden="true" /> Request Change</button>
    </header>

    <Toast v-if="successMessage" type="success">{{ successMessage }}</Toast>
    <div v-if="errorMessage" class="alert alert--danger" role="alert"><span>{{ errorMessage }}</span><button class="btn btn--secondary btn--sm" type="button" @click="loadRequests">Retry</button></div>
    <div v-if="pendingRequest" class="alert alert--warning" role="status"><span>You already have a pending request. You can cancel it before submitting another.</span></div>
    <LoadingSpinner v-if="isLoading && requests.length === 0" label="Loading seat requests" />

    <template v-else>
      <StudentSummaryCards :items="summaryItems" aria-label="Seat request summary" />
      <section class="card request-history" aria-labelledby="request-history-title">
        <header class="request-history__header"><div><h2 id="request-history-title" class="text-h4 m-0">Request History</h2><p class="text-small text-muted m-0">The library owner reviews and resolves each request.</p></div><span class="text-small text-muted">{{ requests.length }} requests</span></header>
        <div v-if="requests.length === 0" class="request-history__empty"><ClipboardList :size="30" aria-hidden="true" /><strong>No seat requests yet</strong><p class="text-muted m-0">Your requests and their review status will appear here.</p><button class="btn btn--primary" type="button" @click="isRequestModalOpen = true"><ClipboardPlus :size="17" aria-hidden="true" /> Request Change</button></div>
        <div v-else class="request-list">
          <article v-for="request in requests" :key="request.id" class="request-card">
            <header><div><span class="text-small text-muted">Submitted {{ formatDate(request.submittedAt) }}</span><h3>{{ request.preferredSeatNumber || 'Any available seat' }}</h3></div><span class="badge" :class="requestStatusClass(request.status)">{{ formatLabel(request.status) }}</span></header>
            <dl>
              <div><dt>Preferred Shift</dt><dd>{{ formatLabel(request.preferredShiftName) }}</dd></div>
              <div><dt>Preferred Floor</dt><dd>{{ request.preferredFloor ? `Floor ${request.preferredFloor}` : 'No preference' }}</dd></div>
              <div><dt>Current Seat</dt><dd>{{ request.currentSeatNumber || 'Not assigned' }}</dd></div>
              <div><dt>Resolved</dt><dd>{{ request.resolvedAt ? formatDate(request.resolvedAt) : 'Awaiting review' }}</dd></div>
            </dl>
            <div class="request-card__reason"><span class="text-label text-muted">Reason</span><p class="m-0">{{ request.reason }}</p></div>
            <div v-if="request.adminNote" class="request-card__note"><span class="text-label">Library Response</span><p class="m-0">{{ request.adminNote }}</p></div>
            <footer v-if="request.status === 'pending'"><button class="btn btn--danger btn--sm" type="button" @click="requestToCancel = request">Cancel Request</button></footer>
          </article>
        </div>
      </section>
    </template>

    <SeatRequestModal v-if="isRequestModalOpen" :current-seat-number="seat?.seatNumber" :shifts="shifts" :is-saving="isSaving" @close="isRequestModalOpen = false" @submit="handleCreateRequest" />
    <ConfirmDialog :is-open="Boolean(requestToCancel)" title="Cancel seat request?" message="This request will no longer be reviewed by the library team." confirm-label="Cancel Request" confirming-label="Cancelling" :is-confirming="isSaving" @cancel="requestToCancel = null" @confirm="handleCancelRequest" />
  </section>
</template>

<script setup>
import { CircleCheckBig, CircleX, ClipboardList, ClipboardPlus, Clock3 } from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import ConfirmDialog from '../../components/common/ConfirmDialog.vue'
import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import Toast from '../../components/common/Toast.vue'
import SeatRequestModal from '../../components/student/SeatRequestModal.vue'
import StudentSummaryCards from '../../components/student/StudentSummaryCards.vue'
import { useAuthStore } from '../../stores/authStore'
import { useStudentPortalStore } from '../../stores/studentPortalStore'

const authStore = useAuthStore()
const portalStore = useStudentPortalStore()
const { currentUser } = storeToRefs(authStore)
const { requests, shifts, seat, pendingRequest, isLoading, isSaving, errorMessage } = storeToRefs(portalStore)
const isRequestModalOpen = ref(false)
const requestToCancel = ref(null)
const successMessage = ref('')
let successTimer = null

const summaryItems = computed(() => {
  const count = (status) => requests.value.filter((request) => request.status === status).length
  return [
    { label: 'Total Requests', value: requests.value.length, detail: 'All submitted requests', icon: ClipboardList, tone: 'primary' },
    { label: 'Pending', value: count('pending'), detail: 'Awaiting library review', icon: Clock3, tone: 'warning' },
    { label: 'Approved', value: count('approved'), detail: 'Accepted requests', icon: CircleCheckBig, tone: 'success' },
    { label: 'Closed', value: count('rejected') + count('cancelled'), detail: 'Rejected or cancelled', icon: CircleX, tone: 'info' },
  ]
})

function formatLabel(value) { return String(value || '-').replace(/[-_]/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase()) }
function formatDate(value) { return value ? new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(value)) : '-' }
function requestStatusClass(status) { return { approved: 'badge--success', pending: 'badge--warning', rejected: 'badge--cancelled', cancelled: 'badge--inactive' }[status] || 'badge--inactive' }
function showSuccess(message) { successMessage.value = message; window.clearTimeout(successTimer); successTimer = window.setTimeout(() => { successMessage.value = '' }, 3500) }
async function loadRequests() { try { await portalStore.fetchRequests(currentUser.value?.id); if (!seat.value) await portalStore.fetchSeat(currentUser.value?.id) } catch { /* Store-owned errors are rendered above. */ } }
async function handleCreateRequest(payload) { try { await portalStore.createSeatRequest(currentUser.value?.id, payload); isRequestModalOpen.value = false; showSuccess('Your seat change request was submitted.') } catch { /* Store-owned errors are rendered above. */ } }
async function handleCancelRequest() { if (!requestToCancel.value) return; try { await portalStore.cancelSeatRequest(currentUser.value?.id, requestToCancel.value.id); requestToCancel.value = null; showSuccess('Your seat change request was cancelled.') } catch { /* Store-owned errors are rendered above. */ } }

onMounted(loadRequests)
onBeforeUnmount(() => window.clearTimeout(successTimer))
</script>

<style scoped>
.student-requests { display: grid; gap: var(--space-6); }
.requests-header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-5); }
.requests-header__title { margin: var(--space-1) 0 0; }
.requests-header__description { margin: var(--space-2) 0 0; color: var(--color-text-muted); }
.request-history { overflow: hidden; }
.request-history__header { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); padding: var(--space-5); border-bottom: 1px solid var(--color-divider); }
.request-history__empty { display: grid; justify-items: center; gap: var(--space-3); padding: var(--space-8); text-align: center; }
.request-list { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-4); padding: var(--space-5); }
.request-card { display: grid; gap: var(--space-4); min-width: 0; padding: var(--space-5); border: 1px solid var(--color-border); border-radius: var(--radius-md); }
.request-card header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-3); }
.request-card h3 { margin: var(--space-1) 0 0; font-size: var(--font-size-h5); }
.request-card dl { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-3); margin: 0; }
.request-card dl div { display: grid; gap: var(--space-1); }
.request-card dt { color: var(--color-text-muted); font-size: var(--font-size-xs); }
.request-card dd { margin: 0; font-size: var(--font-size-sm); }
.request-card__reason, .request-card__note { display: grid; gap: var(--space-2); padding: var(--space-3); border-radius: var(--radius-md); background: var(--color-surface-secondary); }
.request-card__note { border-left: 3px solid var(--color-primary); }
.request-card footer { display: flex; justify-content: flex-end; padding-top: var(--space-2); border-top: 1px solid var(--color-divider); }
@media (max-width: 900px) { .request-list { grid-template-columns: 1fr; } }
@media (max-width: 600px) { .requests-header { flex-direction: column; } .requests-header .btn { width: 100%; } .request-history__header { align-items: flex-start; } .request-list { padding: var(--space-3); } .request-card dl { grid-template-columns: 1fr; } }
</style>
