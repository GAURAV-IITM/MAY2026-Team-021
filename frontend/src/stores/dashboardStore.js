import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import * as dashboardService from '../services/dashboardService.js'

export const useDashboardStore = defineStore('dashboard', () => {
  const summary = ref(null)
  const isLoading = ref(false)
  const error = ref(null)
  let latestRequest = 0

  const hasSummary = computed(() => Boolean(summary.value))
  const metrics = computed(() => summary.value?.metrics || {})
  const seatStatus = computed(() => summary.value?.seatStatus || [])
  const monthlyCollection = computed(
    () => summary.value?.monthlyCollection || [],
  )
  const shiftAvailability = computed(
    () => summary.value?.shiftAvailability || [],
  )
  const studentsRequiringAttention = computed(
    () => summary.value?.studentsRequiringAttention || [],
  )
  const recentActivity = computed(() => summary.value?.recentActivity || [])
  const errorMessage = computed(() => {
    if (!error.value) return ''

    return (
      error.value?.response?.data?.message ||
      error.value?.message ||
      'An unexpected dashboard service error occurred.'
    )
  })
  const requestId = computed(
    () =>
      error.value?.response?.headers?.['x-request-id'] ||
      error.value?.response?.data?.error?.requestId ||
      '',
  )

  async function fetchDashboardSummary(filters = {}) {
    const request = ++latestRequest
    isLoading.value = true
    error.value = null

    try {
      const response = await dashboardService.getDashboardSummary(filters)
      if (request === latestRequest) summary.value = response.data
      return response
    } catch (requestError) {
      if (request === latestRequest) error.value = requestError
      throw requestError
    } finally {
      if (request === latestRequest) isLoading.value = false
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    summary,
    isLoading,
    error,
    hasSummary,
    metrics,
    seatStatus,
    monthlyCollection,
    shiftAvailability,
    studentsRequiringAttention,
    recentActivity,
    errorMessage,
    requestId,
    fetchDashboardSummary,
    refreshDashboard: fetchDashboardSummary,
    clearError,
  }
})
