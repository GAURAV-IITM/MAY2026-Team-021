import axios from 'axios'

import { clearAuthState, getAccessToken, setAccessToken } from './authSession.js'

// src/api: Shared HTTP clients and API adapters for backend integration.
const API_BASE_URL = import.meta.env?.VITE_API_BASE_URL || '/api/v1'
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'X-Requested-With': 'XMLHttpRequest',
  },
})

const refreshClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    'X-Requested-With': 'XMLHttpRequest',
  },
})

let refreshPromise = null

function isPublicAuthRequest(config = {}) {
  const url = String(config.url || '')
  return url.includes('/auth/session/login') || url.includes('/auth/session/register-library')
}

function isSessionProbe(config = {}) {
  return String(config.url || '').includes('/auth/me')
}

async function refreshAccessToken() {
  if (!refreshPromise) {
    refreshPromise = refreshClient
      .post('/auth/session/refresh')
      .then(({ data }) => {
        setAccessToken(data.accessToken)
        return data.accessToken
      })
      .finally(() => {
        refreshPromise = null
      })
  }

  return refreshPromise
}

function redirectToLogin() {
  if (typeof window === 'undefined' || window.location.pathname === '/login') return

  const redirect = `${window.location.pathname}${window.location.search}`
  window.location.assign(`/login?redirect=${encodeURIComponent(redirect)}`)
}

apiClient.interceptors.request.use(
  (config) => {
    const token = getAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !isPublicAuthRequest(originalRequest)
    ) {
      originalRequest._retry = true

      try {
        const accessToken = await refreshAccessToken()
        originalRequest.headers.Authorization = `Bearer ${accessToken}`
        return apiClient(originalRequest)
      } catch (refreshError) {
        clearAuthState()
        if (!isSessionProbe(originalRequest)) {
          redirectToLogin()
        }
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  },
)

export { apiClient, refreshAccessToken, refreshClient }
export default apiClient
