export const ANNOUNCEMENT_CATEGORIES = Object.freeze([
  { value: 'general', label: 'General' },
  { value: 'schedule', label: 'Schedule' },
  { value: 'fees', label: 'Fees' },
  { value: 'policy', label: 'Policy' },
  { value: 'facility', label: 'Facility' },
])

export const ANNOUNCEMENT_AUDIENCES = Object.freeze([
  { value: 'all_students', label: 'All students' },
  { value: 'active_students', label: 'Active students' },
  { value: 'pending_fee_students', label: 'Students with pending fees' },
])

export const ANNOUNCEMENT_STATUSES = Object.freeze({
  DRAFT: 'draft',
  SCHEDULED: 'scheduled',
  PUBLISHED: 'published',
  EXPIRED: 'expired',
  ARCHIVED: 'archived',
})

export const ANNOUNCEMENT_PRIORITIES = Object.freeze({
  NORMAL: 'normal',
  IMPORTANT: 'important',
})
