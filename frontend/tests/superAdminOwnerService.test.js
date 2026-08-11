import assert from 'node:assert/strict'
import test from 'node:test'

import apiClient from '../src/api/axios.js'
import {
  assignOwner,
  buildPlatformOwnerParams,
  createOwner,
  getOwner,
  getOwners,
  setOwnerStatus,
  updateOwner,
} from '../src/services/superAdminService.js'


function response(config, data, status = 200) {
  return { config, data, headers: {}, status, statusText: 'OK' }
}


test('maps server-side owner filters, pagination, and assignment summaries', async () => {
  assert.deepEqual(buildPlatformOwnerParams({
    search: ' aditi ',
    status: 'active',
    libraryId: 'library-id',
    invitationStatus: 'accepted',
    page: 2,
    pageSize: 10,
    sortBy: 'name',
    sortOrder: 'asc',
  }), {
    page: 2,
    pageSize: 10,
    search: 'aditi',
    status: 'active',
    libraryId: 'library-id',
    invitationStatus: 'accepted',
    sortBy: 'name',
    sortOrder: 'asc',
  })

  let request
  apiClient.defaults.adapter = async (config) => {
    request = config
    return response(config, {
      message: 'Owners fetched.',
      data: [{
        id: 'owner-id',
        userId: 'owner-id',
        name: 'Aditi Owner',
        assignments: [{ id: 'library-id', name: 'Central Library', status: 'active' }],
      }],
      meta: { page: 2, pageSize: 10, totalItems: 11, totalPages: 2 },
      summary: { total: 11, active: 8, invited: 2, suspended: 1 },
    })
  }
  const result = await getOwners({ search: 'aditi', page: 2 })

  assert.equal(request.url, '/platform/owners')
  assert.equal(request.params.search, 'aditi')
  assert.equal(result.data[0].libraryId, 'library-id')
  assert.equal(result.data[0].libraryName, 'Central Library')
  assert.equal(result.data[0].isInvitation, false)
  assert.equal(result.meta.totalItems, 11)
})


test('uses explicit owner endpoints and never sends password, role, email edit, or status in profile updates', async () => {
  const requests = []
  apiClient.defaults.adapter = async (config) => {
    requests.push(config)
    const owner = {
      id: 'owner-id',
      userId: 'owner-id',
      name: 'Owner',
      assignments: [],
    }
    if (config.url.endsWith('/invitations')) {
      return response(config, {
        message: 'Owner invitation created.',
        data: { owner, createdInvitation: true, invitationSetupUrl: 'https://example.test/setup' },
      }, 201)
    }
    return response(config, { message: 'Saved.', data: owner })
  }

  await createOwner({
    name: 'Owner',
    email: 'owner@example.com',
    phone: '9999999999',
    libraryId: 'library-id',
    password: 'must-not-be-sent',
    role: 'super_admin',
  })
  await updateOwner('owner-id', {
    name: 'Updated Owner',
    phone: '9000000000',
    email: 'changed@example.com',
    status: 'suspended',
    expectedUpdatedAt: '2026-08-03T10:00:00Z',
  })
  await assignOwner('owner-id', { libraryId: 'library-id' })
  await setOwnerStatus('owner-id', { status: 'suspended', reason: 'Review' })
  await getOwner('owner-id')

  assert.deepEqual(requests.map((item) => item.url), [
    '/platform/owners/invitations',
    '/platform/owners/owner-id',
    '/platform/owners/owner-id/assignment',
    '/platform/owners/owner-id/status',
    '/platform/owners/owner-id',
  ])
  const inviteBody = JSON.parse(requests[0].data)
  assert.equal(inviteBody.email, 'owner@example.com')
  assert.equal('password' in inviteBody, false)
  assert.equal('role' in inviteBody, false)
  const updateBody = JSON.parse(requests[1].data)
  assert.deepEqual(updateBody, {
    name: 'Updated Owner',
    phone: '9000000000',
    expectedUpdatedAt: '2026-08-03T10:00:00Z',
  })
  assert.equal(JSON.parse(requests[2].data).libraryId, 'library-id')
  assert.equal(JSON.parse(requests[3].data).reason, 'Review')
})
