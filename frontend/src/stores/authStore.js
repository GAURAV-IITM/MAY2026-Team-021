import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import * as authService from '../services/authService'

/**
 * Authentication store for Smart Library App.
 *
 * Responsibilities:
 * - Own auth-related UI state such as loading, errors, remember-me, and placeholders.
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

  async function runAuthServiceRequest(serviceRequest) {
    isLoading.value = true
    error.value = null

    try {
      return await serviceRequest()
    } catch (requestError) {
      error.value = requestError
      throw requestError
    } finally {
      isLoading.value = false
    }
  }

  async function login(credentials) {
    authStatus.value = 'checking'
    return runAuthServiceRequest(() => authService.login(credentials))
  }

  async function logout() {
    authStatus.value = 'checking'
    return runAuthServiceRequest(() => authService.logout())
  }

  async function register(registrationData) {
    authStatus.value = 'checking'
    return runAuthServiceRequest(() => authService.registerLibrary(registrationData))
  }

  async function forgotPassword(payload) {
    authStatus.value = 'checking'
    return runAuthServiceRequest(() => authService.forgotPassword(payload))
  }

  async function checkSession() {
    authStatus.value = 'checking'
    return runAuthServiceRequest(() => authService.getCurrentUser())
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
