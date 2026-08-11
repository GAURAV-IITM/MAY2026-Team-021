import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import LibraryStatusModal from '../../src/components/superadmin/LibraryStatusModal.vue'


describe('LibraryStatusModal', () => {
  it('requires a reason and emits an auditable suspension command', async () => {
    const wrapper = mount(LibraryStatusModal, {
      props: {
        isOpen: true,
        targetStatus: 'suspended',
        library: { name: 'Central Library', updatedAt: '2026-08-03T10:00:00Z' },
      },
    })
    await wrapper.get('#library-status-form').trigger('submit')
    expect(wrapper.emitted('confirm')).toBeUndefined()
    expect(wrapper.text()).toContain('Enter a clear suspension reason')

    await wrapper.get('#suspension-reason').setValue('Policy review')
    await wrapper.get('#library-status-form').trigger('submit')
    expect(wrapper.emitted('confirm')[0][0]).toEqual({
      status: 'suspended',
      reason: 'Policy review',
      expectedUpdatedAt: '2026-08-03T10:00:00Z',
    })
  })

  it('activates without a reason and keeps server conflicts visible', async () => {
    const wrapper = mount(LibraryStatusModal, {
      props: {
        isOpen: true,
        targetStatus: 'active',
        library: { name: 'Central Library', updatedAt: '2026-08-03T10:00:00Z' },
        serverError: 'This library changed after it was opened.',
      },
    })
    expect(wrapper.text()).toContain('changed after it was opened')
    expect(wrapper.find('#suspension-reason').exists()).toBe(false)
    await wrapper.get('#library-status-form').trigger('submit')
    expect(wrapper.emitted('confirm')[0][0].status).toBe('active')
    expect(wrapper.emitted('confirm')[0][0].reason).toBeNull()
  })
})
