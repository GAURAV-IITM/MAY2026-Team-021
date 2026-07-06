import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import * as seatService from '../services/seatService'

// src/stores: Centralized Seat Management state for the Smart Library App.
// TODO: Keep this store as the single frontend state boundary when FastAPI seat APIs are added.
export const useSeatStore = defineStore('seat', () => {
  const seats = ref([])
  const selectedSeatRecord = ref(null)
  const selectedStudent = ref(null)
  const selectedShift = ref('')
  const seatFilters = ref({
    search: '',
    status: '',
    shift: '',
  })
  const seatAvailability = ref(null)
  const isLoading = ref(false)
  const error = ref(null)

  const occupiedSeats = computed(() => {
    return seats.value.filter((seat) => isOccupiedSeat(seat))
  })

  const availableSeats = computed(() => {
    return seats.value.filter((seat) => isAvailableSeat(seat))
  })

  const totalSeats = computed(() => seats.value.length)

  const occupancyPercentage = computed(() => {
    if (totalSeats.value === 0) return 0

    return Math.round((occupiedSeats.value.length / totalSeats.value) * 100)
  })

  const seatsByShift = computed(() => {
    return seats.value.reduce((groupedSeats, seat) => {
      const shifts = Array.isArray(seat.activeShifts)
        ? seat.activeShifts
        : [seat.shift || 'unassigned']

      shifts.forEach((shift) => {
        if (!groupedSeats[shift]) {
          groupedSeats[shift] = []
        }

        groupedSeats[shift].push(seat)
      })

      return groupedSeats
    }, {})
  })

  const selectedSeat = computed(() => selectedSeatRecord.value)

  const errorMessage = computed(() => {
    return error.value ? getErrorMessage(error.value) : ''
  })

  function isOccupiedSeat(seat) {
    if (seat?.status) {
      return seat.status === 'occupied'
    }

    return (
      Boolean(
        seat?.studentId ||
          seat?.student?.id ||
          seat?.student ||
          seat?.assignedStudent?.id ||
          seat?.assignedStudent,
      )
    )
  }

  function isAvailableSeat(seat) {
    return seat?.status === 'available' && !isOccupiedSeat(seat)
  }

  function getErrorMessage(requestError) {
    return (
      requestError?.response?.data?.message ||
      requestError?.message ||
      'An unexpected seat service error occurred.'
    )
  }

  async function runSeatServiceRequest(serviceRequest) {
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

  function getResponseData(response) {
    return response?.data ?? response ?? null
  }

  function replaceSeatInList(updatedSeat) {
    if (!updatedSeat?.id) return

    const seatIndex = seats.value.findIndex((seat) => seat.id === updatedSeat.id)

    if (seatIndex === -1) {
      seats.value.push(updatedSeat)
      return
    }

    seats.value.splice(seatIndex, 1, updatedSeat)
  }

  function syncSeatStateFromResponse(response) {
    const data = getResponseData(response)

    if (!data) return

    if (Array.isArray(data)) {
      seats.value = data
      return
    }

    if (Array.isArray(data.seats)) {
      data.seats.forEach((seat) => replaceSeatInList(seat))
    }

    const updatedSeat = data.seat || data.updatedSeat || data.targetSeat

    if (updatedSeat) {
      replaceSeatInList(updatedSeat)
      selectedSeatRecord.value = updatedSeat
    }

    if (data.student || data.selectedStudent) {
      selectedStudent.value = data.student || data.selectedStudent
    }

    if (data.shift || data.selectedShift) {
      selectedShift.value = data.shift || data.selectedShift
    }
  }

  /**
   * Fetches seat records through seatService and stores them as the frontend source of truth.
   * TODO: Replace the mock service response with FastAPI query parameters for filters.
   */
  async function fetchSeats(filters = seatFilters.value) {
    const response = await runSeatServiceRequest(() =>
      seatService.getSeats({ ...filters }),
    )

    const data = getResponseData(response)
    const responseSeats = Array.isArray(data) ? data : data?.seats

    if (Array.isArray(responseSeats)) {
      seats.value = responseSeats
    }

    if (data?.availability) {
      seatAvailability.value = data.availability
    }

    return response
  }

  /**
   * Allocates a seat by delegating to seatService and syncing the returned seat/student state.
   * TODO: Move allocation rules and conflict checks to FastAPI.
   */
  async function allocateSeat(allocationPayload) {
    const response = await runSeatServiceRequest(() =>
      seatService.allocateSeat(allocationPayload),
    )

    syncSeatStateFromResponse(response)

    return response
  }

  /**
   * Transfers a student between seats through seatService and updates affected seat records.
   * TODO: Replace mock transfer responses with transactional FastAPI endpoints.
   */
  async function transferSeat(transferPayload) {
    const response = await runSeatServiceRequest(() =>
      seatService.transferSeat(transferPayload),
    )

    syncSeatStateFromResponse(response)

    return response
  }

  /**
   * Updates the selected shift through seatService and stores the service-confirmed shift.
   * TODO: Persist shift preferences and availability windows through FastAPI.
   */
  async function updateShift(shiftPayload) {
    const response = await runSeatServiceRequest(() =>
      seatService.updateShift(shiftPayload),
    )

    syncSeatStateFromResponse(response)

    const data = getResponseData(response)
    selectedShift.value =
      data?.shift || data?.selectedShift || shiftPayload?.shift || shiftPayload || ''

    return response
  }

  /**
   * Refreshes seat availability through seatService without exposing mock data to pages.
   * TODO: Replace mock availability calculations with FastAPI availability endpoints.
   */
  async function refreshSeatAvailability(filters = seatFilters.value) {
    const response = await runSeatServiceRequest(() =>
      seatService.refreshSeatAvailability({ ...filters }),
    )

    const data = getResponseData(response)
    seatAvailability.value = data?.availability || data || null

    return response
  }

  /**
   * Selects a seat by loading the service-confirmed record into store state.
   * TODO: Replace mock detail fetch with FastAPI GET /seats/{seatId}.
   */
  async function selectSeat(seatId) {
    const response = await runSeatServiceRequest(() =>
      seatService.getSeatById(seatId),
    )

    const data = getResponseData(response)
    const seat = data?.seat || data

    selectedSeatRecord.value = seat
    selectedStudent.value = seat?.assignedStudent || null
    selectedShift.value = seat?.activeShifts?.[0] || ''

    return response
  }

  /**
   * Clears seat, student, and shift selections after delegating to seatService.
   * TODO: Keep this local-only unless future backend workflows require session selection state.
   */
  async function clearSelection() {
    await runSeatServiceRequest(() => seatService.clearSelection())

    selectedSeatRecord.value = null
    selectedStudent.value = null
    selectedShift.value = ''
  }

  function clearError() {
    error.value = null
  }

  return {
    seats,
    selectedStudent,
    selectedShift,
    seatFilters,
    seatAvailability,
    isLoading,
    error,

    occupiedSeats,
    availableSeats,
    totalSeats,
    occupancyPercentage,
    seatsByShift,
    selectedSeat,
    errorMessage,

    fetchSeats,
    allocateSeat,
    transferSeat,
    updateShift,
    refreshSeatAvailability,
    selectSeat,
    clearSelection,
    clearError,
  }
})
