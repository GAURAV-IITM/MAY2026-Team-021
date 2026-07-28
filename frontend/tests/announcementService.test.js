import assert from 'node:assert/strict'
import test from 'node:test'

import apiClient from '../src/api/axios.js'
import {
  archiveAnnouncement,
  buildAnnouncementParams,
  createAnnouncement,
  deleteAnnouncement,
  getAnnouncements,
  publishAnnouncement,
  updateAnnouncement,
} from '../src/services/announcementService.js'


function response(config, data, status = 200) {
  return {
    config,
    data,
    headers: {},
    status,
    statusText: status === 201 ? 'Created' : 'OK',
  }
}


test('maps announcement list filters and preserves pagination and summary', async () => {
  assert.deepEqual(
    buildAnnouncementParams({
      search: ' fee ',
      status: 'scheduled',
      category: 'fees',
      priority: 'important',
      audience: 'pending_fee_students',
      page: 2,
      pageSize: 10,
    }),
    {
      page: 2,
      pageSize: 10,
      search: 'fee',
      status: 'scheduled',
      category: 'fees',
      priority: 'important',
      audience: 'pending_fee_students',
      sortBy: 'createdAt',
      sortOrder: 'desc',
    },
  )

  let requestConfig
  apiClient.defaults.adapter = async (config) => {
    requestConfig = config
    return response(config, {
      message: 'Announcements fetched.',
      data: [{ id: 'announcement-id', status: 'scheduled' }],
      meta: { page: 2, pageSize: 10, totalItems: 1, totalPages: 1 },
      summary: { total: 3, scheduled: 1 },
    })
  }
  const result = await getAnnouncements({
    search: 'fee',
    status: 'scheduled',
    page: 2,
  })

  assert.equal(requestConfig.url, '/announcements')
  assert.equal(requestConfig.params.status, 'scheduled')
  assert.equal(result.data.announcements[0].id, 'announcement-id')
  assert.equal(result.summary.total, 3)
})


test('uses explicit lifecycle endpoints and never sends tenant fields', async () => {
  const requests = []
  apiClient.defaults.adapter = async (config) => {
    requests.push(config)
    return response(
      config,
      {
        message: 'Announcement saved.',
        data: {
          id: 'announcement-id',
          updatedAt: '2026-07-28T10:00:00Z',
        },
      },
      config.method === 'post' && config.url === '/announcements' ? 201 : 200,
    )
  }

  const payload = {
    title: 'Library timing update',
    body: 'Library timing has changed for the coming weekend.',
    category: 'schedule',
    priority: 'important',
    audience: 'all_students',
    status: 'scheduled',
    scheduledAt: '2026-08-01T09:00:00Z',
    expiresAt: '2026-08-02T09:00:00Z',
    libraryId: 'must-not-be-sent',
  }
  await createAnnouncement(payload)
  await updateAnnouncement('announcement-id', {
    ...payload,
    expectedUpdatedAt: '2026-07-28T10:00:00Z',
  })
  await publishAnnouncement('announcement-id')
  await archiveAnnouncement('announcement-id', 'No longer relevant')
  await deleteAnnouncement('announcement-id')

  assert.equal(requests[0].url, '/announcements')
  assert.equal(requests[1].url, '/announcements/announcement-id')
  assert.equal(requests[2].url, '/announcements/announcement-id/publish')
  assert.equal(requests[3].url, '/announcements/announcement-id/archive')
  assert.equal(requests[4].url, '/announcements/announcement-id')
  const createBody = JSON.parse(requests[0].data)
  assert.equal(createBody.status, 'scheduled')
  assert.equal(createBody.scheduledAt, '2026-08-01T09:00:00Z')
  assert.equal('libraryId' in createBody, false)
  assert.equal(
    JSON.parse(requests[1].data).expectedUpdatedAt,
    '2026-07-28T10:00:00Z',
  )
  assert.deepEqual(JSON.parse(requests[3].data), {
    reason: 'No longer relevant',
  })
})
