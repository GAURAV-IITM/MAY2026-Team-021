import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import AnnouncementActionMenu from '../../src/components/announcement/AnnouncementActionMenu.vue'


async function actionsFor(status) {
  const wrapper = mount(AnnouncementActionMenu, {
    props: { announcement: { id: 'announcement-id', status } },
  })
  await wrapper.get('button[aria-label="Announcement actions"]').trigger('click')
  return wrapper.text()
}


describe('AnnouncementActionMenu', () => {
  it('shows only backend-supported actions for each lifecycle state', async () => {
    expect(await actionsFor('draft')).toContain('Edit')
    expect(await actionsFor('draft')).toContain('Publish now')
    expect(await actionsFor('published')).not.toContain('Edit')
    expect(await actionsFor('published')).toContain('Archive')
    expect(await actionsFor('archived')).toContain('Delete')
    expect(await actionsFor('archived')).not.toContain('Publish now')
  })
})
