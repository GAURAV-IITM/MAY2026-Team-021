const SESSION_KEY = 'smart_library_auth_session'
const LEGACY_ACCESS_TOKEN_KEY = 'smart_library_access_token'
const LEGACY_REFRESH_TOKEN_KEY = 'smart_library_refresh_token'

let accessToken = null
let memorySession = null
const accessTokenListeners = new Set()
const sessionClearedListeners = new Set()

function getStorage(storageName) {
  if (typeof window === 'undefined') return null

  try {
    return window[storageName] || null
  } catch {
    return null
  }
}

function parseSession(value) {
  if (!value) return null

  try {
    return JSON.parse(value)
  } catch {
    return null
  }
}

function removeStoredSession() {
  for (const storageName of ['localStorage', 'sessionStorage']) {
    const storage = getStorage(storageName)
    storage?.removeItem(SESSION_KEY)
    storage?.removeItem(LEGACY_ACCESS_TOKEN_KEY)
    storage?.removeItem(LEGACY_REFRESH_TOKEN_KEY)
  }
}

export function getAccessToken() {
  return accessToken
}

export function setAccessToken(token) {
  accessToken = token || null
  accessTokenListeners.forEach((listener) => listener(accessToken))
}

export function subscribeAccessToken(listener) {
  accessTokenListeners.add(listener)
  return () => accessTokenListeners.delete(listener)
}

export function subscribeSessionCleared(listener) {
  sessionClearedListeners.add(listener)
  return () => sessionClearedListeners.delete(listener)
}

export function persistAuthSession(session) {
  const normalizedSession = {
    ...session,
    token: undefined,
    rememberMe: Boolean(session?.rememberMe),
  }
  memorySession = normalizedSession
  removeStoredSession()

  const storage = getStorage(normalizedSession.rememberMe ? 'localStorage' : 'sessionStorage')
  storage?.setItem(SESSION_KEY, JSON.stringify(normalizedSession))
  return normalizedSession
}

export function readAuthSession() {
  const persistentSession = parseSession(getStorage('localStorage')?.getItem(SESSION_KEY))
  if (persistentSession) {
    memorySession = persistentSession
    return persistentSession
  }

  const tabSession = parseSession(getStorage('sessionStorage')?.getItem(SESSION_KEY))
  if (tabSession) {
    memorySession = tabSession
    return tabSession
  }

  return memorySession
}

export function clearAuthState() {
  accessToken = null
  memorySession = null
  removeStoredSession()
  accessTokenListeners.forEach((listener) => listener(null))
  sessionClearedListeners.forEach((listener) => listener())
}
