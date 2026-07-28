import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import AnnouncementFormModal from '../../src/components/announcement/AnnouncementFormModal.vue'


const categories = [{ value: 'general', label: 'General' }]
const audiences = [{ value: 'all_students', label: 'All students' }]


function mountModal(overrides = {}) {
  return mount(AnnouncementFormModal, {
    props: {
      isOpen: true,
      categories,
      audiences,
      ...overrides,
    },
  })
}


describe('AnnouncementFormModal', () => {
  it('emits a future scheduled lifecycle payload with UTC dates', async () => {
    const wrapper = mountModal()
    await wrapper.get('#announcement-title').setValue('Exam schedule update')
    await wrapper.get('#announcement-body').setValue(
      'The library schedule will change during the examination period.',
    )
    await wrapper.get('input[value="scheduled"]').setValue()
    const future = new Date(Date.now() + 86_400_000)
    const local = new Date(
      future.getTime() - future.getTimezoneOffset() * 60_000,
    ).toISOString().slice(0, 16)
    await wrapper.get('#announcement-publish-at').setValue(local)
    await wrapper.get('button.btn--primary').trigger('click')

    const payload = wrapper.emitted('save')[0][0]
    expect(payload.status).toBe('scheduled')
    expect(payload.scheduledAt).toMatch(/Z$/)
    expect(payload.audience).toBe('all_students')
    expect(payload).not.toHaveProperty('libraryId')
    expect(payload).not.toHaveProperty('publishedAt')
  })

  it('keeps server errors visible and does not offer publish-now while editing', () => {
    const wrapper = mountModal({
      mode: 'edit',
      serverError: 'This announcement changed after it was opened.',
      announcement: {
        id: 'announcement-id',
        title: 'Editable announcement',
        body: 'This scheduled content is still eligible for editing.',
        category: 'general',
        audience: 'all_students',
        priority: 'normal',
        status: 'draft',
        updatedAt: '2026-07-28T10:00:00Z',
      },
    })

    expect(wrapper.text()).toContain('changed after it was opened')
    expect(wrapper.find('input[value="published"]').exists()).toBe(false)
  })
})
