import apiClient from '../api/axios.js'

function normalizeTransaction(transaction) {
  if (!transaction) return null

  return {
    ...transaction,
    transactionId: transaction.referenceNumber || transaction.id,
  }
}

export function normalizeReceipt(receipt) {
  if (!receipt) return null

  const isDetail = Boolean(receipt.library && receipt.fee && receipt.payment)
  if (isDetail) {
    return {
      ...receipt,
      studentId: receipt.student.id,
      studentName: receipt.student.name,
      enrollmentNumber: receipt.student.enrollmentNumber,
      month: receipt.fee.billingMonth,
      amount: Number(receipt.payment.amount),
      paymentMethod: receipt.payment.method,
      paymentReference: receipt.payment.referenceNumber,
      transactionId: receipt.payment.id,
      paidAt: receipt.payment.paidAt,
      remainingBalance: Number(receipt.fee.remainingBalance),
    }
  }

  return {
    ...receipt,
    studentId: receipt.student.id,
    studentName: receipt.student.name,
    enrollmentNumber: receipt.student.enrollmentNumber,
    month: receipt.billingMonth,
    amount: Number(receipt.amount),
    transactionId: receipt.paymentTransactionId,
  }
}

export function normalizePayment(payment) {
  const latestTransaction = normalizeTransaction(payment.latestTransaction)

  return {
    ...payment,
    studentId: payment.student.id,
    studentName: payment.student.name,
    studentEmail: payment.student.email,
    studentPhone: payment.student.phone,
    enrollmentNumber: payment.student.enrollmentNumber,
    amount: Number(payment.totalAmount),
    baseAmount: Number(payment.baseAmount),
    discountAmount: Number(payment.discountAmount),
    lateFeeAmount: Number(payment.lateFeeAmount),
    totalAmount: Number(payment.totalAmount),
    paidAmount: Number(payment.paidAmount),
    balanceAmount: Number(payment.balanceAmount),
    paymentMethod: latestTransaction?.method || null,
    transactionId: latestTransaction?.transactionId || null,
    paidAt: latestTransaction?.paidAt || null,
    latestTransaction,
    transactions: payment.transactions.map(normalizeTransaction),
  }
}

export function buildPaymentParams(filters = {}) {
  return {
    page: filters.page || 1,
    pageSize: filters.pageSize || 20,
    search: filters.search || undefined,
    sortBy: filters.sortBy || 'month',
    sortOrder: filters.sortOrder || 'desc',
    month: filters.month || undefined,
    status: filters.status || undefined,
    studentId: filters.studentId || undefined,
    dueDateFrom: filters.dueDateFrom || undefined,
    dueDateTo: filters.dueDateTo || undefined,
    hasTransactions: filters.hasTransactions ?? undefined,
  }
}

export function buildReceiptParams(filters = {}) {
  return {
    page: filters.page || 1,
    pageSize: filters.pageSize || 20,
    search: filters.search || undefined,
    sortBy: filters.sortBy || 'issuedAt',
    sortOrder: filters.sortOrder || 'desc',
    billingMonth: filters.billingMonth || filters.month || undefined,
    paymentMethod: filters.paymentMethod || undefined,
    studentId: filters.studentId || undefined,
    status: filters.status || undefined,
    dateFrom: filters.dateFrom || undefined,
    dateTo: filters.dateTo || undefined,
  }
}

export async function getPayments(filters = {}) {
  const response = await apiClient.get('/payments', {
    params: buildPaymentParams(filters),
  })

  return {
    ...response.data,
    data: {
      payments: response.data.data.map(normalizePayment),
    },
  }
}

export async function generateMonthlyPayments(month) {
  const response = await apiClient.post('/payments/monthly-generation', {
    month,
  })

  return {
    ...response.data,
    data: {
      ...response.data.data,
      createdPayments: response.data.data.createdPayments.map(normalizePayment),
    },
  }
}

export async function recordPayment(feeRecordId, payload = {}) {
  const response = await apiClient.post(
    `/payments/${feeRecordId}/transactions`,
    {
      amount: payload.amount,
      method: payload.method,
      paidAt: payload.paidAt || undefined,
      referenceNumber: payload.referenceNumber || undefined,
      notes: payload.notes || undefined,
    },
  )

  return {
    ...response.data,
    data: {
      ...response.data.data,
      payment: normalizePayment(response.data.data.payment),
      transaction: normalizeTransaction(response.data.data.transaction),
      receipt: normalizeReceipt(response.data.data.receipt),
    },
  }
}

export async function getPaymentHistory(filters = {}) {
  return getPayments({
    ...filters,
    month: filters.month || undefined,
    hasTransactions: true,
  })
}

export async function getReceipts(filters = {}) {
  const response = await apiClient.get('/payments/receipts', {
    params: buildReceiptParams(filters),
  })
  return {
    ...response.data,
    data: {
      receipts: response.data.data.map(normalizeReceipt),
    },
  }
}

export async function getReceipt(receiptId) {
  const response = await apiClient.get(`/payments/receipts/${receiptId}`)
  return {
    ...response.data,
    data: normalizeReceipt(response.data.data),
  }
}

function filenameFromDisposition(value, receiptId) {
  const encoded = String(value || '').match(/filename\*=UTF-8''([^;]+)/i)
  if (encoded) return decodeURIComponent(encoded[1])
  const plain = String(value || '').match(/filename="?([^";]+)"?/i)
  return plain?.[1] || `receipt-${receiptId}.pdf`
}

export async function downloadReceipt(receiptId) {
  const response = await apiClient.get(
    `/payments/receipts/${receiptId}/download`,
    { responseType: 'blob' },
  )
  return {
    blob: response.data,
    filename: filenameFromDisposition(
      response.headers?.['content-disposition'],
      receiptId,
    ),
  }
}

export async function createWhatsAppReminder(feeRecordId, payload = {}) {
  const response = await apiClient.post(
    `/payments/${feeRecordId}/reminders`,
    {
      channel: 'whatsapp',
      message: payload.message?.trim() || undefined,
    },
  )
  return response.data
}
