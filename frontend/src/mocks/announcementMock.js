import { studentAnnouncementMock } from './studentPortalMock.js'

export const ANNOUNCEMENT_NETWORK_DELAY_MS = 400

export const ANNOUNCEMENT_CATEGORIES = Object.freeze([
  { value: 'general', label: 'General' },
  { value: 'schedule', label: 'Schedule' },
  { value: 'fees', label: 'Fees & Payments' },
  { value: 'policy', label: 'Policy' },
  { value: 'facility', label: 'Facility' },
])

export const ANNOUNCEMENT_STATUSES = Object.freeze({
  DRAFT: 'draft',
  PUBLISHED: 'published',
  SCHEDULED: 'scheduled',
  EXPIRED: 'expired',
  ARCHIVED: 'archived',
})

export const ANNOUNCEMENT_PRIORITIES = Object.freeze({
  NORMAL: 'normal',
  IMPORTANT: 'important',
})

export const ANNOUNCEMENT_AUDIENCES = Object.freeze([
  { value: 'all', label: 'All students' },
  { value: 'active', label: 'Active students' },
  { value: 'pending-fees', label: 'Students with pending fees' },
])

export const announcementMock = studentAnnouncementMock.map((announcement) => ({
  ...announcement,
  libraryName: 'Central Study Library',
  audience: 'all',
  status: ANNOUNCEMENT_STATUSES.PUBLISHED,
  author: { id: 'owner-001', name: 'Library Owner' },
  createdAt: announcement.publishedAt,
  updatedAt: announcement.publishedAt,
}))
