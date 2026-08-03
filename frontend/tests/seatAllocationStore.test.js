import assert from 'node:assert/strict'
import test from 'node:test'

import { AxiosError } from 'axios'
import { createPinia, setActivePinia } from 'pinia'

import apiClient from '../src/api/axios.js'
import { useSeatStore } from '../src/stores/seatStore.js'

function response(config, data, status = 200) {
  return {
    config,
    data,
    headers: {},
    status,
    statusText: 'OK',
  }
}

test.beforeEach(() => {
  setActivePinia(createPinia())
})

test('tracks loading and applies only the latest availability response', async () => {
  const pending = []
  apiClient.defaults.adapter = (config) =>
    new Promise((resolve) => pending.push({ config, resolve }))

  const store = useSeatStore()
  const first = store.fetchAllocationAvailability({
    shiftIds: ['first'],
    startDate: '2026-08-01',
  })
  assert.equal(store.isAvailabilityLoading, true)
  await new Promise((resolve) => setImmediate(resolve))
  const second = store.fetchAllocationAvailability({
    shiftIds: ['second'],
    startDate: '2026-08-01',
  })
  await new Promise((resolve) => setImmediate(resolve))

  pending[1].resolve(
    response(pending[1].config, {
      data: { shiftIds: ['second'], seats: [] },
    }),
  )
  await second
  pending[0].resolve(
    response(pending[0].config, {
      data: { shiftIds: ['first'], seats: [{ seatId: 'stale-seat' }] },
    }),
  )
  await first

  assert.deepEqual(store.allocationAvailability.shiftIds, ['second'])
  assert.deepEqual(store.allocationAvailability.seats, [])
  assert.equal(store.isAvailabilityLoading, false)
})

test('stores allocation conflicts without replacing form-facing state', async () => {
  apiClient.defaults.adapter = (config) => {
    const conflict = response(
      config,
      {
        error: {
          code: 'STUDENT_ALLOCATION_CONFLICT',
          message: 'Student already has an overlapping seat.',
        },
        requestId: 'student-conflict-request',
      },
      409,
    )
    return Promise.reject(
      new AxiosError('Conflict', AxiosError.ERR_BAD_REQUEST, config, null, conflict),
    )
  }

  const store = useSeatStore()
  await assert.rejects(
    store.allocateSeat({
      studentId: 'student-id',
      seatId: 'seat-id',
      shiftIds: ['shift-id'],
      startDate: '2026-08-01',
      endDate: '2026-08-31',
    }),
  )

  assert.equal(store.isAllocationSubmitting, false)
  assert.equal(
    store.allocationError.response.data.error.code,
    'STUDENT_ALLOCATION_CONFLICT',
  )
  assert.equal(
    store.allocationErrorMessage,
    'Student already has an overlapping seat.',
  )
})

test('stores empty allocation pages and updates a closed history row', async () => {
  const store = useSeatStore()
  apiClient.defaults.adapter = async (config) =>
    response(config, {
      data: [],
      meta: { page: 1, pageSize: 20, totalItems: 0, totalPages: 0 },
    })
  await store.fetchAllocations()
  assert.deepEqual(store.allocations, [])
  assert.equal(store.allocationMeta.totalItems, 0)

  store.allocations = [{ id: 'allocation-id', status: 'active' }]
  apiClient.defaults.adapter = async (config) =>
    response(config, {
      data: { id: 'allocation-id', status: 'completed' },
    })
  await store.closeAllocation('allocation-id', {
    status: 'completed',
    closeReason: 'Completed',
  })
  assert.equal(store.allocations[0].status, 'completed')
})
