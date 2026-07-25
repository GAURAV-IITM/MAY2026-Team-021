import apiClient from '../api/axios'
import {
  clearAuthState,
  getAccessToken,
  persistAuthSession,
  readAuthSession,
  setAccessToken,
} from '../api/authSession.js'

// src/services: Auth service integrated with FastAPI-backed JWT and session handling.

function delay(ms = 500) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms)
  })
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

function getApiErrorMessage(error, fallbackMessage) {
  return error.response?.data?.error?.message || error.response?.data?.detail || fallbackMessage
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
        libraryId: user.libraryId,
        libraryName: user.libraryName,
      },
      role: user.role,
      token: accessToken,
      rememberMe: rememberMe,
      isAuthenticated: true,
    },
  }
}

export async function login(credentials = {}) {
  const { email, password, rememberMe = false } = credentials

  if (!email || !password) {
    throw createAuthError('Email and password are required.', 422, 'VALIDATION_ERROR')
  }

  try {
    const response = await apiClient.post('/auth/session/login', {
      email,
      password,
      rememberMe,
    })
    const { accessToken, user } = response.data
    setAccessToken(accessToken)

    const frontendSession = mapBackendUserToFrontend(user, accessToken, rememberMe)
    persistAuthSession(frontendSession.data)

    return frontendSession
  } catch (err) {
    const message = getApiErrorMessage(err, 'Invalid email or password.')
    throw createAuthError(message, err.response?.status || 401, 'INVALID_CREDENTIALS')
  }
}

export async function logout() {
  try {
    await apiClient.post('/auth/session/logout')
  } catch (err) {
    console.error('Logout API call failed:', err)
  }

  clearAuthState()

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

  const payload = {
    libraryName,
    ownerName,
    email,
    password,
    phone: phone || null,
    address: registrationData.address || null,
    seatCount,
  }

  try {
    const response = await apiClient.post('/auth/session/register-library', payload)
    const { accessToken, user } = response.data
    setAccessToken(accessToken)

    const frontendSession = mapBackendUserToFrontend(user, accessToken, false)
    frontendSession.data.registrationStatus = 'created'
    frontendSession.data.seatCount = seatCount
    frontendSession.data.seatsCreated = seatCount

    persistAuthSession(frontendSession.data)

    return frontendSession
  } catch (err) {
    const message = getApiErrorMessage(err, 'Registration failed.')
    throw createAuthError(message, err.response?.status || 400, 'REGISTRATION_ERROR')
  }
}

export async function registerLibrary(registrationData = {}) {
  return register(registrationData)
}

export async function validateStudentInvitation(token) {
  try {
    const response = await apiClient.get('/auth/invitations/validate', {
      params: { token },
    })
    return response.data
  } catch (err) {
    throw createAuthError(
      getApiErrorMessage(err, 'This invitation is invalid or has expired.'),
      err.response?.status || 422,
      'INVITATION_INVALID',
    )
  }
}

export async function acceptStudentInvitation(token, password) {
  try {
    const response = await apiClient.post('/auth/invitations/accept', {
      token,
      password,
    })
    return response.data
  } catch (err) {
    throw createAuthError(
      getApiErrorMessage(err, 'Unable to create the student password.'),
      err.response?.status || 422,
      'INVITATION_ACCEPT_FAILED',
    )
  }
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
  const persistedSession = readAuthSession()

  try {
    const response = await apiClient.get('/auth/me')
    const user = response.data
    const accessToken = getAccessToken()

    const frontendSession = mapBackendUserToFrontend(
      user,
      accessToken,
      persistedSession?.rememberMe,
    )
    persistAuthSession(frontendSession.data)

    return frontendSession
  } catch (err) {
    console.error('Session validation failed:', err)
    clearAuthState()
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

  try {
    const response = await apiClient.patch('/auth/profile', {
      name,
      email,
      phone,
    })
    const session = readAuthSession()
    const frontendSession = mapBackendUserToFrontend(
      response.data,
      getAccessToken(),
      session?.rememberMe,
    )
    persistAuthSession(frontendSession.data)
    return createSuccessResponse('Owner profile updated successfully.', frontendSession.data)
  } catch (err) {
    const message = getApiErrorMessage(err, 'Profile update failed.')
    throw createAuthError(message, err.response?.status || 400, 'PROFILE_UPDATE_ERROR')
  }
}

export async function changeOwnerPassword(payload = {}) {
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

  try {
    await apiClient.post('/auth/change-password', {
      currentPassword,
      newPassword,
    })
    return createSuccessResponse('Password changed successfully.', readAuthSession())
  } catch (err) {
    const message = getApiErrorMessage(err, 'Password change failed.')
    throw createAuthError(message, err.response?.status || 400, 'PASSWORD_CHANGE_ERROR')
  }
}
