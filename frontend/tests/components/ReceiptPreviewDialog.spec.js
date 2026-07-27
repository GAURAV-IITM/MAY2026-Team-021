import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import ReceiptPreviewDialog from '../../src/components/payment/ReceiptPreviewDialog.vue'

const receipt = {
  id: 'receipt-id',
  receiptNumber: 'REC-2026-ABC',
  status: 'issued',
  issuedAt: '2026-07-27T10:00:01Z',
  currency: 'INR',
  library: {
    id: 'library-id',
    name: 'Central Study Library',
    address: '1 Reading Lane',
    phone: '+91 99999 99999',
    email: 'library@example.com',
  },
  student: {
    id: 'student-id',
    name: 'Aarav Sharma',
    enrollmentNumber: 'STU-00001',
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
    recordedBy: { id: 'owner-id', name: 'Library Owner' },
    notes: null,
  },
}

describe('ReceiptPreviewDialog', () => {
  it('renders the immutable receipt fields and emits download', async () => {
    const wrapper = mount(ReceiptPreviewDialog, {
      props: { isOpen: true, receipt },
    })

    expect(wrapper.text()).toContain('REC-2026-ABC')
    expect(wrapper.text()).toContain('Central Study Library')
    expect(wrapper.text()).toContain('Aarav Sharma')
    expect(wrapper.text()).toContain('STU-00001')
    expect(wrapper.text()).toContain('₹400.00')
    expect(wrapper.text()).toContain('₹600.00')
    expect(wrapper.text()).toContain('UPI-001')
    expect(wrapper.text()).toContain('Library Owner')

    await wrapper.get('button.btn--primary').trigger('click')
    expect(wrapper.emitted('download')).toHaveLength(1)
  })

  it('shows request errors and exposes retry without stale receipt data', async () => {
    const wrapper = mount(ReceiptPreviewDialog, {
      props: {
        isOpen: true,
        receipt: null,
        errorMessage: 'Receipt not found.',
        requestId: 'receipt-request-404',
      },
    })

    expect(wrapper.text()).toContain('Receipt not found.')
    expect(wrapper.text()).toContain('receipt-request-404')
    expect(wrapper.text()).not.toContain('Aarav Sharma')
    await wrapper.get('button.btn--sm').trigger('click')
    expect(wrapper.emitted('retry')).toHaveLength(1)
  })
})
