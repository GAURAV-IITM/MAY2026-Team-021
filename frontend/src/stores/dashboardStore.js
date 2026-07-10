import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import * as dashboardService from '../services/dashboardService.js'

export const useDashboardStore = defineStore('dashboard', () => {
  const summary = ref(null)
  const isLoading = ref(false)
  const error = ref(null)

  const hasSummary = computed(() => Boolean(summary.value))
  const metrics = computed(() => summary.value?.metrics || {})
  const seatStatus = computed(() => summary.value?.seatStatus || [])
  const monthlyCollection = computed(
    () => summary.value?.monthlyCollection || [],
  )
  const shiftAvailability = computed(
    () => summary.value?.shiftAvailability || [],
  )
  const attentionItems = computed(() => summary.value?.attentionItems || [])
  const recentActivity = computed(() => summary.value?.recentActivity || [])
  const errorMessage = computed(() => {
    if (!error.value) return ''

    return (
      error.value?.response?.data?.message ||
      error.value?.message ||
      'An unexpected dashboard service error occurred.'
    )
  })

  async function fetchDashboardSummary() {
    isLoading.value = true
    error.value = null

    try {
      const response = await dashboardService.getDashboardSummary()
      summary.value = response.data

      return response
    } catch (requestError) {
      error.value = requestError
      throw requestError
    } finally {
      isLoading.value = false
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
    attentionItems,
    recentActivity,
    errorMessage,
    fetchDashboardSummary,
    refreshDashboard: fetchDashboardSummary,
    clearError,
  }
})
