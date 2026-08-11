import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import LibraryFormModal from '../../src/components/superadmin/LibraryFormModal.vue'


describe('LibraryFormModal', () => {
  it('creates a validated library without seat, status, or credential fields', async () => {
    const wrapper = mount(LibraryFormModal, {
      props: {
        isOpen: true,
        owners: [{ id: 'owner-id', name: 'Eligible Owner', email: 'owner@example.com' }],
      },
    })
    await wrapper.get('#library-name').setValue('Central Study Library')
    await wrapper.get('#library-code').setValue('csl')
    await wrapper.get('#library-email').setValue('library@example.com')
    await wrapper.get('#library-phone').setValue('+91 9876543210')
    await wrapper.get('#library-owner').setValue('owner-id')
    await wrapper.get('#library-form').trigger('submit')

    const payload = wrapper.emitted('save')[0][0]
    expect(payload.code).toBe('CSL')
    expect(payload.ownerId).toBe('owner-id')
    expect(payload.timezone).toBe('Asia/Kolkata')
    expect(payload).not.toHaveProperty('seatCount')
    expect(payload).not.toHaveProperty('status')
    expect(payload).not.toHaveProperty('password')
  })

  it('keeps code immutable and includes stale-write metadata while editing', async () => {
    const wrapper = mount(LibraryFormModal, {
      props: {
        isOpen: true,
        mode: 'edit',
        library: {
          id: 'library-id',
          name: 'Existing Library',
          code: 'EXISTING',
          contactEmail: 'existing@example.com',
          timezone: 'Asia/Kolkata',
          updatedAt: '2026-08-03T10:00:00Z',
        },
        serverError: 'A library with this name already exists.',
      },
    })
    expect(wrapper.get('#library-code').attributes('disabled')).toBeDefined()
    expect(wrapper.text()).toContain('already exists')
    await wrapper.get('#library-name').setValue('Updated Library')
    await wrapper.get('#library-form').trigger('submit')

    const payload = wrapper.emitted('save')[0][0]
    expect(payload.expectedUpdatedAt).toBe('2026-08-03T10:00:00Z')
    expect(payload).not.toHaveProperty('code')
    expect(payload).not.toHaveProperty('ownerId')
  })
})
