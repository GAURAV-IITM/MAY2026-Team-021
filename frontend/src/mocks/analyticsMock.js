// src/mocks: Report configuration used until FastAPI analytics APIs are available.

export const ANALYTICS_NETWORK_DELAY_MS = 350

export const REPORT_DEFAULT_MONTH_COUNT = 3

export const REPORT_TABS = Object.freeze([
  { id: 'overview', label: 'Overview' },
  { id: 'revenue', label: 'Revenue' },
  { id: 'occupancy', label: 'Seat Occupancy' },
  { id: 'students', label: 'Students' },
  { id: 'pending', label: 'Pending Payments' },
])

export const REPORT_STATUS_LABELS = Object.freeze({
  available: 'Available',
  occupied: 'Allotted',
  blocked: 'Blocked',
  reserved: 'Reserved',
  maintenance: 'Maintenance',
})

export const REPORT_BENCHMARKS = Object.freeze({
  healthyCollectionRate: 85,
  healthyOccupancyRate: 70,
  highOccupancyRate: 90,
})

