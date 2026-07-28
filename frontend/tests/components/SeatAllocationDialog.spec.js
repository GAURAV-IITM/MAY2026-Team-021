import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import SeatAllocationDialog from '../../src/components/seat/SeatAllocationDialog.vue'

const students = [
  {
    id: 'student-id',
    firstName: 'Aarav',
    lastName: 'Sharma',
    enrollmentNumber: 'STU-001',
    status: 'active',
  },
]
const shifts = [
  {
    id: 'morning-id',
    name: 'Morning',
    startTime: '06:00',
    endTime: '12:00',
    isEnabled: true,
  },
  {
    id: 'evening-id',
    name: 'Evening',
    startTime: '18:00',
    endTime: '23:00',
    isEnabled: true,
  },
  {
    id: 'office-id',
    name: 'Office Hours',
    startTime: '09:00',
    endTime: '17:00',
    isEnabled: true,
  },
]
const seats = [
  {
    id: 'seat-id',
    seatNumber: 'A-01',
    floorName: 'Ground Floor',
    status: 'available',
    isAvailable: true,
  },
]

function mountDialog(props = {}) {
  return mount(SeatAllocationDialog, {
    props: {
      isOpen: true,
      seats,
      students,
      shifts,
      initialSeatId: 'seat-id',
      initialShiftIds: ['morning-id'],
      initialStartDate: '2026-08-01',
      initialEndDate: '2026-08-31',
      ...props,
    },
  })
}

async function selectStudent(wrapper) {
  await wrapper.get('#allocation-student').setValue('student-id')
}

describe('SeatAllocationDialog', () => {
  it('validates required fields and rejects reversed dates', async () => {
    const wrapper = mountDialog({
      initialSeatId: '',
      initialShiftIds: [],
      initialStartDate: '',
      initialEndDate: '',
    })
    await wrapper.get('button.btn--primary').trigger('click')
    expect(wrapper.text()).toContain('Select an active student.')
    expect(wrapper.text()).toContain('Select a seat.')
    expect(wrapper.text()).toContain('Select at least one shift.')

    await selectStudent(wrapper)
    await wrapper.get('#allocation-seat').setValue('seat-id')
    await wrapper.get('#allocation-start-date').setValue('2026-08-10')
    await wrapper.get('#allocation-end-date').setValue('2026-08-01')
    await wrapper.get('input[value="morning-id"]').setValue(true)
    await wrapper.get('button.btn--primary').trigger('click')
    expect(wrapper.text()).toContain('End date cannot be earlier than start date.')
  })

  it('submits every selected non-overlapping shift', async () => {
    const wrapper = mountDialog()
    await selectStudent(wrapper)
    await wrapper.get('input[value="evening-id"]').setValue(true)
    await wrapper.get('button.btn--primary').trigger('click')

    expect(wrapper.emitted('confirm')).toHaveLength(1)
    expect(wrapper.emitted('confirm')[0][0]).toEqual({
      studentId: 'student-id',
      seatId: 'seat-id',
      shiftIds: ['morning-id', 'evening-id'],
      startDate: '2026-08-01',
      endDate: '2026-08-31',
      notes: null,
    })
  })

  it('detects overlapping shifts before submission', async () => {
    const wrapper = mountDialog()
    await selectStudent(wrapper)
    await wrapper.get('input[value="office-id"]').setValue(true)
    await wrapper.get('button.btn--primary').trigger('click')

    expect(wrapper.emitted('confirm')).toBeUndefined()
    expect(wrapper.text()).toContain('Morning overlaps with Office Hours')
  })

  it('shows conflict details and retains entered values', async () => {
    const wrapper = mountDialog()
    await selectStudent(wrapper)
    await wrapper.get('#allocation-notes').setValue('Keep this note')
    await wrapper.setProps({
      submissionError: {
        message: 'Seat A-01 is occupied by another student.',
        requestId: 'request-409',
      },
    })

    expect(wrapper.text()).toContain('Seat A-01 is occupied by another student.')
    expect(wrapper.text()).toContain('request-409')
    expect(wrapper.get('#allocation-student').element.value).toBe('student-id')
    expect(wrapper.get('#allocation-notes').element.value).toBe('Keep this note')
  })

  it('displays maintenance seats as unavailable', () => {
    const wrapper = mountDialog({
      seats: [
        {
          ...seats[0],
          status: 'maintenance',
          physicalStatus: 'maintenance',
          isAvailable: false,
        },
      ],
    })
    expect(wrapper.text()).toContain('Maintenance')
  })
})
