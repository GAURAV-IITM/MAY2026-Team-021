import assert from 'node:assert/strict'
import test from 'node:test'

import apiClient from '../src/api/axios.js'
import { buildPlatformDashboardParams, getDashboard } from '../src/services/superAdminService.js'

function response(config, data) {
  return { config, data, headers: {}, status: 200, statusText: 'OK' }
}

test('loads the platform dashboard from the real API with month filters', async () => {
  assert.deepEqual(buildPlatformDashboardParams({ startMonth: '2026-01', endMonth: '2026-07' }), {
    startMonth: '2026-01',
    endMonth: '2026-07',
  })

  let request
  const payload = {
    message: 'Dashboard fetched.',
    data: {
      totals: { totalLibraries: 4, totalOwners: 2, totalStudents: 20 },
      libraryStatus: [],
      trend: [],
      topLibraries: [],
      recentActivity: [],
    },
  }
  apiClient.defaults.adapter = async (config) => {
    request = config
    return response(config, payload)
  }

  const result = await getDashboard({ startMonth: '2026-01', endMonth: '2026-07' })
  assert.equal(request.url, '/platform/dashboard')
  assert.equal(request.params.startMonth, '2026-01')
  assert.equal(request.params.endMonth, '2026-07')
  assert.equal(result.data.totals.totalLibraries, 4)
})

test('propagates dashboard API failures without mock fallback', async () => {
  apiClient.defaults.adapter = async (config) => {
    const error = new Error('Dashboard unavailable')
    error.config = config
    error.response = {
      status: 500,
      headers: { 'x-request-id': 'dashboard-request-id' },
      data: {
        error: { code: 'INTERNAL_SERVER_ERROR', message: 'Dashboard unavailable' },
        requestId: 'dashboard-request-id',
      },
    }
    throw error
  }

  await assert.rejects(() => getDashboard(), /Dashboard unavailable/)
})
