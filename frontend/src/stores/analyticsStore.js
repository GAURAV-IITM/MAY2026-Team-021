import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { REPORT_DEFAULT_MONTH_COUNT } from '../constants/reports.js'
import * as analyticsService from '../services/analyticsService.js'

export const useAnalyticsStore = defineStore('analytics', () => {
  const reports = ref(null)
  const options = ref({ months: [], floors: [], shifts: [] })
  const filters = ref({
    startMonth: '',
    endMonth: '',
    floorId: '',
    shiftId: '',
  })
  const isLoading = ref(false)
  const isOptionsLoading = ref(false)
  const isExporting = ref(false)
  const error = ref(null)
  let latestReportRequest = 0
  let latestOptionsRequest = 0

  const hasReports = computed(() => Boolean(reports.value))
  const errorMessage = computed(() => {
    if (!error.value) return ''

    return (
      error.value?.response?.data?.message ||
      error.value?.message ||
      'An unexpected reports service error occurred.'
    )
  })
  const requestId = computed(
    () =>
      error.value?.response?.headers?.['x-request-id'] ||
      error.value?.response?.data?.error?.requestId ||
      '',
  )

  function setDefaultFilters() {
    if (!options.value.months.length) return

    const latestMonth = options.value.months.at(-1).value
    const startIndex = Math.max(
      0,
      options.value.months.length - REPORT_DEFAULT_MONTH_COUNT,
    )

    filters.value = {
      startMonth: options.value.months[startIndex].value,
      endMonth: latestMonth,
      floorId: '',
      shiftId: '',
    }
  }

  async function fetchOptions() {
    const request = ++latestOptionsRequest
    isOptionsLoading.value = true

    try {
      const response = await analyticsService.getReportOptions()
      if (request !== latestOptionsRequest) return response

      options.value = response.data
      if (!filters.value.startMonth || !filters.value.endMonth) {
        setDefaultFilters()
      }
      return response
    } catch (requestError) {
      if (request === latestOptionsRequest) error.value = requestError
      throw requestError
    } finally {
      if (request === latestOptionsRequest) isOptionsLoading.value = false
    }
  }

  async function fetchReports(nextFilters = filters.value) {
    const request = ++latestReportRequest
    isLoading.value = true
    error.value = null

    try {
      if (!options.value.months.length) await fetchOptions()

      const requestedFilters = { ...filters.value, ...nextFilters }
      const response = await analyticsService.getReports(requestedFilters)
      if (request !== latestReportRequest) return response

      reports.value = response.data
      filters.value = {
        startMonth: response.data.filters.startMonth,
        endMonth: response.data.filters.endMonth,
        floorId: response.data.filters.floorId || '',
        shiftId: response.data.filters.shiftId || '',
      }
      return response
    } catch (requestError) {
      if (request === latestReportRequest) error.value = requestError
      throw requestError
    } finally {
      if (request === latestReportRequest) isLoading.value = false
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
    isOptionsLoading,
    isExporting,
    error,
    hasReports,
    errorMessage,
    requestId,
    fetchOptions,
    fetchReports,
    refreshReports: fetchReports,
    resetFilters,
    exportCurrentReport,
    clearError,
  }
})
