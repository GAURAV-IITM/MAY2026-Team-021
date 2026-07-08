import {
  STUDENT_NETWORK_DELAY_MS,
  STUDENT_STATUSES,
  studentMock,
} from '../mocks/studentMock'

// src/services: Mock student service used during Milestone 2.
// TODO: Replace mock operations with Axios-backed FastAPI requests in Milestone 3.

let students = structuredClone(studentMock)

function delay(ms = STUDENT_NETWORK_DELAY_MS) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms)
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
      source: 'mock-student-service',
      timestamp: new Date().toISOString(),
    },
  }
}

function createStudentError(message, status = 400, code = 'STUDENT_ERROR') {
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

function findStudentIndexById(studentId) {
  return students.findIndex((student) => student.id === String(studentId))
}

function generateStudentId() {
  const numericIds = students
    .map((student) => Number.parseInt(student.id.replace('student-', ''), 10))
    .filter(Number.isFinite)

  const nextId = Math.max(0, ...numericIds) + 1

  return `student-${String(nextId).padStart(3, '0')}`
}

function normalizeStudentRecord(studentData = {}) {
  const student = clone(studentData)
  const activeShifts = Array.isArray(student.activeShifts)
    ? student.activeShifts
    : [student.shift]

  student.activeShifts = [
    ...new Set(activeShifts.filter(Boolean).map((shift) => String(shift))),
  ]

  delete student.shift

  return student
}

export async function getStudents() {
  await delay()

  return createSuccessResponse('Students fetched successfully.', students)
}

export async function getStudentById(studentId) {
  await delay()

  const student = students.find((item) => item.id === String(studentId))

  if (!student) {
    throw createStudentError('Student not found.', 404, 'STUDENT_NOT_FOUND')
  }

  return createSuccessResponse('Student fetched successfully.', student)
}

export async function createStudent(studentData = {}) {
  await delay()

  const now = new Date().toISOString()
  const normalizedStudentData = normalizeStudentRecord(studentData)

  const student = {
    ...normalizedStudentData,
    id: generateStudentId(),
    status: normalizedStudentData.status || STUDENT_STATUSES.ACTIVE,
    createdAt: now,
    updatedAt: now,
  }

  students.push(student)

  return createSuccessResponse('Student created successfully.', student)
}

export async function updateStudent(studentId, studentData = {}) {
  await delay()

  const studentIndex = findStudentIndexById(studentId)

  if (studentIndex === -1) {
    throw createStudentError('Student not found.', 404, 'STUDENT_NOT_FOUND')
  }

  const existingStudent = students[studentIndex]

  const updatedStudent = normalizeStudentRecord({
    ...existingStudent,
    ...clone(studentData),
    id: existingStudent.id,
    createdAt: existingStudent.createdAt,
    updatedAt: new Date().toISOString(),
  })

  students[studentIndex] = updatedStudent

  return createSuccessResponse('Student updated successfully.', updatedStudent)
}

export async function deactivateStudent(studentId) {
  await delay()

  const studentIndex = findStudentIndexById(studentId)

  if (studentIndex === -1) {
    throw createStudentError('Student not found.', 404, 'STUDENT_NOT_FOUND')
  }

  students[studentIndex] = {
    ...students[studentIndex],
    status: STUDENT_STATUSES.INACTIVE,
    updatedAt: new Date().toISOString(),
  }

  return createSuccessResponse(
    'Student deactivated successfully.',
    students[studentIndex],
  )
}

// Temporary compatibility alias for the original placeholder service contract.
// Student Management should use deactivateStudent because records are not hard-deleted.
export async function deleteStudent(studentId) {
  return deactivateStudent(studentId)
}
