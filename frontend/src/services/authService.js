import {
  AUTH_NETWORK_DELAY_MS,
  AUTH_STORAGE_KEYS,
  AUTH_ROLES,
  mockUsers,
  toPublicUser,
} from '../mocks/authMock'
import { initializeLibrarySeats } from './seatService'

// src/services: Mock auth service. Replace this file with FastAPI-backed requests later.
// TODO: Replace localStorage fake JWT handling with secure backend-issued JWT/session handling.

let memorySession = null

function delay(ms = AUTH_NETWORK_DELAY_MS) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms)
  })
}

function getBrowserStorage() {
  if (typeof window === 'undefined' || !window.localStorage) return null
  return window.localStorage
}

function encodeTokenPayload(payload) {
  const serializedPayload = JSON.stringify(payload)

  if (typeof window !== 'undefined' && window.btoa) {
    return window.btoa(serializedPayload)
  }

  return encodeURIComponent(serializedPayload)
}

function createFakeJwt(user) {
  const payload = {
    sub: user.id,
    role: user.role,
    email: user.email,
    iat: Date.now(),
  }

  return `mock-jwt.${encodeTokenPayload(payload)}.signature`
}

function createSuccessResponse(message, data = {}) {
  return {
    success: true,
    message,
    data,
    meta: {
      source: 'mock-auth-service',
      timestamp: new Date().toISOString(),
    },
  }
}

function createAuthError(message, status = 400, code = 'AUTH_ERROR') {
  const error = new Error(message)

  error.response = {
    status,
    data: {
      success: false,
      message,
      error: { code },
    },
  }

  return error
}

function findUserByEmail(email) {
  return mockUsers.find((user) => user.email.toLowerCase() === String(email).toLowerCase())
}

function persistSession(session) {
  memorySession = session

  const storage = getBrowserStorage()
  if (!storage) return

  storage.setItem(AUTH_STORAGE_KEYS.TOKEN, session.token)
  storage.setItem(AUTH_STORAGE_KEYS.SESSION, JSON.stringify(session))
}

function readSession() {
  const storage = getBrowserStorage()
  if (!storage) return memorySession

  const token = storage.getItem(AUTH_STORAGE_KEYS.TOKEN)
  const session = storage.getItem(AUTH_STORAGE_KEYS.SESSION)

  if (!token || !session) return null

  try {
    const parsedSession = JSON.parse(session)
    return parsedSession.token === token ? parsedSession : null
  } catch {
    return null
  }
}

function clearSession() {
  memorySession = null

  const storage = getBrowserStorage()
  if (!storage) return

  storage.removeItem(AUTH_STORAGE_KEYS.TOKEN)
  storage.removeItem(AUTH_STORAGE_KEYS.SESSION)
}

export async function login(credentials = {}) {
  await delay()

  const { email, password, rememberMe = false } = credentials

  if (!email || !password) {
    throw createAuthError('Email and password are required.', 422, 'VALIDATION_ERROR')
  }

  const user = findUserByEmail(email)

  if (!user || user.password !== password) {
    throw createAuthError('Invalid email or password.', 401, 'INVALID_CREDENTIALS')
  }

  const publicUser = toPublicUser(user)
  const token = createFakeJwt(user)
  const session = {
    user: publicUser,
    role: user.role,
    token,
    rememberMe,
    isAuthenticated: true,
    issuedAt: new Date().toISOString(),
  }

  persistSession(session)

  return createSuccessResponse('Login successful.', session)
}

export async function logout() {
  await delay()
  clearSession()

  return createSuccessResponse('Logout successful.', {
    user: null,
    role: null,
    token: null,
    rememberMe: false,
    isAuthenticated: false,
  })
}

export async function register(registrationData = {}) {
  await delay()

  const libraryName = String(registrationData.libraryName || '').trim()
  const ownerName = String(registrationData.ownerName || '').trim()
  const email = String(registrationData.email || '').trim().toLowerCase()
  const password = String(registrationData.password || '')
  const seatCount = Number(registrationData.seatCount)

  if (!libraryName || !ownerName || !email || !password) {
    throw createAuthError(
      'Library and owner account details are required.',
      422,
      'REGISTRATION_DETAILS_REQUIRED',
    )
  }

  if (!Number.isInteger(seatCount) || seatCount < 1 || seatCount > 1000) {
    throw createAuthError(
      'Seat count must be a whole number between 1 and 1000.',
      422,
      'LIBRARY_SEAT_COUNT_INVALID',
    )
  }

  if (findUserByEmail(email)) {
    throw createAuthError(
      'An account already exists for this email address.',
      409,
      'ACCOUNT_ALREADY_EXISTS',
    )
  }

  const now = Date.now()
  const libraryId = `library-${now}`

  const user = {
    id: `owner-${now}`,
    name: ownerName,
    email,
    password,
    role: AUTH_ROLES.LIBRARY_OWNER,
    roleLabel: 'Library Owner',
    libraryId,
    libraryName,
  }

  const seatResponse = await initializeLibrarySeats({
    seatCount,
    libraryId,
    libraryName,
  })
  mockUsers.push(user)

  const publicUser = toPublicUser(user)
  const token = createFakeJwt(user)
  const session = {
    user: publicUser,
    role: publicUser.role,
    token,
    rememberMe: false,
    isAuthenticated: true,
    issuedAt: new Date().toISOString(),
  }

  persistSession(session)

  return createSuccessResponse('Library registration successful.', {
    ...session,
    registrationStatus: 'created',
    seatCount,
    seatsCreated: seatResponse.data.createdSeatCount,
  })
}

export async function registerLibrary(registrationData = {}) {
  return register(registrationData)
}

export async function forgotPassword(payload = {}) {
  await delay()

  return createSuccessResponse('Password reset request accepted.', {
    email: payload.email || '',
    resetLinkSent: true,
    delivery: 'placeholder',
  })
}

export async function checkSession() {
  await delay()

  const session = readSession()

  if (!session) {
    return createSuccessResponse('No active session.', {
      user: null,
      role: null,
      token: null,
      rememberMe: false,
      isAuthenticated: false,
    })
  }

  return createSuccessResponse('Active session found.', session)
}

export async function getCurrentUser() {
  return checkSession()
}
