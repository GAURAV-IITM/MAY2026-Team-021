import {
  SEAT_NETWORK_DELAY_MS,
  SEAT_STATUSES,
  seatMock,
  shiftMock,
} from '../mocks/seatMock'

// src/services: Mock seat service used during Milestone 2.
// TODO: Replace these mock operations with Axios-backed FastAPI requests in Milestone 3.

let seats = clone(seatMock)
let shifts = clone(shiftMock)

const ALLOCATION_STATUSES = Object.freeze({
  ACTIVE: 'active',
  RESERVED: 'reserved',
})

const INITIAL_ALLOCATION_SHIFTS_BY_SEAT = Object.freeze({
  'seat-001': ['office-hours'],
  'seat-003': ['afternoon'],
  'seat-004': ['evening'],
  'seat-005': ['late-night'],
  'seat-008': ['early-morning'],
  'seat-010': ['morning'],
})

let seatAllocations = buildInitialSeatAllocations(seats)

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

function buildInitialSeatAllocations(sourceSeats = []) {
  return sourceSeats.flatMap((seat) => {
    if (!seat.assignedStudent) return []
    if (
      seat.status !== SEAT_STATUSES.OCCUPIED &&
      seat.status !== SEAT_STATUSES.RESERVED
    ) {
      return []
    }

    const allocationShifts =
      INITIAL_ALLOCATION_SHIFTS_BY_SEAT[seat.id] || seat.activeShifts || []

    return allocationShifts.map((shiftId) => {
      const shift = getShiftById(shiftId).shift

      return {
        id: `${seat.id}-${shiftId}-allocation`,
        seatId: seat.id,
        seatNumber: seat.seatNumber,
        shiftId,
        shiftName: shift.name,
        startTime: shift.startTime,
        endTime: shift.endTime,
        student: clone(seat.assignedStudent),
        status:
          seat.status === SEAT_STATUSES.RESERVED
            ? ALLOCATION_STATUSES.RESERVED
            : ALLOCATION_STATUSES.ACTIVE,
        createdAt: '2026-01-01T06:00:00.000Z',
        updatedAt: '2026-01-01T06:00:00.000Z',
      }
    })
  })
}

function parseTimeToMinutes(time) {
  const [hour = '0', minute = '0'] = String(time || '00:00').split(':')

  return Number(hour) * 60 + Number(minute)
}

function normalizeTimeInterval(startTime, endTime) {
  const start = parseTimeToMinutes(startTime)
  let end = parseTimeToMinutes(endTime)

  if (end <= start) {
    end += 24 * 60
  }

  return { start, end }
}

function getShiftInterval(shift) {
  return normalizeTimeInterval(shift.startTime, shift.endTime)
}

function getAllocationInterval(allocation) {
  return normalizeTimeInterval(allocation.startTime, allocation.endTime)
}

function intervalsOverlap(firstInterval, secondInterval) {
  return (
    firstInterval.start < secondInterval.end &&
    secondInterval.start < firstInterval.end
  )
}

function doShiftTimingsOverlap(firstShift, secondShift) {
  return intervalsOverlap(getShiftInterval(firstShift), getShiftInterval(secondShift))
}

function findOverlappingSelectedShifts(shiftIds = []) {
  const selectedShifts = shiftIds
    .map((shiftId) => shifts.find((shift) => shift.id === shiftId))
    .filter(Boolean)

  for (let index = 0; index < selectedShifts.length; index += 1) {
    for (
      let compareIndex = index + 1;
      compareIndex < selectedShifts.length;
      compareIndex += 1
    ) {
      if (
        doShiftTimingsOverlap(selectedShifts[index], selectedShifts[compareIndex])
      ) {
        return [selectedShifts[index], selectedShifts[compareIndex]]
      }
    }
  }

  return []
}

function getBlockingAllocationForShift(seatId, shift) {
  const shiftInterval = getShiftInterval(shift)

  return getSeatAllocations(seatId).find((allocation) => {
    return intervalsOverlap(shiftInterval, getAllocationInterval(allocation))
  })
}

function getSeatPhysicalStatus(seat) {
  if (seat.status === SEAT_STATUSES.MAINTENANCE) {
    return SEAT_STATUSES.MAINTENANCE
  }

  if (seat.status === SEAT_STATUSES.BLOCKED) {
    return SEAT_STATUSES.BLOCKED
  }

  return SEAT_STATUSES.AVAILABLE
}

function getSeatAllocations(seatId) {
  return seatAllocations.filter((allocation) => {
    return (
      allocation.seatId === seatId &&
      [ALLOCATION_STATUSES.ACTIVE, ALLOCATION_STATUSES.RESERVED].includes(
        allocation.status,
      )
    )
  })
}

function buildShiftAvailabilityForSeat(seat) {
  const physicalStatus = getSeatPhysicalStatus(seat)
  const activeShifts = Array.isArray(seat.activeShifts) ? seat.activeShifts : []

  return shifts
    .filter((shift) => activeShifts.includes(shift.id))
    .map((shift) => {
      const allocation = getBlockingAllocationForShift(seat.id, shift)
      let status = SEAT_STATUSES.AVAILABLE

      if (physicalStatus === SEAT_STATUSES.MAINTENANCE) {
        status = SEAT_STATUSES.MAINTENANCE
      } else if (physicalStatus === SEAT_STATUSES.BLOCKED) {
        status = SEAT_STATUSES.BLOCKED
      } else if (allocation?.status === ALLOCATION_STATUSES.RESERVED) {
        status = SEAT_STATUSES.RESERVED
      } else if (allocation?.status === ALLOCATION_STATUSES.ACTIVE) {
        status = SEAT_STATUSES.OCCUPIED
      }

      return {
        shiftId: shift.id,
        name: shift.name,
        startTime: shift.startTime,
        endTime: shift.endTime,
        status,
        assignedStudent: allocation?.student || null,
        blockingAllocation: allocation
          ? {
              id: allocation.id,
              shiftId: allocation.shiftId,
              shiftName: allocation.shiftName,
              startTime: allocation.startTime,
              endTime: allocation.endTime,
              student: allocation.student,
            }
          : null,
        isPartialBlock: Boolean(allocation && allocation.shiftId !== shift.id),
      }
    })
}

function getAggregateSeatStatus(shiftAvailability) {
  if (
    shiftAvailability.length > 0 &&
    shiftAvailability.every((shift) => shift.status === SEAT_STATUSES.MAINTENANCE)
  ) {
    return SEAT_STATUSES.MAINTENANCE
  }

  if (
    shiftAvailability.length > 0 &&
    shiftAvailability.every((shift) => shift.status === SEAT_STATUSES.BLOCKED)
  ) {
    return SEAT_STATUSES.BLOCKED
  }

  const hasAvailableShift = shiftAvailability.some((shift) => {
    return shift.status === SEAT_STATUSES.AVAILABLE
  })
  const hasUnavailableShift = shiftAvailability.some((shift) => {
    return shift.status !== SEAT_STATUSES.AVAILABLE
  })

  if (hasAvailableShift && hasUnavailableShift) {
    return SEAT_STATUSES.PARTIAL
  }

  if (hasAvailableShift) {
    return SEAT_STATUSES.AVAILABLE
  }

  if (shiftAvailability.some((shift) => shift.status === SEAT_STATUSES.OCCUPIED)) {
    return SEAT_STATUSES.OCCUPIED
  }

  if (shiftAvailability.some((shift) => shift.status === SEAT_STATUSES.RESERVED)) {
    return SEAT_STATUSES.RESERVED
  }

  return SEAT_STATUSES.AVAILABLE
}

function enrichSeat(seat) {
  const physicalStatus = getSeatPhysicalStatus(seat)
  const activeSeatAllocations = getSeatAllocations(seat.id)
  const shiftAvailability = buildShiftAvailabilityForSeat(seat)
  const occupiedShifts = shiftAvailability.filter((shift) => {
    return shift.status === SEAT_STATUSES.OCCUPIED && !shift.isPartialBlock
  })
  const blockedShifts = shiftAvailability.filter((shift) => {
    return shift.isPartialBlock
  })
  const reservedShifts = shiftAvailability.filter((shift) => {
    return shift.status === SEAT_STATUSES.RESERVED && !shift.isPartialBlock
  })
  const availableShifts = shiftAvailability.filter((shift) => {
    return shift.status === SEAT_STATUSES.AVAILABLE
  })

  return {
    ...seat,
    seatType: seat.seatType || 'Standard',
    status: getAggregateSeatStatus(shiftAvailability),
    physicalStatus,
    isOccupied: activeSeatAllocations.some((allocation) => {
      return allocation.status === ALLOCATION_STATUSES.ACTIVE
    }),
    assignedStudent: occupiedShifts[0]?.assignedStudent || null,
    assignedStudents: occupiedShifts
      .map((shift) => shift.assignedStudent)
      .filter(Boolean),
    shiftAvailability,
    occupiedShiftCount: occupiedShifts.length,
    blockedShiftCount: blockedShifts.length,
    reservedShiftCount: reservedShifts.length,
    availableShiftCount: availableShifts.length,
    availableShiftIds: availableShifts.map((shift) => shift.shiftId),
    occupiedShiftIds: occupiedShifts.map((shift) => shift.shiftId),
    blockedShiftIds: blockedShifts.map((shift) => shift.shiftId),
    reservedShiftIds: reservedShifts.map((shift) => shift.shiftId),
  }
}

function enrichSeats(sourceSeats = seats) {
  return sourceSeats.map((seat) => enrichSeat(seat))
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
    const assignedStudentNames = (seat.shiftAvailability || [])
      .map((shift) => shift.assignedStudent?.name)
      .filter(Boolean)
      .join(' ')
    const matchesSearch =
      !normalizedFilters.search ||
      seat.seatNumber.toLowerCase().includes(normalizedFilters.search) ||
      assignedStudentNames.toLowerCase().includes(normalizedFilters.search)

    const matchesStatus =
      !normalizedFilters.status ||
      seat.status === normalizedFilters.status ||
      seat.shiftAvailability?.some((shift) => {
        return shift.status === normalizedFilters.status
      })

    const matchesShift =
      !normalizedFilters.shift ||
      seat.shiftAvailability?.some((shift) => {
        return shift.shiftId === normalizedFilters.shift
      })

    const matchesFloor =
      !normalizedFilters.floor || seat.floor === normalizedFilters.floor

    return matchesSearch && matchesStatus && matchesShift && matchesFloor
  })
}

function buildSeatAvailability(sourceSeats = seats, filters = {}) {
  const filteredSeats = filterSeats(enrichSeats(sourceSeats), filters)
  const totalSeats = filteredSeats.length
  const occupiedSeats = filteredSeats.filter(
    (seat) => seat.occupiedShiftCount > 0,
  ).length
  const availableSeats = filteredSeats.filter(
    (seat) => seat.availableShiftCount > 0,
  ).length
  const maintenanceSeats = filteredSeats.filter(
    (seat) => seat.physicalStatus === SEAT_STATUSES.MAINTENANCE,
  ).length
  const reservedSeats = filteredSeats.filter(
    (seat) => seat.reservedShiftCount > 0,
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
  return shifts.reduce((availability, shift) => {
    const shiftSeats = sourceSeats.filter((seat) => {
      return seat.shiftAvailability?.some((item) => item.shiftId === shift.id)
    })
    const getShiftStatus = (seat) => {
      return seat.shiftAvailability?.find((item) => item.shiftId === shift.id)
        ?.status
    }

    availability[shift.id] = {
      shiftId: shift.id,
      name: shift.name,
      isEnabled: shift.isEnabled,
      totalSeats: shiftSeats.length,
      occupiedSeats: shiftSeats.filter(
        (seat) => {
          const shiftAvailability = seat.shiftAvailability?.find((item) => {
            return item.shiftId === shift.id
          })

          return (
            shiftAvailability?.status === SEAT_STATUSES.OCCUPIED &&
            !shiftAvailability.isPartialBlock
          )
        },
      ).length,
      blockedSeats: shiftSeats.filter((seat) => {
        const shiftAvailability = seat.shiftAvailability?.find((item) => {
          return item.shiftId === shift.id
        })

        return Boolean(shiftAvailability?.isPartialBlock)
      }).length,
      availableSeats: shiftSeats.filter(
        (seat) => getShiftStatus(seat) === SEAT_STATUSES.AVAILABLE,
      ).length,
      reservedSeats: shiftSeats.filter(
        (seat) => {
          const shiftAvailability = seat.shiftAvailability?.find((item) => {
            return item.shiftId === shift.id
          })

          return (
            shiftAvailability?.status === SEAT_STATUSES.RESERVED &&
            !shiftAvailability.isPartialBlock
          )
        },
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

function ensureSeatCanBeAllocated(
  seat,
  requestedShifts = [],
  assignedStudent = null,
  ignoredStudentSeatId = '',
) {
  if (getSeatPhysicalStatus(seat) === SEAT_STATUSES.MAINTENANCE) {
    throw createSeatError(
      'Seat is under maintenance and cannot be allocated.',
      409,
      'SEAT_UNDER_MAINTENANCE',
    )
  }

  if (requestedShifts.length === 0) {
    throw createSeatError(
      'Select at least one shift for allocation.',
      422,
      'SEAT_SHIFT_REQUIRED',
    )
  }

  const overlappingSelectedShifts = findOverlappingSelectedShifts(requestedShifts)

  if (overlappingSelectedShifts.length > 0) {
    throw createSeatError(
      `${overlappingSelectedShifts[0].name} overlaps with ${overlappingSelectedShifts[1].name}. Select non-overlapping shifts.`,
      409,
      'SELECTED_SHIFTS_OVERLAP',
    )
  }

  const unsupportedShift = requestedShifts.find((shiftId) => {
    return !seat.activeShifts?.includes(shiftId)
  })

  if (unsupportedShift) {
    throw createSeatError(
      'Selected seat does not support one or more selected shifts.',
      422,
      'SEAT_SHIFT_UNSUPPORTED',
    )
  }

  const conflictingShift = requestedShifts.find((shiftId) => {
    const shift = getShiftById(shiftId).shift

    return Boolean(getBlockingAllocationForShift(seat.id, shift))
  })

  if (conflictingShift) {
    const shift = getShiftById(conflictingShift).shift
    const allocation = getBlockingAllocationForShift(seat.id, shift)
    const studentName = allocation?.student?.name || 'another student'

    throw createSeatError(
      `${seat.seatNumber} is already allocated to ${studentName} from ${allocation.startTime} to ${allocation.endTime}.`,
      409,
      'SEAT_SHIFT_ALREADY_OCCUPIED',
    )
  }

  if (assignedStudent) {
    const studentConflict = requestedShifts.find((shiftId) => {
      const requestedShift = getShiftById(shiftId).shift
      const requestedInterval = getShiftInterval(requestedShift)

      return seatAllocations.some((allocation) => {
        return (
          allocation.student?.id === assignedStudent.id &&
          allocation.seatId !== ignoredStudentSeatId &&
          intervalsOverlap(requestedInterval, getAllocationInterval(allocation)) &&
          allocation.status === ALLOCATION_STATUSES.ACTIVE
        )
      })
    })

    if (studentConflict) {
      const shift = getShiftById(studentConflict).shift

      throw createSeatError(
        `${assignedStudent.name} already has a seat during ${shift.name}.`,
        409,
        'STUDENT_SHIFT_ALREADY_ALLOCATED',
      )
    }
  }
}

function ensureSeatCanChangeStatus(seat, nextStatus) {
  const allowedOperationalStatuses = [
    SEAT_STATUSES.AVAILABLE,
    SEAT_STATUSES.MAINTENANCE,
    SEAT_STATUSES.BLOCKED,
  ]

  if (!allowedOperationalStatuses.includes(nextStatus)) {
    throw createSeatError(
      'Only available and maintenance statuses can be changed from this workflow.',
      422,
      'SEAT_STATUS_INVALID',
    )
  }

  if (getSeatPhysicalStatus(seat) === nextStatus) {
    throw createSeatError(
      `Seat is already marked as ${nextStatus}.`,
      409,
      'SEAT_STATUS_UNCHANGED',
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
  const allowedShifts = getShiftIds()

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

function generateSeatId() {
  const numericIds = seats
    .map((seat) => Number.parseInt(String(seat.id).replace('seat-', ''), 10))
    .filter(Number.isFinite)
  const nextId = Math.max(0, ...numericIds) + 1

  return `seat-${String(nextId).padStart(3, '0')}`
}

function getValidPhysicalStatus(status = SEAT_STATUSES.AVAILABLE) {
  const normalizedStatus = String(status || SEAT_STATUSES.AVAILABLE)
    .trim()
    .toLowerCase()
  const allowedStatuses = [
    SEAT_STATUSES.AVAILABLE,
    SEAT_STATUSES.MAINTENANCE,
    SEAT_STATUSES.BLOCKED,
  ]

  if (!allowedStatuses.includes(normalizedStatus)) {
    throw createSeatError(
      'Seat status must be available, maintenance, or blocked.',
      422,
      'SEAT_STATUS_INVALID',
    )
  }

  return normalizedStatus
}

function ensureSeatNumberIsUnique(seatNumber, ignoredSeatId = '') {
  const normalizedSeatNumber = String(seatNumber || '').trim().toLowerCase()
  const duplicateSeat = seats.find((seat) => {
    return (
      seat.id !== ignoredSeatId &&
      seat.seatNumber.toLowerCase() === normalizedSeatNumber
    )
  })

  if (duplicateSeat) {
    throw createSeatError(
      'Seat number already exists.',
      409,
      'SEAT_NUMBER_DUPLICATE',
    )
  }
}

function normalizeSeatPayload(payload = {}, existingSeat = null) {
  const seatNumber = String(payload.seatNumber ?? existingSeat?.seatNumber ?? '')
    .trim()
  const floorValue = payload.floor ?? existingSeat?.floor ?? ''
  const floor = Number(floorValue)
  const seatType = String(payload.seatType ?? existingSeat?.seatType ?? 'Standard')
    .trim()
  const notes = String(payload.notes ?? existingSeat?.notes ?? '').trim()
  const status = getValidPhysicalStatus(
    payload.status ?? existingSeat?.physicalStatus ?? existingSeat?.status,
  )

  if (!seatNumber) {
    throw createSeatError(
      'Seat number is required.',
      422,
      'SEAT_NUMBER_REQUIRED',
    )
  }

  if (!Number.isFinite(floor) || floor < 1) {
    throw createSeatError(
      'Floor must be a positive number.',
      422,
      'SEAT_FLOOR_INVALID',
    )
  }

  if (!seatType) {
    throw createSeatError(
      'Seat type is required.',
      422,
      'SEAT_TYPE_REQUIRED',
    )
  }

  return {
    seatNumber,
    floor,
    seatType,
    status,
    notes,
  }
}

function buildOperationData(extraData = {}) {
  return {
    ...extraData,
    shifts: enrichShifts(),
    availability: buildSeatAvailability(seats),
  }
}

function getShiftIds() {
  return shifts.map((shift) => shift.id)
}

function buildStatusChangeNotes(seat, statusPayload) {
  const reason = String(statusPayload.reason || '').trim()

  if (reason) {
    return reason
  }

  if (statusPayload.status === SEAT_STATUSES.AVAILABLE) {
    return 'Maintenance completed. Seat is ready for allocation.'
  }

  if (statusPayload.status === SEAT_STATUSES.MAINTENANCE) {
    return 'Seat marked under maintenance by admin.'
  }

  if (statusPayload.status === SEAT_STATUSES.BLOCKED) {
    return 'Seat blocked by admin.'
  }

  return seat.notes
}

function formatStatusForMessage(status) {
  return String(status || '').replace(/[-_]/g, ' ')
}

function generateAllocationId(seatId, shiftId, studentId) {
  const sequence = seatAllocations.length + 1

  return `${seatId}-${shiftId}-${studentId}-${sequence}`
}

function getShiftSeatCounts(shiftId, sourceSeats = seats) {
  const shiftSeats = enrichSeats(sourceSeats).filter((seat) => {
    return seat.shiftAvailability?.some((shift) => shift.shiftId === shiftId)
  })
  const getShiftStatus = (seat) => {
    return seat.shiftAvailability?.find((shift) => shift.shiftId === shiftId)?.status
  }

  return {
    totalSeatCount: shiftSeats.length,
    occupiedSeatCount: shiftSeats.filter((seat) => {
      return getShiftStatus(seat) === SEAT_STATUSES.OCCUPIED
    }).length,
    availableSeatCount: shiftSeats.filter((seat) => {
      return getShiftStatus(seat) === SEAT_STATUSES.AVAILABLE
    }).length,
    reservedSeatCount: shiftSeats.filter((seat) => {
      return getShiftStatus(seat) === SEAT_STATUSES.RESERVED
    }).length,
  }
}

function enrichShift(shift, sourceSeats = seats) {
  return {
    ...shift,
    ...getShiftSeatCounts(shift.id, sourceSeats),
  }
}

function enrichShifts(sourceShifts = shifts, sourceSeats = seats) {
  return sourceShifts.map((shift) => enrichShift(shift, sourceSeats))
}

function getShiftById(shiftId) {
  const shiftIndex = shifts.findIndex((shift) => shift.id === String(shiftId))

  if (shiftIndex === -1) {
    throw createSeatError('Shift not found.', 404, 'SHIFT_NOT_FOUND')
  }

  return { shiftIndex, shift: shifts[shiftIndex] }
}

function slugifyShiftName(name) {
  return String(name || '')
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

function generateShiftId(name) {
  const baseId = slugifyShiftName(name) || 'shift'
  let shiftId = baseId
  let suffix = 2

  while (shifts.some((shift) => shift.id === shiftId)) {
    shiftId = `${baseId}-${suffix}`
    suffix += 1
  }

  return shiftId
}

function normalizeShiftPayload(payload = {}, existingShift = {}) {
  const name = String(payload.name ?? existingShift.name ?? '').trim()
  const startTime = String(
    payload.startTime ?? payload.timing?.startTime ?? existingShift.startTime ?? '',
  ).trim()
  const endTime = String(
    payload.endTime ?? payload.timing?.endTime ?? existingShift.endTime ?? '',
  ).trim()
  const isEnabled =
    typeof payload.isEnabled === 'boolean'
      ? payload.isEnabled
      : existingShift.isEnabled !== false

  if (!name) {
    throw createSeatError('Shift name is required.', 422, 'SHIFT_NAME_REQUIRED')
  }

  if (!startTime || !endTime) {
    throw createSeatError(
      'Shift start and end time are required.',
      422,
      'SHIFT_TIMING_REQUIRED',
    )
  }

  if (startTime === endTime) {
    throw createSeatError(
      'Shift start and end time must be different.',
      422,
      'SHIFT_TIMING_INVALID',
    )
  }

  return {
    name,
    startTime,
    endTime,
    isEnabled,
  }
}

function removeShiftFromSeats(shiftId) {
  seats = seats.map((seat) => {
    if (!Array.isArray(seat.activeShifts) || !seat.activeShifts.includes(shiftId)) {
      return seat
    }

    return {
      ...seat,
      activeShifts: seat.activeShifts.filter((shift) => shift !== shiftId),
    }
  })
}

// TODO: Replace with GET /api/seats when FastAPI endpoints are ready.
export async function fetchSeats(filters = {}) {
  await delay()

  const enrichedSeats = enrichSeats()
  const filteredSeats = filterSeats(enrichedSeats, filters)

  return createSuccessResponse(
    'Seats fetched successfully.',
    {
      seats: filteredSeats,
      shifts: enrichShifts(),
      availability: buildSeatAvailability(seats, filters),
    },
    {
      count: filteredSeats.length,
      filters: normalizeFilters(filters),
    },
  )
}

// TODO: Replace with POST /api/seats when FastAPI endpoints are ready.
export async function createSeat(seatPayload = {}) {
  await delay()

  const normalizedSeat = normalizeSeatPayload(seatPayload)

  ensureSeatNumberIsUnique(normalizedSeat.seatNumber)

  const now = new Date().toISOString()
  const seat = {
    id: generateSeatId(),
    ...normalizedSeat,
    assignedStudent: null,
    activeShifts: getShiftIds(),
    createdAt: now,
    updatedAt: now,
  }

  seats.push(seat)

  return createSuccessResponse(
    'Seat created successfully.',
    buildOperationData({
      seat: enrichSeat(seat),
      seats: enrichSeats(),
    }),
  )
}

// TODO: Replace with PATCH /api/seats/{seatId} when FastAPI endpoints are ready.
export async function updateSeat(seatId, seatPayload = {}) {
  await delay()

  const { seatIndex, seat } = getSeatByIdentifier(seatId)
  const normalizedSeat = normalizeSeatPayload(seatPayload, seat)

  ensureSeatNumberIsUnique(normalizedSeat.seatNumber, seat.id)

  const updatedSeat = {
    ...seat,
    ...normalizedSeat,
    id: seat.id,
    assignedStudent: seat.assignedStudent || null,
    activeShifts: seat.activeShifts?.length ? clone(seat.activeShifts) : getShiftIds(),
    createdAt: seat.createdAt,
    updatedAt: new Date().toISOString(),
  }

  seats[seatIndex] = updatedSeat

  return createSuccessResponse(
    'Seat updated successfully.',
    buildOperationData({
      seat: enrichSeat(updatedSeat),
      seats: enrichSeats(),
    }),
  )
}

// TODO: Replace with DELETE /api/seats/{seatId} when FastAPI endpoints are ready.
export async function deleteSeat(seatId) {
  await delay()

  const { seatIndex, seat } = getSeatByIdentifier(seatId)

  seats.splice(seatIndex, 1)
  seatAllocations = seatAllocations.filter((allocation) => {
    return allocation.seatId !== seat.id
  })

  return createSuccessResponse(
    'Seat deleted successfully.',
    buildOperationData({
      deletedSeat: enrichSeat(seat),
      deletedSeatIds: [seat.id],
      seats: enrichSeats(),
    }),
  )
}

// TODO: Replace with PATCH /api/seats/bulk-status when FastAPI endpoints are ready.
export async function bulkUpdateSeatStatus(seatIds = [], statusPayload = {}) {
  await delay()

  const targetSeatIds = new Set(seatIds.map((seatId) => String(seatId)))
  const nextStatus = getValidPhysicalStatus(statusPayload.status)
  const now = new Date().toISOString()
  let updatedCount = 0

  seats = seats.map((seat) => {
    if (!targetSeatIds.has(seat.id)) return seat

    updatedCount += 1

    return {
      ...seat,
      status: nextStatus,
      notes: buildStatusChangeNotes(seat, { ...statusPayload, status: nextStatus }),
      updatedAt: now,
    }
  })

  if (updatedCount === 0) {
    throw createSeatError('No matching seats were found.', 404, 'SEATS_NOT_FOUND')
  }

  return createSuccessResponse(
    'Seat statuses updated successfully.',
    buildOperationData({
      seats: enrichSeats(),
      updatedSeatIds: [...targetSeatIds],
      status: nextStatus,
    }),
  )
}

// TODO: Replace with DELETE /api/seats/bulk when FastAPI endpoints are ready.
export async function bulkDeleteSeats(seatIds = []) {
  await delay()

  const targetSeatIds = new Set(seatIds.map((seatId) => String(seatId)))
  const deletedSeats = seats.filter((seat) => targetSeatIds.has(seat.id))

  if (deletedSeats.length === 0) {
    throw createSeatError('No matching seats were found.', 404, 'SEATS_NOT_FOUND')
  }

  seats = seats.filter((seat) => !targetSeatIds.has(seat.id))
  seatAllocations = seatAllocations.filter((allocation) => {
    return !targetSeatIds.has(allocation.seatId)
  })

  return createSuccessResponse(
    'Seats deleted successfully.',
    buildOperationData({
      deletedSeats: deletedSeats.map((seat) => enrichSeat(seat)),
      deletedSeatIds: deletedSeats.map((seat) => seat.id),
      seats: enrichSeats(),
    }),
  )
}

// TODO: Replace with GET /api/shifts when FastAPI endpoints are ready.
export async function fetchShifts() {
  await delay()

  return createSuccessResponse(
    'Shifts fetched successfully.',
    buildOperationData({ shifts: enrichShifts() }),
    { count: shifts.length },
  )
}

// TODO: Replace with POST /api/shifts when FastAPI endpoints are ready.
export async function createShift(shiftPayload = {}) {
  await delay()

  const now = new Date().toISOString()
  const normalizedShift = normalizeShiftPayload(shiftPayload)
  const shift = {
    id: generateShiftId(normalizedShift.name),
    ...normalizedShift,
    isDefault: false,
    createdAt: now,
    updatedAt: now,
  }

  shifts.push(shift)
  seats = seats.map((seat) => ({
    ...seat,
    activeShifts: [...new Set([...(seat.activeShifts || []), shift.id])],
  }))

  return createSuccessResponse(
    'Shift created successfully.',
    buildOperationData({
      shift: enrichShift(shift),
      shifts: enrichShifts(),
    }),
  )
}

// TODO: Replace with PATCH /api/shifts/{shiftId} when FastAPI endpoints are ready.
export async function updateStudyShift(shiftId, shiftPayload = {}) {
  await delay()

  const { shiftIndex, shift } = getShiftById(shiftId)
  const normalizedShift = normalizeShiftPayload(shiftPayload, shift)
  const updatedShift = {
    ...shift,
    ...normalizedShift,
    id: shift.id,
    isDefault: shift.isDefault,
    createdAt: shift.createdAt,
    updatedAt: new Date().toISOString(),
  }

  shifts[shiftIndex] = updatedShift

  return createSuccessResponse(
    'Shift updated successfully.',
    buildOperationData({
      shift: enrichShift(updatedShift),
      shifts: enrichShifts(),
    }),
  )
}

// TODO: Replace with PATCH /api/shifts/{shiftId}/timing when FastAPI endpoints are ready.
export async function updateShiftTiming(shiftId, timingPayload = {}) {
  return updateStudyShift(shiftId, {
    startTime: timingPayload.startTime,
    endTime: timingPayload.endTime,
  })
}

// TODO: Replace with PATCH /api/shifts/{shiftId}/status when FastAPI endpoints are ready.
export async function toggleStudyShift(shiftId, isEnabled) {
  await delay()

  const { shiftIndex, shift } = getShiftById(shiftId)
  const updatedShift = {
    ...shift,
    isEnabled: Boolean(isEnabled),
    updatedAt: new Date().toISOString(),
  }

  shifts[shiftIndex] = updatedShift

  return createSuccessResponse(
    `Shift ${updatedShift.isEnabled ? 'enabled' : 'disabled'} successfully.`,
    buildOperationData({
      shift: enrichShift(updatedShift),
      shifts: enrichShifts(),
    }),
  )
}

// TODO: Replace with DELETE /api/shifts/{shiftId} when FastAPI endpoints are ready.
export async function deleteStudyShift(shiftId) {
  await delay()

  const { shiftIndex, shift } = getShiftById(shiftId)

  shifts.splice(shiftIndex, 1)
  removeShiftFromSeats(shift.id)
  seatAllocations = seatAllocations.filter((allocation) => {
    return allocation.shiftId !== shift.id
  })

  return createSuccessResponse(
    'Shift deleted successfully.',
    buildOperationData({
      shift,
      shifts: enrichShifts(),
      seats: enrichSeats(),
    }),
  )
}

// TODO: Replace with GET /api/seats/{seatId} when FastAPI endpoints are ready.
export async function getSeatById(seatId) {
  await delay()

  const { seat } = getSeatByIdentifier(seatId)

  return createSuccessResponse('Seat fetched successfully.', {
    seat: enrichSeat(seat),
  })
}

// TODO: Replace with PATCH /api/seats/{seatId}/status when FastAPI endpoints are ready.
export async function updateSeatStatus(seatId, statusPayload = {}) {
  await delay()

  const nextStatus = String(statusPayload.status || '').trim().toLowerCase()
  const { seatIndex, seat } = getSeatByIdentifier(seatId)

  ensureSeatCanChangeStatus(seat, nextStatus)

  const updatedSeat = {
    ...seat,
    status: nextStatus,
    activeShifts: seat.activeShifts?.length ? clone(seat.activeShifts) : getShiftIds(),
    notes: buildStatusChangeNotes(seat, { ...statusPayload, status: nextStatus }),
    updatedAt: new Date().toISOString(),
  }

  seats[seatIndex] = updatedSeat

  return createSuccessResponse(
    `Seat marked as ${formatStatusForMessage(nextStatus)} successfully.`,
    buildOperationData({ seat: enrichSeat(updatedSeat) }),
  )
}

// TODO: Replace with POST /api/seats/{seatId}/allocate when FastAPI endpoints are ready.
export async function allocateSeat(allocationPayload = {}) {
  await delay()

  const { seat } = getSeatByIdentifier(
    getPayloadSeatId(allocationPayload),
  )

  const assignedStudent = normalizeAssignedStudent(
    getPayloadStudent(allocationPayload),
  )
  const activeShifts =
    normalizeActiveShifts(
      allocationPayload.activeShifts || allocationPayload.shift,
    ) || []

  ensureSeatCanBeAllocated(seat, activeShifts, assignedStudent)

  const now = new Date().toISOString()
  const newAllocations = activeShifts.map((shiftId) => {
    const shift = getShiftById(shiftId).shift

    return {
      id: generateAllocationId(seat.id, shiftId, assignedStudent.id),
      seatId: seat.id,
      seatNumber: seat.seatNumber,
      shiftId,
      shiftName: shift.name,
      startTime: shift.startTime,
      endTime: shift.endTime,
      student: assignedStudent,
      status: ALLOCATION_STATUSES.ACTIVE,
      notes: allocationPayload.notes || '',
      createdAt: now,
      updatedAt: now,
    }
  })

  seatAllocations.push(...newAllocations)

  const updatedSeat = enrichSeat(seat)

  return createSuccessResponse(
    'Seat allocated successfully.',
    buildOperationData({
      seat: updatedSeat,
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
      seat: enrichSeat(updatedSeat),
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

  const { seat } = getSeatByIdentifier(seatId)
  seatAllocations = seatAllocations.filter((allocation) => {
    return allocation.seatId !== seat.id
  })
  const updatedSeat = enrichSeat(seat)

  return createSuccessResponse(
    'Seat released successfully.',
    buildOperationData({ seat: updatedSeat }),
  )
}
