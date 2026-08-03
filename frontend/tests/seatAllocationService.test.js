import assert from 'node:assert/strict'
import test from 'node:test'

import { AxiosError } from 'axios'

import apiClient from '../src/api/axios.js'
import {
  allocateSeat,
  buildSeatAllocationParams,
  buildSeatAvailabilityParams,
  closeSeatAllocation,
  fetchSeatAvailability,
} from '../src/services/seatService.js'

function response(config, data, status = 200) {
  return {
    config,
    data,
    headers: {},
    status,
    statusText: status === 200 ? 'OK' : 'Conflict',
  }
}

test('maps repeated shift IDs and availability filters to query parameters', async () => {
  const params = buildSeatAvailabilityParams({
    shiftIds: ['morning-id', 'evening-id'],
    startDate: '2026-08-01',
    endDate: '2026-08-31',
    floorId: 'floor-id',
  })

  assert.deepEqual(params.getAll('shiftId'), ['morning-id', 'evening-id'])
  assert.equal(params.get('startDate'), '2026-08-01')
  assert.equal(params.get('endDate'), '2026-08-31')
  assert.equal(params.get('floorId'), 'floor-id')

  let requestConfig
  apiClient.defaults.adapter = async (config) => {
    requestConfig = config
    return response(config, { data: { seats: [] } })
  }
  await fetchSeatAvailability({
    shiftIds: ['morning-id'],
    startDate: '2026-08-01',
  })
  assert.equal(requestConfig.url, '/seat-allocations/availability')
  assert.equal(requestConfig.params.get('shiftId'), 'morning-id')
})

test('maps allocation list defaults and create payload without dropping shifts', async () => {
  assert.deepEqual(buildSeatAllocationParams({ status: 'active' }), {
    page: 1,
    pageSize: 20,
    search: undefined,
    sortBy: 'allocatedAt',
    sortOrder: 'desc',
    studentId: undefined,
    seatId: undefined,
    shiftId: undefined,
    status: 'active',
    startDate: undefined,
    endDate: undefined,
  })

  let requestConfig
  apiClient.defaults.adapter = async (config) => {
    requestConfig = config
    return response(config, { data: { allocationCount: 2, allocations: [] } }, 201)
  }
  await allocateSeat({
    studentId: 'student-id',
    seatId: 'seat-id',
    shiftIds: ['morning-id', 'evening-id'],
    startDate: '2026-08-01',
    endDate: '2026-08-31',
    notes: 'Window seat',
    shift: 'must-not-be-sent',
  })

  assert.equal(requestConfig.url, '/seat-allocations')
  assert.deepEqual(JSON.parse(requestConfig.data), {
    studentId: 'student-id',
    seatId: 'seat-id',
    shiftIds: ['morning-id', 'evening-id'],
    startDate: '2026-08-01',
    endDate: '2026-08-31',
    notes: 'Window seat',
  })
})

test('maps status updates and preserves structured conflict errors', async () => {
  let requestConfig
  apiClient.defaults.adapter = async (config) => {
    requestConfig = config
    return response(config, { data: { id: 'allocation-id', status: 'cancelled' } })
  }
  await closeSeatAllocation('allocation-id', {
    status: 'cancelled',
    effectiveEndDate: '2026-08-10',
    closeReason: 'Student left',
  })
  assert.equal(requestConfig.url, '/seat-allocations/allocation-id/status')
  assert.deepEqual(JSON.parse(requestConfig.data), {
    status: 'cancelled',
    effectiveEndDate: '2026-08-10',
    closeReason: 'Student left',
  })

  apiClient.defaults.adapter = (config) => {
    const conflictResponse = response(
      config,
      {
        error: {
          code: 'SEAT_ALLOCATION_CONFLICT',
          message: 'Seat A-01 is already allocated.',
          details: { studentName: 'Existing Student' },
        },
        requestId: 'request-409',
      },
      409,
    )
    return Promise.reject(
      new AxiosError(
        'Conflict',
        AxiosError.ERR_BAD_REQUEST,
        config,
        null,
        conflictResponse,
      ),
    )
  }

  await assert.rejects(
    allocateSeat({
      studentId: 'student-id',
      seatId: 'seat-id',
      shiftIds: ['morning-id'],
      startDate: '2026-08-01',
      endDate: '2026-08-31',
    }),
    (error) => {
      assert.equal(error.response.data.error.code, 'SEAT_ALLOCATION_CONFLICT')
      assert.equal(error.response.data.requestId, 'request-409')
      return true
    },
  )
})
