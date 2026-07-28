import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import SeatRequestReviewModal from '../../src/components/student/SeatRequestReviewModal.vue'


const request = {
  id: 'request-id',
  status: 'pending',
  studentName: 'Aarav Sharma',
  enrollmentNumber: 'STU-001',
  currentSeatNumber: 'A-01',
  currentShiftName: 'Morning',
  preferredSeatNumber: 'B-02',
  preferredFloorName: 'First Floor',
  preferredShiftName: 'Evening',
  reason: 'Need a quieter seat for examination preparation.',
  submittedAt: '2026-08-02T09:30:00Z',
}


describe('SeatRequestReviewModal', () => {
  it('warns that approval does not transfer a seat', () => {
    const wrapper = mount(SeatRequestReviewModal, { props: { request } })
    expect(wrapper.text()).toContain('will not change the student’s seat or shift')
    expect(wrapper.text()).toContain('First Floor')
    expect(wrapper.text()).not.toContain('Seat transferred')
  })

  it('requires a rejection note and preserves it during submission errors', async () => {
    const wrapper = mount(SeatRequestReviewModal, { props: { request } })
    await wrapper.get('button.btn--danger').trigger('click')
    expect(wrapper.text()).toContain('Add a short reason')
    await wrapper.get('textarea').setValue('Preferred seat is unavailable.')
    await wrapper.setProps({
      serverError: 'This request has already been reviewed.',
      errorCode: 'SEAT_REQUEST_ALREADY_REVIEWED',
    })
    expect(wrapper.get('textarea').element.value).toBe(
      'Preferred seat is unavailable.',
    )
    expect(wrapper.text()).toContain('already reviewed by another user')
    expect(wrapper.find('button.btn--primary').exists()).toBe(false)
  })
})
