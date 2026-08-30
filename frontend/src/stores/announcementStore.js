import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import {
  ANNOUNCEMENT_AUDIENCES,
  ANNOUNCEMENT_CATEGORIES,
  ANNOUNCEMENT_STATUSES,
} from '../constants/announcement.js'
import * as announcementService from '../services/announcementService.js'

function emptySummary() {
  return {
    total: 0,
    published: 0,
    drafts: 0,
    scheduled: 0,
    archived: 0,
    expired: 0,
    important: 0,
  }
}

function emptyPagination() {
  return {
    page: 1,
    pageSize: 10,
    totalItems: 0,
    totalPages: 0,
  }
}

function initialFilters() {
  return {
    search: '',
    status: '',
    category: '',
    priority: '',
    page: 1,
    pageSize: 10,
    sortBy: 'createdAt',
    sortOrder: 'desc',
  }
}

export const useAnnouncementStore = defineStore('announcements', () => {
  const announcements = ref([])
  const summary = ref(emptySummary())
  const pagination = ref(emptyPagination())
  const filters = ref(initialFilters())
  const isLoading = ref(false)
  const isSaving = ref(false)
  const error = ref(null)
  let latestListRequest = 0

  const categories = ref(ANNOUNCEMENT_CATEGORIES)
  const audiences = ref(ANNOUNCEMENT_AUDIENCES)
  const errorMessage = computed(() => {
    if (!error.value) return ''

    return (
      error.value?.response?.data?.error?.message ||
      error.value?.response?.data?.message ||
      error.value?.message ||
      'An unexpected announcement service error occurred.'
    )
  })
  const errorRequestId = computed(
    () => error.value?.response?.data?.requestId || '',
  )

  function syncListResponse(response) {
    announcements.value = response?.data?.announcements || []
    summary.value = response?.summary || emptySummary()
    pagination.value = response?.meta || emptyPagination()
  }

  async function fetchAnnouncements(nextFilters = filters.value) {
    filters.value = { ...filters.value, ...nextFilters }
    const requestNumber = ++latestListRequest
    isLoading.value = true
    error.value = null
    try {
      const response = await announcementService.getAnnouncements({
        ...filters.value,
      })
      if (requestNumber === latestListRequest) {
        syncListResponse(response)
      }
      return response
    } catch (requestError) {
      if (requestNumber === latestListRequest) {
        error.value = requestError
      }
      throw requestError
    } finally {
      if (requestNumber === latestListRequest) {
        isLoading.value = false
      }
    }
  }

  async function refreshAfterMutation() {
    if (
      filters.value.page > 1 &&
      announcements.value.length === 1
    ) {
      filters.value.page -= 1
    }
    return fetchAnnouncements()
  }

  async function runMutation(request) {
    isSaving.value = true
    error.value = null
    try {
      const response = await request()
      await refreshAfterMutation()
      return response
    } catch (requestError) {
      error.value = requestError
      if (requestError?.response?.status === 409) {
        const conflict = requestError
        try {
          await fetchAnnouncements()
        } catch {
          // Keep the mutation conflict as the actionable error.
        } finally {
          error.value = conflict
        }
      }
      throw requestError
    } finally {
      isSaving.value = false
    }
  }

  async function createAnnouncement(payload) {
    return runMutation(async () => {
      if (payload.status !== ANNOUNCEMENT_STATUSES.PUBLISHED) {
        return announcementService.createAnnouncement(payload)
      }
      const created = await announcementService.createAnnouncement({
        ...payload,
        status: ANNOUNCEMENT_STATUSES.DRAFT,
        scheduledAt: null,
      })
      return announcementService.publishAnnouncement(created.data.id)
    })
  }

  async function updateAnnouncement(announcementId, payload) {
    return runMutation(() =>
      announcementService.updateAnnouncement(announcementId, payload),
    )
  }

  async function publishAnnouncement(announcementId) {
    return runMutation(() =>
      announcementService.publishAnnouncement(announcementId),
    )
  }

  async function archiveAnnouncement(announcementId, reason) {
    return runMutation(() =>
      announcementService.archiveAnnouncement(announcementId, reason),
    )
  }

  async function deleteAnnouncement(announcementId) {
    return runMutation(() =>
      announcementService.deleteAnnouncement(announcementId),
    )
  }

  function clearFilters() {
    filters.value = initialFilters()
  }

  function setPage(page) {
    filters.value.page = page
    return fetchAnnouncements()
  }

  function clearError() {
    error.value = null
  }

  return {
    announcements,
    summary,
    pagination,
    categories,
    audiences,
    filters,
    isLoading,
    isSaving,
    error,
    errorMessage,
    errorRequestId,
    fetchAnnouncements,
    createAnnouncement,
    updateAnnouncement,
    publishAnnouncement,
    archiveAnnouncement,
    deleteAnnouncement,
    clearFilters,
    setPage,
    clearError,
  }
})
