import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import * as superAdminService from '../services/superAdminService.js'

export const useSuperAdminStore = defineStore('superAdmin', () => {
  const dashboard = ref(null)
  const libraries = ref([])
  const owners = ref([])
  const analytics = ref(null)
  const settings = ref(null)
  const isLoading = ref(false)
  const isSaving = ref(false)
  const error = ref(null)

  const errorMessage = computed(() => {
    if (!error.value) return ''

    return (
      error.value?.response?.data?.message ||
      error.value?.message ||
      'An unexpected Super Admin service error occurred.'
    )
  })
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

  async function fetchLibraries() {
    const response = await runRequest(() => superAdminService.getLibraries())
    libraries.value = response.data.libraries
    return response
  }

  async function createLibrary(payload) {
    const response = await runRequest(
      () => superAdminService.createLibrary(payload),
      true,
    )
    syncManagementData(response.data)
    return response
  }

  async function updateLibrary(libraryId, payload) {
    const response = await runRequest(
      () => superAdminService.updateLibrary(libraryId, payload),
      true,
    )
    syncManagementData(response.data)
    return response
  }

  async function setLibraryStatus(libraryId, status) {
    const response = await runRequest(
      () => superAdminService.setLibraryStatus(libraryId, status),
      true,
    )
    syncManagementData(response.data)
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
    owners,
    analytics,
    settings,
    isLoading,
    isSaving,
    error,
    errorMessage,
    activeLibraries,
    availableLibraries,
    activeOwners,
    fetchDashboard,
    fetchLibraries,
    createLibrary,
    updateLibrary,
    setLibraryStatus,
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
