import {
  ANNOUNCEMENT_AUDIENCES,
  ANNOUNCEMENT_CATEGORIES,
  ANNOUNCEMENT_NETWORK_DELAY_MS,
  ANNOUNCEMENT_PRIORITIES,
  ANNOUNCEMENT_STATUSES,
  announcementMock,
} from '../mocks/announcementMock.js'

// TODO: Replace this shared mock state with library-scoped FastAPI endpoints.

let announcements = structuredClone(announcementMock)

function clone(value) {
  return structuredClone(value)
}

function delay(ms = ANNOUNCEMENT_NETWORK_DELAY_MS) {
  return new Promise((resolve) => globalThis.setTimeout(resolve, ms))
}

function createSuccessResponse(message, data, meta = {}) {
  return {
    success: true,
    message,
    data: clone(data),
    meta: {
      source: 'mock-announcement-service',
      timestamp: new Date().toISOString(),
      ...meta,
    },
  }
}

function createAnnouncementError(
  message,
  status = 400,
  code = 'ANNOUNCEMENT_ERROR',
) {
  const error = new Error(message)
  error.response = {
    status,
    data: { success: false, message, error: { code } },
  }
  return error
}

function normalizeAdmin(admin = {}) {
  const id = String(admin.id || '').trim()
  const libraryName = String(admin.libraryName || '').trim()

  if (!id || !libraryName) {
    throw createAnnouncementError(
      'A logged-in library owner is required.',
      401,
      'ANNOUNCEMENT_ADMIN_REQUIRED',
    )
  }

  return { id, name: String(admin.name || 'Library Owner'), libraryName }
}

function normalizeFilters(filters = {}) {
  return {
    search: String(filters.search || '').trim().toLowerCase(),
    status: String(filters.status || '').trim().toLowerCase(),
    category: String(filters.category || '').trim().toLowerCase(),
  }
}

function getEffectiveStatus(announcement) {
  let status = announcement.status

  if (
    status === ANNOUNCEMENT_STATUSES.SCHEDULED &&
    announcement.publishedAt &&
    new Date(announcement.publishedAt) <= new Date()
  ) {
    status = ANNOUNCEMENT_STATUSES.PUBLISHED
  }

  if (
    status === ANNOUNCEMENT_STATUSES.PUBLISHED &&
    announcement.expiresAt &&
    new Date(announcement.expiresAt) <= new Date()
  ) {
    status = ANNOUNCEMENT_STATUSES.EXPIRED
  }

  return status
}

function normalizeLifecycle() {
  announcements = announcements.map((announcement) => ({
    ...announcement,
    status: getEffectiveStatus(announcement),
  }))
}

function getLibraryAnnouncements(libraryName) {
  normalizeLifecycle()
  return announcements
    .filter((announcement) => announcement.libraryName === libraryName)
    .sort((first, second) => {
      const firstDate = first.publishedAt || first.updatedAt || first.createdAt
      const secondDate = second.publishedAt || second.updatedAt || second.createdAt
      return secondDate.localeCompare(firstDate)
    })
}

function getAnnouncementById(announcementId, libraryName) {
  const announcementIndex = announcements.findIndex((announcement) => {
    return (
      announcement.id === String(announcementId) &&
      announcement.libraryName === libraryName
    )
  })

  if (announcementIndex === -1) {
    throw createAnnouncementError(
      'Announcement was not found.',
      404,
      'ANNOUNCEMENT_NOT_FOUND',
    )
  }

  return { announcementIndex, announcement: announcements[announcementIndex] }
}

function normalizePayload(payload = {}, existing = {}) {
  const title = String(payload.title ?? existing.title ?? '').trim()
  const body = String(payload.body ?? existing.body ?? '').trim()
  const category = String(payload.category ?? existing.category ?? 'general')
  const priority = String(payload.priority ?? existing.priority ?? 'normal')
  const audience = String(payload.audience ?? existing.audience ?? 'all')
  const requestedStatus = String(payload.status ?? existing.status ?? 'draft')
  const publishedAt = payload.publishedAt ?? existing.publishedAt ?? null
  const expiresAt = payload.expiresAt ?? existing.expiresAt ?? null

  if (title.length < 5 || title.length > 120) {
    throw createAnnouncementError(
      'Title must contain between 5 and 120 characters.',
      422,
      'ANNOUNCEMENT_TITLE_INVALID',
    )
  }

  if (body.length < 10 || body.length > 1000) {
    throw createAnnouncementError(
      'Message must contain between 10 and 1000 characters.',
      422,
      'ANNOUNCEMENT_BODY_INVALID',
    )
  }

  if (!ANNOUNCEMENT_CATEGORIES.some((item) => item.value === category)) {
    throw createAnnouncementError('Select a valid category.', 422, 'ANNOUNCEMENT_CATEGORY_INVALID')
  }

  if (!Object.values(ANNOUNCEMENT_PRIORITIES).includes(priority)) {
    throw createAnnouncementError('Select a valid priority.', 422, 'ANNOUNCEMENT_PRIORITY_INVALID')
  }

  if (!ANNOUNCEMENT_AUDIENCES.some((item) => item.value === audience)) {
    throw createAnnouncementError('Select a valid audience.', 422, 'ANNOUNCEMENT_AUDIENCE_INVALID')
  }

  if (!Object.values(ANNOUNCEMENT_STATUSES).includes(requestedStatus)) {
    throw createAnnouncementError('Select a valid announcement status.', 422, 'ANNOUNCEMENT_STATUS_INVALID')
  }

  const normalizedPublishedAt = publishedAt ? new Date(publishedAt).toISOString() : null
  const normalizedExpiresAt = expiresAt ? new Date(expiresAt).toISOString() : null

  if (
    normalizedPublishedAt &&
    normalizedExpiresAt &&
    normalizedExpiresAt <= normalizedPublishedAt
  ) {
    throw createAnnouncementError(
      'Expiry date must be later than the publish date.',
      422,
      'ANNOUNCEMENT_EXPIRY_INVALID',
    )
  }

  let status = requestedStatus
  if (
    requestedStatus === ANNOUNCEMENT_STATUSES.PUBLISHED &&
    normalizedPublishedAt &&
    new Date(normalizedPublishedAt) > new Date()
  ) {
    status = ANNOUNCEMENT_STATUSES.SCHEDULED
  }

  return {
    title,
    body,
    category,
    priority,
    audience,
    status,
    publishedAt: normalizedPublishedAt,
    expiresAt: normalizedExpiresAt,
  }
}

function buildSummary(records) {
  const now = new Date()
  return {
    total: records.length,
    published: records.filter((item) => item.status === 'published').length,
    drafts: records.filter((item) => item.status === 'draft').length,
    scheduled: records.filter((item) => item.status === 'scheduled').length,
    archived: records.filter((item) => item.status === 'archived').length,
    expired: records.filter((item) => item.status === 'expired').length,
    important: records.filter(
      (item) =>
        item.priority === 'important' &&
        item.status === 'published' &&
        (!item.expiresAt || new Date(item.expiresAt) > now),
    ).length,
  }
}

function buildAdminData(admin, filters = {}) {
  const records = getLibraryAnnouncements(admin.libraryName)
  const normalizedFilters = normalizeFilters(filters)
  const filtered = records.filter((announcement) => {
    const matchesSearch =
      !normalizedFilters.search ||
      `${announcement.title} ${announcement.body}`
        .toLowerCase()
        .includes(normalizedFilters.search)
    const matchesStatus =
      !normalizedFilters.status || announcement.status === normalizedFilters.status
    const matchesCategory =
      !normalizedFilters.category || announcement.category === normalizedFilters.category

    return matchesSearch && matchesStatus && matchesCategory
  })

  return {
    announcements: filtered,
    summary: buildSummary(records),
    filters: normalizedFilters,
    categories: ANNOUNCEMENT_CATEGORIES,
    audiences: ANNOUNCEMENT_AUDIENCES,
  }
}

export async function getAnnouncements(admin, filters = {}) {
  await delay()
  const scopedAdmin = normalizeAdmin(admin)
  return createSuccessResponse(
    'Announcements fetched successfully.',
    buildAdminData(scopedAdmin, filters),
  )
}

export async function createAnnouncement(admin, payload = {}) {
  await delay()
  const scopedAdmin = normalizeAdmin(admin)
  const now = new Date().toISOString()
  const normalized = normalizePayload(payload)
  const status = normalized.status
  const publishedAt =
    status === ANNOUNCEMENT_STATUSES.PUBLISHED && !normalized.publishedAt
      ? now
      : normalized.publishedAt

  const announcement = {
    id: `announcement-${Date.now()}`,
    ...normalized,
    publishedAt,
    libraryName: scopedAdmin.libraryName,
    author: { id: scopedAdmin.id, name: scopedAdmin.name },
    readBy: [],
    createdAt: now,
    updatedAt: now,
  }
  announcements.push(announcement)

  return createSuccessResponse('Announcement created successfully.', {
    announcement,
    ...buildAdminData(scopedAdmin),
  })
}

export async function updateAnnouncement(admin, announcementId, payload = {}) {
  await delay()
  const scopedAdmin = normalizeAdmin(admin)
  const { announcementIndex, announcement } = getAnnouncementById(
    announcementId,
    scopedAdmin.libraryName,
  )
  const normalized = normalizePayload(payload, announcement)
  const now = new Date().toISOString()

  announcements[announcementIndex] = {
    ...announcement,
    ...normalized,
    publishedAt:
      normalized.status === ANNOUNCEMENT_STATUSES.PUBLISHED &&
      !normalized.publishedAt
        ? now
        : normalized.publishedAt,
    updatedAt: now,
  }

  return createSuccessResponse('Announcement updated successfully.', {
    announcement: announcements[announcementIndex],
    ...buildAdminData(scopedAdmin),
  })
}

export async function publishAnnouncement(admin, announcementId) {
  await delay()
  const scopedAdmin = normalizeAdmin(admin)
  const { announcementIndex, announcement } = getAnnouncementById(
    announcementId,
    scopedAdmin.libraryName,
  )
  const now = new Date().toISOString()
  announcements[announcementIndex] = {
    ...announcement,
    status: ANNOUNCEMENT_STATUSES.PUBLISHED,
    publishedAt: now,
    expiresAt:
      announcement.expiresAt && new Date(announcement.expiresAt) <= new Date()
        ? null
        : announcement.expiresAt,
    updatedAt: now,
  }

  return createSuccessResponse('Announcement published successfully.', {
    announcement: announcements[announcementIndex],
    ...buildAdminData(scopedAdmin),
  })
}

export async function archiveAnnouncement(admin, announcementId) {
  await delay()
  const scopedAdmin = normalizeAdmin(admin)
  const { announcementIndex, announcement } = getAnnouncementById(
    announcementId,
    scopedAdmin.libraryName,
  )
  announcements[announcementIndex] = {
    ...announcement,
    status: ANNOUNCEMENT_STATUSES.ARCHIVED,
    updatedAt: new Date().toISOString(),
  }

  return createSuccessResponse('Announcement archived successfully.', {
    announcement: announcements[announcementIndex],
    ...buildAdminData(scopedAdmin),
  })
}

export async function deleteAnnouncement(admin, announcementId) {
  await delay()
  const scopedAdmin = normalizeAdmin(admin)
  const { announcementIndex, announcement } = getAnnouncementById(
    announcementId,
    scopedAdmin.libraryName,
  )

  if (
    ![
      ANNOUNCEMENT_STATUSES.DRAFT,
      ANNOUNCEMENT_STATUSES.ARCHIVED,
    ].includes(announcement.status)
  ) {
    throw createAnnouncementError(
      'Only draft or archived announcements can be deleted.',
      409,
      'ANNOUNCEMENT_ARCHIVE_REQUIRED',
    )
  }

  announcements.splice(announcementIndex, 1)
  return createSuccessResponse('Announcement deleted successfully.', {
    deletedId: announcement.id,
    ...buildAdminData(scopedAdmin),
  })
}

export function getPublishedAnnouncementsForStudent(
  studentId,
  libraryName = 'Central Study Library',
) {
  const now = new Date()
  return getLibraryAnnouncements(libraryName)
    .filter((announcement) => {
      return (
        announcement.status === ANNOUNCEMENT_STATUSES.PUBLISHED &&
        (!announcement.publishedAt || new Date(announcement.publishedAt) <= now) &&
        (!announcement.expiresAt || new Date(announcement.expiresAt) > now)
      )
    })
    .map((announcement) => ({
      ...announcement,
      isRead: announcement.readBy.includes(studentId),
    }))
}

export function markAnnouncementReadForStudent(
  studentId,
  announcementId,
  libraryName = 'Central Study Library',
) {
  const { announcementIndex, announcement } = getAnnouncementById(
    announcementId,
    libraryName,
  )

  if (!announcement.readBy.includes(studentId)) {
    announcements[announcementIndex] = {
      ...announcement,
      readBy: [...announcement.readBy, studentId],
    }
  }

  return clone(announcements[announcementIndex])
}
