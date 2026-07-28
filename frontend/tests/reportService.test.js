import assert from 'node:assert/strict'
import test from 'node:test'

import apiClient from '../src/api/axios.js'
import {
  buildReportParams,
  exportReport,
  getReportOptions,
  getReports,
} from '../src/services/analyticsService.js'
import {
  buildDashboardParams,
  getDashboardSummary,
} from '../src/services/dashboardService.js'


function response(config, data) {
  return {
    config,
    data,
    headers: { 'x-request-id': 'report-service-test' },
    status: 200,
    statusText: 'OK',
  }
}


test('maps dashboard filters without accepting tenant identifiers', async () => {
  assert.deepEqual(
    buildDashboardParams({
      date: '2026-07-28',
      billingMonth: '2026-07',
      libraryId: 'must-not-be-sent',
    }),
    {
      date: '2026-07-28',
      billingMonth: '2026-07',
    },
  )

  let requestConfig
  apiClient.defaults.adapter = async (config) => {
    requestConfig = config
    return response(config, {
      message: 'Dashboard fetched.',
      data: { metrics: { totalStudents: 0 } },
    })
  }

  const result = await getDashboardSummary({ billingMonth: '2026-07' })
  assert.equal(requestConfig.url, '/reports/dashboard')
  assert.equal(requestConfig.params.billingMonth, '2026-07')
  assert.equal(result.data.metrics.totalStudents, 0)
})


test('loads report options and maps report filters', async () => {
  assert.deepEqual(
    buildReportParams({
      startMonth: '2026-05',
      endMonth: '2026-07',
      floorId: 'floor-id',
      shiftId: 'shift-id',
      libraryId: 'must-not-be-sent',
    }),
    {
      startMonth: '2026-05',
      endMonth: '2026-07',
      floorId: 'floor-id',
      shiftId: 'shift-id',
    },
  )

  const requests = []
  apiClient.defaults.adapter = async (config) => {
    requests.push(config)
    const data = config.url.endsWith('/options')
      ? { months: [], floors: [], shifts: [] }
      : { filters: { startMonth: '2026-05', endMonth: '2026-07' } }
    return response(config, { message: 'Fetched.', data })
  }

  await getReportOptions()
  const reports = await getReports({
    startMonth: '2026-05',
    endMonth: '2026-07',
    floorId: 'floor-id',
    shiftId: 'shift-id',
  })

  assert.equal(requests[0].url, '/reports/options')
  assert.equal(requests[1].url, '/reports')
  assert.equal(requests[1].params.floorId, 'floor-id')
  assert.equal(requests[1].params.shiftId, 'shift-id')
  assert.equal(reports.data.filters.endMonth, '2026-07')
})


test('CSV export uses loaded report data and safely escapes text', async () => {
  const result = await exportReport('pending', {
    generatedAt: '2026-07-28T10:00:00Z',
    filters: {
      startMonth: '2026-07',
      endMonth: '2026-07',
      floorId: null,
      shiftId: null,
      reportDate: '2026-07-28',
    },
    pendingPayments: {
      records: [
        {
          studentName: 'Sharma, "Aarav"',
          enrollmentNumber: 'STU-1',
          phone: '9876543210',
          seatNumber: 'A-01',
          month: '2026-07',
          totalAmount: '1000.00',
          paidAmount: '300.00',
          amount: '700.00',
          dueDate: '2026-07-10',
          ageing: '18 days overdue',
        },
      ],
    },
  })

  assert.equal(result.data.fileName, 'pending-report-2026-07-to-2026-07.csv')
  assert.match(result.data.content, /"Sharma, ""Aarav"""/)
  assert.match(result.data.content, /700\.00/)
})
