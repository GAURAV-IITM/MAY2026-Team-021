import {
  SEAT_NETWORK_DELAY_MS,
  SEAT_SHIFTS,
  SEAT_STATUSES,
  seatMock,
} from '../mocks/seatMock'

// src/services: Mock seat service used during Milestone 2.
// TODO: Replace these mock operations with Axios-backed FastAPI requests in Milestone 3.

let seats = clone(seatMock)

function delay(ms = SEAT_NETWORK_DELAY_MS) {
  return new Promise((resolve) => {
    globalThis.setTimeout(resolve, ms)
  })
}

function clone(value) {
  return structuredClone(value)
}

function createSuccessResponse(message, data, meta = {}) {
  return {
    success: true,
    message,
    data: clone(data),
    meta: {
      source: 'mock-seat-service',
      timestamp: new Date().toISOString(),
      ...meta,
    },
  }
}

function createSeatError(message, status = 400, code = 'SEAT_ERROR') {
  const error = new Error(message)

  error.response = {
    status,
    data: {
      success: false,
      message,
      error: { code },
    },
  }

  return error
}

function normalizeFilters(filters = {}) {
  return {
    search: String(filters.search || '').trim().toLowerCase(),
    status: String(filters.status || '').trim().toLowerCase(),
    shift: String(filters.shift || '').trim().toLowerCase(),
    floor: filters.floor ? Number(filters.floor) : '',
  }
}

function filterSeats(sourceSeats, filters = {}) {
  const normalizedFilters = normalizeFilters(filters)

  return sourceSeats.filter((seat) => {
    const assignedStudentName = seat.assignedStudent?.name || ''
    const matchesSearch =
      !normalizedFilters.search ||
      seat.seatNumber.toLowerCase().includes(normalizedFilters.search) ||
      assignedStudentName.toLowerCase().includes(normalizedFilters.search)

    const matchesStatus =
      !normalizedFilters.status || seat.status === normalizedFilters.status

    const matchesShift =
      !normalizedFilters.shift ||
      seat.activeShifts.includes(normalizedFilters.shift)

    const matchesFloor =
      !normalizedFilters.floor || seat.floor === normalizedFilters.floor

    return matchesSearch && matchesStatus && matchesShift && matchesFloor
  })
}

function buildSeatAvailability(sourceSeats = seats, filters = {}) {
  const filteredSeats = filterSeats(sourceSeats, filters)
  const totalSeats = filteredSeats.length
  const occupiedSeats = filteredSeats.filter(
    (seat) => seat.status === SEAT_STATUSES.OCCUPIED,
  ).length
  const availableSeats = filteredSeats.filter(
    (seat) => seat.status === SEAT_STATUSES.AVAILABLE,
  ).length
  const maintenanceSeats = filteredSeats.filter(
    (seat) => seat.status === SEAT_STATUSES.MAINTENANCE,
  ).length
  const reservedSeats = filteredSeats.filter(
    (seat) => seat.status === SEAT_STATUSES.RESERVED,
  ).length

  return {
    totalSeats,
    occupiedSeats,
    availableSeats,
    reservedSeats,
    maintenanceSeats,
    occupancyPercentage:
      totalSeats === 0 ? 0 : Math.round((occupiedSeats / totalSeats) * 100),
    byShift: buildShiftAvailability(filteredSeats),
    filters: normalizeFilters(filters),
  }
}

function buildShiftAvailability(sourceSeats) {
  return Object.values(SEAT_SHIFTS).reduce((availability, shift) => {
    const shiftSeats = sourceSeats.filter((seat) =>
      seat.activeShifts.includes(shift),
    )

    availability[shift] = {
      totalSeats: shiftSeats.length,
      occupiedSeats: shiftSeats.filter(
        (seat) => seat.status === SEAT_STATUSES.OCCUPIED,
      ).length,
      availableSeats: shiftSeats.filter(
        (seat) => seat.status === SEAT_STATUSES.AVAILABLE,
      ).length,
      reservedSeats: shiftSeats.filter(
        (seat) => seat.status === SEAT_STATUSES.RESERVED,
      ).length,
    }

    return availability
  }, {})
}

function resolveSeatIndex(seatIdentifier) {
  const normalizedIdentifier =
    typeof seatIdentifier === 'object'
      ? seatIdentifier.id || seatIdentifier.seatId || seatIdentifier.seatNumber
      : seatIdentifier

  return seats.findIndex((seat) => {
    return (
      seat.id === String(normalizedIdentifier) ||
      seat.seatNumber === String(normalizedIdentifier)
    )
  })
}

function getSeatByIdentifier(seatIdentifier) {
  const seatIndex = resolveSeatIndex(seatIdentifier)

  if (seatIndex === -1) {
    throw createSeatError('Seat not found.', 404, 'SEAT_NOT_FOUND')
  }

  return { seatIndex, seat: seats[seatIndex] }
}

function ensureSeatCanBeAllocated(seat) {
  if (seat.status === SEAT_STATUSES.MAINTENANCE) {
    throw createSeatError(
      'Seat is under maintenance and cannot be allocated.',
      409,
      'SEAT_UNDER_MAINTENANCE',
    )
  }

  if (seat.status === SEAT_STATUSES.RESERVED) {
    throw createSeatError(
      'Seat is reserved and cannot be allocated.',
      409,
      'SEAT_RESERVED',
    )
  }

  if (seat.status === SEAT_STATUSES.OCCUPIED || seat.assignedStudent) {
    throw createSeatError(
      'Seat is already occupied.',
      409,
      'SEAT_ALREADY_OCCUPIED',
    )
  }
}

function normalizeAssignedStudent(student) {
  if (!student) {
    throw createSeatError(
      'Assigned student is required.',
      422,
      'ASSIGNED_STUDENT_REQUIRED',
    )
  }

  const studentName =
    student.name ||
    [student.firstName, student.lastName].filter(Boolean).join(' ') ||
    'Selected Student'

  return {
    id: String(student.id || student.studentId || 'student-pending'),
    name: studentName,
    email: student.email || '',
  }
}

function normalizeActiveShifts(value) {
  const shifts = Array.isArray(value) ? value : [value]
  const allowedShifts = Object.values(SEAT_SHIFTS)

  return shifts
    .filter(Boolean)
    .map((shift) => String(shift).toLowerCase())
    .filter((shift) => allowedShifts.includes(shift))
}

function getPayloadStudent(payload = {}) {
  return payload.assignedStudent || payload.student || payload.selectedStudent
}

function getPayloadSeatId(payload = {}) {
  return payload.seatId || payload.id || payload.seatNumber
}

function buildOperationData(extraData = {}) {
  return {
    ...extraData,
    availability: buildSeatAvailability(seats),
  }
}

// TODO: Replace with GET /api/seats when FastAPI endpoints are ready.
export async function fetchSeats(filters = {}) {
  await delay()

  const filteredSeats = filterSeats(seats, filters)

  return createSuccessResponse(
    'Seats fetched successfully.',
    {
      seats: filteredSeats,
      availability: buildSeatAvailability(seats, filters),
    },
    {
      count: filteredSeats.length,
      filters: normalizeFilters(filters),
    },
  )
}

// TODO: Replace with GET /api/seats/{seatId} when FastAPI endpoints are ready.
export async function getSeatById(seatId) {
  await delay()

  const { seat } = getSeatByIdentifier(seatId)

  return createSuccessResponse('Seat fetched successfully.', { seat })
}

// TODO: Replace with POST /api/seats/{seatId}/allocate when FastAPI endpoints are ready.
export async function allocateSeat(allocationPayload = {}) {
  await delay()

  const { seatIndex, seat } = getSeatByIdentifier(
    getPayloadSeatId(allocationPayload),
  )

  ensureSeatCanBeAllocated(seat)

  const assignedStudent = normalizeAssignedStudent(
    getPayloadStudent(allocationPayload),
  )
  const activeShifts =
    normalizeActiveShifts(
      allocationPayload.activeShifts || allocationPayload.shift,
    ) || []

  const updatedSeat = {
    ...seat,
    status: SEAT_STATUSES.OCCUPIED,
    assignedStudent,
    activeShifts:
      activeShifts.length > 0 ? activeShifts : clone(seat.activeShifts),
    notes: allocationPayload.notes || seat.notes,
  }

  seats[seatIndex] = updatedSeat

  return createSuccessResponse(
    'Seat allocated successfully.',
    buildOperationData({
      seat: updatedSeat,
      assignedStudent,
      student: assignedStudent,
    }),
  )
}

// TODO: Replace with POST /api/seats/transfer when FastAPI endpoints are ready.
export async function transferSeat(transferPayload = {}) {
  await delay()

  const sourceSeatId =
    transferPayload.fromSeatId ||
    transferPayload.sourceSeatId ||
    transferPayload.currentSeatId
  const targetSeatId =
    transferPayload.toSeatId ||
    transferPayload.targetSeatId ||
    transferPayload.newSeatId

  const source = getSeatByIdentifier(sourceSeatId)
  const target = getSeatByIdentifier(targetSeatId)

  if (source.seat.id === target.seat.id) {
    throw createSeatError(
      'Source and target seats must be different.',
      422,
      'SAME_SOURCE_AND_TARGET_SEAT',
    )
  }

  ensureSeatCanBeAllocated(target.seat)

  const assignedStudent = normalizeAssignedStudent(
    getPayloadStudent(transferPayload) || source.seat.assignedStudent,
  )
  const activeShifts = normalizeActiveShifts(
    transferPayload.activeShifts || transferPayload.shift,
  )

  const updatedSourceSeat = {
    ...source.seat,
    status: SEAT_STATUSES.AVAILABLE,
    assignedStudent: null,
    notes: transferPayload.sourceNotes || source.seat.notes,
  }
  const updatedTargetSeat = {
    ...target.seat,
    status: SEAT_STATUSES.OCCUPIED,
    assignedStudent,
    activeShifts:
      activeShifts.length > 0 ? activeShifts : clone(target.seat.activeShifts),
    notes: transferPayload.targetNotes || target.seat.notes,
  }

  seats[source.seatIndex] = updatedSourceSeat
  seats[target.seatIndex] = updatedTargetSeat

  return createSuccessResponse(
    'Seat transferred successfully.',
    buildOperationData({
      seats: [updatedSourceSeat, updatedTargetSeat],
      sourceSeat: updatedSourceSeat,
      targetSeat: updatedTargetSeat,
      seat: updatedTargetSeat,
      assignedStudent,
      student: assignedStudent,
    }),
  )
}

// TODO: Replace with PATCH /api/seats/{seatId}/shifts when FastAPI endpoints are ready.
export async function updateShift(shiftPayload = {}) {
  await delay()

  const selectedShift =
    typeof shiftPayload === 'string'
      ? shiftPayload
      : shiftPayload.shift || shiftPayload.selectedShift || ''
  const seatId = getPayloadSeatId(shiftPayload)

  if (!seatId) {
    return createSuccessResponse(
      'Selected shift updated successfully.',
      buildOperationData({
        shift: selectedShift,
        selectedShift,
      }),
    )
  }

  const { seatIndex, seat } = getSeatByIdentifier(seatId)
  const activeShifts = normalizeActiveShifts(
    shiftPayload.activeShifts || selectedShift || seat.activeShifts,
  )
  const updatedSeat = {
    ...seat,
    activeShifts,
  }

  seats[seatIndex] = updatedSeat

  return createSuccessResponse(
    'Seat shifts updated successfully.',
    buildOperationData({
      seat: updatedSeat,
      shift: selectedShift || activeShifts[0] || '',
      selectedShift: selectedShift || activeShifts[0] || '',
    }),
  )
}

// TODO: Replace with GET /api/seats/availability when FastAPI endpoints are ready.
export async function fetchSeatAvailability(filters = {}) {
  await delay()

  return createSuccessResponse(
    'Seat availability fetched successfully.',
    {
      availability: buildSeatAvailability(seats, filters),
    },
    {
      filters: normalizeFilters(filters),
    },
  )
}

// Compatibility aliases for the current store contract.
// TODO: Remove aliases after all callers use the final REST-style method names.
export async function getSeats(filters = {}) {
  return fetchSeats(filters)
}

export async function refreshSeatAvailability(filters = {}) {
  return fetchSeatAvailability(filters)
}

export async function assignSeat(allocationPayload = {}) {
  return allocateSeat(allocationPayload)
}

export async function clearSelection() {
  await delay(0)

  return createSuccessResponse('Seat selection cleared successfully.', {
    selectedSeat: null,
    selectedStudent: null,
    selectedShift: '',
  })
}

export async function releaseSeat(seatId) {
  await delay()

  const { seatIndex, seat } = getSeatByIdentifier(seatId)
  const updatedSeat = {
    ...seat,
    status: SEAT_STATUSES.AVAILABLE,
    assignedStudent: null,
  }

  seats[seatIndex] = updatedSeat

  return createSuccessResponse(
    'Seat released successfully.',
    buildOperationData({ seat: updatedSeat }),
  )
}
