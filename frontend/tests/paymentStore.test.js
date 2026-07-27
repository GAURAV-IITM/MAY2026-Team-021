import assert from 'node:assert/strict'
import test from 'node:test'

import { createPinia, setActivePinia } from 'pinia'

import apiClient from '../src/api/axios.js'
import { usePaymentStore } from '../src/stores/paymentStore.js'

function response(config, studentName) {
  return {
    config,
    headers: {},
    status: 200,
    statusText: 'OK',
    data: {
      message: 'Payments fetched.',
      data: [
        {
          id: `${studentName}-fee`,
          student: {
            id: `${studentName}-id`,
            enrollmentNumber: 'STU-001',
            name: studentName,
            email: `${studentName}@example.com`,
          },
          month: '2026-07',
          dueDate: '2026-07-10',
          baseAmount: '100.00',
          discountAmount: '0.00',
          lateFeeAmount: '0.00',
          totalAmount: '100.00',
          paidAmount: '0.00',
          balanceAmount: '100.00',
          status: 'unpaid',
          notes: null,
          latestTransaction: null,
          transactions: [],
          createdAt: '2026-07-01T00:00:00Z',
          updatedAt: '2026-07-01T00:00:00Z',
        },
      ],
      meta: { page: 1, pageSize: 10, totalItems: 1, totalPages: 1 },
      summary: {
        totalRecords: 1,
        unpaidCount: 1,
        partiallyPaidCount: 0,
        paidCount: 0,
        totalBilledAmount: '100.00',
        totalCollectedAmount: '0.00',
        totalPendingAmount: '100.00',
      },
    },
  }
}

test.beforeEach(() => {
  setActivePinia(createPinia())
})

test('defaults the monthly view to the current billing month', () => {
  const store = usePaymentStore()
  const now = new Date()
  const expected = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  assert.equal(store.paymentFilters.month, expected)
})

test('keeps the latest filtered response when requests finish out of order', async () => {
  const pending = []
  apiClient.defaults.adapter = (config) =>
    new Promise((resolve) => pending.push({ config, resolve }))

  const store = usePaymentStore()
  const first = store.fetchPayments({ search: 'first', month: '2026-07' })
  await new Promise((resolve) => setImmediate(resolve))
  const second = store.fetchPayments({ search: 'second', month: '2026-07' })
  await new Promise((resolve) => setImmediate(resolve))

  pending[1].resolve(response(pending[1].config, 'Second Student'))
  await second
  pending[0].resolve(response(pending[0].config, 'Stale Student'))
  await first

  assert.equal(store.payments[0].studentName, 'Second Student')
  assert.equal(store.isLoading, false)
  assert.equal(store.totalPendingAmount, 100)
})
