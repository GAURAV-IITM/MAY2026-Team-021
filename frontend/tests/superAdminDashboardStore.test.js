import assert from 'node:assert/strict'
import test from 'node:test'

import { createPinia, setActivePinia } from 'pinia'

import apiClient from '../src/api/axios.js'
import { useSuperAdminStore } from '../src/stores/superAdminStore.js'

function dashboardResponse(config, totalLibraries) {
  return {
    config,
    headers: {},
    status: 200,
    statusText: 'OK',
    data: {
      message: 'Dashboard fetched.',
      data: {
        totals: { totalLibraries },
        libraryStatus: [],
        trend: [],
        topLibraries: [],
        recentActivity: [],
      },
    },
  }
}

test.beforeEach(() => setActivePinia(createPinia()))

test('keeps the latest dashboard range and response', async () => {
  const pending = []
  apiClient.defaults.adapter = (config) =>
    new Promise((resolve) => pending.push({ config, resolve }))
  const store = useSuperAdminStore()

  const first = store.fetchDashboard({ startMonth: '2026-01', endMonth: '2026-07' })
  await new Promise((resolve) => setImmediate(resolve))
  const second = store.fetchDashboard({ startMonth: '2025-08', endMonth: '2026-07' })
  await new Promise((resolve) => setImmediate(resolve))
  pending[1].resolve(dashboardResponse(pending[1].config, 12))
  await second
  pending[0].resolve(dashboardResponse(pending[0].config, 7))
  await first

  assert.equal(store.dashboard.totals.totalLibraries, 12)
  assert.deepEqual(store.dashboardFilters, {
    startMonth: '2025-08',
    endMonth: '2026-07',
  })
})

test('exposes dashboard request IDs and retains the last successful data', async () => {
  let shouldFail = false
  apiClient.defaults.adapter = async (config) => {
    if (!shouldFail) return dashboardResponse(config, 3)
    const error = new Error('Request failed')
    error.config = config
    error.response = {
      status: 500,
      headers: { 'x-request-id': 'dashboard-request-500' },
      data: {
        error: { code: 'INTERNAL_SERVER_ERROR', message: 'Dashboard unavailable.' },
        requestId: 'dashboard-request-500',
      },
    }
    throw error
  }
  const store = useSuperAdminStore()
  await store.fetchDashboard()
  shouldFail = true

  await assert.rejects(() => store.fetchDashboard())
  assert.equal(store.dashboard.totals.totalLibraries, 3)
  assert.equal(store.errorRequestId, 'dashboard-request-500')
  assert.equal(store.errorMessage, 'Dashboard unavailable.')
})
