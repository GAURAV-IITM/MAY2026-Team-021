<template>
  <section class="library-management" aria-labelledby="library-management-title">
    <header class="library-management__header">
      <div>
        <p class="text-label text-muted m-0">Platform Management</p>
        <h1 id="library-management-title" class="text-h2 library-management__title">
          Registered Libraries
        </h1>
        <p class="library-management__description">
          Review registrations and maintain library access across the platform.
        </p>
      </div>
      <button class="btn btn--primary" type="button" @click="openCreateModal">
        <Plus :size="18" aria-hidden="true" /> Add Library
      </button>
    </header>

    <Toast v-if="successMessage" type="success">{{ successMessage }}</Toast>

    <div v-if="errorMessage" class="alert alert--danger" role="alert">
      <div>
        <strong>Unable to complete the library request.</strong>
        <p class="m-0">{{ errorMessage }}</p>
      </div>
      <button class="btn btn--secondary btn--sm" type="button" @click="loadLibraries">
        Retry
      </button>
    </div>

    <PlatformMetricCards :items="summaryItems" aria-label="Library summary" />

    <section class="card library-management__filters" aria-label="Library filters">
      <SearchBar
        v-model="searchQuery"
        placeholder="Search by library, owner, city, or code"
        @clear="searchQuery = ''"
      />
      <div class="library-management__filter">
        <label class="form-label" for="library-status-filter">Status</label>
        <select id="library-status-filter" v-model="statusFilter" class="form-select">
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="pending">Pending</option>
          <option value="suspended">Suspended</option>
        </select>
      </div>
      <div class="library-management__filter">
        <label class="form-label" for="library-state-filter">State</label>
        <select id="library-state-filter" v-model="stateFilter" class="form-select">
          <option value="">All states</option>
          <option v-for="state in states" :key="state" :value="state">{{ state }}</option>
        </select>
      </div>
      <button
        class="btn btn--secondary"
        type="button"
        :disabled="!hasFilters"
        @click="clearFilters"
      >
        <RotateCcw :size="16" aria-hidden="true" /> Clear Filters
      </button>
    </section>

    <div v-if="isInitialLoading" class="library-management__loading">
      <LoadingSpinner label="Loading libraries" />
    </div>

    <template v-else>
      <EmptyState
        v-if="filteredLibraries.length === 0"
        title="No libraries found"
        description="Adjust the filters or register a new library."
      >
        <template #icon><Building2 :size="27" /></template>
        <template #primary-action>
          <button class="btn btn--primary" type="button" @click="openCreateModal">
            <Plus :size="17" aria-hidden="true" /> Add Library
          </button>
        </template>
        <template #secondary-action>
          <button v-if="hasFilters" class="btn btn--secondary" type="button" @click="clearFilters">
            Clear Filters
          </button>
          <span v-else></span>
        </template>
      </EmptyState>

      <template v-else>
        <div class="library-management__desktop-table">
          <DataTable
            :columns="columns"
            :rows="paginatedLibraries"
            aria-label="Registered libraries"
          >
            <template #cell-name="{ row }">
              <div class="library-management__primary-cell">
                <strong>{{ row.name }}</strong>
                <span>{{ row.code }}</span>
              </div>
            </template>
            <template #cell-location="{ row }">{{ row.city }}, {{ row.state }}</template>
            <template #cell-ownerName="{ value }">{{ value || 'Not assigned' }}</template>
            <template #cell-studentCount="{ value }">{{ formatNumber(value) }}</template>
            <template #cell-status="{ value }">
              <span class="badge" :class="getStatusClass(value)">{{ formatLabel(value) }}</span>
            </template>
            <template #cell-lastActivityAt="{ value }">{{ formatDate(value) }}</template>
            <template #actions="{ row }">
              <div class="library-management__row-actions">
                <button class="btn btn--outline btn--sm" type="button" @click="openEditModal(row)">
                  <Pencil :size="15" aria-hidden="true" /> Edit
                </button>
                <button
                  class="btn btn--secondary btn--sm"
                  type="button"
                  @click="openStatusConfirm(row)"
                >
                  <Power :size="15" aria-hidden="true" />
                  {{ getStatusActionLabel(row.status) }}
                </button>
              </div>
            </template>
          </DataTable>
        </div>

        <div class="library-management__mobile-list" aria-label="Registered libraries">
          <article v-for="library in paginatedLibraries" :key="library.id" class="library-card">
            <header>
              <div>
                <strong>{{ library.name }}</strong>
                <span>{{ library.code }}</span>
              </div>
              <span class="badge" :class="getStatusClass(library.status)">
                {{ formatLabel(library.status) }}
              </span>
            </header>
            <dl>
              <div><dt>Location</dt><dd>{{ library.city }}, {{ library.state }}</dd></div>
              <div><dt>Owner</dt><dd>{{ library.ownerName || 'Not assigned' }}</dd></div>
              <div><dt>Students</dt><dd>{{ formatNumber(library.studentCount) }}</dd></div>
              <div><dt>Seats</dt><dd>{{ formatNumber(library.seatCount) }}</dd></div>
            </dl>
            <footer>
              <button class="btn btn--outline btn--sm" type="button" @click="openEditModal(library)">
                <Pencil :size="15" aria-hidden="true" /> Edit
              </button>
              <button class="btn btn--secondary btn--sm" type="button" @click="openStatusConfirm(library)">
                <Power :size="15" aria-hidden="true" />
                {{ getStatusActionLabel(library.status) }}
              </button>
            </footer>
          </article>
        </div>

        <footer class="library-management__pagination">
          <span class="text-small text-muted">
            Showing {{ paginationStart }}-{{ paginationEnd }} of {{ filteredLibraries.length }}
          </span>
          <Pagination v-model:current-page="currentPage" :total-pages="totalPages" />
        </footer>
      </template>
    </template>

    <LibraryFormModal
      :is-open="isFormOpen"
      :mode="formMode"
      :library="selectedLibrary"
      :owners="assignableOwners"
      :is-saving="isSaving"
      @close="closeForm"
      @save="handleSave"
    />

    <ConfirmDialog
      :is-open="Boolean(statusPendingLibrary)"
      :title="statusConfirmTitle"
      :message="statusConfirmMessage"
      :confirm-label="statusConfirmLabel"
      confirming-label="Updating"
      :is-confirming="isSaving"
      @cancel="statusPendingLibrary = null"
      @confirm="handleStatusChange"
    />
  </section>
</template>

<script setup>
import { Ban, Building2, CircleCheckBig, Clock3, Pencil, Plus, Power, RotateCcw } from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import ConfirmDialog from '../../components/common/ConfirmDialog.vue'
import DataTable from '../../components/common/DataTable.vue'
import EmptyState from '../../components/common/EmptyState.vue'
import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import Pagination from '../../components/common/Pagination.vue'
import SearchBar from '../../components/common/SearchBar.vue'
import Toast from '../../components/common/Toast.vue'
import LibraryFormModal from '../../components/superadmin/LibraryFormModal.vue'
import PlatformMetricCards from '../../components/superadmin/PlatformMetricCards.vue'
import { useSuperAdminStore } from '../../stores/superAdminStore'

const PAGE_SIZE = 6
const columns = Object.freeze([
  { key: 'name', label: 'Library' },
  { key: 'location', label: 'Location' },
  { key: 'ownerName', label: 'Owner' },
  { key: 'studentCount', label: 'Students' },
  { key: 'seatCount', label: 'Seats' },
  { key: 'status', label: 'Status' },
  { key: 'lastActivityAt', label: 'Last Activity' },
])

const store = useSuperAdminStore()
const { libraries, owners, isSaving, errorMessage } = storeToRefs(store)
const searchQuery = ref('')
const statusFilter = ref('')
const stateFilter = ref('')
const currentPage = ref(1)
const isPageLoading = ref(false)
const isFormOpen = ref(false)
const formMode = ref('create')
const selectedLibrary = ref(null)
const statusPendingLibrary = ref(null)
const successMessage = ref('')
let toastTimer = null

const summaryItems = computed(() => [
  { label: 'Total Libraries', value: libraries.value.length, detail: 'Registered platform tenants', icon: Building2 },
  { label: 'Active', value: countStatus('active'), detail: 'Operating normally', icon: CircleCheckBig, tone: 'success' },
  { label: 'Pending', value: countStatus('pending'), detail: 'Awaiting approval', icon: Clock3, tone: 'warning' },
  { label: 'Suspended', value: countStatus('suspended'), detail: 'Access restricted', icon: Ban, tone: 'danger' },
])
const states = computed(() => [...new Set(libraries.value.map((library) => library.state))].sort())
const hasFilters = computed(() => Boolean(searchQuery.value.trim() || statusFilter.value || stateFilter.value))
const filteredLibraries = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  return libraries.value.filter((library) => {
    const searchable = [library.name, library.code, library.city, library.state, library.ownerName]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()
    return (!query || searchable.includes(query)) &&
      (!statusFilter.value || library.status === statusFilter.value) &&
      (!stateFilter.value || library.state === stateFilter.value)
  })
})
const totalPages = computed(() => Math.max(1, Math.ceil(filteredLibraries.value.length / PAGE_SIZE)))
const paginatedLibraries = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return filteredLibraries.value.slice(start, start + PAGE_SIZE)
})
const paginationStart = computed(() => filteredLibraries.value.length ? (currentPage.value - 1) * PAGE_SIZE + 1 : 0)
const paginationEnd = computed(() => Math.min(currentPage.value * PAGE_SIZE, filteredLibraries.value.length))
const isInitialLoading = computed(() => isPageLoading.value && libraries.value.length === 0)
const assignableOwners = computed(() => owners.value.filter((owner) => {
  return !owner.libraryId || owner.id === selectedLibrary.value?.ownerId
}))
const nextStatus = computed(() => statusPendingLibrary.value?.status === 'active' ? 'suspended' : 'active')
const statusConfirmTitle = computed(() => nextStatus.value === 'suspended' ? 'Suspend Library' : 'Activate Library')
const statusConfirmLabel = computed(() => nextStatus.value === 'suspended' ? 'Suspend' : 'Activate')
const statusConfirmMessage = computed(() => {
  if (!statusPendingLibrary.value) return ''
  return nextStatus.value === 'suspended'
    ? `Suspend ${statusPendingLibrary.value.name}? Its owner will no longer be able to access library operations.`
    : `Activate ${statusPendingLibrary.value.name} and allow platform access?`
})

function countStatus(status) { return libraries.value.filter((library) => library.status === status).length }
function formatNumber(value) { return new Intl.NumberFormat('en-IN').format(Number(value) || 0) }
function formatDate(value) { return value ? new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(value)) : '—' }
function formatLabel(value) { return String(value || '').replace(/[-_]/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase()) }
function getStatusClass(status) { return status === 'active' ? 'badge--success' : status === 'suspended' ? 'badge--inactive' : 'badge--pending' }
function getStatusActionLabel(status) { return status === 'active' ? 'Suspend' : status === 'pending' ? 'Approve' : 'Activate' }

function clearFilters() { searchQuery.value = ''; statusFilter.value = ''; stateFilter.value = '' }
function openCreateModal() { formMode.value = 'create'; selectedLibrary.value = null; isFormOpen.value = true }
function openEditModal(library) { formMode.value = 'edit'; selectedLibrary.value = library; isFormOpen.value = true }
function closeForm() { if (!isSaving.value) isFormOpen.value = false }
function openStatusConfirm(library) { statusPendingLibrary.value = library }
function showSuccess(message) { successMessage.value = message; window.clearTimeout(toastTimer); toastTimer = window.setTimeout(() => { successMessage.value = '' }, 3500) }

async function handleSave(payload) {
  try {
    if (formMode.value === 'edit') await store.updateLibrary(selectedLibrary.value.id, payload)
    else await store.createLibrary(payload)
    showSuccess(formMode.value === 'edit' ? 'Library updated successfully.' : 'Library created successfully.')
    closeForm()
  } catch { /* Store-owned errors are rendered above. */ }
}

async function handleStatusChange() {
  if (!statusPendingLibrary.value) return
  try {
    const name = statusPendingLibrary.value.name
    const status = nextStatus.value
    await store.setLibraryStatus(statusPendingLibrary.value.id, status)
    statusPendingLibrary.value = null
    showSuccess(`${name} ${status === 'active' ? 'activated' : 'suspended'} successfully.`)
  } catch { /* Store-owned errors are rendered above. */ }
}

async function loadLibraries() {
  isPageLoading.value = true
  try { await Promise.all([store.fetchLibraries(), store.fetchOwners()]) }
  catch { /* Store-owned errors are rendered above. */ }
  finally { isPageLoading.value = false }
}

watch([searchQuery, statusFilter, stateFilter], () => { currentPage.value = 1 })
watch(totalPages, (pages) => { if (currentPage.value > pages) currentPage.value = pages })
onMounted(loadLibraries)
onBeforeUnmount(() => window.clearTimeout(toastTimer))
</script>

<style scoped>
.library-management { display: grid; gap: var(--space-6); }
.library-management__header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-5); }
.library-management__title { margin: var(--space-1) 0 0; }
.library-management__description { margin: var(--space-2) 0 0; color: var(--color-text-muted); }
.library-management__filters { display: grid; grid-template-columns: minmax(260px, 1.5fr) minmax(150px, .7fr) minmax(170px, .8fr) auto; align-items: end; gap: var(--space-4); padding: var(--space-4); }
.library-management__filters :deep(.search-bar) { max-width: none; }
.library-management__filter { display: grid; gap: var(--space-2); }
.library-management__loading { display: grid; min-height: 320px; place-items: center; border: 1px solid var(--color-border); border-radius: var(--radius-lg); background: var(--color-surface-elevated); }
.library-management__primary-cell { display: grid; min-width: 170px; }
.library-management__primary-cell span { color: var(--color-text-muted); font-size: var(--font-size-caption); }
.library-management__row-actions { display: flex; gap: var(--space-2); }
.library-management__pagination { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); }
.library-management__mobile-list { display: none; }

@media (max-width: 1050px) {
  .library-management__filters { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 760px) {
  .library-management__header { flex-direction: column; }
  .library-management__desktop-table { display: none; }
  .library-management__mobile-list { display: grid; gap: var(--space-3); }
  .library-card { display: grid; gap: var(--space-4); padding: var(--space-4); border: 1px solid var(--color-border); border-radius: var(--radius-lg); background: var(--color-surface-elevated); box-shadow: var(--shadow-sm); }
  .library-card header, .library-card footer { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-3); }
  .library-card header > div { display: grid; }
  .library-card header > div span { color: var(--color-text-muted); font-size: var(--font-size-caption); }
  .library-card dl { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-3); margin: 0; }
  .library-card dl div { display: grid; }
  .library-card dt { color: var(--color-text-muted); font-size: var(--font-size-caption); }
  .library-card dd { margin: 0; font-weight: var(--font-weight-medium); }
  .library-management__pagination { align-items: stretch; flex-direction: column; }
}
@media (max-width: 560px) {
  .library-management__filters { grid-template-columns: 1fr; }
  .library-card dl { grid-template-columns: 1fr; }
  .library-card footer { flex-direction: column; }
  .library-card footer .btn { width: 100%; }
}
</style>
