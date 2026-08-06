import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'

import apiClient from '../../src/api/axios.js'
import Analytics from '../../src/pages/superadmin/Analytics.vue'

function dashboardPayload(overrides = {}) {
  return {
    message: 'Super Admin dashboard fetched successfully.',
    data: {
      totals: {
        totalLibraries: 4,
        activeLibraries: 3,
        pendingLibraries: 1,
        suspendedLibraries: 0,
        totalOwners: 5,
        activeOwners: 4,
        suspendedOwners: 0,
        invitedOwners: 1,
        totalStudents: 2048,
        totalSeats: 3200,
        averageOccupancy: 64,
      },
      libraryStatus: [],
      trend: [
        { month: '2026-07', libraries: 4, owners: 5, students: 2048 },
        { month: '2026-08', libraries: 4, owners: 5, students: 2100 },
      ],
      topLibraries: [
        {
          id: 'library-id',
          code: 'LIVE',
          name: 'Live Library',
          city: 'Pune',
          state: 'Maharashtra',
          studentCount: 500,
          seatCount: 800,
          occupiedSeatCount: 400,
          occupancyRate: 50,
        },
      ],
      recentActivity: [],
      range: { startMonth: '2026-07', endMonth: '2026-08', timezone: 'UTC' },
      lastUpdated: '2026-08-06T10:00:00Z',
      ...overrides,
    },
  }
}

function response(config, data) {
  return { config, data, headers: {}, status: 200, statusText: 'OK' }
}

function mountAnalytics() {
  return mount(Analytics, { global: { plugins: [createPinia()] } })
}

describe('Super Admin Analytics', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('loads live dashboard data and renders supported analytics', async () => {
    let request
    apiClient.defaults.adapter = async (config) => {
      request = config
      return response(config, dashboardPayload())
    }

    const wrapper = mountAnalytics()
    await flushPromises()

    expect(request.url).toBe('/platform/dashboard')
    expect(wrapper.text()).toContain('2,048')
    expect(wrapper.text()).toContain('Live Library')
    expect(wrapper.text()).toContain('Platform Owners')
    expect(wrapper.text()).not.toContain('Regional Reach')
    expect(wrapper.findAll('[role="tab"]').map((tab) => tab.text())).toEqual([
      'Students',
      'Libraries',
      'Owners',
    ])
  })

  it('shows the dashboard request error and request ID', async () => {
    apiClient.defaults.adapter = async (config) => {
      const error = new Error('Dashboard unavailable')
      error.config = config
      error.response = {
        status: 500,
        headers: { 'x-request-id': 'analytics-dashboard-request' },
        data: {
          error: { code: 'INTERNAL_SERVER_ERROR', message: 'Dashboard unavailable' },
          requestId: 'analytics-dashboard-request',
        },
      }
      throw error
    }

    const wrapper = mountAnalytics()
    await flushPromises()

    expect(wrapper.text()).toContain('Dashboard unavailable')
    expect(wrapper.text()).toContain('analytics-dashboard-request')
  })
})
