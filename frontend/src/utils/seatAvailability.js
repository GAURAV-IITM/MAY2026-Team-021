export const SHIFT_SEAT_STATUSES = Object.freeze({
  AVAILABLE: 'available',
  OCCUPIED: 'occupied',
  BLOCKED: 'blocked',
  RESERVED: 'reserved',
  MAINTENANCE: 'maintenance',
})

export function getSeatShiftAvailability(seat, shiftId) {
  return seat?.shiftAvailability?.find((shift) => shift.shiftId === shiftId) || null
}

export function getSeatStatusForShift(seat, shiftId) {
  const shiftAvailability = getSeatShiftAvailability(seat, shiftId)

  if (!shiftAvailability) {
    return SHIFT_SEAT_STATUSES.MAINTENANCE
  }

  if (shiftAvailability.isPartialBlock) {
    return SHIFT_SEAT_STATUSES.BLOCKED
  }

  if (Object.values(SHIFT_SEAT_STATUSES).includes(shiftAvailability.status)) {
    return shiftAvailability.status
  }

  return SHIFT_SEAT_STATUSES.AVAILABLE
}

export function summarizeSeatStatusesForShift(seats = [], shiftId = '') {
  const statusCounts = {
    available: 0,
    occupied: 0,
    blocked: 0,
    reserved: 0,
    maintenance: 0,
  }

  seats.forEach((seat) => {
    const status = getSeatStatusForShift(seat, shiftId)

    statusCounts[status] += 1
  })

  return {
    totalSeats: seats.length,
    availableSeats: statusCounts.available,
    occupiedSeats: statusCounts.occupied,
    blockedSeats: statusCounts.blocked,
    reservedSeats: statusCounts.reserved,
    maintenanceSeats: statusCounts.maintenance,
  }
}
