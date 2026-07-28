// Legacy report test configuration. Production reports use the backend API.

export const ANALYTICS_NETWORK_DELAY_MS = 350

export const REPORT_BENCHMARKS = Object.freeze({
  healthyCollectionRate: 85,
  healthyOccupancyRate: 70,
  highOccupancyRate: 90,
})
