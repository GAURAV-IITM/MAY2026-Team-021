import { paymentMock } from './paymentMock.js'
import { seatMock } from './seatMock.js'
import { studentMock } from './studentMock.js'

export const DASHBOARD_NETWORK_DELAY_MS = 450

function getLatestPaymentMonth() {
  return [...new Set(paymentMock.map((payment) => payment.month))]
    .filter(Boolean)
    .sort()
    .at(-1)
}

function buildMonthlyCollection() {
  return [...new Set(paymentMock.map((payment) => payment.month))]
    .filter(Boolean)
    .sort()
    .slice(-3)
    .map((month) => {
      const monthPayments = paymentMock.filter((payment) => payment.month === month)
      const collectedAmount = monthPayments
        .filter((payment) => payment.status === 'paid')
        .reduce((total, payment) => total + payment.amount, 0)
      const expectedAmount = monthPayments.reduce(
        (total, payment) => total + payment.amount,
        0,
      )

      return {
        month,
        collectedAmount,
        expectedAmount,
        collectionRate:
          expectedAmount === 0
            ? 0
            : Math.round((collectedAmount / expectedAmount) * 100),
      }
    })
}

function buildRecentActivity(activeStudents, paidPayments) {
  const paymentActivity = paidPayments.map((payment) => ({
    id: `activity-${payment.id}`,
    type: 'payment',
    title: `Payment received from ${payment.studentName}`,
    detail: `${payment.seatNumber || 'No seat'} · ${payment.paymentMethod || 'Payment recorded'}`,
    amount: payment.amount,
    occurredAt: payment.paidAt || payment.updatedAt,
  }))

  const registrationActivity = activeStudents.map((student) => ({
    id: `activity-${student.id}`,
    type: 'student',
    title: `${student.firstName} ${student.lastName} joined the library`,
    detail: `${student.seatNumber || 'Seat not assigned'} · ${student.activeShifts?.length || 0} shift${student.activeShifts?.length === 1 ? '' : 's'}`,
    amount: null,
    occurredAt: student.createdAt,
  }))

  return [...paymentActivity, ...registrationActivity]
    .sort((firstActivity, secondActivity) => {
      return secondActivity.occurredAt.localeCompare(firstActivity.occurredAt)
    })
    .slice(0, 6)
}

function buildDashboardMock() {
  const currentMonth = getLatestPaymentMonth()
  const activeStudents = studentMock.filter((student) => student.status === 'active')
  const currentMonthPayments = paymentMock.filter(
    (payment) => payment.month === currentMonth,
  )
  const paidPayments = currentMonthPayments.filter(
    (payment) => payment.status === 'paid',
  )
  const unpaidPayments = currentMonthPayments.filter(
    (payment) => payment.status === 'unpaid',
  )
  const collectedAmount = paidPayments.reduce(
    (total, payment) => total + payment.amount,
    0,
  )
  const pendingAmount = unpaidPayments.reduce(
    (total, payment) => total + payment.amount,
    0,
  )
  const expectedAmount = collectedAmount + pendingAmount
  const maintenanceSeats = seatMock.filter((seat) => seat.status === 'maintenance')
  const blockedSeats = seatMock.filter((seat) => seat.status === 'blocked')
  const overdueStudents = activeStudents.filter(
    (student) => student.feeStatus === 'overdue',
  )

  return {
    currentMonth,
    metrics: {
      totalStudents: studentMock.length,
      activeStudents: activeStudents.length,
      inactiveStudents: studentMock.length - activeStudents.length,
      totalSeats: seatMock.length,
      occupiedSeats: seatMock.filter((seat) => seat.status === 'occupied').length,
      availableSeats: seatMock.filter((seat) => seat.status === 'available').length,
      maintenanceSeats: maintenanceSeats.length,
      collectedAmount,
      expectedAmount,
      pendingAmount,
      paidPaymentCount: paidPayments.length,
      unpaidPaymentCount: unpaidPayments.length,
      collectionRate:
        expectedAmount === 0
          ? 0
          : Math.round((collectedAmount / expectedAmount) * 100),
    },
    seatStatus: [
      {
        status: 'available',
        label: 'Available',
        count: seatMock.filter((seat) => seat.status === 'available').length,
      },
      {
        status: 'occupied',
        label: 'Occupied',
        count: seatMock.filter((seat) => seat.status === 'occupied').length,
      },
      {
        status: 'reserved',
        label: 'Reserved',
        count: seatMock.filter((seat) => seat.status === 'reserved').length,
      },
      {
        status: 'maintenance',
        label: 'Maintenance',
        count: maintenanceSeats.length,
      },
      {
        status: 'blocked',
        label: 'Blocked',
        count: blockedSeats.length,
      },
    ],
    monthlyCollection: buildMonthlyCollection(),
    shiftAvailability: [],
    attentionItems: [
      {
        id: 'pending-payments',
        tone: 'warning',
        label: 'Payments pending',
        value: unpaidPayments.length,
        detail: `${pendingAmount} due for the current month`,
        routeName: 'adminPayments',
      },
      {
        id: 'overdue-fees',
        tone: 'danger',
        label: 'Overdue follow-up',
        value: overdueStudents.length,
        detail: 'Active students marked with overdue fees',
        routeName: 'adminPayments',
      },
      {
        id: 'maintenance-seats',
        tone: 'info',
        label: 'Seats under maintenance',
        value: maintenanceSeats.length,
        detail: maintenanceSeats.map((seat) => seat.seatNumber).join(', ') || 'No seats',
        routeName: 'adminSeatManagement',
      },
    ],
    recentActivity: buildRecentActivity(activeStudents, paidPayments),
  }
}

export const dashboardMock = buildDashboardMock()
