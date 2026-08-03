import assert from 'node:assert/strict'
import test from 'node:test'

import { AxiosError } from 'axios'

import apiClient from '../src/api/axios.js'
import {
  buildReceiptParams,
  buildPaymentParams,
  createWhatsAppReminder,
  downloadReceipt,
  generateMonthlyPayments,
  getPayments,
  getReceipt,
  getReceipts,
  recordPayment,
} from '../src/services/paymentService.js'

function response(config, data, status = 200) {
  return {
    config,
    data,
    headers: {},
    status,
    statusText: status === 200 ? 'OK' : 'Unprocessable Content',
  }
}

function apiPayment(overrides = {}) {
  return {
    id: 'fee-id',
    student: {
      id: 'student-id',
      enrollmentNumber: 'STU-00001',
      name: 'Aarav Sharma',
      email: 'aarav@example.com',
    },
    month: '2026-07',
    dueDate: '2026-07-10',
    baseAmount: '1200.00',
    discountAmount: '0.00',
    lateFeeAmount: '0.00',
    totalAmount: '1200.00',
    paidAmount: '400.00',
    balanceAmount: '800.00',
    status: 'partially_paid',
    notes: null,
    latestTransaction: {
      id: 'transaction-id',
      amount: '400.00',
      method: 'upi',
      status: 'completed',
      referenceNumber: 'UPI-001',
      paidAt: '2026-07-27T10:00:00Z',
      notes: null,
      recordedBy: { id: 'owner-id', name: 'Owner' },
      createdAt: '2026-07-27T10:00:00Z',
    },
    transactions: [],
    createdAt: '2026-07-01T00:00:00Z',
    updatedAt: '2026-07-27T10:00:00Z',
    ...overrides,
  }
}

function apiReceipt(overrides = {}) {
  return {
    id: 'receipt-id',
    receiptNumber: 'REC-2026-ABC',
    student: {
      id: 'student-id',
      name: 'Aarav Sharma',
      enrollmentNumber: 'STU-00001',
    },
    feeRecordId: 'fee-id',
    paymentTransactionId: 'transaction-id',
    billingMonth: '2026-07',
    amount: '400.00',
    paymentMethod: 'upi',
    paymentReference: 'UPI-001',
    paidAt: '2026-07-27T10:00:00Z',
    issuedAt: '2026-07-27T10:00:01Z',
    status: 'issued',
    currency: 'INR',
    downloadAvailable: true,
    ...overrides,
  }
}

test('maps server-side list filters and calculated payment fields', async () => {
  assert.deepEqual(
    buildPaymentParams({
      month: '2026-07',
      status: 'partially_paid',
      search: 'Aarav',
      page: 2,
      pageSize: 10,
    }),
    {
      page: 2,
      pageSize: 10,
      search: 'Aarav',
      sortBy: 'month',
      sortOrder: 'desc',
      month: '2026-07',
      status: 'partially_paid',
      studentId: undefined,
      dueDateFrom: undefined,
      dueDateTo: undefined,
      hasTransactions: undefined,
    },
  )

  let requestConfig
  apiClient.defaults.adapter = async (config) => {
    requestConfig = config
    return response(config, {
      message: 'Payments fetched.',
      data: [apiPayment()],
      meta: { page: 2, pageSize: 10, totalItems: 1, totalPages: 1 },
      summary: { totalRecords: 1 },
    })
  }
  const result = await getPayments({
    month: '2026-07',
    status: 'partially_paid',
    page: 2,
    pageSize: 10,
  })

  assert.equal(requestConfig.url, '/payments')
  assert.equal(requestConfig.params.month, '2026-07')
  assert.equal(result.data.payments[0].studentName, 'Aarav Sharma')
  assert.equal(result.data.payments[0].amount, 1200)
  assert.equal(result.data.payments[0].paidAmount, 400)
  assert.equal(result.data.payments[0].balanceAmount, 800)
  assert.equal(result.data.payments[0].transactionId, 'UPI-001')
})

test('monthly generation sends only the selected month', async () => {
  let requestConfig
  apiClient.defaults.adapter = async (config) => {
    requestConfig = config
    return response(
      config,
      {
        message: 'Generated.',
        data: {
          month: '2026-07',
          createdCount: 0,
          existingCount: 1,
          skippedCount: 0,
          activeStudentCount: 1,
          eligibleStudentCount: 1,
          createdPayments: [],
          skippedStudents: [],
        },
      },
      201,
    )
  }

  await generateMonthlyPayments('2026-07')
  assert.equal(requestConfig.url, '/payments/monthly-generation')
  assert.deepEqual(JSON.parse(requestConfig.data), { month: '2026-07' })
})

test('record payment sends transaction facts and preserves backend errors', async () => {
  let requestConfig
  apiClient.defaults.adapter = async (config) => {
    requestConfig = config
    return response(
      config,
      {
        message: 'Recorded.',
        data: {
          payment: apiPayment({ paidAmount: '1200.00', balanceAmount: '0.00' }),
          transaction: apiPayment().latestTransaction,
          receipt: apiReceipt(),
        },
      },
      201,
    )
  }

  await recordPayment('fee-id', {
    amount: '800.00',
    method: 'cash',
    paidAt: '2026-07-27T10:30:00Z',
    referenceNumber: 'CASH-001',
    notes: 'Final payment',
    status: 'paid',
  })
  assert.equal(requestConfig.url, '/payments/fee-id/transactions')
  assert.deepEqual(JSON.parse(requestConfig.data), {
    amount: '800.00',
    method: 'cash',
    paidAt: '2026-07-27T10:30:00Z',
    referenceNumber: 'CASH-001',
    notes: 'Final payment',
  })

  apiClient.defaults.adapter = (config) => {
    const errorResponse = response(
      config,
      {
        error: {
          code: 'PAYMENT_AMOUNT_EXCEEDS_BALANCE',
          message: 'Payment amount cannot exceed the remaining balance.',
          details: { remainingBalance: '50.00' },
        },
        requestId: 'payment-request-422',
      },
      422,
    )
    return Promise.reject(
      new AxiosError(
        'Validation failed',
        AxiosError.ERR_BAD_REQUEST,
        config,
        null,
        errorResponse,
      ),
    )
  }

  await assert.rejects(
    recordPayment('fee-id', { amount: '60.00', method: 'cash' }),
    (error) => {
      assert.equal(
        error.response.data.error.code,
        'PAYMENT_AMOUNT_EXCEEDS_BALANCE',
      )
      assert.equal(error.response.data.requestId, 'payment-request-422')
      return true
    },
  )
})

test('maps receipt filters, list items, and snapshot detail requests', async () => {
  assert.deepEqual(
    buildReceiptParams({
      search: 'Aarav',
      billingMonth: '2026-07',
      paymentMethod: 'upi',
      status: 'issued',
      page: 2,
      pageSize: 10,
    }),
    {
      page: 2,
      pageSize: 10,
      search: 'Aarav',
      sortBy: 'issuedAt',
      sortOrder: 'desc',
      billingMonth: '2026-07',
      paymentMethod: 'upi',
      studentId: undefined,
      status: 'issued',
      dateFrom: undefined,
      dateTo: undefined,
    },
  )

  const requests = []
  apiClient.defaults.adapter = async (config) => {
    requests.push(config)
    if (config.url.endsWith('/receipt-id')) {
      return response(config, {
        message: 'Receipt fetched.',
        data: {
          ...apiReceipt(),
          library: {
            id: 'library-id',
            name: 'Central Library',
            address: 'Reading Lane',
            phone: null,
            email: 'library@example.com',
          },
          fee: {
            id: 'fee-id',
            billingMonth: '2026-07',
            dueDate: '2026-07-10',
            totalAmount: '1000.00',
            previouslyPaidAmount: '0.00',
            paymentAmount: '400.00',
            remainingBalance: '600.00',
            paymentStatus: 'partially_paid',
          },
          payment: {
            id: 'transaction-id',
            amount: '400.00',
            method: 'upi',
            referenceNumber: 'UPI-001',
            paidAt: '2026-07-27T10:00:00Z',
            recordedBy: { id: 'owner-id', name: 'Owner' },
            notes: null,
          },
        },
      })
    }
    return response(config, {
      message: 'Receipts fetched.',
      data: [apiReceipt()],
      meta: { page: 2, pageSize: 10, totalItems: 1, totalPages: 1 },
    })
  }

  const listed = await getReceipts({
    billingMonth: '2026-07',
    page: 2,
    pageSize: 10,
  })
  assert.equal(requests[0].url, '/payments/receipts')
  assert.equal(requests[0].params.billingMonth, '2026-07')
  assert.equal(listed.data.receipts[0].studentName, 'Aarav Sharma')
  assert.equal(listed.data.receipts[0].amount, 400)

  const detail = await getReceipt('receipt-id')
  assert.equal(requests[1].url, '/payments/receipts/receipt-id')
  assert.equal(detail.data.remainingBalance, 600)
  assert.equal(detail.data.paymentReference, 'UPI-001')
})

test('requests an authenticated receipt blob and maps reminder payload', async () => {
  const requests = []
  const pdf = new Blob(['receipt'], { type: 'application/pdf' })
  apiClient.defaults.adapter = async (config) => {
    requests.push(config)
    if (config.url.endsWith('/download')) {
      return {
        ...response(config, pdf),
        headers: {
          'content-disposition': 'attachment; filename="receipt-REC-1.pdf"',
        },
      }
    }
    return response(
      config,
      {
        message: 'Reminder attempt recorded.',
        data: {
          reminder: {
            id: 'reminder-id',
            outcome: 'link_generated',
          },
          whatsappUrl: 'https://wa.me/919999999999?text=Hello',
        },
      },
      201,
    )
  }

  const downloaded = await downloadReceipt('receipt-id')
  assert.equal(requests[0].responseType, 'blob')
  assert.equal(
    requests[0].url,
    '/payments/receipts/receipt-id/download',
  )
  assert.equal(downloaded.filename, 'receipt-REC-1.pdf')
  assert.equal(downloaded.blob, pdf)

  const reminder = await createWhatsAppReminder('fee-id', {
    message: 'Please review your balance.',
  })
  assert.equal(requests[1].url, '/payments/fee-id/reminders')
  assert.deepEqual(JSON.parse(requests[1].data), {
    channel: 'whatsapp',
    message: 'Please review your balance.',
  })
  assert.equal(reminder.data.reminder.outcome, 'link_generated')
  assert.equal('delivered' in reminder.data.reminder, false)
})
