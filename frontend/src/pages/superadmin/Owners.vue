<template>
  <section class="owner-management" aria-labelledby="owner-management-title">
    <header class="owner-management__header">
      <div>
        <p class="text-label text-muted m-0">Access Management</p>
        <h1 id="owner-management-title" class="text-h2 owner-management__title">Library Owners</h1>
        <p class="owner-management__description">
          Invite owners, manage library responsibility, and control platform access.
        </p>
      </div>
      <button class="btn btn--primary" type="button" @click="openInviteModal()">
        <UserPlus :size="18" aria-hidden="true" /> Invite Owner
      </button>
    </header>

    <Toast v-if="successMessage" type="success">{{ successMessage }}</Toast>

    <section v-if="invitationSetupUrl" class="owner-management__invitation" aria-label="Owner invitation link">
      <div>
        <strong>Owner invitation created</strong>
        <span>Share this one-time setup link through your approved delivery channel.</span>
      </div>
      <input class="form-input" :value="invitationSetupUrl" readonly aria-label="Invitation setup URL" />
      <button class="btn btn--secondary" type="button" @click="copyInvitationLink">
        <Copy :size="16" aria-hidden="true" /> Copy Link
      </button>
      <button class="btn btn--ghost btn--icon" type="button" title="Dismiss invitation link" @click="invitationSetupUrl = ''">
        <X :size="17" aria-hidden="true" />
      </button>
    </section>

    <div v-if="errorMessage" class="alert alert--danger" role="alert">
      <div>
        <strong>Unable to complete the owner request.</strong>
        <p class="m-0">{{ friendlyErrorMessage }}</p>
        <small v-if="errorRequestId">Request ID: {{ errorRequestId }}</small>
      </div>
      <button class="btn btn--secondary btn--sm" type="button" @click="loadPage">Retry</button>
    </div>

    <PlatformMetricCards :items="summaryItems" aria-label="Owner summary" />

    <section class="card owner-management__filters" aria-label="Owner filters">
      <SearchBar
        v-model="searchQuery"
        placeholder="Search owner, email, phone, or library"
        @clear="searchQuery = ''"
      />
      <div class="owner-management__filter">
        <label class="form-label" for="owner-status-filter">Owner Status</label>
        <select id="owner-status-filter" v-model="statusFilter" class="form-select">
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="invited">Invited</option>
          <option value="suspended">Suspended</option>
        </select>
      </div>
      <div class="owner-management__filter">
        <label class="form-label" for="owner-library-filter">Library</label>
        <select id="owner-library-filter" v-model="libraryFilter" class="form-select">
          <option value="">All libraries</option>
          <option v-for="library in ownerLibraries" :key="library.id" :value="library.id">{{ library.name }}</option>
        </select>
      </div>
      <div class="owner-management__filter">
        <label class="form-label" for="owner-invitation-filter">Invitation</label>
        <select id="owner-invitation-filter" v-model="invitationFilter" class="form-select">
          <option value="">All invitations</option>
          <option value="pending">Pending</option>
          <option value="accepted">Accepted</option>
          <option value="expired">Expired</option>
          <option value="revoked">Revoked</option>
        </select>
      </div>
      <div class="owner-management__filter">
        <label class="form-label" for="owner-sort">Sort</label>
        <select id="owner-sort" v-model="sortOption" class="form-select">
          <option value="createdAt:desc">Newest first</option>
          <option value="createdAt:asc">Oldest first</option>
          <option value="name:asc">Name A-Z</option>
          <option value="name:desc">Name Z-A</option>
          <option value="lastLoginAt:desc">Recent login</option>
        </select>
      </div>
      <button class="btn btn--secondary" type="button" :disabled="!hasFilters" @click="clearFilters">
        <RotateCcw :size="16" aria-hidden="true" /> Clear
      </button>
    </section>

    <div v-if="isInitialLoading" class="owner-management__loading">
      <LoadingSpinner label="Loading owners" />
    </div>

    <template v-else>
      <EmptyState
        v-if="owners.length === 0"
        :title="hasFilters ? 'No owners match these filters' : 'No owners found'"
        :description="hasFilters ? 'Clear or adjust the filters to see more owners.' : 'Invite the first library owner to begin.'"
      >
        <template #icon><UserCog :size="27" /></template>
        <template #primary-action>
          <button v-if="hasFilters" class="btn btn--primary" type="button" @click="clearFilters">Clear Filters</button>
          <button v-else class="btn btn--primary" type="button" @click="openInviteModal()"><UserPlus :size="17" /> Invite Owner</button>
        </template>
      </EmptyState>

      <template v-else>
        <div class="owner-management__desktop-table">
          <DataTable :columns="columns" :rows="owners" aria-label="Library owners">
            <template #cell-name="{ row }">
              <button class="owner-management__owner-link" type="button" @click="openDetails(row)">
                <strong>{{ row.name }}</strong><span>{{ row.email }}</span>
              </button>
            </template>
            <template #cell-libraryName="{ value }">{{ value || 'Not assigned' }}</template>
            <template #cell-status="{ value }"><span class="badge" :class="getStatusClass(value)">{{ formatLabel(value) }}</span></template>
            <template #cell-invitationStatus="{ value }"><span v-if="value" class="badge badge--neutral">{{ formatLabel(value) }}</span><span v-else>Not applicable</span></template>
            <template #cell-lastLoginAt="{ value }">{{ value ? formatDate(value) : 'Never' }}</template>
            <template #actions="{ row }">
              <div class="owner-management__row-actions">
                <button class="btn btn--outline btn--sm" type="button" @click="openDetails(row)"><Eye :size="15" /> View</button>
                <template v-if="!row.isInvitation">
                  <button class="btn btn--outline btn--sm" type="button" @click="openEditModal(row)"><Pencil :size="15" /> Edit</button>
                  <button class="btn btn--outline btn--sm" type="button" @click="openAssignmentModal(row)"><Building2 :size="15" /> Assign</button>
                  <button class="btn btn--secondary btn--sm" type="button" @click="openStatusModal(row)"><Power :size="15" /> {{ row.status === 'active' ? 'Suspend' : 'Activate' }}</button>
                </template>
                <button v-else-if="row.invitationStatus === 'expired'" class="btn btn--secondary btn--sm" type="button" @click="openInviteModal(row)"><RefreshCw :size="15" /> Reissue</button>
              </div>
            </template>
          </DataTable>
        </div>

        <div class="owner-management__mobile-list" aria-label="Library owners">
          <article v-for="owner in owners" :key="owner.id" class="owner-card">
            <header><div><strong>{{ owner.name }}</strong><span>{{ owner.email }}</span></div><span class="badge" :class="getStatusClass(owner.status)">{{ formatLabel(owner.status) }}</span></header>
            <dl>
              <div><dt>Library</dt><dd>{{ owner.libraryName || 'Not assigned' }}</dd></div>
              <div><dt>Phone</dt><dd>{{ owner.phone || 'Not provided' }}</dd></div>
              <div><dt>Invitation</dt><dd>{{ formatLabel(owner.invitationStatus || 'Not applicable') }}</dd></div>
              <div><dt>Last Login</dt><dd>{{ owner.lastLoginAt ? formatDate(owner.lastLoginAt) : 'Never' }}</dd></div>
            </dl>
            <footer>
              <button class="btn btn--outline btn--sm" type="button" @click="openDetails(owner)"><Eye :size="15" /> View</button>
              <template v-if="!owner.isInvitation">
                <button class="btn btn--outline btn--sm" type="button" @click="openEditModal(owner)"><Pencil :size="15" /> Edit</button>
                <button class="btn btn--outline btn--sm" type="button" @click="openAssignmentModal(owner)"><Building2 :size="15" /> Assign</button>
                <button class="btn btn--secondary btn--sm" type="button" @click="openStatusModal(owner)"><Power :size="15" /> {{ owner.status === 'active' ? 'Suspend' : 'Activate' }}</button>
              </template>
              <button v-else-if="owner.invitationStatus === 'expired'" class="btn btn--secondary btn--sm" type="button" @click="openInviteModal(owner)"><RefreshCw :size="15" /> Reissue</button>
            </footer>
          </article>
        </div>

        <footer class="owner-management__pagination">
          <span class="text-small text-muted">Showing {{ paginationStart }}-{{ paginationEnd }} of {{ ownerPagination.totalItems }}</span>
          <Pagination v-model:current-page="currentPage" :total-pages="Math.max(1, ownerPagination.totalPages)" />
        </footer>
      </template>
    </template>

    <OwnerFormModal :is-open="isFormOpen" :mode="formMode" :owner="selectedOwner" :libraries="inviteLibraries" :is-saving="isSaving" @close="closeForm" @save="handleSave" />
    <OwnerAssignmentModal :is-open="Boolean(assignmentOwner)" :owner="assignmentOwner" :libraries="assignmentLibraries" :is-saving="isSaving" @close="assignmentOwner = null" @save="handleAssignment" />
    <OwnerStatusModal :is-open="Boolean(statusOwner)" :owner="statusOwner" :status="nextStatus" :is-saving="isSaving" @close="statusOwner = null" @save="handleStatusChange" />
    <OwnerDetailModal :is-open="isDetailOpen" :owner="selectedOwnerDetail" :is-loading="isDetailLoading" @close="isDetailOpen = false" />
  </section>
</template>

<script setup>
import { Ban, Building2, CircleCheckBig, Clock3, Copy, Eye, Pencil, Power, RefreshCw, RotateCcw, UserCog, UserPlus, X } from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import DataTable from '../../components/common/DataTable.vue'
import EmptyState from '../../components/common/EmptyState.vue'
import LoadingSpinner from '../../components/common/LoadingSpinner.vue'
import Pagination from '../../components/common/Pagination.vue'
import SearchBar from '../../components/common/SearchBar.vue'
import Toast from '../../components/common/Toast.vue'
import OwnerAssignmentModal from '../../components/superadmin/OwnerAssignmentModal.vue'
import OwnerDetailModal from '../../components/superadmin/OwnerDetailModal.vue'
import OwnerFormModal from '../../components/superadmin/OwnerFormModal.vue'
import OwnerStatusModal from '../../components/superadmin/OwnerStatusModal.vue'
import PlatformMetricCards from '../../components/superadmin/PlatformMetricCards.vue'
import { useSuperAdminStore } from '../../stores/superAdminStore'

const columns = Object.freeze([
  { key: 'name', label: 'Owner' },
  { key: 'phone', label: 'Phone' },
  { key: 'libraryName', label: 'Library' },
  { key: 'status', label: 'Owner Status' },
  { key: 'invitationStatus', label: 'Invitation' },
  { key: 'lastLoginAt', label: 'Last Login' },
])

const store = useSuperAdminStore()
const { owners, ownerLibraries, ownerSummary, ownerPagination, isLoading, isSaving, errorMessage, errorRequestId, errorCode } = storeToRefs(store)
const searchQuery = ref('')
const statusFilter = ref('')
const libraryFilter = ref('')
const invitationFilter = ref('')
const sortOption = ref('createdAt:desc')
const currentPage = ref(1)
const isFormOpen = ref(false)
const formMode = ref('create')
const selectedOwner = ref(null)
const assignmentOwner = ref(null)
const statusOwner = ref(null)
const isDetailOpen = ref(false)
const isDetailLoading = ref(false)
const selectedOwnerDetail = ref(null)
const successMessage = ref('')
const invitationSetupUrl = ref('')
let filterTimer = null
let toastTimer = null

const summaryItems = computed(() => [
  { label: 'Total Owners', value: ownerSummary.value.total, detail: 'Accounts and invitations', icon: UserCog },
  { label: 'Active', value: ownerSummary.value.active, detail: 'Access enabled', icon: CircleCheckBig, tone: 'success' },
  { label: 'Invited', value: ownerSummary.value.invited, detail: 'Awaiting setup', icon: Clock3, tone: 'warning' },
  { label: 'Suspended', value: ownerSummary.value.suspended, detail: 'Access blocked', icon: Ban, tone: 'danger' },
])
const hasFilters = computed(() => Boolean(searchQuery.value.trim() || statusFilter.value || libraryFilter.value || invitationFilter.value || sortOption.value !== 'createdAt:desc'))
const isInitialLoading = computed(() => isLoading.value && owners.value.length === 0)
const paginationStart = computed(() => ownerPagination.value.totalItems ? (ownerPagination.value.page - 1) * ownerPagination.value.pageSize + 1 : 0)
const paginationEnd = computed(() => Math.min(ownerPagination.value.page * ownerPagination.value.pageSize, ownerPagination.value.totalItems))
const inviteLibraries = computed(() => ownerLibraries.value.filter((library) => library.status !== 'suspended' && !library.ownerId))
const assignmentLibraries = computed(() => inviteLibraries.value.filter((library) => library.id !== assignmentOwner.value?.libraryId))
const nextStatus = computed(() => statusOwner.value?.status === 'active' ? 'suspended' : 'active')
const friendlyErrorMessage = computed(() => ({
  PLATFORM_OWNER_EMAIL_EXISTS: 'That email belongs to an account that is not eligible for this owner invitation.',
  PLATFORM_OWNER_INVITATION_EXISTS: 'An active owner invitation already exists for this email or library.',
  PLATFORM_OWNER_ASSIGNMENT_CONFLICT: 'The selected owner or library already has a conflicting assignment.',
  PLATFORM_OWNER_LIBRARY_INELIGIBLE: 'Suspended libraries cannot receive owner invitations or assignments.',
  PLATFORM_OWNER_STATE_CHANGED: 'This owner changed in another session. Refresh and try again.',
}[errorCode.value] || errorMessage.value))

function formatLabel(value) { return String(value || '').replace(/[-_]/g, ' ').replace(/\b\w/g, (character) => character.toUpperCase()) }
function formatDate(value) { return new Intl.DateTimeFormat('en-IN', { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(value)) }
function getStatusClass(status) { return status === 'active' ? 'badge--success' : status === 'suspended' ? 'badge--inactive' : 'badge--pending' }
function showSuccess(message) { successMessage.value = message; window.clearTimeout(toastTimer); toastTimer = window.setTimeout(() => { successMessage.value = '' }, 4000) }

function queryFilters(page = currentPage.value) {
  const [sortBy, sortOrder] = sortOption.value.split(':')
  return { search: searchQuery.value, status: statusFilter.value, libraryId: libraryFilter.value, invitationStatus: invitationFilter.value, page, pageSize: 10, sortBy, sortOrder }
}

async function loadOwners(page = currentPage.value) {
  await store.fetchOwners(queryFilters(page))
  currentPage.value = ownerPagination.value.page
}

async function loadPage() {
  try { await Promise.all([loadOwners(), store.fetchOwnerLibraries()]) } catch { /* Store errors are rendered above. */ }
}

function clearFilters() {
  searchQuery.value = ''
  statusFilter.value = ''
  libraryFilter.value = ''
  invitationFilter.value = ''
  sortOption.value = 'createdAt:desc'
}

function openInviteModal(owner = null) { formMode.value = 'create'; selectedOwner.value = owner; isFormOpen.value = true }
function openEditModal(owner) { formMode.value = 'edit'; selectedOwner.value = owner; isFormOpen.value = true }
function closeForm() { if (!isSaving.value) isFormOpen.value = false }
function openAssignmentModal(owner) { assignmentOwner.value = owner }
function openStatusModal(owner) { statusOwner.value = owner }

async function openDetails(owner) {
  selectedOwnerDetail.value = owner
  isDetailOpen.value = true
  isDetailLoading.value = true
  try { selectedOwnerDetail.value = (await store.fetchOwner(owner.id)).data } catch { /* Main alert exposes the request failure. */ }
  finally { isDetailLoading.value = false }
}

async function refreshAfterMutation() {
  await Promise.all([loadOwners(), store.fetchOwnerLibraries()])
}

async function handleSave(payload) {
  try {
    if (formMode.value === 'edit') {
      await store.updateOwner(selectedOwner.value.id, { ...payload, expectedUpdatedAt: selectedOwner.value.updatedAt })
      showSuccess('Owner profile updated successfully.')
    } else {
      const response = await store.createOwner(payload)
      invitationSetupUrl.value = response.data.invitationSetupUrl || ''
      showSuccess(response.data.createdInvitation ? 'Owner invitation created.' : 'Existing owner assigned successfully.')
    }
    closeForm()
    await refreshAfterMutation()
  } catch { /* Store errors are rendered above. */ }
}

async function handleAssignment(payload) {
  try {
    const owner = assignmentOwner.value
    await store.assignOwner(owner.id, { ...payload, expectedUpdatedAt: owner.updatedAt })
    assignmentOwner.value = null
    showSuccess(`${owner.name} was assigned to the selected library.`)
    await refreshAfterMutation()
  } catch { /* Store errors are rendered above. */ }
}

async function handleStatusChange(payload) {
  try {
    const owner = statusOwner.value
    await store.setOwnerStatus(owner.id, { ...payload, expectedUpdatedAt: owner.updatedAt })
    statusOwner.value = null
    showSuccess(`${owner.name} ${payload.status === 'active' ? 'activated' : 'suspended'} successfully.`)
    await refreshAfterMutation()
  } catch { /* Store errors are rendered above. */ }
}

async function copyInvitationLink() {
  await navigator.clipboard.writeText(invitationSetupUrl.value)
  showSuccess('Invitation link copied.')
}

watch([searchQuery, statusFilter, libraryFilter, invitationFilter, sortOption], () => {
  window.clearTimeout(filterTimer)
  filterTimer = window.setTimeout(async () => {
    currentPage.value = 1
    try { await loadOwners(1) } catch { /* Store errors are rendered above. */ }
  }, 300)
})
watch(currentPage, async (page, previousPage) => {
  if (page === previousPage || page === ownerPagination.value.page) return
  try { await loadOwners(page) } catch { /* Store errors are rendered above. */ }
})

onMounted(loadPage)
onBeforeUnmount(() => { window.clearTimeout(filterTimer); window.clearTimeout(toastTimer) })
</script>

<style scoped>
.owner-management { display: grid; gap: var(--space-6); }
.owner-management__header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-5); }
.owner-management__title { margin: var(--space-1) 0 0; }
.owner-management__description { margin: var(--space-2) 0 0; color: var(--color-text-muted); }
.owner-management__invitation { display: grid; grid-template-columns: minmax(190px, .8fr) minmax(240px, 1.5fr) auto auto; align-items: center; gap: var(--space-3); padding: var(--space-4); border: 1px solid var(--color-success); border-radius: var(--radius-md); background: var(--color-success-light); }
.owner-management__invitation > div { display: grid; }
.owner-management__invitation span { color: var(--color-text-muted); font-size: var(--font-size-caption); }
.owner-management__filters { position: sticky; z-index: 5; top: var(--space-3); display: grid; grid-template-columns: minmax(240px, 1.5fr) repeat(4, minmax(140px, .75fr)) auto; align-items: end; gap: var(--space-3); padding: var(--space-4); }
.owner-management__filters :deep(.search-bar) { max-width: none; }
.owner-management__filter { display: grid; gap: var(--space-2); }
.owner-management__loading { display: grid; min-height: 320px; place-items: center; border: 1px solid var(--color-border); border-radius: var(--radius-lg); background: var(--color-surface-elevated); }
.owner-management__owner-link { display: grid; min-width: 190px; padding: 0; border: 0; background: transparent; color: inherit; text-align: left; cursor: pointer; }
.owner-management__owner-link span { color: var(--color-text-muted); font-size: var(--font-size-caption); }
.owner-management__owner-link:hover strong { color: var(--color-primary); }
.owner-management__row-actions { display: flex; flex-wrap: wrap; gap: var(--space-2); min-width: 280px; }
.owner-management__pagination { display: flex; align-items: center; justify-content: space-between; gap: var(--space-4); }
.owner-management__mobile-list { display: none; }
@media (max-width: 1280px) { .owner-management__filters { grid-template-columns: repeat(3, minmax(0, 1fr)); } .owner-management__invitation { grid-template-columns: 1fr auto auto; } .owner-management__invitation > div { grid-column: 1 / -1; } }
@media (max-width: 900px) { .owner-management__filters { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 760px) {
  .owner-management__header { flex-direction: column; }
  .owner-management__desktop-table { display: none; }
  .owner-management__mobile-list { display: grid; gap: var(--space-3); }
  .owner-card { display: grid; gap: var(--space-4); padding: var(--space-4); border: 1px solid var(--color-border); border-radius: var(--radius-lg); background: var(--color-surface-elevated); box-shadow: var(--shadow-sm); }
  .owner-card header, .owner-card footer { display: flex; flex-wrap: wrap; align-items: flex-start; justify-content: space-between; gap: var(--space-3); }
  .owner-card header > div { display: grid; min-width: 0; }
  .owner-card header span { overflow: hidden; color: var(--color-text-muted); font-size: var(--font-size-caption); text-overflow: ellipsis; }
  .owner-card dl { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--space-3); margin: 0; }
  .owner-card dl div { display: grid; }
  .owner-card dt { color: var(--color-text-muted); font-size: var(--font-size-caption); }
  .owner-card dd { margin: 0; font-weight: var(--font-weight-medium); }
  .owner-management__pagination { align-items: stretch; flex-direction: column; }
}
@media (max-width: 560px) { .owner-management__filters, .owner-card dl { grid-template-columns: 1fr; } .owner-card footer .btn { flex: 1 1 130px; } .owner-management__invitation { grid-template-columns: 1fr auto; } .owner-management__invitation .form-input { grid-column: 1 / -1; } }
</style>
