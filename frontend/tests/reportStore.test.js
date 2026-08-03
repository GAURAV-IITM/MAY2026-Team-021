import assert from 'node:assert/strict'
import test from 'node:test'

import { createPinia, setActivePinia } from 'pinia'

import apiClient from '../src/api/axios.js'
import { useAnalyticsStore } from '../src/stores/analyticsStore.js'
import { useDashboardStore } from '../src/stores/dashboardStore.js'


function response(config, data) {
  return {
    config,
    headers: {},
    status: 200,
    statusText: 'OK',
    data: {
      message: 'Fetched.',
      data,
    },
  }
}


test.beforeEach(() => {
  setActivePinia(createPinia())
})


test('dashboard store keeps zero values and supports refresh', async () => {
  let requestCount = 0
  apiClient.defaults.adapter = async (config) => {
    requestCount += 1
    return response(config, {
      metrics: {
        totalStudents: 0,
        activeStudents: 0,
        collectedAmount: '0.00',
      },
      seatStatus: [],
      monthlyCollection: [],
      shiftAvailability: [],
      studentsRequiringAttention: [],
      recentActivity: [],
    })
  }

  const store = useDashboardStore()
  await store.fetchDashboardSummary()
  await store.refreshDashboard()

  assert.equal(store.hasSummary, true)
  assert.equal(store.metrics.totalStudents, 0)
  assert.deepEqual(store.studentsRequiringAttention, [])
  assert.equal(store.isLoading, false)
  assert.equal(requestCount, 2)
})


test('report store keeps the newest filtered response', async () => {
  const pending = []
  apiClient.defaults.adapter = (config) =>
    new Promise((resolve) => pending.push({ config, resolve }))

  const store = useAnalyticsStore()
  store.options = {
    months: [
      { value: '2026-06', label: 'June 2026' },
      { value: '2026-07', label: 'July 2026' },
    ],
    floors: [],
    shifts: [],
  }
  store.filters = {
    startMonth: '2026-06',
    endMonth: '2026-07',
    floorId: '',
    shiftId: '',
  }

  const first = store.fetchReports({ startMonth: '2026-06' })
  await new Promise((resolve) => setImmediate(resolve))
  const second = store.fetchReports({ startMonth: '2026-07' })
  await new Promise((resolve) => setImmediate(resolve))

  pending[1].resolve(
    response(pending[1].config, {
      marker: 'newest',
      filters: {
        startMonth: '2026-07',
        endMonth: '2026-07',
        floorId: null,
        shiftId: null,
      },
    }),
  )
  await second
  pending[0].resolve(
    response(pending[0].config, {
      marker: 'stale',
      filters: {
        startMonth: '2026-06',
        endMonth: '2026-07',
        floorId: null,
        shiftId: null,
      },
    }),
  )
  await first

  assert.equal(store.reports.marker, 'newest')
  assert.equal(store.filters.startMonth, '2026-07')
  assert.equal(store.isLoading, false)
})


test('report reset keeps options and restores the default period', async () => {
  apiClient.defaults.adapter = async (config) =>
    response(config, {
      marker: 'reset',
      filters: {
        startMonth: config.params.startMonth,
        endMonth: config.params.endMonth,
        floorId: null,
        shiftId: null,
      },
    })

  const store = useAnalyticsStore()
  store.options = {
    months: [
      { value: '2026-04', label: 'April 2026' },
      { value: '2026-05', label: 'May 2026' },
      { value: '2026-06', label: 'June 2026' },
      { value: '2026-07', label: 'July 2026' },
    ],
    floors: [{ value: 'floor-id', label: 'Floor 1' }],
    shifts: [{ value: 'shift-id', label: 'Morning' }],
  }
  store.filters = {
    startMonth: '2026-04',
    endMonth: '2026-05',
    floorId: 'floor-id',
    shiftId: 'shift-id',
  }

  await store.resetFilters()

  assert.deepEqual(store.filters, {
    startMonth: '2026-05',
    endMonth: '2026-07',
    floorId: '',
    shiftId: '',
  })
  assert.equal(store.reports.marker, 'reset')
})
