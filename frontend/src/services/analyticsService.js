import apiClient from '../api/axios.js'
import { REPORT_STATUS_LABELS } from '../constants/reports.js'

const REPORT_TYPES = new Set([
  'overview',
  'revenue',
  'occupancy',
  'students',
  'pending',
])

export function buildReportParams(filters = {}) {
  return {
    startMonth: filters.startMonth || undefined,
    endMonth: filters.endMonth || undefined,
    floorId: filters.floorId || undefined,
    shiftId: filters.shiftId || undefined,
  }
}

export async function getReportOptions() {
  const response = await apiClient.get('/reports/options')
  return response.data
}

export async function getReports(filters = {}) {
  const response = await apiClient.get('/reports', {
    params: buildReportParams(filters),
  })
  return response.data
}

function csvCell(value) {
  if (value === null || value === undefined) return ''

  const text = String(value)
  return /[",\r\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text
}

function csvRows(rows) {
  return rows.map((row) => row.map(csvCell).join(',')).join('\r\n')
}

function filterRows(filters = {}) {
  return [
    ['Applied filters'],
    ['Start month', filters.startMonth],
    ['End month', filters.endMonth],
    ['Floor', filters.floorId || 'All floors'],
    ['Shift', filters.shiftId || 'All shifts'],
    ['Report date', filters.reportDate],
    [],
  ]
}

function overviewRows(reports) {
  return [
    ['Metric', 'Value'],
    ['Collected revenue', reports.metrics.collectedRevenue],
    ['Pending revenue', reports.metrics.pendingRevenue],
    ['Collection rate', reports.metrics.collectionRate],
    ['Active students', reports.metrics.activeStudents],
    ['Total students', reports.metrics.totalStudents],
    ['Occupied seats', reports.metrics.occupiedSeats],
    ['Total seats', reports.metrics.totalSeats],
    ['Occupancy rate', reports.metrics.occupancyRate],
  ]
}

function revenueRows(reports) {
  return [
    ['Month', 'Expected', 'Collected', 'Pending', 'Collection rate', 'Payments'],
    ...reports.revenue.series.map((item) => [
      item.month,
      item.expected,
      item.collected,
      item.pending,
      item.collectionRate,
      item.paymentCount,
    ]),
  ]
}

function occupancyRows(reports) {
  return [
    [
      'Shift',
      'Timing',
      'Total seats',
      'Available',
      'Allotted',
      'Blocked',
      'Reserved',
      'Maintenance',
      'Occupancy rate',
    ],
    ...reports.occupancy.byShift.map((item) => [
      item.name,
      item.timing,
      item.totalSeats,
      item.available,
      item.occupied,
      item.blocked,
      item.reserved,
      item.maintenance,
      item.occupancyRate,
    ]),
  ]
}

function studentRows(reports) {
  return [
    ['Month', 'Joined students', 'Active students at month end'],
    ...reports.students.joiningTrend.map((item) => [
      item.month,
      item.joined,
      item.activeStudentsAtEnd,
    ]),
    [],
    ['Status', 'Count'],
    ...reports.students.statusDistribution.map((item) => [
      REPORT_STATUS_LABELS[item.status] || item.label,
      item.count,
    ]),
  ]
}

function pendingRows(reports) {
  return [
    [
      'Student',
      'Enrollment number',
      'Phone',
      'Seat',
      'Fee month',
      'Total',
      'Paid',
      'Outstanding',
      'Due date',
      'Ageing',
    ],
    ...reports.pendingPayments.records.map((item) => [
      item.studentName,
      item.enrollmentNumber,
      item.phone,
      item.seatNumber,
      item.month,
      item.totalAmount,
      item.paidAmount,
      item.amount,
      item.dueDate,
      item.ageing,
    ]),
  ]
}

function reportRows(reportType, reports) {
  if (reportType === 'revenue') return revenueRows(reports)
  if (reportType === 'occupancy') return occupancyRows(reports)
  if (reportType === 'students') return studentRows(reports)
  if (reportType === 'pending') return pendingRows(reports)
  return overviewRows(reports)
}

function filenamePart(value, fallback) {
  return String(value || fallback)
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '')
}

export async function exportReport(reportType, reports) {
  if (!REPORT_TYPES.has(reportType)) {
    throw new Error('Select a valid report to export.')
  }
  if (!reports) {
    throw new Error('Load a report before exporting it.')
  }

  const filters = reports.filters || {}
  const content = csvRows([
    [`${reportType === 'pending' ? 'Pending fees' : reportType} report`],
    ['Generated at', reports.generatedAt],
    [],
    ...filterRows(filters),
    ...reportRows(reportType, reports),
  ])
  const suffix = [
    filenamePart(filters.startMonth, 'start'),
    'to',
    filenamePart(filters.endMonth, 'end'),
  ].join('-')

  return {
    success: true,
    message: 'Report export prepared.',
    data: {
      content,
      fileName: `${filenamePart(reportType, 'report')}-report-${suffix}.csv`,
      mimeType: 'text/csv;charset=utf-8',
    },
  }
}
