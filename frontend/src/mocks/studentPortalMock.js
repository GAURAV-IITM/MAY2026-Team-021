import { paymentMock } from './paymentMock.js'
import { seatMock, shiftMock } from './seatMock.js'
import { studentMock } from './studentMock.js'

export const STUDENT_PORTAL_NETWORK_DELAY_MS = 400

const baseStudent = studentMock.find((student) => student.id === 'student-001')
const assignedSeat = seatMock.find((seat) => seat.seatNumber === baseStudent.seatNumber)
const assignedShifts = shiftMock.filter((shift) => baseStudent.activeShifts.includes(shift.id))

export const studentProfileMock = {
  ...baseStudent,
  fullName: `${baseStudent.firstName} ${baseStudent.lastName}`,
  membershipId: 'CSL-2026-001',
  libraryId: 'library-001',
  libraryName: 'Central Study Library',
  dateOfBirth: '2003-08-17',
  preferredLanguage: 'English',
  profileCompleted: true,
}

export const studentSeatMock = {
  seat: {
    id: assignedSeat.id,
    seatNumber: assignedSeat.seatNumber,
    floor: assignedSeat.floor,
    seatType: assignedSeat.seatType,
    notes: assignedSeat.notes,
  },
  allocations: assignedShifts.map((shift) => ({
    id: `${assignedSeat.id}-${shift.id}-student-allocation`,
    seatId: assignedSeat.id,
    seatNumber: assignedSeat.seatNumber,
    floor: assignedSeat.floor,
    shiftId: shift.id,
    shiftName: shift.name,
    startTime: shift.startTime,
    endTime: shift.endTime,
    startDate: '2026-07-01',
    endDate: '2026-07-31',
    status: 'active',
    allocatedAt: '2026-06-28T09:30:00.000Z',
  })),
}

export const studentPaymentMock = paymentMock.filter(
  (payment) => payment.studentId === studentProfileMock.id,
)

export const seatRequestMock = [
  {
    id: 'seat-request-001',
    studentId: studentProfileMock.id,
    studentName: studentProfileMock.fullName,
    studentEmail: studentProfileMock.email,
    libraryId: studentProfileMock.libraryId,
    libraryName: studentProfileMock.libraryName,
    currentSeatNumber: 'A-03',
    preferredSeatNumber: 'A-01',
    preferredFloor: 1,
    preferredShiftId: 'office-hours',
    preferredShiftName: 'office hours',
    reason: 'A window-side desk would provide better natural light for daytime study.',
    status: 'approved',
    adminNote: 'Approved and transferred to A-01 for the July allocation period.',
    submittedAt: '2026-06-24T08:15:00.000Z',
    resolvedAt: '2026-06-27T11:20:00.000Z',
    reviewedBy: { id: 'owner-001', name: 'Library Owner' },
  },
  {
    id: 'seat-request-002',
    studentId: studentProfileMock.id,
    studentName: studentProfileMock.fullName,
    studentEmail: studentProfileMock.email,
    libraryId: studentProfileMock.libraryId,
    libraryName: studentProfileMock.libraryName,
    currentSeatNumber: 'A-03',
    preferredSeatNumber: 'B-02',
    preferredFloor: 2,
    preferredShiftId: 'morning',
    preferredShiftName: 'Morning',
    reason: 'Requested a quieter floor during the examination preparation period.',
    status: 'rejected',
    adminNote: 'The requested seat was unavailable for the selected shift.',
    submittedAt: '2026-05-18T10:00:00.000Z',
    resolvedAt: '2026-05-20T13:45:00.000Z',
    reviewedBy: { id: 'owner-001', name: 'Library Owner' },
  },
  {
    id: 'seat-request-003',
    studentId: 'student-002',
    studentName: 'Ananya Das',
    studentEmail: 'ananya.das@example.com',
    libraryId: 'library-001',
    libraryName: 'Central Study Library',
    currentSeatNumber: 'A-03',
    preferredSeatNumber: 'B-02',
    preferredFloor: 2,
    preferredShiftId: 'afternoon',
    preferredShiftName: 'Afternoon',
    reason: 'The second floor is quieter during my afternoon study hours.',
    status: 'pending',
    adminNote: '',
    submittedAt: '2026-07-10T09:20:00.000Z',
    resolvedAt: null,
    reviewedBy: null,
  },
  {
    id: 'seat-request-004',
    studentId: 'student-005',
    studentName: 'Aditya Singh',
    studentEmail: 'aditya.singh@example.com',
    libraryId: 'library-001',
    libraryName: 'Central Study Library',
    currentSeatNumber: 'C-03',
    preferredSeatNumber: '',
    preferredFloor: 1,
    preferredShiftId: 'early-morning',
    preferredShiftName: 'early morning',
    reason: 'I need an earlier shift because my college schedule has changed.',
    status: 'pending',
    adminNote: '',
    submittedAt: '2026-07-09T07:45:00.000Z',
    resolvedAt: null,
    reviewedBy: null,
  },
]

export const studentAnnouncementMock = [
  {
    id: 'announcement-001',
    title: 'Library will open late on Sunday',
    body: 'The library will open at 8:00 AM instead of 6:00 AM on Sunday due to scheduled electrical maintenance.',
    category: 'schedule',
    priority: 'important',
    publishedAt: '2026-07-10T06:30:00.000Z',
    expiresAt: '2026-07-13T18:00:00.000Z',
    readBy: [],
  },
  {
    id: 'announcement-002',
    title: 'July fee receipts are available',
    body: 'Students who have completed their July payment can now view their receipt in the Student Portal.',
    category: 'fees',
    priority: 'normal',
    publishedAt: '2026-07-08T09:15:00.000Z',
    expiresAt: null,
    readBy: ['student-001'],
  },
  {
    id: 'announcement-003',
    title: 'New reference books added',
    body: 'The competitive examinations section now includes updated reference books for 2026 entrance tests.',
    category: 'general',
    priority: 'normal',
    publishedAt: '2026-07-06T11:00:00.000Z',
    expiresAt: null,
    readBy: [],
  },
  {
    id: 'announcement-004',
    title: 'Keep personal belongings secure',
    body: 'Please carry valuables with you when leaving your seat. The library is not responsible for unattended belongings.',
    category: 'policy',
    priority: 'important',
    publishedAt: '2026-07-03T07:45:00.000Z',
    expiresAt: null,
    readBy: ['student-001'],
  },
  {
    id: 'announcement-005',
    title: 'Water dispenser maintenance completed',
    body: 'The second-floor water dispenser is operational again after routine servicing.',
    category: 'facility',
    priority: 'normal',
    publishedAt: '2026-07-01T13:30:00.000Z',
    expiresAt: null,
    readBy: ['student-001'],
  },
]

export const studentPortalMock = {
  profile: studentProfileMock,
  seat: studentSeatMock,
  payments: studentPaymentMock,
  requests: seatRequestMock,
  announcements: studentAnnouncementMock,
  shifts: shiftMock.filter((shift) => shift.isEnabled !== false),
}
