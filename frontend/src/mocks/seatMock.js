// src/mocks: Mock seat data used during Milestone 2 before FastAPI APIs are available.
// TODO: Replace this fixture with backend-provided seat records in Milestone 3.

export const SEAT_STATUSES = Object.freeze({
  AVAILABLE: 'available',
  OCCUPIED: 'occupied',
  RESERVED: 'reserved',
  MAINTENANCE: 'maintenance',
})

export const SEAT_SHIFTS = Object.freeze({
  MORNING: 'morning',
  AFTERNOON: 'afternoon',
  EVENING: 'evening',
})

export const SEAT_NETWORK_DELAY_MS = 450

export const seatMock = [
  {
    id: 'seat-001',
    seatNumber: 'A-01',
    floor: 1,
    status: SEAT_STATUSES.OCCUPIED,
    assignedStudent: {
      id: 'student-001',
      name: 'Aarav Sharma',
      email: 'aarav.sharma@example.com',
    },
    activeShifts: [SEAT_SHIFTS.MORNING],
    notes: 'Window-side seat assigned for morning study hours.',
  },
  {
    id: 'seat-002',
    seatNumber: 'A-02',
    floor: 1,
    status: SEAT_STATUSES.AVAILABLE,
    assignedStudent: null,
    activeShifts: [
      SEAT_SHIFTS.MORNING,
      SEAT_SHIFTS.AFTERNOON,
      SEAT_SHIFTS.EVENING,
    ],
    notes: 'Standard desk with charging point.',
  },
  {
    id: 'seat-003',
    seatNumber: 'A-03',
    floor: 1,
    status: SEAT_STATUSES.OCCUPIED,
    assignedStudent: {
      id: 'student-002',
      name: 'Ananya Das',
      email: 'ananya.das@example.com',
    },
    activeShifts: [SEAT_SHIFTS.AFTERNOON],
    notes: 'Assigned near reference shelf.',
  },
  {
    id: 'seat-004',
    seatNumber: 'A-04',
    floor: 1,
    status: SEAT_STATUSES.RESERVED,
    assignedStudent: {
      id: 'student-004',
      name: 'Sneha Gupta',
      email: 'sneha.gupta@example.com',
    },
    activeShifts: [SEAT_SHIFTS.EVENING],
    notes: 'Reserved for evening admission confirmation.',
  },
  {
    id: 'seat-005',
    seatNumber: 'B-01',
    floor: 2,
    status: SEAT_STATUSES.OCCUPIED,
    assignedStudent: {
      id: 'student-003',
      name: 'Rohan Verma',
      email: 'rohan.verma@example.com',
    },
    activeShifts: [SEAT_SHIFTS.EVENING],
    notes: 'Assigned for exam preparation block.',
  },
  {
    id: 'seat-006',
    seatNumber: 'B-02',
    floor: 2,
    status: SEAT_STATUSES.AVAILABLE,
    assignedStudent: null,
    activeShifts: [SEAT_SHIFTS.MORNING, SEAT_SHIFTS.AFTERNOON],
    notes: 'Near group-study notice board.',
  },
  {
    id: 'seat-007',
    seatNumber: 'B-03',
    floor: 2,
    status: SEAT_STATUSES.MAINTENANCE,
    assignedStudent: null,
    activeShifts: [],
    notes: 'Desk lamp repair pending.',
  },
  {
    id: 'seat-008',
    seatNumber: 'B-04',
    floor: 2,
    status: SEAT_STATUSES.OCCUPIED,
    assignedStudent: {
      id: 'student-005',
      name: 'Aditya Singh',
      email: 'aditya.singh@example.com',
    },
    activeShifts: [SEAT_SHIFTS.AFTERNOON],
    notes: 'Long-term monthly allocation.',
  },
  {
    id: 'seat-009',
    seatNumber: 'C-01',
    floor: 3,
    status: SEAT_STATUSES.AVAILABLE,
    assignedStudent: null,
    activeShifts: [
      SEAT_SHIFTS.MORNING,
      SEAT_SHIFTS.AFTERNOON,
      SEAT_SHIFTS.EVENING,
    ],
    notes: 'Premium desk with extra storage.',
  },
  {
    id: 'seat-010',
    seatNumber: 'C-02',
    floor: 3,
    status: SEAT_STATUSES.OCCUPIED,
    assignedStudent: {
      id: 'student-006',
      name: 'Priya Roy',
      email: 'priya.roy@example.com',
    },
    activeShifts: [SEAT_SHIFTS.MORNING],
    notes: 'Assigned close to air conditioning.',
  },
  {
    id: 'seat-011',
    seatNumber: 'C-03',
    floor: 3,
    status: SEAT_STATUSES.AVAILABLE,
    assignedStudent: null,
    activeShifts: [SEAT_SHIFTS.AFTERNOON, SEAT_SHIFTS.EVENING],
    notes: 'Suitable for laptop users.',
  },
  {
    id: 'seat-012',
    seatNumber: 'C-04',
    floor: 3,
    status: SEAT_STATUSES.MAINTENANCE,
    assignedStudent: null,
    activeShifts: [],
    notes: 'Chair replacement scheduled.',
  },
]
