import {
  ANALYTICS_NETWORK_DELAY_MS,
  REPORT_BENCHMARKS,
  REPORT_DEFAULT_MONTH_COUNT,
  REPORT_STATUS_LABELS,
} from '../mocks/analyticsMock.js'
import { getSeatStatusForShift } from '../utils/seatAvailability.js'
import * as paymentService from './paymentService.js'
import * as seatService from './seatService.js'
import * as studentService from './studentService.js'

// TODO: Replace these aggregations with library-scoped FastAPI report endpoints.

const REPORT_TYPES = new Set([
  'overview',
  'revenue',
  'occupancy',
  'students',
  'pending',
])

function delay(ms = ANALYTICS_NETWORK_DELAY_MS) {
  return new Promise((resolve) => globalThis.setTimeout(resolve, ms))
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
      source: 'mock-analytics-service',
      timestamp: new Date().toISOString(),
      ...meta,
    },
  }
}

function createAnalyticsError(message, status = 400, code = 'ANALYTICS_ERROR') {
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

function getMonthRange(startMonth, endMonth) {
  const [startYear, startMonthNumber] = startMonth.split('-').map(Number)
  const [endYear, endMonthNumber] = endMonth.split('-').map(Number)
  const months = []
  const cursor = new Date(startYear, startMonthNumber - 1, 1)
  const end = new Date(endYear, endMonthNumber - 1, 1)

  while (cursor <= end) {
    months.push(
      `${cursor.getFullYear()}-${String(cursor.getMonth() + 1).padStart(2, '0')}`,
    )
    cursor.setMonth(cursor.getMonth() + 1)
  }

  return months
}

function formatMonthLabel(month) {
  const [year, monthNumber] = month.split('-').map(Number)

  return new Intl.DateTimeFormat('en-IN', {
    month: 'short',
    year: 'numeric',
  }).format(new Date(year, monthNumber - 1, 1))
}

function getMonthEnd(month) {
  const [year, monthNumber] = month.split('-').map(Number)
  return new Date(year, monthNumber, 0)
}

function formatDateKey(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

function percentage(part, total) {
  return total > 0 ? Math.round((part / total) * 100) : 0
}

function percentageChange(current, previous) {
  if (!previous) return current > 0 ? 100 : 0
  return Math.round(((current - previous) / previous) * 100)
}

function sum(items, selector) {
  return items.reduce((total, item) => total + Number(selector(item) || 0), 0)
}

function normalizeFilters(filters, availableMonths) {
  const latestMonth = availableMonths.at(-1)
  const defaultStartIndex = Math.max(
    0,
    availableMonths.length - REPORT_DEFAULT_MONTH_COUNT,
  )
  const startMonth = String(
    filters.startMonth || availableMonths[defaultStartIndex] || latestMonth,
  )
  const endMonth = String(filters.endMonth || latestMonth)

  if (!availableMonths.includes(startMonth) || !availableMonths.includes(endMonth)) {
    throw createAnalyticsError(
      'Select a month available in the report data.',
      422,
      'REPORT_MONTH_INVALID',
    )
  }

  if (startMonth > endMonth) {
    throw createAnalyticsError(
      'The start month cannot be after the end month.',
      422,
      'REPORT_RANGE_INVALID',
    )
  }

  return {
    startMonth,
    endMonth,
    floor: filters.floor ? Number(filters.floor) : '',
    shiftId: String(filters.shiftId || ''),
  }
}

function getStudentScope(students, seats, filters) {
  const seatByNumber = new Map(seats.map((seat) => [seat.seatNumber, seat]))

  return students.filter((student) => {
    const seat = seatByNumber.get(student.seatNumber)
    const matchesFloor = !filters.floor || seat?.floor === filters.floor
    const matchesShift =
      !filters.shiftId || student.activeShifts?.includes(filters.shiftId)

    return matchesFloor && matchesShift
  })
}

function buildRevenueReport(payments, months) {
  const series = months.map((month) => {
    const records = payments.filter((payment) => payment.month === month)
    const collected = sum(records, (payment) => payment.paidAmount)
    const expected = sum(records, (payment) => payment.totalAmount)

    return {
      month,
      label: formatMonthLabel(month),
      expected,
      collected,
      pending: expected - collected,
      collectionRate: percentage(collected, expected),
      paymentCount: records.length,
    }
  })
  const expected = sum(series, (item) => item.expected)
  const collected = sum(series, (item) => item.collected)
  const paymentsWithTransactions = payments.filter(
    (payment) => payment.latestTransaction,
  )
  const methodCounts = paymentsWithTransactions.reduce((counts, payment) => {
    const method = payment.paymentMethod || 'not_recorded'
    counts[method] = (counts[method] || 0) + 1
    return counts
  }, {})
  const latest = series.at(-1)?.collected || 0
  const previous = series.at(-2)?.collected || 0

  return {
    totals: {
      expected,
      collected,
      pending: expected - collected,
      collectionRate: percentage(collected, expected),
      paymentCount: payments.length,
      revenueChange: percentageChange(latest, previous),
    },
    series,
    paymentMethods: Object.entries(methodCounts).map(([method, count]) => ({
      method,
      label: method
        .split('_')
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' '),
      count,
      share: percentage(count, paymentsWithTransactions.length),
    })),
  }
}

function countShiftStatuses(seats, shift) {
  const counts = {
    available: 0,
    occupied: 0,
    blocked: 0,
    reserved: 0,
    maintenance: 0,
  }

  seats.forEach((seat) => {
    const status = getSeatStatusForShift(seat, shift.id)
    counts[status] += 1
  })

  return {
    shiftId: shift.id,
    name: shift.name,
    timing: `${shift.startTime} - ${shift.endTime}`,
    totalSeats: seats.length,
    ...counts,
    occupancyRate: percentage(counts.occupied, seats.length),
  }
}

function buildOccupancyReport(seats, shifts, filters) {
  const floorSeats = filters.floor
    ? seats.filter((seat) => seat.floor === filters.floor)
    : seats
  const enabledShifts = shifts.filter((shift) => {
    return shift.isEnabled !== false && (!filters.shiftId || shift.id === filters.shiftId)
  })
  const byShift = enabledShifts.map((shift) => countShiftStatuses(floorSeats, shift))
  const selectedShift = enabledShifts[0]
  const floors = [...new Set(floorSeats.map((seat) => seat.floor))]
    .sort((first, second) => first - second)
    .map((floor) => {
      const records = floorSeats.filter((seat) => seat.floor === floor)
      const occupied = selectedShift
        ? records.filter(
            (seat) => getSeatStatusForShift(seat, selectedShift.id) === 'occupied',
          ).length
        : records.filter((seat) => seat.isOccupied).length

      return {
        floor,
        label: `Floor ${floor}`,
        totalSeats: records.length,
        occupied,
        available: records.length - occupied,
        occupancyRate: percentage(occupied, records.length),
      }
    })
  const occupiedSeatIds = new Set()

  byShift.forEach((shift) => {
    floorSeats.forEach((seat) => {
      if (getSeatStatusForShift(seat, shift.shiftId) === 'occupied') {
        occupiedSeatIds.add(seat.id)
      }
    })
  })

  return {
    totals: {
      totalSeats: floorSeats.length,
      occupiedSeats: occupiedSeatIds.size,
      availableSeats: Math.max(0, floorSeats.length - occupiedSeatIds.size),
      occupancyRate: percentage(occupiedSeatIds.size, floorSeats.length),
      maintenanceSeats: floorSeats.filter(
        (seat) => seat.physicalStatus === 'maintenance',
      ).length,
    },
    byShift,
    byFloor: floors,
  }
}

function buildStudentReport(students, months) {
  const active = students.filter((student) => student.status === 'active')
  const inactive = students.filter((student) => student.status !== 'active')
  const feeStatus = ['paid', 'pending', 'overdue'].map((status) => ({
    status,
    label: status.charAt(0).toUpperCase() + status.slice(1),
    count: students.filter((student) => student.feeStatus === status).length,
  }))
  const shiftCounts = students.reduce((counts, student) => {
    student.activeShifts?.forEach((shiftId) => {
      counts[shiftId] = (counts[shiftId] || 0) + 1
    })
    return counts
  }, {})

  return {
    totals: {
      totalStudents: students.length,
      activeStudents: active.length,
      inactiveStudents: inactive.length,
      activeRate: percentage(active.length, students.length),
      newStudents: students.filter((student) => {
        return months.includes(String(student.joiningDate || '').slice(0, 7))
      }).length,
    },
    joiningTrend: months.map((month) => ({
      month,
      label: formatMonthLabel(month),
      joined: students.filter(
        (student) => String(student.joiningDate || '').slice(0, 7) === month,
      ).length,
    })),
    statusDistribution: [
      { status: 'active', label: 'Active', count: active.length },
      { status: 'inactive', label: 'Inactive', count: inactive.length },
    ],
    feeStatus,
    shiftDistribution: Object.entries(shiftCounts).map(([shiftId, count]) => ({
      shiftId,
      count,
    })),
  }
}

function buildPendingPaymentReport(payments, students) {
  const studentById = new Map(students.map((student) => [student.id, student]))
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const records = payments
    .filter((payment) => ['unpaid', 'partially_paid'].includes(payment.status))
    .map((payment) => {
      const student = studentById.get(payment.studentId)
      const configuredDueDate = String(
        payment.dueDate || student?.feeDueDate || '',
      )
      const appliesToPaymentMonth = configuredDueDate.startsWith(payment.month)
      const dueDate = appliesToPaymentMonth
        ? new Date(`${configuredDueDate}T00:00:00`)
        : getMonthEnd(payment.month)
      const daysOverdue = Math.max(
        0,
        Math.floor((today.getTime() - dueDate.getTime()) / 86400000),
      )

      return {
        id: payment.id,
        studentId: payment.studentId,
        studentName: payment.studentName,
        phone: payment.studentPhone,
        seatNumber: payment.seatNumber || 'Not assigned',
        month: payment.month,
        monthLabel: formatMonthLabel(payment.month),
        amount: payment.balanceAmount,
        dueDate: formatDateKey(dueDate),
        daysOverdue,
        ageing: daysOverdue > 0 ? `${daysOverdue} days overdue` : 'Due this month',
      }
    })
    .sort((first, second) => {
      return second.daysOverdue - first.daysOverdue || second.month.localeCompare(first.month)
    })

  return {
    totals: {
      pendingAmount: sum(records, (record) => record.amount),
      pendingCount: records.length,
      overdueCount: records.filter((record) => record.daysOverdue > 0).length,
      affectedStudents: new Set(records.map((record) => record.studentId)).size,
    },
    records,
    ageing: [
      {
        label: 'Due this month',
        count: records.filter((record) => record.daysOverdue === 0).length,
      },
      {
        label: '1-30 days',
        count: records.filter(
          (record) => record.daysOverdue >= 1 && record.daysOverdue <= 30,
        ).length,
      },
      {
        label: '31+ days',
        count: records.filter((record) => record.daysOverdue > 30).length,
      },
    ],
  }
}

function buildInsights(revenue, occupancy, students, pending) {
  const collectionHealthy =
    revenue.totals.collectionRate >= REPORT_BENCHMARKS.healthyCollectionRate
  const occupancyHigh =
    occupancy.totals.occupancyRate >= REPORT_BENCHMARKS.highOccupancyRate

  return [
    {
      id: 'collection-health',
      tone: collectionHealthy ? 'success' : 'warning',
      title: collectionHealthy ? 'Collections are on track' : 'Collections need attention',
      detail: `${revenue.totals.collectionRate}% of expected fees were collected in this period.`,
    },
    {
      id: 'seat-capacity',
      tone: occupancyHigh ? 'warning' : 'info',
      title: occupancyHigh ? 'Seat capacity is running high' : 'Seat capacity is available',
      detail: `${occupancy.totals.occupancyRate}% current occupancy across the filtered seats.`,
    },
    {
      id: 'student-health',
      tone: 'neutral',
      title: `${students.totals.activeStudents} active students`,
      detail: `${pending.totals.affectedStudents} students have pending payment records in this period.`,
    },
  ]
}

export async function getReportOptions() {
  const [paymentResponse, seatResponse] = await Promise.all([
    paymentService.getPayments({ pageSize: 100 }),
    seatService.fetchSeats(),
  ])
  const payments = paymentResponse.data.payments
  const seats = seatResponse.data.seats
  const months = [...new Set(payments.map((payment) => payment.month))]
    .filter(Boolean)
    .sort()

  return createSuccessResponse('Report options fetched successfully.', {
    months: months.map((month) => ({ value: month, label: formatMonthLabel(month) })),
    floors: [...new Set(seats.map((seat) => seat.floor))]
      .sort((first, second) => first - second)
      .map((floor) => ({ value: floor, label: `Floor ${floor}` })),
    shifts: seatResponse.data.shifts
      .filter((shift) => shift.isEnabled !== false)
      .map((shift) => ({
        value: shift.id,
        label: shift.name,
        timing: `${shift.startTime} - ${shift.endTime}`,
      })),
  })
}

export async function getReports(filters = {}) {
  const [paymentResponse, studentResponse, seatResponse] = await Promise.all([
    paymentService.getPayments({ pageSize: 100 }),
    studentService.getStudents(),
    seatService.fetchSeats(),
    delay(),
  ])
  const allPayments = paymentResponse.data.payments
  const allStudents = studentResponse.data
  const seats = seatResponse.data.seats
  const shifts = seatResponse.data.shifts
  const availableMonths = [...new Set(allPayments.map((payment) => payment.month))]
    .filter(Boolean)
    .sort()
  const normalizedFilters = normalizeFilters(filters, availableMonths)
  const months = getMonthRange(
    normalizedFilters.startMonth,
    normalizedFilters.endMonth,
  )
  const students = getStudentScope(allStudents, seats, normalizedFilters)
  const studentIds = new Set(students.map((student) => student.id))
  const payments = allPayments.filter((payment) => {
    return months.includes(payment.month) && studentIds.has(payment.studentId)
  })
  const revenue = buildRevenueReport(payments, months)
  const occupancy = buildOccupancyReport(seats, shifts, normalizedFilters)
  const studentReport = buildStudentReport(students, months)
  const pendingPayments = buildPendingPaymentReport(payments, students)

  return createSuccessResponse(
    'Reports fetched successfully.',
    {
      generatedAt: new Date().toISOString(),
      filters: normalizedFilters,
      metrics: {
        collectedRevenue: revenue.totals.collected,
        pendingRevenue: revenue.totals.pending,
        collectionRate: revenue.totals.collectionRate,
        activeStudents: studentReport.totals.activeStudents,
        totalStudents: studentReport.totals.totalStudents,
        occupiedSeats: occupancy.totals.occupiedSeats,
        totalSeats: occupancy.totals.totalSeats,
        occupancyRate: occupancy.totals.occupancyRate,
      },
      revenue,
      occupancy,
      students: studentReport,
      pendingPayments,
      insights: buildInsights(revenue, occupancy, studentReport, pendingPayments),
    },
    { filters: normalizedFilters },
  )
}

function escapeCsv(value) {
  const text = String(value ?? '')
  return /[",\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text
}

function rowsToCsv(rows) {
  return rows.map((row) => row.map(escapeCsv).join(',')).join('\n')
}

function getExportRows(reportType, reports) {
  if (reportType === 'revenue') {
    return [
      ['Month', 'Expected', 'Collected', 'Pending', 'Collection Rate'],
      ...reports.revenue.series.map((item) => [
        item.label,
        item.expected,
        item.collected,
        item.pending,
        `${item.collectionRate}%`,
      ]),
    ]
  }

  if (reportType === 'occupancy') {
    return [
      [
        'Shift',
        'Timing',
        'Total Seats',
        'Available',
        'Allotted',
        'Blocked',
        'Reserved',
        'Maintenance',
        'Occupancy Rate',
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
        `${item.occupancyRate}%`,
      ]),
    ]
  }

  if (reportType === 'students') {
    return [
      ['Month', 'Students Joined'],
      ...reports.students.joiningTrend.map((item) => [item.label, item.joined]),
      [],
      ['Status', 'Students'],
      ...reports.students.statusDistribution.map((item) => [item.label, item.count]),
      [],
      ['Fee Status', 'Students'],
      ...reports.students.feeStatus.map((item) => [item.label, item.count]),
    ]
  }

  if (reportType === 'pending') {
    return [
      ['Student', 'Phone', 'Seat', 'Fee Month', 'Amount', 'Due Date', 'Ageing'],
      ...reports.pendingPayments.records.map((item) => [
        item.studentName,
        item.phone,
        item.seatNumber,
        item.monthLabel,
        item.amount,
        item.dueDate.slice(0, 10),
        item.ageing,
      ]),
    ]
  }

  return [
    ['Metric', 'Value'],
    ['Collected Revenue', reports.metrics.collectedRevenue],
    ['Pending Revenue', reports.metrics.pendingRevenue],
    ['Collection Rate', `${reports.metrics.collectionRate}%`],
    ['Active Students', reports.metrics.activeStudents],
    ['Total Students', reports.metrics.totalStudents],
    ['Occupied Seats', reports.metrics.occupiedSeats],
    ['Total Seats', reports.metrics.totalSeats],
    ['Occupancy Rate', `${reports.metrics.occupancyRate}%`],
  ]
}

export async function exportReport(reportType, reports) {
  if (!REPORT_TYPES.has(reportType)) {
    throw createAnalyticsError('Select a valid report to export.', 422, 'REPORT_TYPE_INVALID')
  }

  if (!reports) {
    throw createAnalyticsError('Load report data before exporting.', 409, 'REPORT_DATA_MISSING')
  }

  await delay(150)

  return createSuccessResponse('CSV report prepared successfully.', {
    fileName: `smart-library-${reportType}-report-${reports.filters.startMonth}-to-${reports.filters.endMonth}.csv`,
    mimeType: 'text/csv;charset=utf-8',
    content: `\uFEFF${rowsToCsv(getExportRows(reportType, reports))}`,
  })
}

export { REPORT_STATUS_LABELS }
