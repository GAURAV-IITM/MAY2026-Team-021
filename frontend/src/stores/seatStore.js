import { defineStore } from 'pinia'

// src/stores: Pinia state containers for shared frontend state.
export const useSeatStore = defineStore('seat', {
  state: () => ({
    seats: [],
    selectedSeat: null,
    isLoading: false,
    error: null,
  }),
  getters: {
    seatCount: (state) => state.seats.length,
  },
  actions: {
    async fetchSeats() {
      // TODO: Connect to seatService.getSeats after mock contract is ready.
    },
    async fetchSeatById() {
      // TODO: Connect to seatService.getSeatById after mock contract is ready.
    },
    async assignSeat() {
      // TODO: Connect to seatService.assignSeat after allocation rules are approved.
    },
  },
})
