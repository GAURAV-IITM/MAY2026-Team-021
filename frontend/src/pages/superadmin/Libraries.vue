<template>
  <section class="library-management" aria-labelledby="library-management-title">
    <header class="library-management__header">
      <div>
        <p class="text-label text-muted m-0">Platform Management</p>
        <h1 id="library-management-title" class="text-h2 library-management__title">Registered Libraries</h1>
        <p class="library-management__description">
          Review registrations and maintain library access across the platform.
        </p>
      </div>
      <button class="btn btn--primary" type="button" @click="openCreateModal">
        <Plus :size="18" aria-hidden="true" /> Add Library
      </button>
    </header>

    <Toast v-if="toast.message" :type="toast.type">{{ toast.message }}</Toast>

    <div v-if="errorMessage && !isOverlayOpen" class="alert alert--danger" role="alert">
      <div>
        <strong>Unable to complete the library request.</strong>
        <p class="m-0">{{ errorMessage }}</p>
        <small v-if="errorRequestId">Request ID: {{ errorRequestId }}</small>
      </div>
      <button class="btn btn--secondary btn--sm" type="button" @click="loadLibraries">
        <RefreshCw :size="16" aria-hidden="true" /> Retry
      </button>
    </div>

    <PlatformMetricCards :items="summaryItems" aria-label="Library summary" />

    <section class="card library-management__filters" aria-label="Library filters">
      <SearchBar
        v-model="searchQuery"
        placeholder="Search name, code, email, phone, city, or address"
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
        <label class="form-label" for="library-sort">Sort</label>
        <select id="library-sort" v-model="sortBy" class="form-select">
          <option value="createdAt">Date created</option>
          <option value="updatedAt">Last updated</option>
          <option value="name">Library name</option>
          <option value="code">Library code</option>
          <option value="status">Status</option>
        </select>
      </div>
      <button
        class="btn btn--secondary library-management__sort-direction"
        type="button"
        :aria-label="sortOrder === 'asc' ? 'Sort descending' : 'Sort ascending'"
        :title="sortOrder === 'asc' ? 'Sort descending' : 'Sort ascending'"
        @click="sortOrder = sortOrder === 'asc' ? 'desc' : 'asc'"
      >
        <ArrowUpDown :size="17" aria-hidden="true" /> {{ sortOrder === 'asc' ? 'Ascending' : 'Descending' }}
      </button>
      <button class="btn btn--secondary" type="button" :disabled="!hasFilters" @click="clearFilters">
        <RotateCcw :size="16" aria-hidden="true" /> Clear Filters
      </button>
    </section>

    <div v-if="isInitialLoading" class="library-management__loading">
      <LoadingSpinner label="Loading libraries" />
    </div>

    <template v-else>
      <EmptyState
        v-if="!libraries.length && !errorMessage"
        :title="hasFilters ? 'No matching libraries' : 'No libraries registered'"
        :description="hasFilters ? 'Adjust the search or status filter.' : 'Create the first platform-managed library.'"
      >
        <template #icon><Building2 :size="27" /></template>
        <template #primary-action>
          <button v-if="hasFilters" class="btn btn--primary" type="button" @click="clearFilters">Clear Filters</button>
          <button v-else class="btn btn--primary" type="button" @click="openCreateModal">
            <Plus :size="17" aria-hidden="true" /> Add Library
          </button>
        </template>
      </EmptyState>

      <template v-else-if="libraries.length">
        <div class="library-management__desktop-table" :aria-busy="isLoading">
          <DataTable :columns="columns" :rows="libraries" aria-label="Registered libraries">
            <template #cell-name="{ row }">
              <button class="library-management__library-link" type="button" @click="openDetails(row)">
                <strong>{{ row.name }}</strong>
                <span>{{ row.code }}</span>
              </button>
            </template>
            <template #cell-location="{ row }">{{ formatLocation(row) }}</template>
            <template #cell-ownerName="{ value }">{{ value || 'Not assigned' }}</template>
            <template #cell-studentCount="{ value }">{{ formatNumber(value) }}</template>
            <template #cell-seatCount="{ value }">{{ formatNumber(value) }}</template>
            <template #cell-status="{ value }">
              <span class="badge" :class="getStatusClass(value)">{{ formatLabel(value) }}</span>
            </template>
            <template #actions="{ row }">
              <div class="library-management__row-actions">
                <button class="btn btn--outline btn--sm" type="button" @click="openDetails(row)">
                  <Eye :size="15" aria-hidden="true" /> View
                </button>
                <button class="btn btn--outline btn--sm" type="button" @click="openEditModal(row)">
                  <Pencil :size="15" aria-hidden="true" /> Edit
                </button>
                <button class="btn btn--secondary btn--sm" type="button" @click="openStatusModal(row)">
                  <Power :size="15" aria-hidden="true" /> {{ getStatusActionLabel(row.status) }}
                </button>
              </div>
            </template>
          </DataTable>
        </div>

        <div class="library-management__mobile-list" aria-label="Registered libraries" :aria-busy="isLoading">
          <article v-for="library in libraries" :key="library.id" class="library-card">
            <header>
              <button class="library-management__library-link" type="button" @click="openDetails(library)">
                <strong>{{ library.name }}</strong><span>{{ library.code }}</span>
              </button>
              <span class="badge" :class="getStatusClass(library.status)">{{ formatLabel(library.status) }}</span>
            </header>
            <dl>
              <div><dt>Location</dt><dd>{{ formatLocation(library) }}</dd></div>
              <div><dt>Owner</dt><dd>{{ library.ownerName || 'Not assigned' }}</dd></div>
              <div><dt>Students</dt><dd>{{ formatNumber(library.studentCount) }}</dd></div>
              <div><dt>Seats</dt><dd>{{ formatNumber(library.seatCount) }}</dd></div>
            </dl>
            <footer>
              <button class="btn btn--outline btn--sm" type="button" @click="openDetails(library)"><Eye :size="15" /> View</button>
              <button class="btn btn--outline btn--sm" type="button" @click="openEditModal(library)"><Pencil :size="15" /> Edit</button>
              <button class="btn btn--secondary btn--sm" type="button" @click="openStatusModal(library)"><Power :size="15" /> {{ getStatusActionLabel(library.status) }}</button>
            </footer>
          </article>
        </div>

        <footer class="library-management__pagination">
          <span class="text-small text-muted">Showing {{ paginationStart }}-{{ paginationEnd }} of {{ libraryPagination.totalItems }}</span>
          <Pagination
            :current-page="libraryPagination.page"
            :total-pages="libraryPagination.totalPages"
            @update:current-page="changePage"
          />
        </footer>
      </template>
    </template>

    <LibraryFormModal
      :is-open="isFormOpen"
      :mode="formMode"
      :library="formLibrary"
      :owners="libraryOwnerOptions"
      :is-saving="isSaving"
      :server-error="isFormOpen ? errorMessage : ''"
      @close="closeForm"
      @save="handleSave"
    />

    <LibraryStatusModal
      :is-open="Boolean(statusLibrary)"
      :library="statusLibrary"
      :target-status="nextStatus"
      :is-saving="isSaving"
      :server-error="statusLibrary ? errorMessage : ''"
      @close="closeStatusModal"
      @confirm="handleStatusChange"
    />

    <LibraryDetailsModal
      :is-open="isDetailsOpen"
      :library="selectedLibrary"
      :owners="libraryOwnerOptions"
      :is-saving="isSaving"
      :server-error="isDetailsOpen ? errorMessage : ''"
      @close="closeDetails"
      @assign-owner="handleOwnerAssignment"
    />
  </section>
</template>

<script setup>
import {
  ArrowUpDown,
  Ban,
  Building2,
  CircleCheckBig,
  Clock3,
  Eye,
  Pencil,
  Plus,
  Power,
  RefreshCw,
  RotateCcw,
} from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import DataTable from '../../components/common/DataTable.vue'
import EmptyState from '../../components/common/EmptyState.vue'
import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import Pagination from '../../components/common/Pagination.vue'
import SearchBar from '../../components/common/SearchBar.vue'
import Toast from '../../components/common/Toast.vue'
import LibraryDetailsModal from '../../components/superadmin/LibraryDetailsModal.vue'
import LibraryFormModal from '../../components/superadmin/LibraryFormModal.vue'
import LibraryStatusModal from '../../components/superadmin/LibraryStatusModal.vue'
import PlatformMetricCards from '../../components/superadmin/PlatformMetricCards.vue'
import { useSuperAdminStore } from '../../stores/superAdminStore'

const columns = Object.freeze([
  { key: 'name', label: 'Library' },
  { key: 'location', label: 'Location' },
  { key: 'ownerName', label: 'Owner' },
  { key: 'studentCount', label: 'Students' },
  { key: 'seatCount', label: 'Seats' },
  { key: 'status', label: 'Status' },
])
const store = useSuperAdminStore()
const {
  libraries,
  selectedLibrary,
  libraryOwnerOptions,
  librarySummary,
  libraryPagination,
  isLoading,
  isSaving,
  errorMessage,
  errorRequestId,
} = storeToRefs(store)

const searchQuery = ref('')
const statusFilter = ref('')
const sortBy = ref('createdAt')
const sortOrder = ref('desc')
const hasLoaded = ref(false)
const isFormOpen = ref(false)
const formMode = ref('create')
const formLibrary = ref(null)
const statusLibrary = ref(null)
const isDetailsOpen = ref(false)
const toast = ref({ message: '', type: 'success' })
let searchTimer = null
let toastTimer = null

const summaryItems = computed(() => [
  { label: 'Total Libraries', value: librarySummary.value.total, detail: 'Registered platform tenants', icon: Building2 },
  { label: 'Active', value: librarySummary.value.active, detail: 'Operating normally', icon: CircleCheckBig, tone: 'success' },
  { label: 'Pending', value: librarySummary.value.pending, detail: 'Awaiting activation', icon: Clock3, tone: 'warning' },
  { label: 'Suspended', value: librarySummary.value.suspended, detail: 'Access restricted', icon: Ban, tone: 'danger' },
])
const hasFilters = computed(() => Boolean(searchQuery.value.trim() || statusFilter.value))
const isInitialLoading = computed(() => isLoading.value && !hasLoaded.value)
const isOverlayOpen = computed(() => isFormOpen.value || Boolean(statusLibrary.value) || isDetailsOpen.value)
const nextStatus = computed(() => statusLibrary.value?.status === 'active' ? 'suspended' : 'active')
const paginationStart = computed(() => libraryPagination.value.totalItems
  ? (libraryPagination.value.page - 1) * libraryPagination.value.pageSize + 1
  : 0)
const paginationEnd = computed(() => Math.min(
  libraryPagination.value.page * libraryPagination.value.pageSize,
  libraryPagination.value.totalItems,
))

function formatNumber(value) { return new Intl.NumberFormat('en-IN').format(Number(value) || 0) }
function formatLabel(value) { return String(value || '').replace(/[-_]/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase()) }
function formatLocation(library) { return [library.city, library.state].filter(Boolean).join(', ') || 'Not provided' }
function getStatusClass(status) { return status === 'active' ? 'badge--success' : status === 'suspended' ? 'badge--inactive' : 'badge--pending' }
function getStatusActionLabel(status) { return status === 'active' ? 'Suspend' : 'Activate' }

function showToast(message, type = 'success') {
  toast.value = { message, type }
  window.clearTimeout(toastTimer)
  toastTimer = window.setTimeout(() => { toast.value.message = '' }, 3500)
}

function currentFilters(page = libraryPagination.value.page || 1) {
  return {
    search: searchQuery.value,
    status: statusFilter.value,
    sortBy: sortBy.value,
    sortOrder: sortOrder.value,
    page,
    pageSize: 10,
  }
}

async function loadLibraries(page = libraryPagination.value.page || 1) {
  try {
    await store.fetchLibraries(currentFilters(page))
    hasLoaded.value = true
  } catch { /* Store-owned structured error is rendered above. */ }
}

async function loadOwnerOptions() {
  try { await store.fetchLibraryOwnerOptions() } catch { /* Modal renders the structured error. */ }
}

async function openCreateModal() {
  formMode.value = 'create'
  formLibrary.value = null
  isFormOpen.value = true
  await loadOwnerOptions()
}

function openEditModal(library) {
  store.clearError()
  formMode.value = 'edit'
  formLibrary.value = library
  isFormOpen.value = true
}

function closeForm() {
  if (!isSaving.value) { isFormOpen.value = false; store.clearError() }
}

async function openDetails(library) {
  store.clearError()
  selectedLibrary.value = library
  isDetailsOpen.value = true
  await Promise.allSettled([store.fetchLibrary(library.id), loadOwnerOptions()])
}

function closeDetails() {
  if (!isSaving.value) { isDetailsOpen.value = false; store.clearError() }
}

function openStatusModal(library) {
  store.clearError()
  statusLibrary.value = library
}

function closeStatusModal() {
  if (!isSaving.value) { statusLibrary.value = null; store.clearError() }
}

async function handleSave(payload) {
  try {
    const editing = formMode.value === 'edit'
    if (editing) await store.updateLibrary(formLibrary.value.id, payload)
    else await store.createLibrary(payload)
    closeForm()
    await loadLibraries(editing ? libraryPagination.value.page : 1)
    showToast(editing ? 'Library updated successfully.' : 'Library created successfully.')
  } catch { /* Form renders the structured error. */ }
}

async function handleStatusChange(payload) {
  try {
    const name = statusLibrary.value.name
    await store.setLibraryStatus(statusLibrary.value.id, payload)
    closeStatusModal()
    await loadLibraries()
    showToast(`${name} ${payload.status === 'active' ? 'activated' : 'suspended'} successfully.`)
  } catch { /* Modal renders the structured error. */ }
}

async function handleOwnerAssignment(payload) {
  try {
    await store.assignLibraryOwner(selectedLibrary.value.id, payload)
    await loadOwnerOptions()
    await loadLibraries()
    showToast('Library owner assigned successfully.')
  } catch { /* Details modal renders the structured error. */ }
}

function clearFilters() {
  searchQuery.value = ''
  statusFilter.value = ''
  sortBy.value = 'createdAt'
  sortOrder.value = 'desc'
  loadLibraries(1)
}

function changePage(page) { loadLibraries(page) }

watch(searchQuery, () => {
  window.clearTimeout(searchTimer)
  searchTimer = window.setTimeout(() => loadLibraries(1), 300)
})
watch([statusFilter, sortBy, sortOrder], () => loadLibraries(1))
onMounted(() => loadLibraries(1))
onBeforeUnmount(() => {
  window.clearTimeout(searchTimer)
  window.clearTimeout(toastTimer)
})
</script>

<style scoped>
.library-management { display: grid; gap: var(--space-6); }
.library-management__header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-5); }
.library-management__title { margin: var(--space-1) 0 0; }
.library-management__description { margin: var(--space-2) 0 0; color: var(--color-text-muted); }
.library-management__filters { display: grid; grid-template-columns: minmax(280px, 1.5fr) minmax(150px, .7fr) minmax(170px, .8fr) auto auto; align-items: end; gap: var(--space-4); padding: var(--space-4); }
.library-management__filters :deep(.search-bar) { max-width: none; }
.library-management__filter { display: grid; gap: var(--space-2); }
.library-management__sort-direction { white-space: nowrap; }
.library-management__loading { display: grid; min-height: 320px; place-items: center; border: 1px solid var(--color-border); border-radius: var(--radius-lg); background: var(--color-surface-elevated); }
.library-management__library-link { display: grid; min-width: 170px; padding: 0; border: 0; background: transparent; color: var(--color-text); text-align: left; cursor: pointer; }
.library-management__library-link:hover strong { color: var(--color-primary); }
.library-management__library-link span { color: var(--color-text-muted); font-size: var(--font-size-caption); }
.library-management__row-actions { display: flex; flex-wrap: wrap; gap: var(--space-2); min-width: 245px; }
.library-management__pagination { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); }
.library-management__mobile-list { display: none; }

@media (max-width: 1180px) {
  .library-management__filters { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 760px) {
  .library-management__header { flex-direction: column; }
  .library-management__desktop-table { display: none; }
  .library-management__mobile-list { display: grid; gap: var(--space-3); }
  .library-card { display: grid; gap: var(--space-4); padding: var(--space-4); border: 1px solid var(--color-border); border-radius: var(--radius-lg); background: var(--color-surface-elevated); box-shadow: var(--shadow-sm); }
  .library-card header, .library-card footer { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-3); }
  .library-card dl { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-3); margin: 0; }
  .library-card dl div { display: grid; }
  .library-card dt { color: var(--color-text-muted); font-size: var(--font-size-caption); }
  .library-card dd { margin: 0; overflow-wrap: anywhere; font-weight: var(--font-weight-medium); }
  .library-card footer { flex-wrap: wrap; }
  .library-management__pagination { align-items: stretch; flex-direction: column; }
}
@media (max-width: 560px) {
  .library-management__filters { grid-template-columns: 1fr; }
  .library-card dl { grid-template-columns: 1fr; }
  .library-card footer { flex-direction: column; }
  .library-card footer .btn { width: 100%; }
}
</style>
