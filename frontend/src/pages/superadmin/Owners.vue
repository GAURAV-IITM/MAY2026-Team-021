<template>
  <section class="owner-management" aria-labelledby="owner-management-title">
    <header class="owner-management__header">
      <div>
        <p class="text-label text-muted m-0">Access Management</p>
        <h1 id="owner-management-title" class="text-h2 owner-management__title">
          Library Owners
        </h1>
        <p class="owner-management__description">
          Manage owner accounts, library assignments, and platform access.
        </p>
      </div>
      <button class="btn btn--primary" type="button" @click="openCreateModal">
        <UserPlus :size="18" aria-hidden="true" /> Add Owner
      </button>
    </header>

    <Toast v-if="successMessage" type="success">{{ successMessage }}</Toast>

    <div v-if="errorMessage" class="alert alert--danger" role="alert">
      <div>
        <strong>Unable to complete the owner request.</strong>
        <p class="m-0">{{ errorMessage }}</p>
      </div>
      <button class="btn btn--secondary btn--sm" type="button" @click="loadOwners">
        Retry
      </button>
    </div>

    <PlatformMetricCards :items="summaryItems" aria-label="Owner summary" />

    <section class="card owner-management__filters" aria-label="Owner filters">
      <SearchBar
        v-model="searchQuery"
        placeholder="Search by owner, email, or library"
        @clear="searchQuery = ''"
      />
      <div class="owner-management__filter">
        <label class="form-label" for="owner-status-filter">Status</label>
        <select id="owner-status-filter" v-model="statusFilter" class="form-select">
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="invited">Invited</option>
          <option value="suspended">Suspended</option>
        </select>
      </div>
      <div class="owner-management__filter">
        <label class="form-label" for="owner-assignment-filter">Assignment</label>
        <select id="owner-assignment-filter" v-model="assignmentFilter" class="form-select">
          <option value="">All assignments</option>
          <option value="assigned">Assigned</option>
          <option value="unassigned">Unassigned</option>
        </select>
      </div>
      <button class="btn btn--secondary" type="button" :disabled="!hasFilters" @click="clearFilters">
        <RotateCcw :size="16" aria-hidden="true" /> Clear Filters
      </button>
    </section>

    <div v-if="isInitialLoading" class="owner-management__loading">
      <LoadingSpinner label="Loading owners" />
    </div>

    <template v-else>
      <EmptyState
        v-if="filteredOwners.length === 0"
        title="No owners found"
        description="Adjust the filters or create a library owner account."
      >
        <template #icon><UserCog :size="27" /></template>
        <template #primary-action>
          <button class="btn btn--primary" type="button" @click="openCreateModal"><UserPlus :size="17" aria-hidden="true" /> Add Owner</button>
        </template>
        <template #secondary-action>
          <button v-if="hasFilters" class="btn btn--secondary" type="button" @click="clearFilters">
            Clear Filters
          </button>
          <span v-else></span>
        </template>
      </EmptyState>

      <template v-else>
        <div class="owner-management__desktop-table">
          <DataTable :columns="columns" :rows="paginatedOwners" aria-label="Library owners">
            <template #cell-name="{ row }">
              <div class="owner-management__primary-cell">
                <strong>{{ row.name }}</strong>
                <span>{{ row.email }}</span>
              </div>
            </template>
            <template #cell-libraryName="{ value }">{{ value || 'Not assigned' }}</template>
            <template #cell-status="{ value }">
              <span class="badge" :class="getStatusClass(value)">{{ formatLabel(value) }}</span>
            </template>
            <template #cell-lastLoginAt="{ value }">{{ value ? formatDate(value) : 'Never' }}</template>
            <template #actions="{ row }">
              <div class="owner-management__row-actions">
                <button class="btn btn--outline btn--sm" type="button" @click="openEditModal(row)">
                  <Pencil :size="15" aria-hidden="true" /> Edit
                </button>
                <button class="btn btn--secondary btn--sm" type="button" @click="openStatusConfirm(row)">
                  <Power :size="15" aria-hidden="true" />
                  {{ row.status === 'active' ? 'Suspend' : 'Activate' }}
                </button>
              </div>
            </template>
          </DataTable>
        </div>

        <div class="owner-management__mobile-list" aria-label="Library owners">
          <article v-for="owner in paginatedOwners" :key="owner.id" class="owner-card">
            <header>
              <div><strong>{{ owner.name }}</strong><span>{{ owner.email }}</span></div>
              <span class="badge" :class="getStatusClass(owner.status)">{{ formatLabel(owner.status) }}</span>
            </header>
            <dl>
              <div><dt>Library</dt><dd>{{ owner.libraryName || 'Not assigned' }}</dd></div>
              <div><dt>Phone</dt><dd>{{ owner.phone || 'Not provided' }}</dd></div>
              <div><dt>Last Login</dt><dd>{{ owner.lastLoginAt ? formatDate(owner.lastLoginAt) : 'Never' }}</dd></div>
            </dl>
            <footer>
              <button class="btn btn--outline btn--sm" type="button" @click="openEditModal(owner)"><Pencil :size="15" aria-hidden="true" /> Edit</button>
              <button class="btn btn--secondary btn--sm" type="button" @click="openStatusConfirm(owner)">
                <Power :size="15" aria-hidden="true" />
                {{ owner.status === 'active' ? 'Suspend' : 'Activate' }}
              </button>
            </footer>
          </article>
        </div>

        <footer class="owner-management__pagination">
          <span class="text-small text-muted">
            Showing {{ paginationStart }}-{{ paginationEnd }} of {{ filteredOwners.length }}
          </span>
          <Pagination v-model:current-page="currentPage" :total-pages="totalPages" />
        </footer>
      </template>
    </template>

    <OwnerFormModal
      :is-open="isFormOpen"
      :mode="formMode"
      :owner="selectedOwner"
      :libraries="assignableLibraries"
      :is-saving="isSaving"
      @close="closeForm"
      @save="handleSave"
    />

    <ConfirmDialog
      :is-open="Boolean(statusPendingOwner)"
      :title="nextStatus === 'suspended' ? 'Suspend Owner' : 'Activate Owner'"
      :message="statusConfirmMessage"
      :confirm-label="nextStatus === 'suspended' ? 'Suspend' : 'Activate'"
      confirming-label="Updating"
      :is-confirming="isSaving"
      @cancel="statusPendingOwner = null"
      @confirm="handleStatusChange"
    />
  </section>
</template>

<script setup>
import { Ban, CircleCheckBig, Clock3, Pencil, Power, RotateCcw, UserCog, UserPlus } from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import ConfirmDialog from '../../components/common/ConfirmDialog.vue'
import DataTable from '../../components/common/DataTable.vue'
import EmptyState from '../../components/common/EmptyState.vue'
import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import Pagination from '../../components/common/Pagination.vue'
import SearchBar from '../../components/common/SearchBar.vue'
import Toast from '../../components/common/Toast.vue'
import OwnerFormModal from '../../components/superadmin/OwnerFormModal.vue'
import PlatformMetricCards from '../../components/superadmin/PlatformMetricCards.vue'
import { useSuperAdminStore } from '../../stores/superAdminStore'

const PAGE_SIZE = 6
const columns = Object.freeze([
  { key: 'name', label: 'Owner' },
  { key: 'phone', label: 'Phone' },
  { key: 'libraryName', label: 'Library' },
  { key: 'status', label: 'Status' },
  { key: 'lastLoginAt', label: 'Last Login' },
])

const store = useSuperAdminStore()
const { owners, libraries, isSaving, errorMessage } = storeToRefs(store)
const searchQuery = ref('')
const statusFilter = ref('')
const assignmentFilter = ref('')
const currentPage = ref(1)
const isPageLoading = ref(false)
const isFormOpen = ref(false)
const formMode = ref('create')
const selectedOwner = ref(null)
const statusPendingOwner = ref(null)
const successMessage = ref('')
let toastTimer = null

const summaryItems = computed(() => [
  { label: 'Total Owners', value: owners.value.length, detail: 'Platform owner accounts', icon: UserCog },
  { label: 'Active', value: countStatus('active'), detail: 'Access enabled', icon: CircleCheckBig, tone: 'success' },
  { label: 'Invited', value: countStatus('invited'), detail: 'Invitation pending', icon: Clock3, tone: 'warning' },
  { label: 'Suspended', value: countStatus('suspended'), detail: 'Access restricted', icon: Ban, tone: 'danger' },
])
const hasFilters = computed(() => Boolean(searchQuery.value.trim() || statusFilter.value || assignmentFilter.value))
const filteredOwners = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  return owners.value.filter((owner) => {
    const searchable = [owner.name, owner.email, owner.phone, owner.libraryName].filter(Boolean).join(' ').toLowerCase()
    const matchesAssignment = !assignmentFilter.value ||
      (assignmentFilter.value === 'assigned' && owner.libraryId) ||
      (assignmentFilter.value === 'unassigned' && !owner.libraryId)
    return (!query || searchable.includes(query)) &&
      (!statusFilter.value || owner.status === statusFilter.value) && matchesAssignment
  })
})
const totalPages = computed(() => Math.max(1, Math.ceil(filteredOwners.value.length / PAGE_SIZE)))
const paginatedOwners = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return filteredOwners.value.slice(start, start + PAGE_SIZE)
})
const paginationStart = computed(() => filteredOwners.value.length ? (currentPage.value - 1) * PAGE_SIZE + 1 : 0)
const paginationEnd = computed(() => Math.min(currentPage.value * PAGE_SIZE, filteredOwners.value.length))
const isInitialLoading = computed(() => isPageLoading.value && owners.value.length === 0)
const assignableLibraries = computed(() => libraries.value.filter((library) => {
  return library.status !== 'suspended' && (!library.ownerId || library.id === selectedOwner.value?.libraryId)
}))
const nextStatus = computed(() => statusPendingOwner.value?.status === 'active' ? 'suspended' : 'active')
const statusConfirmMessage = computed(() => {
  if (!statusPendingOwner.value) return ''
  return nextStatus.value === 'suspended'
    ? `Suspend ${statusPendingOwner.value.name}? This owner will lose access to library administration.`
    : `Activate ${statusPendingOwner.value.name} and restore platform access?`
})

function countStatus(status) { return owners.value.filter((owner) => owner.status === status).length }
function formatLabel(value) { return String(value || '').replace(/[-_]/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase()) }
function formatDate(value) { return new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(value)) }
function getStatusClass(status) { return status === 'active' ? 'badge--success' : status === 'suspended' ? 'badge--inactive' : 'badge--pending' }
function clearFilters() { searchQuery.value = ''; statusFilter.value = ''; assignmentFilter.value = '' }
function openCreateModal() { formMode.value = 'create'; selectedOwner.value = null; isFormOpen.value = true }
function openEditModal(owner) { formMode.value = 'edit'; selectedOwner.value = owner; isFormOpen.value = true }
function closeForm() { if (!isSaving.value) isFormOpen.value = false }
function openStatusConfirm(owner) { statusPendingOwner.value = owner }
function showSuccess(message) { successMessage.value = message; window.clearTimeout(toastTimer); toastTimer = window.setTimeout(() => { successMessage.value = '' }, 3500) }

async function handleSave(payload) {
  try {
    if (formMode.value === 'edit') await store.updateOwner(selectedOwner.value.id, payload)
    else await store.createOwner(payload)
    showSuccess(formMode.value === 'edit' ? 'Owner updated successfully.' : 'Owner created successfully.')
    closeForm()
  } catch { /* Store-owned errors are rendered above. */ }
}

async function handleStatusChange() {
  if (!statusPendingOwner.value) return
  try {
    const name = statusPendingOwner.value.name
    const status = nextStatus.value
    await store.setOwnerStatus(statusPendingOwner.value.id, status)
    statusPendingOwner.value = null
    showSuccess(`${name} ${status === 'active' ? 'activated' : 'suspended'} successfully.`)
  } catch { /* Store-owned errors are rendered above. */ }
}

async function loadOwners() {
  isPageLoading.value = true
  try { await Promise.all([store.fetchOwners(), store.fetchLibraries()]) }
  catch { /* Store-owned errors are rendered above. */ }
  finally { isPageLoading.value = false }
}

watch([searchQuery, statusFilter, assignmentFilter], () => { currentPage.value = 1 })
watch(totalPages, (pages) => { if (currentPage.value > pages) currentPage.value = pages })
onMounted(loadOwners)
onBeforeUnmount(() => window.clearTimeout(toastTimer))
</script>

<style scoped>
.owner-management { display: grid; gap: var(--space-6); }
.owner-management__header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-5); }
.owner-management__title { margin: var(--space-1) 0 0; }
.owner-management__description { margin: var(--space-2) 0 0; color: var(--color-text-muted); }
.owner-management__filters { display: grid; grid-template-columns: minmax(260px, 1.5fr) minmax(150px, .7fr) minmax(170px, .8fr) auto; align-items: end; gap: var(--space-4); padding: var(--space-4); }
.owner-management__filters :deep(.search-bar) { max-width: none; }
.owner-management__filter { display: grid; gap: var(--space-2); }
.owner-management__loading { display: grid; min-height: 320px; place-items: center; border: 1px solid var(--color-border); border-radius: var(--radius-lg); background: var(--color-surface-elevated); }
.owner-management__primary-cell { display: grid; min-width: 190px; }
.owner-management__primary-cell span { color: var(--color-text-muted); font-size: var(--font-size-caption); }
.owner-management__row-actions { display: flex; gap: var(--space-2); }
.owner-management__pagination { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); }
.owner-management__mobile-list { display: none; }
@media (max-width: 1050px) { .owner-management__filters { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 760px) {
  .owner-management__header { flex-direction: column; }
  .owner-management__desktop-table { display: none; }
  .owner-management__mobile-list { display: grid; gap: var(--space-3); }
  .owner-card { display: grid; gap: var(--space-4); padding: var(--space-4); border: 1px solid var(--color-border); border-radius: var(--radius-lg); background: var(--color-surface-elevated); box-shadow: var(--shadow-sm); }
  .owner-card header, .owner-card footer { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-3); }
  .owner-card header > div { display: grid; min-width: 0; }
  .owner-card header > div span { overflow: hidden; color: var(--color-text-muted); font-size: var(--font-size-caption); text-overflow: ellipsis; }
  .owner-card dl { display: grid; gap: var(--space-3); margin: 0; }
  .owner-card dl div { display: grid; }
  .owner-card dt { color: var(--color-text-muted); font-size: var(--font-size-caption); }
  .owner-card dd { margin: 0; font-weight: var(--font-weight-medium); }
  .owner-management__pagination { align-items: stretch; flex-direction: column; }
}
@media (max-width: 560px) {
  .owner-management__filters { grid-template-columns: 1fr; }
  .owner-card footer { flex-direction: column; }
  .owner-card footer .btn { width: 100%; }
}
</style>
