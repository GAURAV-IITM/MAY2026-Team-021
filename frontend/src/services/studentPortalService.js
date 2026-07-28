import {
  STUDENT_PORTAL_NETWORK_DELAY_MS,
  seatRequestMock,
  studentAnnouncementMock,
  studentPaymentMock,
  studentProfileMock,
  studentSeatMock,
} from '../mocks/studentPortalMock.js'
import { shiftMock } from '../mocks/seatMock.js'
import { getCurrentLibrarySettings } from './librarySettingsService.js'

let profile = clone(studentProfileMock)
let requests = clone(seatRequestMock)
let studentAnnouncements = clone(studentAnnouncementMock)

function clone(value) {
  return structuredClone(value)
}

function delay(ms = STUDENT_PORTAL_NETWORK_DELAY_MS) {
  return new Promise((resolve) => {
    globalThis.setTimeout(resolve, ms)
  })
}

function createSuccessResponse(message, data, meta = {}) {
  return {
    success: true,
    message,
    data: clone(data),
    meta: {
      source: 'mock-student-portal-service',
      timestamp: new Date().toISOString(),
      ...meta,
    },
  }
}

function createPortalError(message, status = 400, code = 'STUDENT_PORTAL_ERROR') {
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

function ensureStudentAccess(studentId) {
  const normalizedStudentId = String(studentId || '').trim()

  if (!normalizedStudentId) {
    throw createPortalError(
      'A logged-in student is required.',
      401,
      'STUDENT_AUTH_REQUIRED',
    )
  }

  if (normalizedStudentId !== profile.id) {
    throw createPortalError(
      'Student portal data is not available for this account.',
      403,
      'STUDENT_ACCESS_DENIED',
    )
  }

  return normalizedStudentId
}

function ensureAdminAccess(admin = {}) {
  const id = String(admin.id || '').trim()
  const libraryName = String(admin.libraryName || '').trim()

  if (!id || !libraryName) {
    throw createPortalError(
      'A logged-in library owner is required.',
      401,
      'ADMIN_AUTH_REQUIRED',
    )
  }

  return { id, name: String(admin.name || 'Library Owner'), libraryName }
}

function getStudentPayments(studentId) {
  return studentPaymentMock
    .filter((payment) => payment.studentId === studentId)
    .sort((first, second) => second.month.localeCompare(first.month))
}

function buildReceipt(payment) {
  return {
    id: `receipt-${payment.id}`,
    receiptNumber: payment.receiptNumber,
    paymentId: payment.id,
    studentId: payment.studentId,
    studentName: payment.studentName,
    studentEmail: payment.studentEmail,
    seatNumber: payment.seatNumber,
    month: payment.month,
    amount: payment.amount,
    paidAt: payment.paidAt,
    paymentMethod: payment.paymentMethod,
    transactionId: payment.transactionId,
  }
}

function getStudentReceipts(studentId) {
  return getStudentPayments(studentId)
    .filter((payment) => payment.status === 'paid')
    .map((payment) => buildReceipt(payment))
}

function getStudentAnnouncements(studentId) {
  const now = new Date()
  return studentAnnouncements
    .filter((announcement) => {
      return (
        (!announcement.publishedAt ||
          new Date(announcement.publishedAt) <= now) &&
        (!announcement.expiresAt || new Date(announcement.expiresAt) > now)
      )
    })
    .sort((first, second) =>
      second.publishedAt.localeCompare(first.publishedAt),
    )
    .map((announcement) => ({
      ...announcement,
      isRead: announcement.readBy.includes(studentId),
    }))
}

function getStudentRequests(studentId) {
  return requests
    .filter((request) => request.studentId === studentId)
    .sort((first, second) => second.submittedAt.localeCompare(first.submittedAt))
}

function getFeeSummary(studentId) {
  const payments = getStudentPayments(studentId)
  const currentPayment = payments[0] || null
  const totalPaid = payments
    .filter((payment) => payment.status === 'paid')
    .reduce((total, payment) => total + payment.amount, 0)
  const totalOutstanding = payments
    .filter((payment) => payment.status === 'unpaid')
    .reduce((total, payment) => total + payment.amount, 0)

  return {
    currentPayment,
    payments,
    totalPaid,
    totalOutstanding,
    paidCount: payments.filter((payment) => payment.status === 'paid').length,
    unpaidCount: payments.filter((payment) => payment.status === 'unpaid').length,
    nextDueDate: profile.feeDueDate,
  }
}

export async function getDashboard(studentId) {
  await delay()
  const scopedStudentId = ensureStudentAccess(studentId)
  const studentAnnouncements = getStudentAnnouncements(scopedStudentId)
  const studentRequests = getStudentRequests(scopedStudentId)

  return createSuccessResponse('Student dashboard fetched successfully.', {
    profile,
    seat: studentSeatMock.seat,
    allocations: studentSeatMock.allocations,
    feeSummary: getFeeSummary(scopedStudentId),
    recentAnnouncements: studentAnnouncements.slice(0, 3),
    unreadAnnouncementCount: studentAnnouncements.filter((item) => !item.isRead).length,
    activeRequest: studentRequests.find((request) => request.status === 'pending') || null,
    lastUpdated: new Date().toISOString(),
  })
}

export async function getSeat(studentId) {
  await delay()
  ensureStudentAccess(studentId)

  return createSuccessResponse('Seat allocation fetched successfully.', {
    ...studentSeatMock,
  })
}

export async function getFees(studentId) {
  await delay()
  const scopedStudentId = ensureStudentAccess(studentId)

  return createSuccessResponse('Student fees fetched successfully.', {
    feeSummary: getFeeSummary(scopedStudentId),
  })
}

export async function getReceipts(studentId) {
  await delay()
  const scopedStudentId = ensureStudentAccess(studentId)

  return createSuccessResponse('Student receipts fetched successfully.', {
    receipts: getStudentReceipts(scopedStudentId),
  })
}

export async function getRequests(studentId) {
  await delay()
  const scopedStudentId = ensureStudentAccess(studentId)

  return createSuccessResponse('Seat change requests fetched successfully.', {
    requests: getStudentRequests(scopedStudentId),
    shifts: shiftMock.filter((shift) => shift.isEnabled !== false),
  })
}

export async function createSeatRequest(studentId, payload = {}) {
  await delay()
  const scopedStudentId = ensureStudentAccess(studentId)
  const librarySettings = getCurrentLibrarySettings()
  const preferredShiftId = String(payload.preferredShiftId || '').trim()
  const reason = String(payload.reason || '').trim()
  const preferredSeatNumber = String(payload.preferredSeatNumber || '').trim()
  const preferredFloor = payload.preferredFloor ? Number(payload.preferredFloor) : null
  const selectedShift = shiftMock.find((shift) => shift.id === preferredShiftId)

  if (!librarySettings.allowSeatChangeRequests) {
    throw createPortalError(
      'Seat change requests are currently disabled by the library owner.',
      403,
      'SEAT_REQUESTS_DISABLED',
    )
  }

  if (
    !selectedShift ||
    (librarySettings.requireSeatRequestReason && reason.length < 15)
  ) {
    throw createPortalError(
      librarySettings.requireSeatRequestReason
        ? 'Select a valid shift and provide a reason of at least 15 characters.'
        : 'Select a valid shift.',
      422,
      'SEAT_REQUEST_VALIDATION_ERROR',
    )
  }

  const hasPendingRequest = requests.some((request) => {
    return request.studentId === scopedStudentId && request.status === 'pending'
  })

  if (hasPendingRequest) {
    throw createPortalError(
      'You already have a pending seat change request.',
      409,
      'SEAT_REQUEST_ALREADY_PENDING',
    )
  }

  const request = {
    id: `seat-request-${Date.now()}`,
    studentId: scopedStudentId,
    studentName: profile.fullName,
    studentEmail: profile.email,
    libraryId: profile.libraryId,
    libraryName: profile.libraryName,
    currentSeatNumber: studentSeatMock.seat.seatNumber,
    preferredSeatNumber,
    preferredFloor,
    preferredShiftId,
    preferredShiftName: selectedShift.name,
    reason,
    status: 'pending',
    adminNote: '',
    submittedAt: new Date().toISOString(),
    resolvedAt: null,
    reviewedBy: null,
  }

  requests.push(request)

  return createSuccessResponse('Seat change request submitted successfully.', {
    request,
    requests: getStudentRequests(scopedStudentId),
  })
}

export async function cancelSeatRequest(studentId, requestId) {
  await delay()
  const scopedStudentId = ensureStudentAccess(studentId)
  const request = requests.find((item) => {
    return item.id === String(requestId) && item.studentId === scopedStudentId
  })

  if (!request) {
    throw createPortalError('Seat request was not found.', 404, 'SEAT_REQUEST_NOT_FOUND')
  }

  if (request.status !== 'pending') {
    throw createPortalError(
      'Only pending requests can be cancelled.',
      409,
      'SEAT_REQUEST_NOT_PENDING',
    )
  }

  request.status = 'cancelled'
  request.resolvedAt = new Date().toISOString()

  return createSuccessResponse('Seat change request cancelled successfully.', {
    request,
    requests: getStudentRequests(scopedStudentId),
  })
}

export async function getAdminSeatRequests(admin) {
  await delay()
  const scopedAdmin = ensureAdminAccess(admin)
  const libraryRequests = requests
    .filter((request) => request.libraryName === scopedAdmin.libraryName)
    .sort((first, second) => second.submittedAt.localeCompare(first.submittedAt))

  return createSuccessResponse('Seat change requests fetched successfully.', {
    requests: libraryRequests,
  })
}

export async function reviewSeatRequest(admin, requestId, payload = {}) {
  await delay()
  const scopedAdmin = ensureAdminAccess(admin)
  const decision = String(payload.decision || '').trim().toLowerCase()
  const adminNote = String(payload.adminNote || '').trim()
  const request = requests.find((item) => {
    return item.id === String(requestId) && item.libraryName === scopedAdmin.libraryName
  })

  if (!request) {
    throw createPortalError('Seat request was not found.', 404, 'SEAT_REQUEST_NOT_FOUND')
  }

  if (request.status !== 'pending') {
    throw createPortalError(
      'Only pending requests can be reviewed.',
      409,
      'SEAT_REQUEST_ALREADY_REVIEWED',
    )
  }

  if (!['approved', 'rejected'].includes(decision)) {
    throw createPortalError(
      'Choose either approve or reject.',
      422,
      'SEAT_REQUEST_DECISION_REQUIRED',
    )
  }

  if (decision === 'rejected' && adminNote.length < 5) {
    throw createPortalError(
      'Add a short reason before rejecting the request.',
      422,
      'SEAT_REQUEST_REJECTION_NOTE_REQUIRED',
    )
  }

  request.status = decision
  request.adminNote = adminNote
  request.resolvedAt = new Date().toISOString()
  request.reviewedBy = { id: scopedAdmin.id, name: scopedAdmin.name }

  const libraryRequests = requests
    .filter((item) => item.libraryName === scopedAdmin.libraryName)
    .sort((first, second) => second.submittedAt.localeCompare(first.submittedAt))

  return createSuccessResponse(`Seat request ${decision} successfully.`, {
    request,
    requests: libraryRequests,
  })
}

export async function getAnnouncements(studentId) {
  await delay()
  const scopedStudentId = ensureStudentAccess(studentId)

  return createSuccessResponse('Announcements fetched successfully.', {
    announcements: getStudentAnnouncements(scopedStudentId),
  })
}

export async function markAnnouncementRead(studentId, announcementId) {
  await delay()
  const scopedStudentId = ensureStudentAccess(studentId)
  const index = studentAnnouncements.findIndex(
    (item) => item.id === String(announcementId),
  )
  if (index === -1) {
    throw createPortalError(
      'Announcement was not found.',
      404,
      'ANNOUNCEMENT_NOT_FOUND',
    )
  }
  const announcement = studentAnnouncements[index]
  if (!announcement.readBy.includes(scopedStudentId)) {
    studentAnnouncements[index] = {
      ...announcement,
      readBy: [...announcement.readBy, scopedStudentId],
    }
  }

  return createSuccessResponse('Announcement marked as read.', {
    announcement: {
      ...studentAnnouncements[index],
      isRead: true,
    },
    announcements: getStudentAnnouncements(scopedStudentId),
  })
}

export async function getProfile(studentId) {
  await delay()
  ensureStudentAccess(studentId)

  return createSuccessResponse('Student profile fetched successfully.', {
    profile,
  })
}

export async function updateProfile(studentId, payload = {}) {
  await delay()
  ensureStudentAccess(studentId)

  const phone = String(payload.phone ?? profile.phone ?? '').trim()
  const address = String(payload.address ?? profile.address ?? '').trim()
  const guardianName = String(payload.guardianName ?? profile.guardianName ?? '').trim()
  const guardianPhone = String(
    payload.guardianPhone ?? profile.guardianPhone ?? '',
  ).trim()
  const preferredLanguage = String(
    payload.preferredLanguage ?? profile.preferredLanguage ?? 'English',
  ).trim()

  if (!phone || !address || !guardianName || !guardianPhone) {
    throw createPortalError(
      'Phone, address, guardian name, and guardian phone are required.',
      422,
      'PROFILE_VALIDATION_ERROR',
    )
  }

  profile = {
    ...profile,
    phone,
    address,
    guardianName,
    guardianPhone,
    preferredLanguage,
    updatedAt: new Date().toISOString(),
  }

  return createSuccessResponse('Profile updated successfully.', {
    profile,
  })
}
