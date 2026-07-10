import {
  PAYMENT_METHODS,
  PAYMENT_NETWORK_DELAY_MS,
  PAYMENT_STATUSES,
  paymentMock,
} from '../mocks/paymentMock.js'

// src/services: Mock payment service used during Milestone 2.
// TODO: Replace mock operations with Axios-backed FastAPI requests during Milestone 3.

let payments = clone(paymentMock)

function clone(value) {
  return structuredClone(value)
}

function delay(ms = PAYMENT_NETWORK_DELAY_MS) {
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
      source: 'mock-payment-service',
      timestamp: new Date().toISOString(),
      ...meta,
    },
  }
}

function createPaymentError(message, status = 400, code = 'PAYMENT_ERROR') {
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

function normalizeFilters(filters = {}) {
  return {
    search: String(filters.search || '').trim().toLowerCase(),
    month: String(filters.month || '').trim(),
    status: String(filters.status || '').trim().toLowerCase(),
  }
}

function filterPayments(sourcePayments, filters = {}) {
  const normalizedFilters = normalizeFilters(filters)

  return sourcePayments.filter((payment) => {
    const searchableText = [
      payment.studentName,
      payment.studentEmail,
      payment.seatNumber,
      payment.transactionId,
      payment.receiptNumber,
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase()

    const matchesSearch =
      !normalizedFilters.search ||
      searchableText.includes(normalizedFilters.search)

    const matchesMonth =
      !normalizedFilters.month || payment.month === normalizedFilters.month

    const matchesStatus =
      !normalizedFilters.status || payment.status === normalizedFilters.status

    return matchesSearch && matchesMonth && matchesStatus
  })
}

function sortPaymentsNewestFirst(sourcePayments) {
  return [...sourcePayments].sort((firstPayment, secondPayment) => {
    if (firstPayment.month !== secondPayment.month) {
      return secondPayment.month.localeCompare(firstPayment.month)
    }

    return secondPayment.updatedAt.localeCompare(firstPayment.updatedAt)
  })
}

function getPaymentByIdentifier(paymentId) {
  const normalizedPaymentId = String(paymentId || '').trim()
  const paymentIndex = payments.findIndex(
    (payment) => payment.id === normalizedPaymentId,
  )

  if (paymentIndex === -1) {
    throw createPaymentError(
      'Payment record was not found.',
      404,
      'PAYMENT_NOT_FOUND',
    )
  }

  return {
    paymentIndex,
    payment: payments[paymentIndex],
  }
}

function getValidPaymentStatus(status) {
  const normalizedStatus = String(status || '').trim().toLowerCase()

  if (!Object.values(PAYMENT_STATUSES).includes(normalizedStatus)) {
    throw createPaymentError(
      'Payment status must be paid or unpaid.',
      422,
      'PAYMENT_STATUS_INVALID',
    )
  }

  return normalizedStatus
}

function getValidPaymentMethod(method) {
  const normalizedMethod = String(method || '').trim().toLowerCase()

  if (!Object.values(PAYMENT_METHODS).includes(normalizedMethod)) {
    throw createPaymentError(
      'A valid payment method is required when marking a payment as paid.',
      422,
      'PAYMENT_METHOD_INVALID',
    )
  }

  return normalizedMethod
}

function generateTransactionId(payment) {
  const monthToken = payment.month.replace('-', '')
  return `TXN-${monthToken}-${payment.id}-${Date.now()}`
}

function generateReceiptNumber(payment) {
  const monthToken = payment.month.replace('-', '')
  return `RCP-${monthToken}-${payment.studentId}-${Date.now()}`
}

function buildReceipt(payment) {
  if (payment.status !== PAYMENT_STATUSES.PAID) {
    throw createPaymentError(
      'Receipts can only be generated for paid payments.',
      409,
      'PAYMENT_NOT_PAID',
    )
  }

  return {
    id: `receipt-${payment.id}`,
    receiptNumber: payment.receiptNumber,
    paymentId: payment.id,
    studentId: payment.studentId,
    studentName: payment.studentName,
    studentEmail: payment.studentEmail,
    studentPhone: payment.studentPhone,
    seatNumber: payment.seatNumber,
    month: payment.month,
    amount: payment.amount,
    paidAt: payment.paidAt,
    paymentMethod: payment.paymentMethod,
    transactionId: payment.transactionId,
    generatedAt: new Date().toISOString(),
    downloadStatus: 'placeholder',
  }
}

function buildWhatsAppReminder(payment, reminderPayload = {}) {
  if (payment.status !== PAYMENT_STATUSES.UNPAID) {
    throw createPaymentError(
      'Payment reminders can only be generated for unpaid payments.',
      409,
      'PAYMENT_ALREADY_PAID',
    )
  }

  const customMessage = String(reminderPayload.message || '').trim()
  const defaultMessage =
    `Hello ${payment.studentName}, this is a reminder that your library fee ` +
    `of ₹${payment.amount} for ${payment.month} is pending. ` +
    'Please complete the payment at your earliest convenience.'

  const message = customMessage || defaultMessage
  const normalizedPhone = String(payment.studentPhone || '').replace(/\D/g, '')

  if (!normalizedPhone) {
    throw createPaymentError(
      'A valid student phone number is required for WhatsApp reminders.',
      422,
      'STUDENT_PHONE_REQUIRED',
    )
  }

  return {
    paymentId: payment.id,
    studentId: payment.studentId,
    studentName: payment.studentName,
    studentPhone: normalizedPhone,
    month: payment.month,
    amount: payment.amount,
    message,
    whatsappUrl: `https://wa.me/${normalizedPhone}?text=${encodeURIComponent(message)}`,
    deliveryStatus: 'placeholder',
    generatedAt: new Date().toISOString(),
  }
}

export async function getPayments(filters = {}) {
  await delay()

  const filteredPayments = sortPaymentsNewestFirst(
    filterPayments(payments, filters),
  )

  return createSuccessResponse(
    'Payments fetched successfully.',
    {
      payments: filteredPayments,
    },
    {
      count: filteredPayments.length,
      filters: normalizeFilters(filters),
    },
  )
}

export async function getPaymentById(paymentId) {
  await delay()

  const { payment } = getPaymentByIdentifier(paymentId)

  return createSuccessResponse('Payment fetched successfully.', {
    payment,
  })
}

export async function createPayment(paymentPayload = {}) {
  await delay()

  const studentId = String(paymentPayload.studentId || '').trim()
  const studentName = String(paymentPayload.studentName || '').trim()
  const month = String(paymentPayload.month || '').trim()
  const amount = Number(paymentPayload.amount)

  if (!studentId || !studentName || !month || !Number.isFinite(amount) || amount <= 0) {
    throw createPaymentError(
      'Student, month, and a valid payment amount are required.',
      422,
      'PAYMENT_VALIDATION_ERROR',
    )
  }

  const duplicatePayment = payments.some((payment) => {
    return payment.studentId === studentId && payment.month === month
  })

  if (duplicatePayment) {
    throw createPaymentError(
      'A payment record already exists for this student and month.',
      409,
      'PAYMENT_ALREADY_EXISTS',
    )
  }

  const now = new Date().toISOString()
  const payment = {
    id: `payment-${Date.now()}`,
    studentId,
    studentName,
    studentEmail: String(paymentPayload.studentEmail || '').trim(),
    studentPhone: String(paymentPayload.studentPhone || '').trim(),
    seatNumber: String(paymentPayload.seatNumber || '').trim(),
    month,
    amount,
    status: PAYMENT_STATUSES.UNPAID,
    paidAt: null,
    paymentMethod: null,
    transactionId: null,
    receiptNumber: null,
    createdAt: now,
    updatedAt: now,
  }

  payments.push(payment)

  return createSuccessResponse('Payment record created successfully.', {
    payment,
    payments: sortPaymentsNewestFirst(payments),
  })
}

export async function generateMonthlyPayments(month, studentRecords = []) {
  await delay()

  const normalizedMonth = String(month || '').trim()

  if (!/^\d{4}-\d{2}$/.test(normalizedMonth)) {
    throw createPaymentError(
      'A valid payment month is required.',
      422,
      'PAYMENT_MONTH_INVALID',
    )
  }

  if (!Array.isArray(studentRecords)) {
    throw createPaymentError(
      'Student records are required to generate monthly payments.',
      422,
      'PAYMENT_STUDENTS_INVALID',
    )
  }

  const activeStudents = studentRecords.filter(
    (student) => student.status === 'active',
  )

  const createdPayments = []
  const skippedStudents = []

  for (const student of activeStudents) {
    const duplicatePayment = payments.some((payment) => {
      return (
        payment.studentId === student.id &&
        payment.month === normalizedMonth
      )
    })

    if (duplicatePayment) {
      skippedStudents.push({
        studentId: student.id,
        studentName: `${student.firstName} ${student.lastName}`.trim(),
        reason: 'payment-already-exists',
      })

      continue
    }

    const amount = Number(student.feeAmount)

    if (!Number.isFinite(amount) || amount <= 0) {
      skippedStudents.push({
        studentId: student.id,
        studentName: `${student.firstName} ${student.lastName}`.trim(),
        reason: 'invalid-fee-amount',
      })

      continue
    }

    const now = new Date().toISOString()

    const payment = {
      id: `payment-${Date.now()}-${student.id}`,
      studentId: student.id,
      studentName: `${student.firstName} ${student.lastName}`.trim(),
      studentEmail: String(student.email || '').trim(),
      studentPhone: String(student.phone || '').trim(),
      seatNumber: String(student.seatNumber || '').trim(),
      month: normalizedMonth,
      amount,
      status: PAYMENT_STATUSES.UNPAID,
      paidAt: null,
      paymentMethod: null,
      transactionId: null,
      receiptNumber: null,
      createdAt: now,
      updatedAt: now,
    }

    payments.push(payment)
    createdPayments.push(payment)
  }

  return createSuccessResponse(
    'Monthly payment generation completed.',
    {
      createdPayments,
      skippedStudents,
      payments: sortPaymentsNewestFirst(payments),
    },
    {
      month: normalizedMonth,
      activeStudentCount: activeStudents.length,
      createdCount: createdPayments.length,
      skippedCount: skippedStudents.length,
    },
  )
}

export async function updatePaymentStatus(paymentId, statusPayload = {}) {
  await delay()

  const { paymentIndex, payment } = getPaymentByIdentifier(paymentId)
  const nextStatus = getValidPaymentStatus(statusPayload.status)

  if (payment.status === nextStatus) {
    throw createPaymentError(
      `Payment is already marked as ${nextStatus}.`,
      409,
      'PAYMENT_STATUS_UNCHANGED',
    )
  }

  const now = new Date().toISOString()

  const updatedPayment =
    nextStatus === PAYMENT_STATUSES.PAID
      ? {
          ...payment,
          status: PAYMENT_STATUSES.PAID,
          paidAt: now,
          paymentMethod: getValidPaymentMethod(statusPayload.paymentMethod),
          transactionId:
            String(statusPayload.transactionId || '').trim() ||
            generateTransactionId(payment),
          receiptNumber: payment.receiptNumber || generateReceiptNumber(payment),
          updatedAt: now,
        }
      : {
          ...payment,
          status: PAYMENT_STATUSES.UNPAID,
          paidAt: null,
          paymentMethod: null,
          transactionId: null,
          receiptNumber: null,
          updatedAt: now,
        }

  payments[paymentIndex] = updatedPayment

  return createSuccessResponse(
    `Payment marked as ${nextStatus} successfully.`,
    {
      payment: updatedPayment,
      payments: sortPaymentsNewestFirst(payments),
    },
  )
}

export async function generateReceipt(paymentId) {
  await delay()

  const { payment } = getPaymentByIdentifier(paymentId)
  const receipt = buildReceipt(payment)

  return createSuccessResponse('Receipt generated successfully.', {
    receipt,
    payment,
  })
}

export async function getReceipts(filters = {}) {
  await delay()

  const paidPayments = filterPayments(payments, {
    ...filters,
    status: PAYMENT_STATUSES.PAID,
  })

  const receipts = sortPaymentsNewestFirst(paidPayments).map((payment) =>
    buildReceipt(payment),
  )

  return createSuccessResponse(
    'Receipts fetched successfully.',
    {
      receipts,
    },
    {
      count: receipts.length,
      filters: normalizeFilters(filters),
    },
  )
}

export async function getPaymentHistory(filters = {}) {
  await delay()

  const history = sortPaymentsNewestFirst(
    filterPayments(payments, {
      ...filters,
      status: PAYMENT_STATUSES.PAID,
    }),
  )

  return createSuccessResponse(
    'Payment history fetched successfully.',
    {
      payments: history,
    },
    {
      count: history.length,
      filters: normalizeFilters({
        ...filters,
        status: PAYMENT_STATUSES.PAID,
      }),
    },
  )
}

export async function getPendingPayments(filters = {}) {
  await delay()

  const pendingPayments = sortPaymentsNewestFirst(
    filterPayments(payments, {
      ...filters,
      status: PAYMENT_STATUSES.UNPAID,
    }),
  )

  return createSuccessResponse(
    'Pending payments fetched successfully.',
    {
      payments: pendingPayments,
    },
    {
      count: pendingPayments.length,
      filters: normalizeFilters(filters),
    },
  )
}

export async function generateWhatsAppReminder(
  paymentId,
  reminderPayload = {},
) {
  await delay()

  const { payment } = getPaymentByIdentifier(paymentId)
  const reminder = buildWhatsAppReminder(payment, reminderPayload)

  return createSuccessResponse(
    'WhatsApp payment reminder generated successfully.',
    {
      reminder,
      payment,
    },
  )
}