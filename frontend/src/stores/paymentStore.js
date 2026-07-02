import { defineStore } from 'pinia'

// src/stores: Pinia state containers for shared frontend state.
export const usePaymentStore = defineStore('payment', {
  state: () => ({
    payments: [],
    selectedPayment: null,
    isLoading: false,
    error: null,
  }),
  getters: {
    paymentCount: (state) => state.payments.length,
  },
  actions: {
    async fetchPayments() {
      // TODO: Connect to paymentService.getPayments after mock contract is ready.
    },
    async fetchPaymentById() {
      // TODO: Connect to paymentService.getPaymentById after mock contract is ready.
    },
  },
})
