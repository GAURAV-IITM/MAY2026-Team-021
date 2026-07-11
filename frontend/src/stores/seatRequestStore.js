import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import * as studentPortalService from '../services/studentPortalService.js'

export const useSeatRequestStore = defineStore('seatRequests', () => {
  const requests = ref([])
  const selectedRequest = ref(null)
  const isLoading = ref(false)
  const isSaving = ref(false)
  const error = ref(null)

  const errorMessage = computed(() => {
    if (!error.value) return ''

    return (
      error.value?.response?.data?.message ||
      error.value?.message ||
      'An unexpected seat request error occurred.'
    )
  })
  const pendingCount = computed(
    () => requests.value.filter((request) => request.status === 'pending').length,
  )
  const approvedCount = computed(
    () => requests.value.filter((request) => request.status === 'approved').length,
  )
  const rejectedCount = computed(
    () => requests.value.filter((request) => request.status === 'rejected').length,
  )

  async function fetchRequests(admin) {
    isLoading.value = true
    error.value = null

    try {
      const response = await studentPortalService.getAdminSeatRequests(admin)
      requests.value = response.data.requests
      return response
    } catch (requestError) {
      error.value = requestError
      throw requestError
    } finally {
      isLoading.value = false
    }
  }

  async function reviewRequest(admin, requestId, payload) {
    isSaving.value = true
    error.value = null

    try {
      const response = await studentPortalService.reviewSeatRequest(
        admin,
        requestId,
        payload,
      )
      requests.value = response.data.requests
      selectedRequest.value = response.data.request
      return response
    } catch (requestError) {
      error.value = requestError
      throw requestError
    } finally {
      isSaving.value = false
    }
  }

  function selectRequest(request) {
    selectedRequest.value = request
  }

  function clearSelectedRequest() {
    selectedRequest.value = null
  }

  return {
    requests,
    selectedRequest,
    isLoading,
    isSaving,
    error,
    errorMessage,
    pendingCount,
    approvedCount,
    rejectedCount,
    fetchRequests,
    reviewRequest,
    selectRequest,
    clearSelectedRequest,
  }
})
