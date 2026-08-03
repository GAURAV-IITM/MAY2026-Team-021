import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import * as superAdminService from '../services/superAdminService.js'

export const useSuperAdminStore = defineStore('superAdmin', () => {
  const dashboard = ref(null)
  const libraries = ref([])
  const selectedLibrary = ref(null)
  const libraryOwnerOptions = ref([])
  const librarySummary = ref({ total: 0, active: 0, pending: 0, suspended: 0 })
  const libraryPagination = ref({ page: 1, pageSize: 10, totalItems: 0, totalPages: 0 })
  const libraryFilters = ref({
    search: '',
    status: '',
    ownerId: '',
    state: '',
    page: 1,
    pageSize: 10,
    sortBy: 'createdAt',
    sortOrder: 'desc',
  })
  const owners = ref([])
  const analytics = ref(null)
  const settings = ref(null)
  const isLoading = ref(false)
  const isSaving = ref(false)
  const error = ref(null)

  const errorMessage = computed(() => {
    if (!error.value) return ''

    return (
      error.value?.response?.data?.error?.message ||
      error.value?.response?.data?.message ||
      error.value?.message ||
      'An unexpected Super Admin service error occurred.'
    )
  })
  const errorRequestId = computed(
    () =>
      error.value?.response?.headers?.['x-request-id'] ||
      error.value?.response?.data?.requestId ||
      '',
  )
  const errorCode = computed(
    () => error.value?.response?.data?.error?.code || '',
  )
  const activeLibraries = computed(() =>
    libraries.value.filter((library) => library.status === 'active'),
  )
  const availableLibraries = computed(() =>
    libraries.value.filter((library) => !library.ownerId && library.status !== 'suspended'),
  )
  const activeOwners = computed(() =>
    owners.value.filter((owner) => owner.status === 'active'),
  )

  async function runRequest(request, saving = false) {
    const loadingState = saving ? isSaving : isLoading
    loadingState.value = true
    error.value = null

    try {
      return await request()
    } catch (requestError) {
      error.value = requestError
      throw requestError
    } finally {
      loadingState.value = false
    }
  }

  function syncManagementData(data = {}) {
    if (Array.isArray(data.libraries)) libraries.value = data.libraries
    if (Array.isArray(data.owners)) owners.value = data.owners
  }

  async function fetchDashboard() {
    const response = await runRequest(() => superAdminService.getDashboard())
    dashboard.value = response.data
    return response
  }

  let latestLibraryRequest = 0

  async function fetchLibraries(nextFilters = libraryFilters.value) {
    libraryFilters.value = { ...libraryFilters.value, ...nextFilters }
    const requestNumber = ++latestLibraryRequest
    isLoading.value = true
    error.value = null
    try {
      const response = await superAdminService.getLibraries(libraryFilters.value)
      if (requestNumber === latestLibraryRequest) {
        libraries.value = response.data
        librarySummary.value = response.summary
        libraryPagination.value = response.meta
      }
      return response
    } catch (requestError) {
      if (requestNumber === latestLibraryRequest) error.value = requestError
      throw requestError
    } finally {
      if (requestNumber === latestLibraryRequest) isLoading.value = false
    }
  }

  function upsertLibrary(library) {
    const index = libraries.value.findIndex((item) => item.id === library.id)
    if (index === -1) libraries.value.unshift(library)
    else libraries.value[index] = library
    if (selectedLibrary.value?.id === library.id) selectedLibrary.value = library
  }

  async function fetchLibrary(libraryId) {
    const response = await runRequest(() => superAdminService.getLibrary(libraryId))
    selectedLibrary.value = response.data
    upsertLibrary(response.data)
    return response
  }

  async function createLibrary(payload) {
    const response = await runRequest(
      () => superAdminService.createLibrary(payload),
      true,
    )
    upsertLibrary(response.data)
    return response
  }

  async function updateLibrary(libraryId, payload) {
    const response = await runRequest(
      () => superAdminService.updateLibrary(libraryId, payload),
      true,
    )
    upsertLibrary(response.data)
    return response
  }

  async function setLibraryStatus(libraryId, payload) {
    const response = await runRequest(
      () => superAdminService.setLibraryStatus(libraryId, payload),
      true,
    )
    upsertLibrary(response.data)
    return response
  }

  async function fetchLibraryOwnerOptions() {
    const response = await runRequest(
      () => superAdminService.getLibraryOwnerOptions(),
    )
    libraryOwnerOptions.value = response.data
    return response
  }

  async function assignLibraryOwner(libraryId, payload) {
    const response = await runRequest(
      () => superAdminService.assignLibraryOwner(libraryId, payload),
      true,
    )
    upsertLibrary(response.data)
    return response
  }

  async function fetchOwners() {
    const response = await runRequest(() => superAdminService.getOwners())
    owners.value = response.data.owners
    return response
  }

  async function createOwner(payload) {
    const response = await runRequest(
      () => superAdminService.createOwner(payload),
      true,
    )
    syncManagementData(response.data)
    return response
  }

  async function updateOwner(ownerId, payload) {
    const response = await runRequest(
      () => superAdminService.updateOwner(ownerId, payload),
      true,
    )
    syncManagementData(response.data)
    return response
  }

  async function setOwnerStatus(ownerId, status) {
    const response = await runRequest(
      () => superAdminService.setOwnerStatus(ownerId, status),
      true,
    )
    syncManagementData(response.data)
    return response
  }

  async function fetchAnalytics() {
    const response = await runRequest(() => superAdminService.getAnalytics())
    analytics.value = response.data
    return response
  }

  async function fetchSettings() {
    const response = await runRequest(() => superAdminService.getSettings())
    settings.value = response.data.settings
    return response
  }

  async function updateSettings(payload) {
    const response = await runRequest(
      () => superAdminService.updateSettings(payload),
      true,
    )
    settings.value = response.data.settings
    return response
  }

  function clearError() {
    error.value = null
  }

  return {
    dashboard,
    libraries,
    selectedLibrary,
    libraryOwnerOptions,
    librarySummary,
    libraryPagination,
    libraryFilters,
    owners,
    analytics,
    settings,
    isLoading,
    isSaving,
    error,
    errorMessage,
    errorRequestId,
    errorCode,
    activeLibraries,
    availableLibraries,
    activeOwners,
    fetchDashboard,
    fetchLibraries,
    fetchLibrary,
    createLibrary,
    updateLibrary,
    setLibraryStatus,
    fetchLibraryOwnerOptions,
    assignLibraryOwner,
    fetchOwners,
    createOwner,
    updateOwner,
    setOwnerStatus,
    fetchAnalytics,
    fetchSettings,
    updateSettings,
    clearError,
  }
})
