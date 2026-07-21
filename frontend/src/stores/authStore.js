import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import * as authService from '../services/authService'

/**
 * Authentication store for Smart Library App.
 *
 * Responsibilities:
 * - Own auth-related UI state such as loading, errors, and remember-me preferences.
 * - Expose reusable getters for user, role, and authentication status.
 * - Delegate all authentication operations to authService.
 *
 * Future JWT notes:
 * - token is a placeholder for the eventual JWT or session token.
 * - Token persistence, refresh, expiry checks, and role validation should live in services/guards.
 * - This store should remain a thin state layer, not an authentication engine.
 */
export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const role = ref(null)
  const authStatus = ref('idle')
  const isLoading = ref(false)
  const error = ref(null)
  const token = ref(null)
  const rememberMe = ref(false)

  const isAuthenticated = computed(() => Boolean(user.value))
  const currentRole = computed(() => role.value)
  const currentUser = computed(() => user.value)

  function syncSession(response) {
    const session = response?.data || {}

    user.value = session.user || null
    role.value = session.role || null
    token.value = session.token || null
    rememberMe.value = Boolean(session.rememberMe)
    authStatus.value = session.isAuthenticated ? 'authenticated' : 'guest'
  }

  async function runAuthServiceRequest(serviceRequest, options = {}) {
    isLoading.value = true
    error.value = null

    try {
      const response = await serviceRequest()

      if (options.syncSession) {
        syncSession(response)
      }

      return response
    } catch (requestError) {
      error.value = requestError
      authStatus.value = 'error'
      throw requestError
    } finally {
      isLoading.value = false
    }
  }

  async function login(credentials) {
    authStatus.value = 'checking'
    return runAuthServiceRequest(() => authService.login(credentials), { syncSession: true })
  }

  async function logout() {
    authStatus.value = 'checking'
    return runAuthServiceRequest(() => authService.logout(), { syncSession: true })
  }

  async function register(registrationData) {
    authStatus.value = 'checking'
    return runAuthServiceRequest(() => authService.registerLibrary(registrationData), {
      syncSession: true,
    })
  }

  async function forgotPassword(payload) {
    authStatus.value = 'checking'
    return runAuthServiceRequest(() => authService.forgotPassword(payload))
  }

  async function checkSession() {
    authStatus.value = 'checking'
    return runAuthServiceRequest(() => authService.getCurrentUser(), { syncSession: true })
  }

  return {
    user,
    role,
    authStatus,
    isLoading,
    error,
    token,
    rememberMe,
    isAuthenticated,
    currentRole,
    currentUser,
    login,
    logout,
    register,
    forgotPassword,
    checkSession,
  }
})
