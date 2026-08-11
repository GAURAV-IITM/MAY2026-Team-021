import assert from 'node:assert/strict'
import test from 'node:test'

import apiClient from '../src/api/axios.js'
import {
  assignLibraryOwner,
  buildPlatformLibraryParams,
  createLibrary,
  getLibraries,
  getLibraryOwnerOptions,
  setLibraryStatus,
  updateLibrary,
} from '../src/services/superAdminService.js'


function response(config, data, status = 200) {
  return { config, data, headers: {}, status, statusText: 'OK' }
}


test('maps server-side library filters, pagination, sorting, and owner summaries', async () => {
  assert.deepEqual(
    buildPlatformLibraryParams({
      search: ' pune ',
      status: 'active',
      ownerId: 'owner-id',
      page: 2,
      pageSize: 10,
      sortBy: 'name',
      sortOrder: 'asc',
    }),
    {
      page: 2,
      pageSize: 10,
      search: 'pune',
      status: 'active',
      ownerId: 'owner-id',
      state: undefined,
      sortBy: 'name',
      sortOrder: 'asc',
    },
  )

  let request
  apiClient.defaults.adapter = async (config) => {
    request = config
    return response(config, {
      message: 'Libraries fetched.',
      data: [{
        id: 'library-id',
        name: 'Central Library',
        owner: { id: 'owner-id', name: 'Owner Name' },
        createdAt: '2026-08-03T10:00:00Z',
      }],
      meta: { page: 2, pageSize: 10, totalItems: 11, totalPages: 2 },
      summary: { total: 11, active: 8, pending: 2, suspended: 1 },
    })
  }
  const result = await getLibraries({ search: 'pune', page: 2 })

  assert.equal(request.url, '/platform/libraries')
  assert.equal(request.params.search, 'pune')
  assert.equal(result.data[0].ownerId, 'owner-id')
  assert.equal(result.data[0].ownerName, 'Owner Name')
  assert.equal(result.meta.totalItems, 11)
})


test('uses explicit platform mutation endpoints and sends only approved fields', async () => {
  const requests = []
  apiClient.defaults.adapter = async (config) => {
    requests.push(config)
    if (config.url.endsWith('/owner-options')) {
      return response(config, { message: 'Owners fetched.', data: [] })
    }
    return response(
      config,
      {
        message: 'Saved.',
        data: {
          id: 'library-id',
          code: 'LIB',
          name: 'Library',
          owner: null,
          createdAt: '2026-08-03T10:00:00Z',
        },
      },
      config.method === 'post' ? 201 : 200,
    )
  }

  await createLibrary({
    name: 'Library',
    code: 'LIB',
    contactEmail: 'library@example.com',
    seatCount: 99,
    status: 'active',
    createdBy: 'must-not-be-sent',
  })
  await updateLibrary('library-id', {
    name: 'Updated Library',
    code: 'CHANGED',
    status: 'suspended',
    ownerId: 'owner-id',
    expectedUpdatedAt: '2026-08-03T10:00:00Z',
  })
  await setLibraryStatus('library-id', {
    status: 'suspended',
    reason: 'Policy review',
    expectedUpdatedAt: '2026-08-03T10:00:00Z',
  })
  await assignLibraryOwner('library-id', {
    ownerId: 'owner-id',
    expectedUpdatedAt: '2026-08-03T10:00:00Z',
  })
  await getLibraryOwnerOptions()

  assert.deepEqual(requests.map((item) => item.url), [
    '/platform/libraries',
    '/platform/libraries/library-id',
    '/platform/libraries/library-id/status',
    '/platform/libraries/library-id/owner',
    '/platform/libraries/owner-options',
  ])
  const createBody = JSON.parse(requests[0].data)
  assert.equal(createBody.code, 'LIB')
  assert.equal('seatCount' in createBody, false)
  assert.equal('status' in createBody, false)
  assert.equal('createdBy' in createBody, false)

  const updateBody = JSON.parse(requests[1].data)
  assert.equal(updateBody.name, 'Updated Library')
  assert.equal('code' in updateBody, false)
  assert.equal('status' in updateBody, false)
  assert.equal('ownerId' in updateBody, false)
  assert.equal(JSON.parse(requests[2].data).reason, 'Policy review')
  assert.equal(JSON.parse(requests[3].data).ownerId, 'owner-id')
})
