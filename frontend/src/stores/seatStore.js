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
    floor: '',
    seatNumber: '',
    studentName: '',
    availability: '',
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

  const availableFloors = computed(() => {
    return [...new Set(seats.value.map((seat) => seat.floor))]
      .filter(Boolean)
      .sort((firstFloor, secondFloor) => firstFloor - secondFloor)
  })

  const filteredSeats = computed(() => {
    const filters = normalizeSeatFilters(seatFilters.value)

    return seats.value.filter((seat) => {
      const assignedStudentName = seat.assignedStudent?.name || ''
      const searchableText = [
        seat.seatNumber,
        seat.status,
        seat.floor,
        assignedStudentName,
        seat.notes,
        ...(seat.activeShifts || []),
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()

      const matchesSearch =
        !filters.search || searchableText.includes(filters.search)
      const matchesStatus = !filters.status || seat.status === filters.status
      const matchesShift =
        !filters.shift || seat.activeShifts?.includes(filters.shift)
      const matchesFloor = !filters.floor || String(seat.floor) === filters.floor
      const matchesSeatNumber =
        !filters.seatNumber ||
        seat.seatNumber.toLowerCase().includes(filters.seatNumber)
      const matchesStudentName =
        !filters.studentName ||
        assignedStudentName.toLowerCase().includes(filters.studentName)
      const matchesAvailability = matchesAvailabilityFilter(
        seat,
        filters.availability,
      )

      return (
        matchesSearch &&
        matchesStatus &&
        matchesShift &&
        matchesFloor &&
        matchesSeatNumber &&
        matchesStudentName &&
        matchesAvailability
      )
    })
  })

  const hasActiveSeatFilters = computed(() => {
    return Object.values(seatFilters.value).some((value) =>
      Boolean(String(value || '').trim()),
    )
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

  function normalizeSeatFilters(filters = {}) {
    return {
      search: String(filters.search || '').trim().toLowerCase(),
      status: String(filters.status || '').trim().toLowerCase(),
      shift: String(filters.shift || '').trim().toLowerCase(),
      floor: filters.floor ? String(filters.floor) : '',
      seatNumber: String(filters.seatNumber || '').trim().toLowerCase(),
      studentName: String(filters.studentName || '').trim().toLowerCase(),
      availability: String(filters.availability || '').trim().toLowerCase(),
    }
  }

  function matchesAvailabilityFilter(seat, availability) {
    if (!availability) return true

    const hasStudent = Boolean(seat.assignedStudent)
    const hasActiveShift = Array.isArray(seat.activeShifts)
      ? seat.activeShifts.length > 0
      : false

    if (availability === 'available-now') {
      return seat.status === 'available' && !hasStudent
    }

    if (availability === 'assigned') {
      return hasStudent
    }

    if (availability === 'unassigned') {
      return !hasStudent
    }

    if (availability === 'blocked') {
      return seat.status === 'reserved' || seat.status === 'maintenance'
    }

    if (availability === 'has-active-shift') {
      return hasActiveShift
    }

    return true
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
  async function fetchSeats() {
    const response = await runSeatServiceRequest(() =>
      seatService.getSeats(),
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

  function updateSeatFilter(filterName, value) {
    if (!(filterName in seatFilters.value)) return

    seatFilters.value = {
      ...seatFilters.value,
      [filterName]: value,
    }
  }

  function resetSeatFilters() {
    seatFilters.value = {
      search: '',
      status: '',
      shift: '',
      floor: '',
      seatNumber: '',
      studentName: '',
      availability: '',
    }
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
    availableFloors,
    filteredSeats,
    hasActiveSeatFilters,
    selectedSeat,
    errorMessage,

    fetchSeats,
    allocateSeat,
    transferSeat,
    updateShift,
    refreshSeatAvailability,
    selectSeat,
    clearSelection,
    updateSeatFilter,
    resetSeatFilters,
    clearError,
  }
})
