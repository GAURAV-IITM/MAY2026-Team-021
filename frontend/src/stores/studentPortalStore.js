import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import * as studentPortalService from '../services/studentPortalService.js'

export const useStudentPortalStore = defineStore('studentPortal', () => {
  const dashboard = ref(null)
  const profile = ref(null)
  const seat = ref(null)
  const allocations = ref([])
  const feeSummary = ref(null)
  const receipts = ref([])
  const requests = ref([])
  const shifts = ref([])
  const announcements = ref([])
  const selectedReceipt = ref(null)
  const isLoading = ref(false)
  const isSaving = ref(false)
  const error = ref(null)

  const errorMessage = computed(() => {
    if (!error.value) return ''

    return (
      error.value?.response?.data?.message ||
      error.value?.message ||
      'An unexpected student portal error occurred.'
    )
  })
  const unreadAnnouncementCount = computed(
    () => announcements.value.filter((announcement) => !announcement.isRead).length,
  )
  const pendingRequest = computed(
    () => requests.value.find((request) => request.status === 'pending') || null,
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

  async function fetchDashboard(studentId) {
    const response = await runRequest(() => studentPortalService.getDashboard(studentId))
    dashboard.value = response.data
    profile.value = response.data.profile
    seat.value = response.data.seat
    allocations.value = response.data.allocations
    feeSummary.value = response.data.feeSummary
    return response
  }

  async function fetchSeat(studentId) {
    const response = await runRequest(() => studentPortalService.getSeat(studentId))
    seat.value = response.data.seat
    allocations.value = response.data.allocations
    return response
  }

  async function fetchFees(studentId) {
    const response = await runRequest(() => studentPortalService.getFees(studentId))
    feeSummary.value = response.data.feeSummary
    return response
  }

  async function fetchReceipts(studentId) {
    const response = await runRequest(() => studentPortalService.getReceipts(studentId))
    receipts.value = response.data.receipts
    return response
  }

  async function fetchRequests(studentId) {
    const response = await runRequest(() => studentPortalService.getRequests(studentId))
    requests.value = response.data.requests
    shifts.value = response.data.shifts
    return response
  }

  async function createSeatRequest(studentId, payload) {
    const response = await runRequest(
      () => studentPortalService.createSeatRequest(studentId, payload),
      true,
    )
    requests.value = response.data.requests
    return response
  }

  async function cancelSeatRequest(studentId, requestId) {
    const response = await runRequest(
      () => studentPortalService.cancelSeatRequest(studentId, requestId),
      true,
    )
    requests.value = response.data.requests
    return response
  }

  async function fetchAnnouncements(studentId) {
    const response = await runRequest(() => studentPortalService.getAnnouncements(studentId))
    announcements.value = response.data.announcements
    return response
  }

  async function markAnnouncementRead(studentId, announcementId) {
    const response = await runRequest(
      () => studentPortalService.markAnnouncementRead(studentId, announcementId),
      true,
    )
    announcements.value = response.data.announcements
    return response
  }

  async function fetchProfile(studentId) {
    const response = await runRequest(() => studentPortalService.getProfile(studentId))
    profile.value = response.data.profile
    return response
  }

  async function updateProfile(studentId, payload) {
    const response = await runRequest(
      () => studentPortalService.updateProfile(studentId, payload),
      true,
    )
    profile.value = response.data.profile
    return response
  }

  function selectReceipt(receipt) {
    selectedReceipt.value = receipt
  }

  function clearSelectedReceipt() {
    selectedReceipt.value = null
  }

  function clearError() {
    error.value = null
  }

  return {
    dashboard,
    profile,
    seat,
    allocations,
    feeSummary,
    receipts,
    requests,
    shifts,
    announcements,
    selectedReceipt,
    isLoading,
    isSaving,
    error,
    errorMessage,
    unreadAnnouncementCount,
    pendingRequest,
    fetchDashboard,
    fetchSeat,
    fetchFees,
    fetchReceipts,
    fetchRequests,
    createSeatRequest,
    cancelSeatRequest,
    fetchAnnouncements,
    markAnnouncementRead,
    fetchProfile,
    updateProfile,
    selectReceipt,
    clearSelectedReceipt,
    clearError,
  }
})
