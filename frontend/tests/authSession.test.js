import assert from 'node:assert/strict'
import test from 'node:test'

import { AxiosError } from 'axios'

import { apiClient, refreshClient } from '../src/api/axios.js'
import {
  clearAuthState,
  getAccessToken,
  persistAuthSession,
  readAuthSession,
  setAccessToken,
} from '../src/api/authSession.js'

class MemoryStorage {
  constructor() {
    this.values = new Map()
  }

  getItem(key) {
    return this.values.get(key) ?? null
  }

  setItem(key, value) {
    this.values.set(key, String(value))
  }

  removeItem(key) {
    this.values.delete(key)
  }
}

function installBrowserStorage() {
  let assignedLocation = null
  globalThis.window = {
    localStorage: new MemoryStorage(),
    sessionStorage: new MemoryStorage(),
    location: {
      pathname: '/login',
      search: '',
      assign(value) {
        assignedLocation = value
      },
    },
    get assignedLocation() {
      return assignedLocation
    },
  }
}

function axiosResponse(config, data, status = 200) {
  return {
    config,
    data,
    headers: {},
    status,
    statusText: status === 200 ? 'OK' : 'Unauthorized',
  }
}

function unauthorized(config) {
  const response = axiosResponse(config, { detail: 'Unauthorized' }, 401)
  return Promise.reject(
    new AxiosError('Unauthorized', AxiosError.ERR_BAD_REQUEST, config, null, response),
  )
}

test.beforeEach(() => {
  installBrowserStorage()
  clearAuthState()
})

test('stores only session metadata in the selected browser storage', () => {
  persistAuthSession({
    user: { id: 'user-1' },
    role: 'admin',
    token: 'must-not-be-persisted',
    rememberMe: false,
    isAuthenticated: true,
  })

  const tabValue = window.sessionStorage.getItem('smart_library_auth_session')
  assert.ok(tabValue)
  assert.equal(window.localStorage.getItem('smart_library_auth_session'), null)
  assert.equal(tabValue.includes('must-not-be-persisted'), false)
  assert.equal(readAuthSession().rememberMe, false)

  persistAuthSession({
    user: { id: 'user-1' },
    role: 'admin',
    token: 'still-must-not-be-persisted',
    rememberMe: true,
    isAuthenticated: true,
  })

  const persistentValue = window.localStorage.getItem('smart_library_auth_session')
  assert.ok(persistentValue)
  assert.equal(window.sessionStorage.getItem('smart_library_auth_session'), null)
  assert.equal(persistentValue.includes('still-must-not-be-persisted'), false)
  assert.equal(readAuthSession().rememberMe, true)
})

test('uses one refresh request for simultaneous unauthorized responses', async () => {
  let refreshCalls = 0

  refreshClient.defaults.adapter = async (config) => {
    refreshCalls += 1
    await new Promise((resolve) => setTimeout(resolve, 10))
    return axiosResponse(config, { accessToken: 'rotated-access-token' })
  }

  apiClient.defaults.adapter = (config) => {
    if (!config._retry) return unauthorized(config)
    return Promise.resolve(
      axiosResponse(config, {
        authorization: config.headers.Authorization,
      }),
    )
  }

  const [first, second] = await Promise.all([
    apiClient.get('/first-protected-resource'),
    apiClient.get('/second-protected-resource'),
  ])

  assert.equal(refreshCalls, 1)
  assert.equal(getAccessToken(), 'rotated-access-token')
  assert.equal(first.data.authorization, 'Bearer rotated-access-token')
  assert.equal(second.data.authorization, 'Bearer rotated-access-token')
})

test('clears legacy browser-readable token keys', () => {
  window.localStorage.setItem('smart_library_access_token', 'old-access')
  window.localStorage.setItem('smart_library_refresh_token', 'old-refresh')
  window.sessionStorage.setItem('smart_library_access_token', 'old-access')
  setAccessToken('memory-access')

  clearAuthState()

  assert.equal(getAccessToken(), null)
  assert.equal(window.localStorage.getItem('smart_library_access_token'), null)
  assert.equal(window.localStorage.getItem('smart_library_refresh_token'), null)
  assert.equal(window.sessionStorage.getItem('smart_library_access_token'), null)
})

test('does not redirect guest-only pages when the session probe fails', async () => {
  window.location.pathname = '/register-library'
  refreshClient.defaults.adapter = unauthorized
  apiClient.defaults.adapter = unauthorized

  await assert.rejects(apiClient.get('/auth/me'))

  assert.equal(window.assignedLocation, null)
  assert.equal(getAccessToken(), null)
})
