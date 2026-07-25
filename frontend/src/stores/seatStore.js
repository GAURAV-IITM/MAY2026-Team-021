import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import * as seatService from '../services/seatService'

// src/stores: Centralized Seat Management state for the Smart Library App.
// TODO: Keep this store as the single frontend state boundary when FastAPI seat APIs are added.
export const useSeatStore = defineStore('seat', () => {
  const seats = ref([])
  const studyShifts = ref([])
  const floors = ref([])
  const selectedSeatRecord = ref(null)
  const selectedStudent = ref(null)
  const selectedShift = ref('')
  const seatFilters = ref({
    search: '',
    status: '',
    floor: '',
  })
  const seatAvailability = ref(null)
  const isLoading = ref(false)
  const error = ref(null)

  const occupiedSeats = computed(() => {
    return seats.value.filter((seat) => isOccupiedSeat(seat))
  })

  const availableSeats = computed(() => {
    return seats.value.filter((seat) => {
      return seat.physicalStatus === 'available' && !isOccupiedSeat(seat)
    })
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

  const enabledShifts = computed(() => {
    return studyShifts.value.filter((shift) => shift.isEnabled !== false)
  })

  const shiftRows = computed(() => {
    return studyShifts.value.map((shift) => ({
      ...shift,
      ...getShiftSeatCounts(shift.id),
    }))
  })

  const availableFloors = computed(() => {
    return [...new Set(seats.value.map((seat) => seat.floor))]
      .filter(Boolean)
      .sort((firstFloor, secondFloor) => firstFloor - secondFloor)
  })

  const filteredSeats = computed(() => {
    const filters = normalizeSeatFilters(seatFilters.value)

    return seats.value.filter((seat) => {
      const searchableText = [
        seat.seatNumber,
        seat.physicalStatus,
        seat.floor,
        seat.notes,
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()

      const matchesSearch =
        !filters.search || searchableText.includes(filters.search)
      const matchesStatus =
        !filters.status ||
        (filters.status === 'occupied' && isOccupiedSeat(seat)) ||
        (filters.status === 'available' &&
          seat.physicalStatus === 'available' &&
          !isOccupiedSeat(seat)) ||
        (!['available', 'occupied'].includes(filters.status) &&
          seat.physicalStatus === filters.status)
      const matchesFloor = !filters.floor || String(seat.floor) === filters.floor

      return matchesSearch && matchesStatus && matchesFloor
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
    return Boolean(seat?.isOccupied) || Number(seat?.occupiedShiftCount || 0) > 0
  }

  function getShiftSeatCounts(shiftId) {
    const shiftSeats = seats.value.filter((seat) => {
      return seat.shiftAvailability?.some((shift) => shift.shiftId === shiftId)
    })
    const getShiftStatus = (seat) => {
      return seat.shiftAvailability?.find((shift) => shift.shiftId === shiftId)
        ?.status
    }

    return {
      totalSeatCount: shiftSeats.length,
      occupiedSeatCount: shiftSeats.filter((seat) => {
        const shiftAvailability = seat.shiftAvailability?.find((shift) => {
          return shift.shiftId === shiftId
        })

        return (
          shiftAvailability?.status === 'occupied' &&
          !shiftAvailability.isPartialBlock
        )
      }).length,
      blockedSeatCount: shiftSeats.filter((seat) => {
        return Boolean(
          seat.shiftAvailability?.find((shift) => shift.shiftId === shiftId)
            ?.isPartialBlock,
        )
      }).length,
      availableSeatCount: shiftSeats.filter((seat) => {
        return getShiftStatus(seat) === 'available'
      }).length,
      reservedSeatCount: shiftSeats.filter((seat) => {
        const shiftAvailability = seat.shiftAvailability?.find((shift) => {
          return shift.shiftId === shiftId
        })

        return (
          shiftAvailability?.status === 'reserved' &&
          !shiftAvailability.isPartialBlock
        )
      }).length,
    }
  }

  function normalizeSeatFilters(filters = {}) {
    return {
      search: String(filters.search || '').trim().toLowerCase(),
      status: String(filters.status || '').trim().toLowerCase(),
      floor: filters.floor ? String(filters.floor) : '',
    }
  }

  function getErrorMessage(requestError) {
    return (
      requestError?.response?.data?.error?.message ||
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
      seats.value = data.seats
    }

    if (Array.isArray(data.deletedSeatIds)) {
      const deletedSeatIds = new Set(data.deletedSeatIds.map((seatId) => String(seatId)))

      seats.value = seats.value.filter((seat) => !deletedSeatIds.has(seat.id))

      if (deletedSeatIds.has(selectedSeatRecord.value?.id)) {
        selectedSeatRecord.value = null
      }
    }

    if (Array.isArray(data.shifts)) {
      studyShifts.value = data.shifts
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

    if (Array.isArray(data?.shifts)) {
      studyShifts.value = data.shifts
    }

    return response
  }

  async function fetchFloors() {
    const response = await runSeatServiceRequest(() => seatService.fetchFloors())
    floors.value = response.data
    return response
  }

  async function createFloor(payload) {
    const response = await runSeatServiceRequest(() => seatService.createFloor(payload))
    await fetchFloors()
    return response
  }

  async function updateFloor(floorId, payload) {
    const response = await runSeatServiceRequest(() =>
      seatService.updateFloor(floorId, payload),
    )
    await fetchFloors()
    return response
  }

  async function deleteFloor(floorId) {
    const response = await runSeatServiceRequest(() => seatService.deleteFloor(floorId))
    await fetchFloors()
    return response
  }

  async function createSeat(seatPayload) {
    const response = await runSeatServiceRequest(() =>
      seatService.createSeat(seatPayload),
    )

    syncSeatStateFromResponse(response)

    return response
  }

  async function updateSeat(seatId, seatPayload) {
    const response = await runSeatServiceRequest(() =>
      seatService.updateSeat(seatId, seatPayload),
    )

    syncSeatStateFromResponse(response)

    return response
  }

  async function deleteSeat(seatId) {
    const response = await runSeatServiceRequest(() =>
      seatService.deleteSeat(seatId),
    )

    syncSeatStateFromResponse(response)

    return response
  }

  async function bulkUpdateSeatStatus(seatIds, statusPayload) {
    const response = await runSeatServiceRequest(() =>
      seatService.bulkUpdateSeatStatus(seatIds, statusPayload),
    )

    syncSeatStateFromResponse(response)

    return response
  }

  async function bulkDeleteSeats(seatIds) {
    const response = await runSeatServiceRequest(() =>
      seatService.bulkDeleteSeats(seatIds),
    )

    syncSeatStateFromResponse(response)

    return response
  }

  /**
   * Fetches study shifts through seatService and stores them for dynamic shift workflows.
   * TODO: Replace the mock service response with FastAPI GET /shifts.
   */
  async function fetchShifts() {
    const response = await runSeatServiceRequest(() =>
      seatService.fetchShifts(),
    )

    syncSeatStateFromResponse(response)

    const data = getResponseData(response)

    if (data?.availability) {
      seatAvailability.value = data.availability
    }

    return response
  }

  /**
   * Creates a study shift through seatService.
   * TODO: Persist unlimited tenant-defined shifts through FastAPI.
   */
  async function createShift(shiftPayload) {
    const response = await runSeatServiceRequest(() =>
      seatService.createShift(shiftPayload),
    )

    syncSeatStateFromResponse(response)

    return response
  }

  /**
   * Updates shift name, status, and timing through seatService.
   * TODO: Add backend validation for tenant-specific shift overlaps in FastAPI.
   */
  async function updateStudyShift(shiftId, shiftPayload) {
    const response = await runSeatServiceRequest(() =>
      seatService.updateStudyShift(shiftId, shiftPayload),
    )

    syncSeatStateFromResponse(response)

    return response
  }

  /**
   * Updates only shift timing through seatService.
   * TODO: Replace mock timing updates with FastAPI PATCH /shifts/{id}/timing.
   */
  async function updateShiftTiming(shiftId, timingPayload) {
    const response = await runSeatServiceRequest(() =>
      seatService.updateShiftTiming(shiftId, timingPayload),
    )

    syncSeatStateFromResponse(response)

    return response
  }

  /**
   * Enables or disables a study shift through seatService.
   * TODO: Let FastAPI enforce whether disabled shifts can accept new allocations.
   */
  async function toggleStudyShift(shiftId, isEnabled) {
    const response = await runSeatServiceRequest(() =>
      seatService.toggleStudyShift(shiftId, isEnabled),
    )

    syncSeatStateFromResponse(response)

    return response
  }

  /**
   * Deletes a study shift through seatService and syncs affected seat availability.
   * TODO: Replace mock deletion with FastAPI delete semantics and audit logging.
   */
  async function deleteStudyShift(shiftId) {
    const response = await runSeatServiceRequest(() =>
      seatService.deleteStudyShift(shiftId),
    )

    syncSeatStateFromResponse(response)

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
   * Updates a seat's operational status through seatService.
   * TODO: Replace mock status updates with FastAPI PATCH /seats/{id}/status and audit logging.
   */
  async function updateSeatStatus(seatId, statusPayload) {
    const response = await runSeatServiceRequest(() =>
      seatService.updateSeatStatus(seatId, statusPayload),
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
      floor: '',
    }
  }

  function clearError() {
    error.value = null
  }

  return {
    seats,
    studyShifts,
    floors,
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
    enabledShifts,
    shiftRows,
    availableFloors,
    filteredSeats,
    hasActiveSeatFilters,
    selectedSeat,
    errorMessage,

    fetchSeats,
    fetchFloors,
    createFloor,
    updateFloor,
    deleteFloor,
    createSeat,
    updateSeat,
    deleteSeat,
    bulkUpdateSeatStatus,
    bulkDeleteSeats,
    fetchShifts,
    allocateSeat,
    createShift,
    updateStudyShift,
    updateShiftTiming,
    toggleStudyShift,
    deleteStudyShift,
    updateSeatStatus,
    updateShift,
    refreshSeatAvailability,
    selectSeat,
    clearSelection,
    updateSeatFilter,
    resetSeatFilters,
    clearError,
  }
})
