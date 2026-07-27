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

function receiptResponse(config, receiptNumber) {
  return {
    config,
    headers: {},
    status: 200,
    statusText: 'OK',
    data: {
      message: 'Receipts fetched.',
      data: [
        {
          id: `${receiptNumber}-id`,
          receiptNumber,
          student: {
            id: 'student-id',
            name: 'Aarav Sharma',
            enrollmentNumber: 'STU-001',
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
        },
      ],
      meta: { page: 1, pageSize: 10, totalItems: 1, totalPages: 1 },
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

test('keeps the latest receipt list and clears stale preview data', async () => {
  const pending = []
  apiClient.defaults.adapter = (config) =>
    new Promise((resolve) => pending.push({ config, resolve }))

  const store = usePaymentStore()
  const first = store.fetchReceipts({ search: 'first' })
  await new Promise((resolve) => setImmediate(resolve))
  const second = store.fetchReceipts({ search: 'second' })
  await new Promise((resolve) => setImmediate(resolve))

  pending[1].resolve(receiptResponse(pending[1].config, 'REC-SECOND'))
  await second
  pending[0].resolve(receiptResponse(pending[0].config, 'REC-STALE'))
  await first

  assert.equal(store.receipts[0].receiptNumber, 'REC-SECOND')
  assert.equal(store.isReceiptLoading, false)

  let resolvePreview
  apiClient.defaults.adapter = (config) =>
    new Promise((resolve) => {
      resolvePreview = () =>
        resolve({
          ...receiptResponse(config, 'REC-DETAIL'),
          data: {
            message: 'Receipt fetched.',
            data: {
              ...receiptResponse(config, 'REC-DETAIL').data.data[0],
              library: {
                id: 'library-id',
                name: 'Library',
                address: null,
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
                referenceNumber: null,
                paidAt: '2026-07-27T10:00:00Z',
                recordedBy: null,
                notes: null,
              },
            },
          },
        })
    })
  const preview = store.fetchReceiptDetail('receipt-id')
  assert.equal(store.selectedReceipt, null)
  assert.equal(store.isReceiptPreviewLoading, true)
  await new Promise((resolve) => setImmediate(resolve))
  resolvePreview()
  await preview
  assert.equal(store.selectedReceipt.receiptNumber, 'REC-DETAIL')
  assert.equal(store.isReceiptPreviewLoading, false)
})

test('prevents duplicate active reminder requests and keeps honest outcome', async () => {
  let resolveRequest
  let requestCount = 0
  apiClient.defaults.adapter = (config) => {
    requestCount += 1
    return new Promise((resolve) => {
      resolveRequest = () =>
        resolve({
          config,
          headers: {},
          status: 201,
          statusText: 'Created',
          data: {
            message: 'Reminder attempt recorded.',
            data: {
              reminder: {
                id: 'reminder-id',
                outcome: 'link_generated',
                message: 'Reminder',
              },
              whatsappUrl: 'https://wa.me/919999999999?text=Reminder',
            },
          },
        })
    })
  }

  const store = usePaymentStore()
  const first = store.createWhatsAppReminder('fee-id')
  const duplicate = await store.createWhatsAppReminder('fee-id')
  assert.equal(duplicate, null)
  assert.equal(requestCount, 1)
  assert.equal(store.isReminderSubmitting, true)

  resolveRequest()
  await first
  assert.equal(store.isReminderSubmitting, false)
  assert.equal(store.selectedReminder.reminder.outcome, 'link_generated')
  assert.equal('delivered' in store.selectedReminder.reminder, false)
})
