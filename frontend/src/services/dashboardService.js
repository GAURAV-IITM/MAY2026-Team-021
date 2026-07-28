import apiClient from '../api/axios.js'

export function buildDashboardParams(filters = {}) {
  return {
    date: filters.date || undefined,
    billingMonth: filters.billingMonth || undefined,
  }
}

export async function getDashboardSummary(filters = {}) {
  const response = await apiClient.get('/reports/dashboard', {
    params: buildDashboardParams(filters),
  })

  return response.data
}

export async function getDashboardMetrics(filters = {}) {
  const response = await getDashboardSummary(filters)

  return {
    ...response,
    data: response.data.metrics,
  }
}
