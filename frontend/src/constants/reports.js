export const REPORT_TABS = Object.freeze([
  { id: 'overview', label: 'Overview' },
  { id: 'revenue', label: 'Revenue' },
  { id: 'occupancy', label: 'Seat Occupancy' },
  { id: 'students', label: 'Students' },
  { id: 'pending', label: 'Pending Fees' },
])

export const REPORT_STATUS_LABELS = Object.freeze({
  paid: 'Paid',
  pending: 'Pending',
  overdue: 'Overdue',
  not_recorded: 'No fee record',
  active: 'Active',
  inactive: 'Inactive',
  left: 'Left',
  suspended: 'Suspended',
})

export const REPORT_DEFAULT_MONTH_COUNT = 3
