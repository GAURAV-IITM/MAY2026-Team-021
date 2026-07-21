<template>
  <section class="admin-announcements" aria-labelledby="admin-announcements-title">
    <header class="admin-announcements__header">
      <div><p class="text-label text-muted m-0">Student Communication</p><h1 id="admin-announcements-title">Announcements</h1><p>Create and manage notices visible in the Student Portal.</p></div>
      <div><button class="btn btn--secondary btn--icon" type="button" :disabled="isLoading" title="Refresh announcements" aria-label="Refresh announcements" @click="loadAnnouncements"><RefreshCw :size="18" :class="{ 'admin-announcements__spin': isLoading }" /></button><button class="btn btn--primary" type="button" @click="openCreate"><Plus :size="18" /> Create Announcement</button></div>
    </header>

    <div v-if="errorMessage" class="alert alert--danger admin-announcements__error" role="alert"><div><strong>Announcement action failed.</strong><p class="m-0">{{ errorMessage }}</p></div><button class="btn btn--secondary btn--sm" type="button" @click="loadAnnouncements">Retry</button></div>

    <div v-if="isLoading && !hasLoaded" class="admin-announcements__loading"><LoadingSpinner label="Loading announcements" /></div>

    <template v-else>
      <AnnouncementSummaryCards :items="summaryItems" />
      <AnnouncementFilters :filters="filters" :categories="categories" @update:filters="updateFilters" @clear="clearFilters" />

      <section class="admin-announcements__records" aria-labelledby="announcement-list-title">
        <header><div><h2 id="announcement-list-title">Announcement List</h2><p>{{ announcements.length }} matching record{{ announcements.length === 1 ? '' : 's' }}</p></div></header>
        <AnnouncementTable :announcements="announcements" :categories="categories" :audiences="audiences" @action="handleRowAction">
          <template #empty><EmptyState title="No announcements found" description="Create an announcement or clear the current filters."><template #icon><Megaphone :size="28" /></template><template #primary-action><button class="btn btn--primary" type="button" @click="openCreate">Create Announcement</button></template><template #secondary-action><button v-if="hasFilters" class="btn btn--secondary" type="button" @click="clearFilters">Clear Filters</button></template></EmptyState></template>
        </AnnouncementTable>
      </section>
    </template>

    <AnnouncementFormModal :is-open="isFormOpen" :mode="formMode" :announcement="selectedAnnouncement" :categories="categories" :audiences="audiences" :is-submitting="isSaving" @close="closeForm" @save="saveAnnouncement" />
    <ConfirmDialog :is-open="Boolean(pendingConfirmation)" :title="confirmationTitle" :message="confirmationMessage" :confirm-label="pendingConfirmation?.action === 'delete' ? 'Delete' : 'Archive'" :confirming-label="pendingConfirmation?.action === 'delete' ? 'Deleting' : 'Archiving'" :is-confirming="isSaving" @cancel="pendingConfirmation = null" @confirm="confirmAction" />
    <Toast v-if="toastMessage" :type="toastType">{{ toastMessage }}</Toast>
  </section>
</template>

<script setup>
import { CalendarClock, FileText, Megaphone, Plus, RefreshCw, Send } from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import AnnouncementFilters from '../../components/announcement/AnnouncementFilters.vue'
import AnnouncementFormModal from '../../components/announcement/AnnouncementFormModal.vue'
import AnnouncementSummaryCards from '../../components/announcement/AnnouncementSummaryCards.vue'
import AnnouncementTable from '../../components/announcement/AnnouncementTable.vue'
import ConfirmDialog from '../../components/common/ConfirmDialog.vue'
import EmptyState from '../../components/common/EmptyState.vue'
import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import Toast from '../../components/common/Toast.vue'
import { useAnnouncementStore } from '../../stores/announcementStore.js'
import { useAuthStore } from '../../stores/authStore.js'

const store = useAnnouncementStore()
const authStore = useAuthStore()
const { announcements, summary, categories, audiences, filters, isLoading, isSaving, errorMessage } = storeToRefs(store)
const { currentUser } = storeToRefs(authStore)
const hasLoaded = ref(false)
const isFormOpen = ref(false)
const formMode = ref('create')
const selectedAnnouncement = ref(null)
const pendingConfirmation = ref(null)
const toastMessage = ref('')
const toastType = ref('success')
let filterTimer
let toastTimer

const admin = computed(() => currentUser.value || {})
const hasFilters = computed(() => Object.values(filters.value).some(Boolean))
const summaryItems = computed(() => [
  { label: 'Published', value: summary.value.published, detail: 'Visible in Student Portal', icon: Send, tone: 'success' },
  { label: 'Drafts', value: summary.value.drafts, detail: 'Not visible to students', icon: FileText, tone: 'warning' },
  { label: 'Scheduled', value: summary.value.scheduled, detail: 'Waiting to be published', icon: CalendarClock, tone: 'info' },
  { label: 'Important', value: summary.value.important, detail: 'Active priority notices', icon: Megaphone, tone: 'primary' },
])
const confirmationTitle = computed(() => pendingConfirmation.value?.action === 'delete' ? `Delete ${pendingConfirmation.value?.announcement.title}?` : `Archive ${pendingConfirmation.value?.announcement.title}?`)
const confirmationMessage = computed(() => pendingConfirmation.value?.action === 'delete' ? 'This draft or archived announcement will be permanently removed.' : 'Students will no longer see this announcement in their portal.')

function showToast(message, type = 'success') { globalThis.clearTimeout(toastTimer); toastMessage.value = message; toastType.value = type; toastTimer = globalThis.setTimeout(() => { toastMessage.value = '' }, 3200) }
async function loadAnnouncements() {
  try { await store.fetchAnnouncements(admin.value); hasLoaded.value = true } catch { showToast(errorMessage.value, 'error') }
}
function updateFilters(nextFilters) {
  filters.value = nextFilters
  globalThis.clearTimeout(filterTimer)
  filterTimer = globalThis.setTimeout(loadAnnouncements, nextFilters.search ? 300 : 0)
}
function clearFilters() { store.clearFilters(); loadAnnouncements() }
function openCreate() { formMode.value = 'create'; selectedAnnouncement.value = null; isFormOpen.value = true }
function openEdit(announcement) { formMode.value = 'edit'; selectedAnnouncement.value = announcement; isFormOpen.value = true }
function closeForm() { if (!isSaving.value) isFormOpen.value = false }
async function saveAnnouncement(payload) {
  try {
    if (formMode.value === 'edit') await store.updateAnnouncement(admin.value, selectedAnnouncement.value.id, payload)
    else await store.createAnnouncement(admin.value, payload)
    isFormOpen.value = false
    showToast(formMode.value === 'edit' ? 'Announcement updated successfully.' : payload.status === 'draft' ? 'Draft saved successfully.' : 'Announcement created successfully.')
  } catch { showToast(errorMessage.value, 'error') }
}
async function handleRowAction(announcement, action) {
  if (action === 'edit') return openEdit(announcement)
  if (action === 'publish') {
    try { await store.publishAnnouncement(admin.value, announcement.id); showToast('Announcement published successfully.') } catch { showToast(errorMessage.value, 'error') }
    return
  }
  pendingConfirmation.value = { announcement, action }
}
async function confirmAction() {
  const pending = pendingConfirmation.value
  if (!pending) return
  try {
    if (pending.action === 'delete') await store.deleteAnnouncement(admin.value, pending.announcement.id)
    else await store.archiveAnnouncement(admin.value, pending.announcement.id)
    showToast(pending.action === 'delete' ? 'Announcement deleted.' : 'Announcement archived.')
    pendingConfirmation.value = null
  } catch { showToast(errorMessage.value, 'error') }
}

onMounted(loadAnnouncements)
onBeforeUnmount(() => { globalThis.clearTimeout(filterTimer); globalThis.clearTimeout(toastTimer) })
</script>

<style scoped>
.admin-announcements { display: grid; gap: var(--space-5); }
.admin-announcements__header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-5); }
.admin-announcements__header h1 { margin: var(--space-1) 0 0; font-size: var(--font-size-h2); }
.admin-announcements__header p:not(.text-label) { margin: var(--space-2) 0 0; color: var(--color-text-muted); }
.admin-announcements__header > div:last-child { display: flex; gap: var(--space-2); }
.admin-announcements__error { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); }
.admin-announcements__loading { display: grid; min-height: 420px; place-items: center; border: 1px solid var(--color-border); border-radius: var(--radius-md); background: var(--color-surface-elevated); }
.admin-announcements__records { min-width: 0; }
.admin-announcements__records > header { padding: var(--space-4) var(--space-5); border: 1px solid var(--color-border); border-bottom: 0; border-radius: var(--radius-md) var(--radius-md) 0 0; background: var(--color-surface-elevated); }
.admin-announcements__records > header h2, .admin-announcements__records > header p { margin: 0; }
.admin-announcements__records > header h2 { font-size: var(--font-size-h5); }
.admin-announcements__records > header p { margin-top: 2px; color: var(--color-text-muted); font-size: var(--font-size-sm); }
.admin-announcements__spin { animation: announcements-spin 700ms linear infinite; }
@keyframes announcements-spin { to { transform: rotate(360deg); } }
@media (max-width: 700px) { .admin-announcements__header { align-items: stretch; flex-direction: column; } .admin-announcements__header > div:last-child { display: grid; grid-template-columns: 40px minmax(0, 1fr); } .admin-announcements__records > header { border-bottom: 1px solid var(--color-border); border-radius: var(--radius-md); margin-bottom: var(--space-3); } }
@media (max-width: 480px) { .admin-announcements__header h1 { font-size: var(--font-size-h3); } .admin-announcements__header .btn--icon { width: 40px; } .admin-announcements__error { align-items: stretch; flex-direction: column; } }
</style>
