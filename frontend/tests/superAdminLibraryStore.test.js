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
      message: 'Libraries fetched.',
      data: [{ id: name, name, owner: null, createdAt: '2026-08-03T10:00:00Z' }],
      meta: { page, pageSize: 10, totalItems: 1, totalPages: 1 },
      summary: { total: 1, active: 0, pending: 1, suspended: 0 },
    },
  }
}


test.beforeEach(() => setActivePinia(createPinia()))


test('keeps the latest library list response and server-side filters', async () => {
  const pending = []
  apiClient.defaults.adapter = (config) => new Promise((resolve) => pending.push({ config, resolve }))
  const store = useSuperAdminStore()

  const first = store.fetchLibraries({ search: 'first', page: 1 })
  await new Promise((resolve) => setImmediate(resolve))
  const second = store.fetchLibraries({ search: 'second', status: 'pending', page: 2 })
  await new Promise((resolve) => setImmediate(resolve))
  pending[1].resolve(listResponse(pending[1].config, 'Second result', 2))
  await second
  pending[0].resolve(listResponse(pending[0].config, 'Stale result'))
  await first

  assert.equal(store.libraries[0].name, 'Second result')
  assert.equal(store.libraryFilters.search, 'second')
  assert.equal(store.libraryFilters.status, 'pending')
  assert.equal(store.libraryFilters.page, 2)
  assert.equal(store.libraryPagination.page, 2)
})


test('preserves filters and exposes structured conflict details', async () => {
  apiClient.defaults.adapter = async (config) => {
    if (config.method === 'get') return listResponse(config, 'Filtered library')
    const error = new Error('Request failed')
    error.config = config
    error.response = {
      status: 409,
      headers: { 'x-request-id': 'request-123' },
      data: {
        error: {
          code: 'PLATFORM_LIBRARY_STATE_CHANGED',
          message: 'This library changed after it was opened.',
        },
        requestId: 'request-123',
      },
    }
    throw error
  }
  const store = useSuperAdminStore()
  await store.fetchLibraries({ search: 'central', status: 'active', page: 3 })

  await assert.rejects(() => store.setLibraryStatus('library-id', {
    status: 'suspended',
    reason: 'Review',
  }))
  assert.equal(store.errorCode, 'PLATFORM_LIBRARY_STATE_CHANGED')
  assert.equal(store.errorRequestId, 'request-123')
  assert.equal(store.errorMessage, 'This library changed after it was opened.')
  assert.equal(store.libraryFilters.search, 'central')
  assert.equal(store.libraryFilters.status, 'active')
  assert.equal(store.libraryFilters.page, 3)
})
