import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import ReportFilters from '../../src/components/reports/ReportFilters.vue'


const options = {
  months: [
    { value: '2026-06', label: 'June 2026' },
    { value: '2026-07', label: 'July 2026' },
  ],
  floors: [{ value: 'floor-id', label: 'Floor 1' }],
  shifts: [{ value: 'shift-id', label: 'Morning', timing: '06:00 - 12:00' }],
}


describe('ReportFilters', () => {
  it('prevents an invalid month range from being applied', async () => {
    const wrapper = mount(ReportFilters, {
      props: {
        modelValue: {
          startMonth: '2026-06',
          endMonth: '2026-07',
          floorId: '',
          shiftId: '',
        },
        options,
      },
    })
    const selects = wrapper.findAll('select')
    await selects[0].setValue('2026-07')
    await selects[1].setValue('2026-06')
    await wrapper.find('form').trigger('submit')

    expect(wrapper.text()).toContain(
      'The start month cannot be after the end month.',
    )
    expect(wrapper.emitted('apply')).toBeUndefined()
  })

  it('emits tenant-safe floor and shift filter values', async () => {
    const wrapper = mount(ReportFilters, {
      props: {
        modelValue: {
          startMonth: '2026-06',
          endMonth: '2026-07',
          floorId: '',
          shiftId: '',
        },
        options,
      },
    })
    const selects = wrapper.findAll('select')
    await selects[2].setValue('floor-id')
    await selects[3].setValue('shift-id')
    await wrapper.find('form').trigger('submit')

    expect(wrapper.emitted('apply')?.[0]?.[0]).toEqual({
      startMonth: '2026-06',
      endMonth: '2026-07',
      floorId: 'floor-id',
      shiftId: 'shift-id',
    })
  })
})
