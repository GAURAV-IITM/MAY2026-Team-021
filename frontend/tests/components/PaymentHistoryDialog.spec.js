import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import PaymentHistoryDialog from '../../src/components/payment/PaymentHistoryDialog.vue'

describe('PaymentHistoryDialog', () => {
  it('renders every transaction with its actor and reference', () => {
    const wrapper = mount(PaymentHistoryDialog, {
      props: {
        isOpen: true,
        payment: {
          studentName: 'Aarav Sharma',
          month: '2026-07',
          totalAmount: 1000,
          paidAmount: 1000,
          transactions: [
            {
              id: 'second',
              amount: 600,
              method: 'cash',
              paidAt: '2026-07-20T10:00:00Z',
              referenceNumber: 'CASH-002',
              notes: 'Final payment',
              recordedBy: { name: 'Library Owner' },
            },
            {
              id: 'first',
              amount: 400,
              method: 'upi',
              paidAt: '2026-07-10T10:00:00Z',
              referenceNumber: 'UPI-001',
              notes: 'First instalment',
              recordedBy: { name: 'Staff Member' },
            },
          ],
        },
      },
    })

    expect(wrapper.text()).toContain('₹600.00')
    expect(wrapper.text()).toContain('₹400.00')
    expect(wrapper.text()).toContain('CASH-002')
    expect(wrapper.text()).toContain('UPI-001')
    expect(wrapper.text()).toContain('Library Owner')
    expect(wrapper.text()).toContain('Staff Member')
  })
})
