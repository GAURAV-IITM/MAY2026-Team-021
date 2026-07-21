import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import * as announcementService from '../services/announcementService.js'

export const useAnnouncementStore = defineStore('announcements', () => {
  const announcements = ref([])
  const summary = ref({ total: 0, published: 0, drafts: 0, scheduled: 0, archived: 0, expired: 0, important: 0 })
  const categories = ref([])
  const audiences = ref([])
  const filters = ref({ search: '', status: '', category: '' })
  const isLoading = ref(false)
  const isSaving = ref(false)
  const error = ref(null)

  const errorMessage = computed(() => {
    if (!error.value) return ''
    return error.value?.response?.data?.message || error.value?.message || 'An unexpected announcement service error occurred.'
  })

  function syncData(data) {
    announcements.value = data.announcements || []
    summary.value = data.summary || summary.value
    categories.value = data.categories || categories.value
    audiences.value = data.audiences || audiences.value
  }

  async function runRequest(request, saving = false) {
    const state = saving ? isSaving : isLoading
    state.value = true
    error.value = null
    try {
      const response = await request()
      syncData(response.data)
      return response
    } catch (requestError) {
      error.value = requestError
      throw requestError
    } finally {
      state.value = false
    }
  }

  async function fetchAnnouncements(admin, nextFilters = filters.value) {
    filters.value = { ...filters.value, ...nextFilters }
    return runRequest(() => announcementService.getAnnouncements(admin, filters.value))
  }

  async function createAnnouncement(admin, payload) {
    const response = await runRequest(() => announcementService.createAnnouncement(admin, payload), true)
    return fetchAnnouncements(admin, filters.value).then(() => response)
  }

  async function updateAnnouncement(admin, announcementId, payload) {
    const response = await runRequest(() => announcementService.updateAnnouncement(admin, announcementId, payload), true)
    return fetchAnnouncements(admin, filters.value).then(() => response)
  }

  async function publishAnnouncement(admin, announcementId) {
    const response = await runRequest(() => announcementService.publishAnnouncement(admin, announcementId), true)
    return fetchAnnouncements(admin, filters.value).then(() => response)
  }

  async function archiveAnnouncement(admin, announcementId) {
    const response = await runRequest(() => announcementService.archiveAnnouncement(admin, announcementId), true)
    return fetchAnnouncements(admin, filters.value).then(() => response)
  }

  async function deleteAnnouncement(admin, announcementId) {
    const response = await runRequest(() => announcementService.deleteAnnouncement(admin, announcementId), true)
    return fetchAnnouncements(admin, filters.value).then(() => response)
  }

  function clearFilters() {
    filters.value = { search: '', status: '', category: '' }
  }

  return {
    announcements,
    summary,
    categories,
    audiences,
    filters,
    isLoading,
    isSaving,
    error,
    errorMessage,
    fetchAnnouncements,
    createAnnouncement,
    updateAnnouncement,
    publishAnnouncement,
    archiveAnnouncement,
    deleteAnnouncement,
    clearFilters,
  }
})
