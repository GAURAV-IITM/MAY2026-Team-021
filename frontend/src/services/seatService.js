import apiClient from '../api/axios.js'

function operationResponse(response, key) {
  return {
    ...response.data,
    data: key ? { [key]: response.data.data } : response.data.data,
  }
}

function unavailableOperation(message) {
  const error = new Error(message)
  error.response = {
    status: 501,
    data: {
      error: {
        code: 'FEATURE_NOT_AVAILABLE',
        message,
      },
    },
  }
  return Promise.reject(error)
}

export async function fetchSeats(filters = {}) {
  const response = await apiClient.get('/seats', {
    params: {
      search: filters.search || undefined,
      floorId: filters.floorId || undefined,
      status: filters.status || undefined,
    },
  })
  return response.data
}

export async function getSeats(filters = {}) {
  return fetchSeats(filters)
}

export async function createSeat(seatPayload = {}) {
  const response = await apiClient.post('/seats', seatPayload)
  return operationResponse(response, 'seat')
}

export async function updateSeat(seatId, seatPayload = {}) {
  const response = await apiClient.patch(`/seats/${seatId}`, seatPayload)
  return operationResponse(response, 'seat')
}

export async function deleteSeat(seatId) {
  const response = await apiClient.delete(`/seats/${seatId}`)
  return response.data
}

export async function bulkUpdateSeatStatus(seatIds = [], statusPayload = {}) {
  const response = await apiClient.patch('/seats/bulk/status', {
    seatIds,
    ...statusPayload,
  })
  return response.data
}

export async function bulkDeleteSeats(seatIds = []) {
  const response = await apiClient.post('/seats/bulk/delete', { seatIds })
  return response.data
}

export async function getSeatById(seatId) {
  const response = await apiClient.get(`/seats/${seatId}`)
  return response.data
}

export async function updateSeatStatus(seatId, statusPayload = {}) {
  const response = await apiClient.patch(`/seats/${seatId}/status`, statusPayload)
  return operationResponse(response, 'seat')
}

export async function fetchFloors() {
  const response = await apiClient.get('/floors')
  return response.data
}

export async function createFloor(payload = {}) {
  const response = await apiClient.post('/floors', payload)
  return response.data
}

export async function updateFloor(floorId, payload = {}) {
  const response = await apiClient.patch(`/floors/${floorId}`, payload)
  return response.data
}

export async function deleteFloor(floorId) {
  const response = await apiClient.delete(`/floors/${floorId}`)
  return response.data
}

export async function fetchShifts() {
  const response = await apiClient.get('/shifts', {
    params: { includeInactive: true },
  })
  return {
    ...response.data,
    data: { shifts: response.data.data },
  }
}

async function shiftMutation(request) {
  await request
  return fetchShifts()
}

export async function createShift(shiftPayload = {}) {
  return shiftMutation(apiClient.post('/shifts', shiftPayload))
}

export async function updateStudyShift(shiftId, shiftPayload = {}) {
  return shiftMutation(apiClient.patch(`/shifts/${shiftId}`, shiftPayload))
}

export async function updateShiftTiming(shiftId, timingPayload = {}) {
  return updateStudyShift(shiftId, timingPayload)
}

export async function toggleStudyShift(shiftId, isEnabled) {
  return shiftMutation(
    apiClient.patch(`/shifts/${shiftId}/status`, { isEnabled }),
  )
}

export async function deleteStudyShift(shiftId) {
  return shiftMutation(apiClient.delete(`/shifts/${shiftId}`))
}

export async function validateShiftSelection(shiftIds = []) {
  const response = await apiClient.post('/shifts/validate-selection', { shiftIds })
  return response.data
}

export async function fetchSeatAvailability(filters = {}) {
  const params = new URLSearchParams()
  const shiftIds = Array.isArray(filters.shiftIds) ? filters.shiftIds : []

  shiftIds.forEach((shiftId) => {
    params.append('shiftId', shiftId)
  })
  params.set('startDate', filters.startDate)
  params.set('endDate', filters.endDate)
  if (filters.floorId) params.set('floorId', filters.floorId)
  if (filters.excludeStudentId) {
    params.set('excludeStudentId', filters.excludeStudentId)
  }

  const response = await apiClient.get('/seat-allocations/availability', {
    params,
  })
  return response.data
}

export async function refreshSeatAvailability(filters = {}) {
  return fetchSeatAvailability(filters)
}

export async function initializeLibrarySeats() {
  return fetchSeats()
}

export async function allocateSeat() {
  return unavailableOperation(
    'Seat allocation will be connected in Phase 3.',
  )
}

export async function assignSeat(payload = {}) {
  return allocateSeat(payload)
}

export async function releaseSeat() {
  return unavailableOperation(
    'Seat release will be connected in Phase 3.',
  )
}

export async function updateShift(shiftPayload = {}) {
  return {
    success: true,
    message: 'Shift selection updated.',
    data: { selectedShift: shiftPayload.shift || shiftPayload },
  }
}

export async function clearSelection() {
  return {
    success: true,
    message: 'Seat selection cleared.',
    data: null,
  }
}
