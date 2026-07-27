import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import WhatsAppReminderDialog from '../../src/components/payment/WhatsAppReminderDialog.vue'

const payment = {
  id: 'fee-id',
  studentName: 'Aarav Sharma',
  studentPhone: '+91 99999 99999',
  month: '2026-07',
  amount: 1000,
  paidAmount: 400,
  balanceAmount: 600,
  dueDate: '2026-07-10',
  status: 'partially_paid',
}

describe('WhatsAppReminderDialog', () => {
  it('shows the outstanding balance, due date, phone, and honest guidance', () => {
    const wrapper = mount(WhatsAppReminderDialog, {
      props: { isOpen: true, payment },
    })

    expect(wrapper.text()).toContain('Aarav Sharma')
    expect(wrapper.text()).toContain('₹600.00')
    expect(wrapper.text()).toContain('+91 99999 99999')
    expect(wrapper.text()).toContain('10 Jul 2026')
    expect(wrapper.text()).not.toContain('₹1,000.00')
    expect(wrapper.text()).not.toContain('sent successfully')
    expect(wrapper.text()).not.toContain('delivered successfully')
  })

  it('retains an edited message after a server error and disables double submit', async () => {
    const wrapper = mount(WhatsAppReminderDialog, {
      props: { isOpen: true, payment },
    })
    const textarea = wrapper.get('#whatsapp-reminder-message')
    await textarea.setValue('Please review the latest outstanding balance.')
    await wrapper.get('button.btn--primary').trigger('click')
    expect(wrapper.emitted('submit')[0][0]).toEqual({
      message: 'Please review the latest outstanding balance.',
    })

    await wrapper.setProps({
      submissionError: {
        message: 'Add a country code to the student phone number.',
        requestId: 'reminder-request-422',
      },
    })
    expect(textarea.element.value).toBe(
      'Please review the latest outstanding balance.',
    )
    expect(wrapper.text()).toContain('reminder-request-422')

    await wrapper.setProps({ isSubmitting: true })
    expect(wrapper.get('button.btn--primary').attributes('disabled')).toBeDefined()
    await wrapper.get('button.btn--secondary').trigger('click')
    expect(wrapper.emitted('close')).toBeUndefined()
  })
})
