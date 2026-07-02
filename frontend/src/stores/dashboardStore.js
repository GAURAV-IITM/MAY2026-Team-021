import { defineStore } from 'pinia'

// src/stores: Pinia state containers for shared frontend state.
export const useDashboardStore = defineStore('dashboard', {
  state: () => ({
    summary: null,
    isLoading: false,
    error: null,
  }),
  getters: {
    hasSummary: (state) => Boolean(state.summary),
  },
  actions: {
    async fetchDashboardSummary() {
      // TODO: Connect to dashboardService after mock contract is ready.
    },
  },
})
