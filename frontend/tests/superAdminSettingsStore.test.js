import assert from 'node:assert/strict'
import test from 'node:test'

import { createPinia, setActivePinia } from 'pinia'

import apiClient from '../src/api/axios.js'
import { useSuperAdminStore } from '../src/stores/superAdminStore.js'


function settingsResponse(config, overrides = {}) {
  return {
    config,
    headers: {},
    status: 200,
    statusText: 'OK',
    data: {
      message: 'Settings fetched.',
      data: {
        settings: {
          platformName: 'Smart Library API',
          allowLibraryRegistrations: true,
          sessionTimeoutMinutes: 30,
          defaultTimezone: 'Asia/Kolkata',
          ...overrides.settings,
        },
        definitions: overrides.definitions || [{ key: 'platformName', editable: false }],
        version: overrides.version ?? 2,
        updatedAt: overrides.updatedAt ?? '2026-08-05T10:00:00Z',
      },
    },
  }
}


test.beforeEach(() => setActivePinia(createPinia()))


test('stores settings metadata and sends the loaded version on update', async () => {
  const requests = []
  apiClient.defaults.adapter = async (config) => {
    requests.push(config)
    return config.method === 'get'
      ? settingsResponse(config)
      : settingsResponse(config, {
          settings: { sessionTimeoutMinutes: 90 },
          version: 3,
          updatedAt: '2026-08-05T11:00:00Z',
        })
  }
  const store = useSuperAdminStore()
  await store.fetchSettings()
  await store.updateSettings({
    allowLibraryRegistrations: true,
    sessionTimeoutMinutes: 90,
    defaultTimezone: 'Asia/Kolkata',
  })

  assert.equal(JSON.parse(requests[1].data).version, 2)
  assert.equal(store.settingsVersion, 3)
  assert.equal(store.settings.sessionTimeoutMinutes, 90)
  assert.equal(store.settingDefinitions[0].key, 'platformName')
  assert.equal(store.settingsUpdatedAt, '2026-08-05T11:00:00Z')
})


test('preserves loaded settings and exposes stale conflict details', async () => {
  let shouldConflict = false
  apiClient.defaults.adapter = async (config) => {
    if (!shouldConflict) return settingsResponse(config)
    const error = new Error('Conflict')
    error.config = config
    error.response = {
      status: 409,
      headers: { 'x-request-id': 'settings-conflict-request' },
      data: {
        error: {
          code: 'PLATFORM_SETTINGS_UPDATE_CONFLICT',
          message: 'Platform settings changed after this form was loaded.',
        },
        requestId: 'settings-conflict-request',
      },
    }
    throw error
  }
  const store = useSuperAdminStore()
  await store.fetchSettings()
  shouldConflict = true

  await assert.rejects(() => store.updateSettings({ sessionTimeoutMinutes: 90 }))
  assert.equal(store.settings.sessionTimeoutMinutes, 30)
  assert.equal(store.settingsVersion, 2)
  assert.equal(store.errorCode, 'PLATFORM_SETTINGS_UPDATE_CONFLICT')
  assert.equal(store.errorRequestId, 'settings-conflict-request')
})
