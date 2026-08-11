import assert from 'node:assert/strict'
import test from 'node:test'

import apiClient from '../src/api/axios.js'
import { getSettings, updateSettings } from '../src/services/superAdminService.js'


function response(config, data) {
  return { config, data, headers: {}, status: 200, statusText: 'OK' }
}


test('loads platform settings from the real API', async () => {
  let request
  apiClient.defaults.adapter = async (config) => {
    request = config
    return response(config, {
      message: 'Settings fetched.',
      data: {
        settings: { platformName: 'Smart Library API' },
        definitions: [],
        version: 0,
        updatedAt: null,
      },
    })
  }
  const result = await getSettings()
  assert.equal(request.url, '/platform/settings')
  assert.equal(request.method, 'get')
  assert.equal(result.data.version, 0)
})


test('updates only approved editable settings and includes the version', async () => {
  let request
  apiClient.defaults.adapter = async (config) => {
    request = config
    return response(config, {
      message: 'Settings updated.',
      data: {
        settings: {
          platformName: 'Smart Library API',
          allowLibraryRegistrations: false,
          sessionTimeoutMinutes: 90,
          defaultTimezone: 'UTC',
        },
        definitions: [],
        version: 4,
        updatedAt: '2026-08-05T10:00:00Z',
      },
    })
  }
  const result = await updateSettings({
    version: 3,
    allowLibraryRegistrations: false,
    sessionTimeoutMinutes: 90,
    defaultTimezone: 'UTC',
    platformName: 'Must not be sent',
    jwtSecret: 'Must not be sent',
  })
  const body = JSON.parse(request.data)
  assert.equal(request.url, '/platform/settings')
  assert.equal(request.method, 'patch')
  assert.deepEqual(body, {
    version: 3,
    allowLibraryRegistrations: false,
    sessionTimeoutMinutes: 90,
    defaultTimezone: 'UTC',
  })
  assert.equal(result.data.version, 4)
})


test('propagates settings API errors without mock fallback', async () => {
  apiClient.defaults.adapter = async (config) => {
    const error = new Error('Settings unavailable')
    error.config = config
    error.response = {
      status: 500,
      headers: { 'x-request-id': 'settings-service-request' },
      data: {
        error: { code: 'INTERNAL_SERVER_ERROR', message: 'Settings unavailable' },
      },
    }
    throw error
  }
  await assert.rejects(() => getSettings(), /Settings unavailable/)
})
