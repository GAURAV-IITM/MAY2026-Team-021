import assert from 'node:assert/strict'
import test from 'node:test'

import apiClient from '../src/api/axios.js'
import {
  buildSeatRequestParams,
  getSeatRequests,
  reviewSeatRequest,
} from '../src/services/seatRequestService.js'


function response(config, data) {
  return { config, data, headers: {}, status: 200, statusText: 'OK' }
}


test('maps server-backed request filters and normalizes list records', async () => {
  assert.deepEqual(
    buildSeatRequestParams({
      search: ' Aarav ',
      status: 'pending',
      page: 2,
      pageSize: 5,
    }),
    {
      page: 2,
      pageSize: 5,
      search: 'Aarav',
      status: 'pending',
      studentId: undefined,
      preferredFloorId: undefined,
      preferredShiftId: undefined,
      sortBy: 'submittedAt',
      sortOrder: 'desc',
    },
  )
  let requestConfig
  apiClient.defaults.adapter = async (config) => {
    requestConfig = config
    return response(config, {
      message: 'Fetched.',
      data: [{
        id: 'request-id',
        student: { id: 'student-id', name: 'Aarav', enrollmentNumber: 'STU-1' },
        currentAllocation: { seatNumber: 'A-01', shiftName: 'Morning' },
        preferredSeat: { seatNumber: 'B-02' },
        preferredFloor: { name: 'First Floor', levelNumber: 1 },
        preferredShift: { id: 'shift-id', name: 'Evening' },
        reviewNote: null,
        reviewedAt: null,
      }],
      meta: { page: 2, pageSize: 5, totalItems: 1, totalPages: 1 },
      summary: { total: 1, pending: 1 },
    })
  }
  const result = await getSeatRequests({ search: 'Aarav', status: 'pending' })
  assert.equal(requestConfig.url, '/seat-requests')
  assert.equal(result.data.requests[0].currentSeatNumber, 'A-01')
  assert.equal(result.data.requests[0].preferredShiftName, 'Evening')
})


test('sends only the review decision and note', async () => {
  let requestConfig
  apiClient.defaults.adapter = async (config) => {
    requestConfig = config
    return response(config, {
      message: 'Seat-change request rejected.',
      data: {
        id: 'request-id',
        student: { id: 'student-id', name: 'Aarav', enrollmentNumber: 'STU-1' },
        currentAllocation: null,
        preferredSeat: null,
        preferredFloor: null,
        preferredShift: { id: 'shift-id', name: 'Evening' },
        reviewNote: 'Not available.',
        reviewedAt: '2026-08-03T10:00:00Z',
      },
    })
  }
  await reviewSeatRequest('request-id', {
    decision: 'rejected',
    reviewNote: 'Not available.',
    seatId: 'must-not-be-sent',
  })
  assert.equal(requestConfig.url, '/seat-requests/request-id/review')
  assert.deepEqual(JSON.parse(requestConfig.data), {
    decision: 'rejected',
    reviewNote: 'Not available.',
  })
})
