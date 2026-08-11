import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import OwnerAssignmentModal from '../../src/components/superadmin/OwnerAssignmentModal.vue'
import OwnerFormModal from '../../src/components/superadmin/OwnerFormModal.vue'
import OwnerStatusModal from '../../src/components/superadmin/OwnerStatusModal.vue'


describe('Owner management modals', () => {
  it('creates an invitation payload without password, role, or arbitrary status', async () => {
    const wrapper = mount(OwnerFormModal, {
      props: {
        isOpen: true,
        libraries: [{ id: 'library-id', name: 'Central Library' }],
      },
    })
    await wrapper.get('#owner-name').setValue('Aditi Owner')
    await wrapper.get('#owner-email').setValue('aditi@example.com')
    await wrapper.get('#owner-phone').setValue('+91 9876543210')
    await wrapper.get('#owner-library').setValue('library-id')
    await wrapper.get('#owner-form').trigger('submit')

    const payload = wrapper.emitted('save')[0][0]
    expect(payload).toEqual({
      name: 'Aditi Owner',
      email: 'aditi@example.com',
      phone: '+91 9876543210',
      libraryId: 'library-id',
    })
    expect(payload).not.toHaveProperty('password')
    expect(payload).not.toHaveProperty('role')
    expect(payload).not.toHaveProperty('status')
  })

  it('keeps email and assignment outside profile editing', async () => {
    const wrapper = mount(OwnerFormModal, {
      props: {
        isOpen: true,
        mode: 'edit',
        owner: {
          name: 'Existing Owner',
          email: 'existing@example.com',
          phone: '9876543210',
          libraryId: 'library-id',
        },
      },
    })
    expect(wrapper.get('#owner-email').attributes('readonly')).toBeDefined()
    expect(wrapper.find('#owner-library').exists()).toBe(false)
    await wrapper.get('#owner-name').setValue('Updated Owner')
    await wrapper.get('#owner-form').trigger('submit')

    expect(wrapper.emitted('save')[0][0]).toEqual({
      name: 'Updated Owner',
      phone: '9876543210',
    })
  })

  it('requires a suspension reason and emits explicit assignment changes', async () => {
    const status = mount(OwnerStatusModal, {
      props: { isOpen: true, status: 'suspended', owner: { name: 'Owner' } },
    })
    await status.get('#owner-status-form').trigger('submit')
    expect(status.emitted('save')).toBeUndefined()
    expect(status.text()).toContain('Enter a reason')
    await status.get('#owner-suspension-reason').setValue('Administrative review')
    await status.get('#owner-status-form').trigger('submit')
    expect(status.emitted('save')[0][0]).toEqual({
      status: 'suspended',
      reason: 'Administrative review',
    })

    const assignment = mount(OwnerAssignmentModal, {
      props: {
        isOpen: true,
        owner: { name: 'Owner', libraryName: 'Old Library' },
        libraries: [{ id: 'new-library', code: 'NEW', name: 'New Library' }],
      },
    })
    await assignment.get('#owner-assignment-library').setValue('new-library')
    await assignment.get('#owner-assignment-form').trigger('submit')
    expect(assignment.emitted('save')[0][0]).toEqual({ libraryId: 'new-library' })
    expect(assignment.text()).toContain('previous assignment will be closed')
  })
})
