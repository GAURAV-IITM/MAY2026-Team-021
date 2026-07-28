import assert from 'node:assert/strict'
import test from 'node:test'

import { AxiosError } from 'axios'
import { createPinia, setActivePinia } from 'pinia'

import apiClient from '../src/api/axios.js'
import { useSeatRequestStore } from '../src/stores/seatRequestStore.js'


function listResponse(config, id) {
  return {
    config,
    headers: {},
    status: 200,
    statusText: 'OK',
    data: {
      data: [{
        id,
        status: 'pending',
        student: { id: 'student', name: id, enrollmentNumber: 'STU-1' },
        currentAllocation: null,
        preferredSeat: null,
        preferredFloor: null,
        preferredShift: { id: 'shift', name: 'Morning' },
      }],
      meta: { page: 1, pageSize: 10, totalItems: 1, totalPages: 1 },
      summary: { total: 1, pending: 1, approved: 0, rejected: 0, cancelled: 0 },
    },
  }
}


test.beforeEach(() => setActivePinia(createPinia()))


test('applies only the latest request list response', async () => {
  const pending = []
  apiClient.defaults.adapter = (config) =>
    new Promise((resolve) => pending.push({ config, resolve }))
  const store = useSeatRequestStore()
  const first = store.fetchRequests({ search: 'first' })
  await new Promise((resolve) => setImmediate(resolve))
  const second = store.fetchRequests({ search: 'second' })
  await new Promise((resolve) => setImmediate(resolve))
  pending[1].resolve(listResponse(pending[1].config, 'second'))
  await second
  pending[0].resolve(listResponse(pending[0].config, 'stale'))
  await first
  assert.equal(store.requests[0].id, 'second')
  assert.equal(store.pendingCount, 1)
})


test('refreshes counts after review without resetting active filters', async () => {
  const requests = []
  apiClient.defaults.adapter = async (config) => {
    requests.push(config)
    if (config.method === 'patch') {
      return {
        config,
        headers: {},
        status: 200,
        statusText: 'OK',
        data: {
          message: 'Seat-change request approved. No seat allocation was changed.',
          data: {
            id: 'request-id',
            status: 'approved',
            student: {
              id: 'student',
              name: 'Aarav',
              enrollmentNumber: 'STU-1',
            },
            currentAllocation: null,
            preferredSeat: null,
            preferredFloor: null,
            preferredShift: { id: 'shift', name: 'Morning' },
          },
        },
      }
    }
    return {
      ...listResponse(config, 'approved-history'),
      data: {
        ...listResponse(config, 'approved-history').data,
        data: [],
        meta: { page: 1, pageSize: 10, totalItems: 0, totalPages: 0 },
        summary: {
          total: 1,
          pending: 0,
          approved: 1,
          rejected: 0,
          cancelled: 0,
        },
      },
    }
  }
  const store = useSeatRequestStore()
  store.filters = {
    ...store.filters,
    search: 'Aarav',
    status: 'pending',
  }
  await store.reviewRequest('request-id', { decision: 'approved' })

  assert.equal(requests[1].params.search, 'Aarav')
  assert.equal(requests[1].params.status, 'pending')
  assert.equal(store.pendingCount, 0)
  assert.equal(store.approvedCount, 1)
  assert.deepEqual(store.requests, [])
})


test('keeps a concurrent-review conflict and loads the final status', async () => {
  let call = 0
  apiClient.defaults.adapter = async (config) => {
    call += 1
    if (call === 1) {
      const response = {
        config,
        headers: {},
        status: 409,
        statusText: 'Conflict',
        data: {
          error: {
            code: 'SEAT_REQUEST_ALREADY_REVIEWED',
            message: 'This seat-change request has already been reviewed.',
            details: {
              currentStatus: 'approved',
              reviewedAt: '2026-08-03T10:00:00Z',
            },
          },
          requestId: 'conflict-request-id',
        },
      }
      throw new AxiosError(
        'Conflict',
        AxiosError.ERR_BAD_REQUEST,
        config,
        null,
        response,
      )
    }
    return listResponse(config, 'latest-list')
  }
  const store = useSeatRequestStore()
  store.selectRequest({
    id: 'request-id',
    status: 'pending',
    adminNote: '',
  })

  await assert.rejects(
    store.reviewRequest('request-id', {
      decision: 'rejected',
      reviewNote: 'Seat is unavailable.',
    }),
  )

  assert.equal(store.selectedRequest.status, 'approved')
  assert.equal(store.errorCode, 'SEAT_REQUEST_ALREADY_REVIEWED')
  assert.equal(store.errorRequestId, 'conflict-request-id')
  assert.equal(store.requests[0].id, 'latest-list')
})
