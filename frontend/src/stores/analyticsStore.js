import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import * as analyticsService from '../services/analyticsService.js'

export const useAnalyticsStore = defineStore('analytics', () => {
  const reports = ref(null)
  const options = ref({ months: [], floors: [], shifts: [] })
  const filters = ref({ startMonth: '', endMonth: '', floor: '', shiftId: '' })
  const isLoading = ref(false)
  const isExporting = ref(false)
  const error = ref(null)

  const hasReports = computed(() => Boolean(reports.value))
  const errorMessage = computed(() => {
    if (!error.value) return ''

    return (
      error.value?.response?.data?.message ||
      error.value?.message ||
      'An unexpected reports service error occurred.'
    )
  })

  function setDefaultFilters() {
    if (!options.value.months.length) return

    const latestMonth = options.value.months.at(-1).value
    const startIndex = Math.max(0, options.value.months.length - 3)

    filters.value = {
      startMonth: options.value.months[startIndex].value,
      endMonth: latestMonth,
      floor: '',
      shiftId: '',
    }
  }

  async function fetchOptions() {
    const response = await analyticsService.getReportOptions()
    options.value = response.data

    if (!filters.value.startMonth || !filters.value.endMonth) {
      setDefaultFilters()
    }

    return response
  }

  async function fetchReports(nextFilters = filters.value) {
    isLoading.value = true
    error.value = null

    try {
      if (!options.value.months.length) {
        await fetchOptions()
      }

      filters.value = { ...filters.value, ...nextFilters }
      const response = await analyticsService.getReports(filters.value)
      reports.value = response.data
      filters.value = { ...response.data.filters }

      return response
    } catch (requestError) {
      error.value = requestError
      throw requestError
    } finally {
      isLoading.value = false
    }
  }

  async function resetFilters() {
    setDefaultFilters()
    return fetchReports(filters.value)
  }

  async function exportCurrentReport(reportType) {
    isExporting.value = true
    error.value = null

    try {
      return await analyticsService.exportReport(reportType, reports.value)
    } catch (requestError) {
      error.value = requestError
      throw requestError
    } finally {
      isExporting.value = false
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    reports,
    options,
    filters,
    isLoading,
    isExporting,
    error,
    hasReports,
    errorMessage,
    fetchOptions,
    fetchReports,
    refreshReports: fetchReports,
    resetFilters,
    exportCurrentReport,
    clearError,
  }
})
