import { flushPromises, mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { describe, expect, it } from 'vitest'

import apiClient from '../../src/api/axios.js'
import Settings from '../../src/pages/superadmin/Settings.vue'


function payload(overrides = {}) {
  return {
    message: 'Settings fetched.',
    data: {
      settings: {
        platformName: 'Smart Library API',
        allowLibraryRegistrations: true,
        sessionTimeoutMinutes: 30,
        defaultTimezone: 'Asia/Kolkata',
        ...overrides.settings,
      },
      definitions: [],
      version: overrides.version ?? 0,
      updatedAt: overrides.updatedAt ?? null,
    },
  }
}


function response(config, data) {
  return { config, data, headers: {}, status: 200, statusText: 'OK' }
}


function mountSettings() {
  return mount(Settings, { global: { plugins: [createPinia()] } })
}


describe('Super Admin Platform Settings', () => {
  it('renders only known controls and supports dirty reset state', async () => {
    apiClient.defaults.adapter = async (config) => response(config, payload())
    const wrapper = mountSettings()
    await flushPromises()

    expect(wrapper.get('#platform-name').attributes('readonly')).toBeDefined()
    expect(wrapper.get('#platform-name').element.value).toBe('Smart Library API')
    expect(wrapper.text()).not.toContain('Maintenance mode')
    expect(wrapper.text()).not.toContain('Support Email')
    expect(wrapper.text()).not.toContain('Weekly platform summary')

    await wrapper.get('#session-timeout').setValue('90')
    expect(wrapper.text()).toContain('Discard Changes')
    const discard = wrapper
      .findAll('button')
      .find((button) => button.text().includes('Discard Changes'))
    expect(discard.attributes('disabled')).toBeUndefined()
    await discard.trigger('click')
    expect(wrapper.get('#session-timeout').element.value).toBe('30')
  })

  it('validates fields and saves typed settings with the loaded version', async () => {
    const requests = []
    apiClient.defaults.adapter = async (config) => {
      requests.push(config)
      if (config.method === 'get') return response(config, payload())
      return response(
        config,
        payload({
          settings: { sessionTimeoutMinutes: 90, defaultTimezone: 'UTC' },
          version: 1,
          updatedAt: '2026-08-05T10:00:00Z',
        }),
      )
    }
    const wrapper = mountSettings()
    await flushPromises()

    await wrapper.get('#session-timeout').setValue('10')
    await wrapper.get('#session-timeout').trigger('blur')
    expect(wrapper.text()).toContain('Enter a whole number from 15 to 1440.')
    await wrapper.get('#session-timeout').setValue('90')
    await wrapper.get('#session-timeout').trigger('blur')
    await wrapper.get('#platform-timezone').setValue('UTC')
    await wrapper.get('#platform-settings-form').trigger('submit')
    await flushPromises()

    const body = JSON.parse(requests[1].data)
    expect(body).toEqual({
      version: 0,
      allowLibraryRegistrations: true,
      sessionTimeoutMinutes: 90,
      defaultTimezone: 'UTC',
    })
    expect(wrapper.text()).toContain('Platform settings saved successfully.')
    expect(wrapper.text()).toContain('Version 1')
  })

  it('requires confirmation before disabling public registration', async () => {
    const requests = []
    apiClient.defaults.adapter = async (config) => {
      requests.push(config)
      return response(
        config,
        config.method === 'get'
          ? payload()
          : payload({
              settings: { allowLibraryRegistrations: false },
              version: 1,
            }),
      )
    }
    const wrapper = mountSettings()
    await flushPromises()

    await wrapper.get('input[type="checkbox"]').setValue(false)
    await wrapper.get('#platform-settings-form').trigger('submit')
    expect(wrapper.text()).toContain('Disable library registrations?')
    expect(requests).toHaveLength(1)

    const confirm = wrapper
      .findAll('button')
      .find((button) => button.text().includes('Disable Registrations'))
    await confirm.trigger('click')
    await flushPromises()
    expect(requests).toHaveLength(2)
    expect(JSON.parse(requests[1].data).allowLibraryRegistrations).toBe(false)
  })
})
