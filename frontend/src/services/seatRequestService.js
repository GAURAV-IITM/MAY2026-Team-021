import apiClient from '../api/axios.js'


export function buildSeatRequestParams(filters = {}) {
  return {
    page: filters.page || 1,
    pageSize: filters.pageSize || 10,
    search: filters.search?.trim() || undefined,
    status: filters.status || undefined,
    studentId: filters.studentId || undefined,
    preferredFloorId: filters.preferredFloorId || undefined,
    preferredShiftId: filters.preferredShiftId || undefined,
    sortBy: filters.sortBy || 'submittedAt',
    sortOrder: filters.sortOrder || 'desc',
  }
}


export function normalizeSeatRequest(request) {
  return {
    ...request,
    studentId: request.student.id,
    studentName: request.student.name,
    enrollmentNumber: request.student.enrollmentNumber,
    currentSeatNumber: request.currentAllocation?.seatNumber || '',
    currentShiftName: request.currentAllocation?.shiftName || '',
    preferredSeatNumber: request.preferredSeat?.seatNumber || '',
    preferredFloorName: request.preferredFloor?.name || '',
    preferredFloor: request.preferredFloor?.levelNumber ?? null,
    preferredShiftId: request.preferredShift.id,
    preferredShiftName: request.preferredShift.name,
    adminNote: request.reviewNote || '',
    resolvedAt: request.reviewedAt,
  }
}


export async function getSeatRequests(filters = {}) {
  const response = await apiClient.get('/seat-requests', {
    params: buildSeatRequestParams(filters),
  })
  return {
    ...response.data,
    data: {
      requests: response.data.data.map(normalizeSeatRequest),
    },
  }
}


export async function reviewSeatRequest(requestId, payload = {}) {
  const response = await apiClient.patch(
    `/seat-requests/${requestId}/review`,
    {
      decision: payload.decision,
      reviewNote: payload.reviewNote ?? payload.adminNote ?? null,
    },
  )
  return {
    ...response.data,
    data: normalizeSeatRequest(response.data.data),
  }
}
