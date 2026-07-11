import {
  DASHBOARD_NETWORK_DELAY_MS,
  dashboardMock,
} from '../mocks/dashboardMock.js'
import * as seatService from './seatService'

function delay(ms = DASHBOARD_NETWORK_DELAY_MS) {
  return new Promise((resolve) => {
    globalThis.setTimeout(resolve, ms)
  })
}

function clone(value) {
  return structuredClone(value)
}

function createSuccessResponse(message, data) {
  return {
    success: true,
    message,
    data: clone(data),
    meta: {
      source: 'mock-dashboard-service',
      timestamp: new Date().toISOString(),
    },
  }
}

function buildShiftAvailabilitySummary(seatAvailability = {}) {
  return Object.values(seatAvailability.byShift || {})
    .filter((shift) => shift.isEnabled !== false)
    .map((shift) => ({
      id: shift.shiftId,
      name: shift.name,
      timing: `${shift.startTime} - ${shift.endTime}`,
      totalSeats: shift.totalSeats,
      statuses: [
        {
          key: 'available',
          label: 'Available',
          count: shift.availableSeats,
        },
        {
          key: 'occupied',
          label: 'Allotted',
          count: shift.occupiedSeats,
        },
        {
          key: 'blocked',
          label: 'Blocked',
          count: shift.blockedSeats,
        },
        {
          key: 'reserved',
          label: 'Reserved',
          count: shift.reservedSeats,
        },
        {
          key: 'maintenance',
          label: 'Maintenance',
          count: shift.maintenanceSeats,
        },
      ],
    }))
}

export async function getDashboardSummary() {
  const [, seatAvailabilityResponse] = await Promise.all([
    delay(),
    seatService.fetchSeatAvailability(),
  ])
  const seatAvailability = seatAvailabilityResponse.data.availability

  return createSuccessResponse('Dashboard summary fetched successfully.', {
    ...dashboardMock,
    shiftAvailability: buildShiftAvailabilitySummary(seatAvailability),
    lastUpdated: new Date().toISOString(),
  })
}

export async function getDashboardMetrics() {
  await delay()

  return createSuccessResponse(
    'Dashboard metrics fetched successfully.',
    dashboardMock.metrics,
  )
}
