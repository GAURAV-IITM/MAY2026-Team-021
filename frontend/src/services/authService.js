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

function normalizeIndianPhone(value) {
  const digits = String(value || '').replace(/\D/g, '')
  return digits.length === 12 && digits.startsWith('91') ? digits.slice(2) : digits
}

function getAuthenticatedOwner() {
  const session = readSession()

  if (!session?.isAuthenticated || !session.user?.id) {
    throw createAuthError(
      'Your session has expired. Please sign in again.',
      401,
      'SESSION_REQUIRED',
    )
  }

  const user = mockUsers.find((candidate) => candidate.id === session.user.id)

  if (!user) {
    throw createAuthError('The signed-in account could not be found.', 404, 'ACCOUNT_NOT_FOUND')
  }

  if (user.role !== AUTH_ROLES.LIBRARY_OWNER) {
    throw createAuthError(
      'Only library owner accounts can update this profile.',
      403,
      'OWNER_ACCOUNT_REQUIRED',
    )
  }

  return { session, user }
}

function createUpdatedSession(session, user) {
  return {
    ...session,
    user: toPublicUser(user),
    role: user.role,
    token: createFakeJwt(user),
    isAuthenticated: true,
  }
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
  const email = String(registrationData.email || '')
    .trim()
    .toLowerCase()
  const phone = normalizeIndianPhone(registrationData.phone)
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
    phone,
    password,
    role: AUTH_ROLES.LIBRARY_OWNER,
    roleLabel: 'Library Owner',
    libraryId,
    libraryName,
    createdAt: new Date(now).toISOString(),
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

  let session = readSession()

  if (!session) {
    return createSuccessResponse('No active session.', {
      user: null,
      role: null,
      token: null,
      rememberMe: false,
      isAuthenticated: false,
    })
  }

  const currentUser = mockUsers.find((user) => user.id === session.user?.id)

  if (currentUser) {
    session = {
      ...session,
      user: toPublicUser(currentUser),
      role: currentUser.role,
    }
    persistSession(session)
  }

  return createSuccessResponse('Active session found.', session)
}

export async function getCurrentUser() {
  return checkSession()
}

export async function updateOwnerProfile(payload = {}) {
  await delay()

  const { session, user } = getAuthenticatedOwner()
  const name = String(payload.name || '').trim()
  const email = String(payload.email || '')
    .trim()
    .toLowerCase()
  const phone = normalizeIndianPhone(payload.phone)

  if (name.length < 2 || name.length > 80) {
    throw createAuthError(
      'Owner name must contain between 2 and 80 characters.',
      422,
      'OWNER_NAME_INVALID',
    )
  }

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    throw createAuthError('Enter a valid email address.', 422, 'OWNER_EMAIL_INVALID')
  }

  if (!/^[6-9]\d{9}$/.test(phone)) {
    throw createAuthError(
      'Phone number must be a valid 10-digit Indian mobile number.',
      422,
      'OWNER_PHONE_INVALID',
    )
  }

  const existingUser = findUserByEmail(email)
  if (existingUser && existingUser.id !== user.id) {
    throw createAuthError(
      'Another account already uses this email address.',
      409,
      'ACCOUNT_EMAIL_EXISTS',
    )
  }

  Object.assign(user, { name, email, phone })

  const updatedSession = createUpdatedSession(session, user)
  persistSession(updatedSession)

  return createSuccessResponse('Owner profile updated successfully.', updatedSession)
}

export async function changeOwnerPassword(payload = {}) {
  await delay()

  const { session, user } = getAuthenticatedOwner()
  const currentPassword = String(payload.currentPassword || '')
  const newPassword = String(payload.newPassword || '')

  if (!currentPassword || !newPassword) {
    throw createAuthError(
      'Current password and new password are required.',
      422,
      'PASSWORD_FIELDS_REQUIRED',
    )
  }

  if (user.password !== currentPassword) {
    throw createAuthError('The current password is incorrect.', 422, 'CURRENT_PASSWORD_INVALID')
  }

  if (newPassword.length < 8) {
    throw createAuthError(
      'The new password must contain at least 8 characters.',
      422,
      'NEW_PASSWORD_TOO_SHORT',
    )
  }

  if (newPassword === currentPassword) {
    throw createAuthError(
      'The new password must be different from the current password.',
      422,
      'PASSWORD_UNCHANGED',
    )
  }

  user.password = newPassword

  const updatedSession = createUpdatedSession(session, user)
  persistSession(updatedSession)

  return createSuccessResponse('Password changed successfully.', updatedSession)
}
