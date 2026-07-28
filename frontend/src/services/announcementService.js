import apiClient from '../api/axios.js'

export function buildAnnouncementParams(filters = {}) {
  return {
    page: filters.page || 1,
    pageSize: filters.pageSize || 10,
    search: filters.search?.trim() || undefined,
    status: filters.status || undefined,
    category: filters.category || undefined,
    priority: filters.priority || undefined,
    audience: filters.audience || undefined,
    sortBy: filters.sortBy || 'createdAt',
    sortOrder: filters.sortOrder || 'desc',
  }
}

function mutationPayload(payload = {}) {
  return {
    title: payload.title,
    body: payload.body,
    category: payload.category,
    priority: payload.priority,
    audience: payload.audience,
    status: payload.status,
    scheduledAt: payload.scheduledAt ?? null,
    expiresAt: payload.expiresAt ?? null,
  }
}

function patchPayload(payload = {}) {
  const result = {}
  const editableFields = [
    'title',
    'body',
    'category',
    'priority',
    'audience',
    'status',
    'scheduledAt',
    'expiresAt',
    'expectedUpdatedAt',
  ]
  editableFields.forEach((field) => {
    if (Object.prototype.hasOwnProperty.call(payload, field)) {
      result[field] = payload[field]
    }
  })
  return result
}

export async function getAnnouncements(filters = {}) {
  const response = await apiClient.get('/announcements', {
    params: buildAnnouncementParams(filters),
  })
  return {
    ...response.data,
    data: {
      announcements: response.data.data || [],
    },
  }
}

export async function createAnnouncement(payload = {}) {
  const response = await apiClient.post(
    '/announcements',
    mutationPayload(payload),
  )
  return response.data
}

export async function updateAnnouncement(announcementId, payload = {}) {
  const response = await apiClient.patch(
    `/announcements/${announcementId}`,
    patchPayload(payload),
  )
  return response.data
}

export async function publishAnnouncement(announcementId) {
  const response = await apiClient.post(
    `/announcements/${announcementId}/publish`,
  )
  return response.data
}

export async function archiveAnnouncement(announcementId, reason) {
  const response = await apiClient.post(
    `/announcements/${announcementId}/archive`,
    { reason: reason?.trim() || undefined },
  )
  return response.data
}

export async function deleteAnnouncement(announcementId) {
  await apiClient.delete(`/announcements/${announcementId}`)
  return { message: 'Announcement deleted successfully.' }
}
