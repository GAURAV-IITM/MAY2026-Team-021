import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'

import apiClient from '../../src/api/axios.js'
import Dashboard from '../../src/pages/superadmin/Dashboard.vue'

function dashboardPayload(overrides = {}) {
  return {
    message: 'Dashboard fetched.',
    data: {
      totals: {
        totalLibraries: 0,
        activeLibraries: 0,
        pendingLibraries: 0,
        suspendedLibraries: 0,
        totalOwners: 0,
        activeOwners: 0,
        suspendedOwners: 0,
        invitedOwners: 0,
        totalStudents: 0,
        totalSeats: 0,
        averageOccupancy: 0,
      },
      libraryStatus: [
        { status: 'pending', count: 0 },
        { status: 'active', count: 0 },
        { status: 'suspended', count: 0 },
      ],
      trend: [],
      topLibraries: [],
      recentActivity: [],
      range: { startMonth: '2026-02', endMonth: '2026-08', timezone: 'UTC' },
      lastUpdated: '2026-08-04T10:00:00Z',
      ...overrides,
    },
  }
}

function response(config, data) {
  return { config, data, headers: {}, status: 200, statusText: 'OK' }
}

function mountDashboard() {
  return mount(Dashboard, {
    global: {
      plugins: [createPinia()],
      stubs: {
        RouterLink: { template: '<a><slot /></a>' },
      },
    },
  })
}

describe('Super Admin Dashboard', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('renders zero metrics and the empty platform state', async () => {
    apiClient.defaults.adapter = async (config) => response(config, dashboardPayload())
    const wrapper = mountDashboard()
    await flushPromises()

    expect(wrapper.text()).toContain('Registered Libraries')
    expect(wrapper.text()).toContain('No libraries registered yet')
    expect(wrapper.text()).toContain(
      'Platform metrics will appear after the first library is created.',
    )
  })

  it('renders API metrics, safe activity, status data, and empty rankings', async () => {
    apiClient.defaults.adapter = async (config) =>
      response(
        config,
        dashboardPayload({
          totals: {
            totalLibraries: 2,
            activeLibraries: 1,
            pendingLibraries: 1,
            suspendedLibraries: 0,
            totalOwners: 1,
            activeOwners: 1,
            suspendedOwners: 0,
            invitedOwners: 1,
            totalStudents: 23,
            totalSeats: 30,
            averageOccupancy: 40,
          },
          recentActivity: [
            {
              id: 'audit-id',
              action: 'platform.library.created',
              entityType: 'library',
              entityId: 'library-id',
              description: 'Library created',
              category: 'library',
              actor: { id: 'admin-id', name: 'Platform Admin' },
              createdAt: '2026-08-04T10:00:00Z',
            },
          ],
        }),
      )
    const wrapper = mountDashboard()
    await flushPromises()

    expect(wrapper.text()).toContain('23')
    expect(wrapper.text()).toContain('40% current seat utilization')
    expect(wrapper.text()).toContain('Library created')
    expect(wrapper.text()).toContain('Platform Admin')
    expect(wrapper.text()).toContain('No active libraries to rank.')
  })

  it('shows the server error and correlation ID for retry support', async () => {
    apiClient.defaults.adapter = async (config) => {
      const error = new Error('Dashboard unavailable')
      error.config = config
      error.response = {
        status: 500,
        headers: { 'x-request-id': 'dashboard-ui-request' },
        data: {
          error: { code: 'INTERNAL_SERVER_ERROR', message: 'Dashboard unavailable' },
          requestId: 'dashboard-ui-request',
        },
      }
      throw error
    }
    const wrapper = mountDashboard()
    await flushPromises()

    expect(wrapper.text()).toContain('Unable to load the platform dashboard.')
    expect(wrapper.text()).toContain('dashboard-ui-request')
    expect(wrapper.findAll('button').some((button) => button.text().includes('Retry'))).toBe(true)
  })
})
