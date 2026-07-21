<template>
  <section class="my-seat-page" aria-labelledby="my-seat-title">
    <header class="my-seat-page__header">
      <div><p class="text-label text-muted m-0">Seat Allocation</p><h1 id="my-seat-title" class="text-h2 my-seat-page__title">My Seat</h1><p class="my-seat-page__description">View your assigned seat, shifts, and active allocation period.</p></div>
      <RouterLink class="btn btn--secondary" :to="{ name: 'studentRequests' }"><ClipboardPlus :size="17" aria-hidden="true" /> Request a Change</RouterLink>
    </header>

    <div v-if="errorMessage" class="alert alert--danger" role="alert"><div><strong>Unable to load your seat.</strong><p class="m-0">{{ errorMessage }}</p></div><button class="btn btn--secondary btn--sm" type="button" @click="loadSeat">Retry</button></div>
    <div v-if="isLoading && !seat" class="my-seat-page__loading"><LoadingSpinner label="Loading your seat allocation" /></div>

    <template v-else>
      <SeatAllocationCard :seat="seat" :allocations="allocations" />

      <div v-if="seat" class="my-seat-page__details-grid">
        <section class="card my-seat-panel" aria-labelledby="seat-details-title">
          <header class="my-seat-panel__header"><h2 id="seat-details-title">Seat Details</h2></header>
          <dl class="my-seat-panel__details">
            <div><dt>Seat Number</dt><dd>{{ seat.seatNumber }}</dd></div>
            <div><dt>Floor</dt><dd>Floor {{ seat.floor }}</dd></div>
            <div><dt>Seat Type</dt><dd>{{ seat.seatType }}</dd></div>
            <div><dt>Status</dt><dd><span class="badge badge--success">Active</span></dd></div>
          </dl>
        </section>

        <section class="card my-seat-panel" aria-labelledby="seat-guidelines-title">
          <header class="my-seat-panel__header"><h2 id="seat-guidelines-title">Seat Guidelines</h2></header>
          <ul class="my-seat-page__guidelines">
            <li>Use the seat only during your allocated shift.</li>
            <li>Keep the desk clean and remove belongings after your shift.</li>
            <li>Report maintenance issues to the library administrator.</li>
            <li>Submit a request before changing your seat or shift.</li>
          </ul>
        </section>
      </div>

      <section v-if="seat?.notes" class="alert alert--info" aria-label="Seat note"><div><strong>Seat Note</strong><p class="m-0">{{ seat.notes }}</p></div></section>
    </template>
  </section>
</template>

<script setup>
import { ClipboardPlus } from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import SeatAllocationCard from '../../components/student/SeatAllocationCard.vue'
import { useAuthStore } from '../../stores/authStore'
import { useStudentPortalStore } from '../../stores/studentPortalStore'

const authStore = useAuthStore(); const portalStore = useStudentPortalStore()
const { currentUser } = storeToRefs(authStore)
const { seat, allocations, isLoading, errorMessage } = storeToRefs(portalStore)
const studentId = computed(() => currentUser.value?.id || '')
async function loadSeat() { if (!studentId.value) return; try { await portalStore.fetchSeat(studentId.value) } catch { /* Store-owned errors are rendered above. */ } }
onMounted(loadSeat)
</script>

<style scoped>
.my-seat-page { display: grid; gap: var(--space-6); }
.my-seat-page__header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-5); }
.my-seat-page__title { margin: var(--space-1) 0 0; }
.my-seat-page__description { margin: var(--space-2) 0 0; color: var(--color-text-muted); }
.my-seat-page__loading { display: grid; min-height: 360px; place-items: center; border: 1px solid var(--color-border); border-radius: var(--radius-lg); background: var(--color-surface-elevated); }
.my-seat-page__details-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-4); }
.my-seat-panel { overflow: hidden; }
.my-seat-panel:hover { box-shadow: var(--shadow-sm); }
.my-seat-panel__header { padding: var(--space-4) var(--space-5); border-bottom: 1px solid var(--color-divider); }
.my-seat-panel__header h2 { margin: 0; font-size: var(--font-size-h5); }
.my-seat-panel__details { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-5); padding: var(--space-5); margin: 0; }
.my-seat-panel__details div { display: grid; gap: var(--space-1); }
.my-seat-panel__details dt { color: var(--color-text-muted); font-size: var(--font-size-sm); }
.my-seat-panel__details dd { margin: 0; font-weight: var(--font-weight-semibold); }
.my-seat-page__guidelines { display: grid; gap: var(--space-3); padding: var(--space-5) var(--space-5) var(--space-5) var(--space-10); margin: 0; color: var(--color-text-secondary); }
@media (max-width: 800px) { .my-seat-page__details-grid { grid-template-columns: 1fr; } }
@media (max-width: 600px) { .my-seat-page__header { flex-direction: column; } .my-seat-panel__details { grid-template-columns: 1fr; } }
</style>
