import apiClient from '../api/axios.js'

function normalizeTransaction(transaction) {
  if (!transaction) return null

  return {
    ...transaction,
    transactionId: transaction.referenceNumber || transaction.id,
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
