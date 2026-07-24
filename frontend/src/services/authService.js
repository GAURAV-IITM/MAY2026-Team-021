import apiClient from '../api/axios'
import axios from 'axios'

// src/services: Auth service integrated with FastAPI-backed JWT and session handling.

let memorySession = null

function delay(ms = 500) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms)
  })
}

function getBrowserStorage() {
  if (typeof window === 'undefined' || !window.localStorage) return null
  return window.localStorage
}

function createSuccessResponse(message, data = {}) {
  return {
    success: true,
    message,
    data,
    meta: {
      source: 'backend-auth-service',
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

function normalizeIndianPhone(value) {
  const digits = String(value || '').replace(/\D/g, '')
  return digits.length === 12 && digits.startsWith('91') ? digits.slice(2) : digits
}

function mapBackendUserToFrontend(user, accessToken, rememberMe = false) {
  return {
    success: true,
    message: 'Operation successful.',
    data: {
      user: {
        id: user.id,
        name: user.name,
        email: user.email,
        phone: user.phone,
        role: user.role, // 'admin', 'student', or 'superadmin'
        libraryId: user.library_id,
        libraryName: user.library_name,
      },
      role: user.role,
      token: accessToken,
      rememberMe: rememberMe,
      isAuthenticated: true,
    }
  }
}

function persistSession(session) {
  memorySession = session

  const storage = getBrowserStorage()
  if (!storage) return

  storage.setItem('smart_library_access_token', session.token)
  storage.setItem('smart_library_auth_session', JSON.stringify(session))
}

function readSession() {
  const storage = getBrowserStorage()
  if (!storage) return memorySession

  const token = storage.getItem('smart_library_access_token')
  const session = storage.getItem('smart_library_auth_session')

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

  storage.removeItem('smart_library_access_token')
  storage.removeItem('smart_library_refresh_token')
  storage.removeItem('smart_library_auth_session')
}

export async function login(credentials = {}) {
  const { email, password, rememberMe = false } = credentials

  if (!email || !password) {
    throw createAuthError('Email and password are required.', 422, 'VALIDATION_ERROR')
  }

  try {
    const response = await apiClient.post('/auth/login', { email, password })
    const { access_token, refresh_token, user } = response.data

    const storage = getBrowserStorage()
    if (storage) {
      storage.setItem('smart_library_access_token', access_token)
      storage.setItem('smart_library_refresh_token', refresh_token)
    }

    const frontendSession = mapBackendUserToFrontend(user, access_token, rememberMe)
    persistSession(frontendSession.data)

    return frontendSession
  } catch (err) {
    const message = err.response?.data?.detail || 'Invalid email or password.'
    throw createAuthError(message, err.response?.status || 401, 'INVALID_CREDENTIALS')
  }
}

export async function logout() {
  try {
    await apiClient.post('/auth/logout')
  } catch (err) {
    console.error('Logout API call failed:', err)
  }

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
  const libraryName = String(registrationData.libraryName || '').trim()
  const ownerName = String(registrationData.ownerName || '').trim()
  const email = String(registrationData.email || '').trim().toLowerCase()
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

  const payload = {
    library_name: libraryName,
    owner_name: ownerName,
    email,
    password,
    phone: phone || null,
    address: registrationData.address || null,
    seat_count: seatCount,
  }

  try {
    const response = await apiClient.post('/auth/register-library', payload)
    const { access_token, refresh_token, user } = response.data

    const storage = getBrowserStorage()
    if (storage) {
      storage.setItem('smart_library_access_token', access_token)
      storage.setItem('smart_library_refresh_token', refresh_token)
    }

    const frontendSession = mapBackendUserToFrontend(user, access_token, false)
    frontendSession.data.registrationStatus = 'created'
    frontendSession.data.seatCount = seatCount
    frontendSession.data.seatsCreated = seatCount

    persistSession(frontendSession.data)

    return frontendSession
  } catch (err) {
    const message = err.response?.data?.detail || 'Registration failed.'
    throw createAuthError(message, err.response?.status || 400, 'REGISTRATION_ERROR')
  }
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
  const storage = getBrowserStorage()
  const accessToken = storage?.getItem('smart_library_access_token')
  const refreshToken = storage?.getItem('smart_library_refresh_token')

  if (!accessToken || !refreshToken) {
    clearSession()
    return createSuccessResponse('No active session.', {
      user: null,
      role: null,
      token: null,
      rememberMe: false,
      isAuthenticated: false,
    })
  }

  try {
    const response = await apiClient.get('/auth/me')
    const user = response.data

    const frontendSession = mapBackendUserToFrontend(user, accessToken, false)
    persistSession(frontendSession.data)

    return frontendSession
  } catch (err) {
    console.error('Session validation failed:', err)
    clearSession()
    return createSuccessResponse('No active session.', {
      user: null,
      role: null,
      token: null,
      rememberMe: false,
      isAuthenticated: false,
    })
  }
}

export async function getCurrentUser() {
  return checkSession()
}

export async function updateOwnerProfile(payload = {}) {
  await delay()

  const session = readSession()
  if (!session?.isAuthenticated) {
    throw createAuthError(
      'Your session has expired. Please sign in again.',
      401,
      'SESSION_REQUIRED',
    )
  }

  const name = String(payload.name || '').trim()
  const email = String(payload.email || '').trim().toLowerCase()
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

  const updatedUser = { ...session.user, name, email, phone }
  const updatedSession = { ...session, user: updatedUser }
  persistSession(updatedSession)

  return createSuccessResponse('Owner profile updated successfully.', updatedSession)
}

export async function changeOwnerPassword(payload = {}) {
  await delay()

  const session = readSession()
  if (!session?.isAuthenticated) {
    throw createAuthError(
      'Your session has expired. Please sign in again.',
      401,
      'SESSION_REQUIRED',
    )
  }

  const currentPassword = String(payload.currentPassword || '')
  const newPassword = String(payload.newPassword || '')

  if (!currentPassword || !newPassword) {
    throw createAuthError(
      'Current password and new password are required.',
      422,
      'PASSWORD_FIELDS_REQUIRED',
    )
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

  return createSuccessResponse('Password changed successfully.', session)
}
