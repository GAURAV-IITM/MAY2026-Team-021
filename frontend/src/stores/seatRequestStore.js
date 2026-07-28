import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import * as seatRequestService from '../services/seatRequestService.js'


const emptySummary = () => ({
  total: 0,
  pending: 0,
  approved: 0,
  rejected: 0,
  cancelled: 0,
})
const emptyPagination = () => ({
  page: 1,
  pageSize: 10,
  totalItems: 0,
  totalPages: 0,
})
const initialFilters = () => ({
  search: '',
  status: '',
  preferredShiftId: '',
  page: 1,
  pageSize: 10,
  sortBy: 'submittedAt',
  sortOrder: 'desc',
})


export const useSeatRequestStore = defineStore('seatRequests', () => {
  const requests = ref([])
  const selectedRequest = ref(null)
  const summary = ref(emptySummary())
  const pagination = ref(emptyPagination())
  const filters = ref(initialFilters())
  const isLoading = ref(false)
  const isSaving = ref(false)
  const error = ref(null)
  let latestRequest = 0

  const errorMessage = computed(() =>
    error.value?.response?.data?.error?.message ||
    error.value?.response?.data?.message ||
    error.value?.message ||
    '',
  )
  const errorRequestId = computed(
    () => error.value?.response?.data?.requestId || '',
  )
  const errorCode = computed(
    () => error.value?.response?.data?.error?.code || '',
  )
  const pendingCount = computed(() => summary.value.pending)
  const approvedCount = computed(() => summary.value.approved)
  const rejectedCount = computed(() => summary.value.rejected)

  async function fetchRequests(nextFilters = filters.value) {
    filters.value = { ...filters.value, ...nextFilters }
    const requestNumber = ++latestRequest
    isLoading.value = true
    error.value = null
    try {
      const response = await seatRequestService.getSeatRequests({
        ...filters.value,
      })
      if (requestNumber === latestRequest) {
        requests.value = response.data.requests
        summary.value = response.summary || emptySummary()
        pagination.value = response.meta || emptyPagination()
      }
      return response
    } catch (requestError) {
      if (requestNumber === latestRequest) error.value = requestError
      throw requestError
    } finally {
      if (requestNumber === latestRequest) isLoading.value = false
    }
  }

  async function reviewRequest(requestId, payload) {
    isSaving.value = true
    error.value = null
    try {
      const response = await seatRequestService.reviewSeatRequest(
        requestId,
        payload,
      )
      selectedRequest.value = response.data
      await fetchRequests()
      return response
    } catch (requestError) {
      error.value = requestError
      if (requestError?.response?.status === 409) {
        const conflict = requestError
        const details = conflict.response?.data?.error?.details || {}
        if (
          selectedRequest.value &&
          details.currentStatus
        ) {
          selectedRequest.value = {
            ...selectedRequest.value,
            status: details.currentStatus,
            resolvedAt: details.reviewedAt || selectedRequest.value.resolvedAt,
          }
        }
        try {
          await fetchRequests()
        } catch {
          // Preserve the review conflict as the actionable error.
        } finally {
          error.value = conflict
        }
      }
      throw requestError
    } finally {
      isSaving.value = false
    }
  }

  function selectRequest(request) {
    error.value = null
    selectedRequest.value = request
  }
  function clearSelectedRequest() {
    selectedRequest.value = null
    error.value = null
  }
  function clearFilters() {
    filters.value = initialFilters()
  }
  function setPage(page) {
    filters.value.page = page
    return fetchRequests()
  }

  return {
    requests,
    selectedRequest,
    summary,
    pagination,
    filters,
    isLoading,
    isSaving,
    error,
    errorMessage,
    errorRequestId,
    errorCode,
    pendingCount,
    approvedCount,
    rejectedCount,
    fetchRequests,
    reviewRequest,
    selectRequest,
    clearSelectedRequest,
    clearFilters,
    setPage,
  }
})
