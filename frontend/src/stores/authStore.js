import { defineStore } from 'pinia'

// src/stores: Pinia state containers for shared frontend state.
export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    role: null,
    tenant: null,
    isLoading: false,
    error: null,
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.user),
  },
  actions: {
    async login() {
      // TODO: Connect to authService.login when backend or mock contract is ready.
    },
    async logout() {
      // TODO: Connect to authService.logout when backend or mock contract is ready.
    },
    async loadCurrentUser() {
      // TODO: Load current user session when authentication is implemented.
    },
  },
})
