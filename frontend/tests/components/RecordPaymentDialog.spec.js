import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import RecordPaymentDialog from '../../src/components/payment/RecordPaymentDialog.vue'

const payment = {
  id: 'fee-id',
  studentName: 'Aarav Sharma',
  month: '2026-07',
  totalAmount: 1200,
  paidAmount: 400,
  balanceAmount: 800,
  status: 'partially_paid',
}

function mountDialog(overrides = {}) {
  return mount(RecordPaymentDialog, {
    props: {
      isOpen: true,
      payment,
      ...overrides,
    },
  })
}

describe('RecordPaymentDialog', () => {
  it('defaults to the remaining balance and emits transaction facts', async () => {
    const wrapper = mountDialog()
    expect(wrapper.get('#payment-amount').element.value).toBe('800.00')

    await wrapper.get('#payment-method').setValue('upi')
    await wrapper.get('#payment-reference').setValue('UPI-001')
    await wrapper.get('button.btn--primary').trigger('click')

    const payload = wrapper.emitted('confirm')[0][0]
    expect(payload.amount).toBe('800.00')
    expect(payload.method).toBe('upi')
    expect(payload.referenceNumber).toBe('UPI-001')
    expect(payload).not.toHaveProperty('status')
    expect(payload.paidAt).toMatch(/T/)
  })

  it('shows partial-payment guidance and rejects overpayment', async () => {
    const wrapper = mountDialog()
    await wrapper.get('#payment-amount').setValue('300')
    expect(wrapper.text()).toContain('partial payment')

    await wrapper.get('#payment-amount').setValue('900')
    await wrapper.get('#payment-method').setValue('cash')
    await wrapper.get('button.btn--primary').trigger('click')
    expect(wrapper.emitted('confirm')).toBeUndefined()
    expect(wrapper.text()).toContain('Amount cannot exceed')
  })

  it('keeps the dialog open while submission is in progress', async () => {
    const wrapper = mountDialog({ isSubmitting: true })
    await wrapper.get('button.btn--secondary').trigger('click')
    expect(wrapper.emitted('close')).toBeUndefined()
  })
})
