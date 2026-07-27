import assert from 'node:assert/strict'
import test from 'node:test'

import { AxiosError } from 'axios'

import apiClient from '../src/api/axios.js'
import {
  buildPaymentParams,
  generateMonthlyPayments,
  getPayments,
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
