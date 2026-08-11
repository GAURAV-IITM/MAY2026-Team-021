import assert from 'node:assert/strict'
import test from 'node:test'

import { createPinia, setActivePinia } from 'pinia'

import apiClient from '../src/api/axios.js'
import { useSuperAdminStore } from '../src/stores/superAdminStore.js'


function listResponse(config, name, page = 1) {
  return {
    config,
    headers: {},
    status: 200,
    statusText: 'OK',
    data: {
      message: 'Owners fetched.',
      data: [{ id: name, userId: name, name, assignments: [] }],
      meta: { page, pageSize: 10, totalItems: 1, totalPages: 1 },
      summary: { total: 1, active: 1, invited: 0, suspended: 0 },
    },
  }
}


test.beforeEach(() => setActivePinia(createPinia()))


test('keeps the latest owner response and preserves server-side filters', async () => {
  const pending = []
  apiClient.defaults.adapter = (config) => new Promise((resolve) => pending.push({ config, resolve }))
  const store = useSuperAdminStore()

  const first = store.fetchOwners({ search: 'first', page: 1 })
  await new Promise((resolve) => setImmediate(resolve))
  const second = store.fetchOwners({ search: 'second', status: 'active', libraryId: 'library-id', page: 2 })
  await new Promise((resolve) => setImmediate(resolve))
  pending[1].resolve(listResponse(pending[1].config, 'Second owner', 2))
  await second
  pending[0].resolve(listResponse(pending[0].config, 'Stale owner'))
  await first

  assert.equal(store.owners[0].name, 'Second owner')
  assert.equal(store.ownerFilters.search, 'second')
  assert.equal(store.ownerFilters.status, 'active')
  assert.equal(store.ownerFilters.libraryId, 'library-id')
  assert.equal(store.ownerPagination.page, 2)
})


test('exposes assignment conflicts and request IDs without mock fallback', async () => {
  apiClient.defaults.adapter = async (config) => {
    if (config.method === 'get') return listResponse(config, 'Filtered owner')
    const error = new Error('Request failed')
    error.config = config
    error.response = {
      status: 409,
      headers: { 'x-request-id': 'owner-request-123' },
      data: {
        error: {
          code: 'PLATFORM_OWNER_ASSIGNMENT_CONFLICT',
          message: 'The selected library already has an owner.',
        },
        requestId: 'owner-request-123',
      },
    }
    throw error
  }
  const store = useSuperAdminStore()
  await store.fetchOwners({ search: 'central', status: 'active', page: 3 })

  await assert.rejects(() => store.assignOwner('owner-id', { libraryId: 'library-id' }))
  assert.equal(store.errorCode, 'PLATFORM_OWNER_ASSIGNMENT_CONFLICT')
  assert.equal(store.errorRequestId, 'owner-request-123')
  assert.equal(store.ownerFilters.search, 'central')
  assert.equal(store.ownerFilters.page, 3)
})
