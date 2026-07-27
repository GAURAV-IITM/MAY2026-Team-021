import { paymentMock } from '../mocks/paymentMock.js'

// Receipt APIs are intentionally outside Phase 3. This isolated adapter keeps
// the existing receipt page usable without mixing mock data into payments.
function clone(value) {
  return structuredClone(value)
}

function buildReceipt(payment) {
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
    generatedAt: payment.updatedAt,
    downloadStatus: 'placeholder',
  }
}

export async function getReceipts(filters = {}) {
  const search = String(filters.search || '').trim().toLowerCase()
  const month = String(filters.month || '').trim()
  const receipts = paymentMock
    .filter((payment) => payment.status === 'paid')
    .filter((payment) => !month || payment.month === month)
    .filter((payment) => {
      if (!search) return true
      return [payment.studentName, payment.receiptNumber, payment.transactionId]
        .some((value) => String(value || '').toLowerCase().includes(search))
    })
    .map(buildReceipt)

  return {
    message: 'Mock receipts fetched successfully.',
    data: { receipts: clone(receipts) },
    meta: { source: 'isolated-receipt-mock' },
  }
}
