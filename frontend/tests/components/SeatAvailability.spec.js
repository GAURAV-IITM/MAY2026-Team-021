import { flushPromises, mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const serviceMocks = vi.hoisted(() => ({
  fetchShifts: vi.fn(),
  fetchFloors: vi.fn(),
  fetchSeatAvailability: vi.fn(),
  allocateSeat: vi.fn(),
  getStudents: vi.fn(),
}))

vi.mock('../../src/services/seatService.js', () => ({
  fetchShifts: serviceMocks.fetchShifts,
  fetchFloors: serviceMocks.fetchFloors,
  fetchSeatAvailability: serviceMocks.fetchSeatAvailability,
  allocateSeat: serviceMocks.allocateSeat,
}))

vi.mock('../../src/services/studentService.js', () => ({
  getStudents: serviceMocks.getStudents,
}))

import SeatAvailability from '../../src/pages/admin/SeatAvailability.vue'

const shift = {
  id: 'morning-id',
  name: 'Morning',
  startTime: '06:00',
  endTime: '12:00',
  isEnabled: true,
}
const availability = {
  shiftIds: ['morning-id'],
  summary: {
    available: 1,
    allotted: 0,
    blocked: 0,
    reserved: 0,
    maintenance: 1,
    physicallyBlocked: 0,
  },
  seats: [
    {
      seatId: 'available-seat',
      seatNumber: 'A-01',
      floorId: 'floor-id',
      floorName: 'Ground Floor',
      physicalStatus: 'available',
      status: 'available',
      isAvailable: true,
      blockers: [],
    },
    {
      seatId: 'maintenance-seat',
      seatNumber: 'A-02',
      floorId: 'floor-id',
      floorName: 'Ground Floor',
      physicalStatus: 'maintenance',
      status: 'maintenance',
      isAvailable: false,
      blockers: [],
    },
  ],
}

describe('SeatAvailability', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    serviceMocks.fetchShifts.mockResolvedValue({
      data: { shifts: [shift] },
    })
    serviceMocks.fetchFloors.mockResolvedValue({
      data: [{ id: 'floor-id', name: 'Ground Floor' }],
    })
    serviceMocks.getStudents.mockResolvedValue({
      data: [
        {
          id: 'student-id',
          firstName: 'Aarav',
          lastName: 'Sharma',
          status: 'active',
        },
      ],
    })
    serviceMocks.fetchSeatAvailability.mockResolvedValue({
      data: availability,
    })
    serviceMocks.allocateSeat.mockResolvedValue({
      data: { allocationCount: 1, allocations: [] },
    })
  })

  it('renders server statuses and refreshes after a successful allocation', async () => {
    const wrapper = mount(SeatAvailability, {
      global: {
        plugins: [createPinia()],
        stubs: {
          RouterLink: {
            template: '<a><slot /></a>',
          },
        },
      },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('A-02')
    expect(wrapper.text()).toContain('Maintenance')

    const availableCard = wrapper
      .findAll('.seat-map-page__seat-card')
      .find((card) => card.text().includes('A-01'))
    await availableCard.trigger('click')
    await wrapper.get('.seat-map-page__details .btn--primary').trigger('click')
    await wrapper.get('#allocation-student').setValue('student-id')
    await wrapper.get('#allocation-notes').setValue('Front desk allocation')
    await wrapper.get('#seat-allocation-dialog-title')
      .element.closest('.modal')
      .querySelector('.btn--primary')
      .click()
    await flushPromises()

    expect(serviceMocks.allocateSeat).toHaveBeenCalledWith(
      expect.objectContaining({
        studentId: 'student-id',
        seatId: 'available-seat',
        shiftIds: ['morning-id'],
      }),
    )
    expect(serviceMocks.fetchSeatAvailability).toHaveBeenCalledTimes(2)
    expect(wrapper.find('#seat-allocation-dialog-title').exists()).toBe(false)
  })
})
