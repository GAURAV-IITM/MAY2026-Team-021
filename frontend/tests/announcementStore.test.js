import assert from 'node:assert/strict'
import test from 'node:test'

import { createPinia, setActivePinia } from 'pinia'

import apiClient from '../src/api/axios.js'
import { useAnnouncementStore } from '../src/stores/announcementStore.js'


function listResponse(config, title) {
  return {
    config,
    headers: {},
    status: 200,
    statusText: 'OK',
    data: {
      message: 'Announcements fetched.',
      data: [{ id: title, title }],
      meta: { page: 1, pageSize: 10, totalItems: 1, totalPages: 1 },
      summary: {
        total: 1,
        drafts: 1,
        scheduled: 0,
        published: 0,
        archived: 0,
        expired: 0,
        important: 0,
      },
    },
  }
}


test.beforeEach(() => {
  setActivePinia(createPinia())
})


test('keeps the latest filtered announcement response', async () => {
  const pending = []
  apiClient.defaults.adapter = (config) =>
    new Promise((resolve) => pending.push({ config, resolve }))

  const store = useAnnouncementStore()
  const first = store.fetchAnnouncements({ search: 'first' })
  await new Promise((resolve) => setImmediate(resolve))
  const second = store.fetchAnnouncements({ search: 'second' })
  await new Promise((resolve) => setImmediate(resolve))

  pending[1].resolve(listResponse(pending[1].config, 'Second result'))
  await second
  pending[0].resolve(listResponse(pending[0].config, 'Stale result'))
  await first

  assert.equal(store.announcements[0].title, 'Second result')
  assert.equal(store.summary.total, 1)
  assert.equal(store.isLoading, false)
})


test('publish-now creation uses create draft then explicit publish', async () => {
  const requests = []
  apiClient.defaults.adapter = async (config) => {
    requests.push(config)
    if (config.method === 'get') {
      return listResponse(config, 'Published announcement')
    }
    return {
      config,
      headers: {},
      status: config.url === '/announcements' ? 201 : 200,
      statusText: 'OK',
      data: {
        message: 'Saved.',
        data: {
          id: 'announcement-id',
          status: config.url.endsWith('/publish') ? 'published' : 'draft',
        },
      },
    }
  }

  const store = useAnnouncementStore()
  await store.createAnnouncement({
    title: 'Immediate announcement',
    body: 'This announcement should be published immediately.',
    category: 'general',
    priority: 'normal',
    audience: 'all_students',
    status: 'published',
    scheduledAt: null,
    expiresAt: null,
  })

  assert.equal(requests[0].url, '/announcements')
  assert.equal(JSON.parse(requests[0].data).status, 'draft')
  assert.equal(requests[1].url, '/announcements/announcement-id/publish')
  assert.equal(requests[2].method, 'get')
  assert.equal(store.announcements[0].title, 'Published announcement')
  assert.equal(store.isSaving, false)
})
