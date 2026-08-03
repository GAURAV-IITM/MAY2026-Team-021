import {
  LIBRARY_STATUSES,
  OWNER_STATUSES,
  SUPER_ADMIN_NETWORK_DELAY_MS,
  libraryMock,
  platformActivityMock,
  platformSettingsMock,
  platformTrendMock,
} from '../mocks/superAdminMock.js'
import apiClient from '../api/axios.js'

let libraries = clone(libraryMock)
let activity = clone(platformActivityMock)
let settings = clone(platformSettingsMock)

function clone(value) {
  return structuredClone(value)
}

function delay(ms = SUPER_ADMIN_NETWORK_DELAY_MS) {
  return new Promise((resolve) => {
    globalThis.setTimeout(resolve, ms)
  })
}

function createSuccessResponse(message, data, meta = {}) {
  return {
    success: true,
    message,
    data: clone(data),
    meta: {
      source: 'mock-super-admin-service',
      timestamp: new Date().toISOString(),
      ...meta,
    },
  }
}

function createServiceError(message, status = 400, code = 'SUPER_ADMIN_ERROR') {
  const error = new Error(message)

  error.response = {
    status,
    data: {
      success: false,
      message,
      error: { code },
    },
  }

  return error
}

function addActivity(type, title, detail = '') {
  activity.unshift({
    id: `platform-activity-${Date.now()}`,
    type,
    title,
    detail,
    occurredAt: new Date().toISOString(),
  })
}

function getStatusDistribution(source, statusValues) {
  return statusValues.map((status) => ({
    status,
    count: source.filter((item) => item.status === status).length,
  }))
}

function getPlatformTotals(ownerSummary = {}) {
  const activeLibraries = libraries.filter(
    (library) => library.status === LIBRARY_STATUSES.ACTIVE,
  )

  return {
    totalLibraries: libraries.length,
    activeLibraries: activeLibraries.length,
    pendingLibraries: libraries.filter(
      (library) => library.status === LIBRARY_STATUSES.PENDING,
    ).length,
    suspendedLibraries: libraries.filter(
      (library) => library.status === LIBRARY_STATUSES.SUSPENDED,
    ).length,
    totalOwners: ownerSummary.total || 0,
    activeOwners: ownerSummary.active || 0,
    invitedOwners: ownerSummary.invited || 0,
    totalStudents: activeLibraries.reduce(
      (total, library) => total + library.studentCount,
      0,
    ),
    totalSeats: activeLibraries.reduce((total, library) => total + library.seatCount, 0),
    averageOccupancy:
      activeLibraries.length === 0
        ? 0
        : Math.round(
            activeLibraries.reduce(
              (total, library) => total + library.occupancyRate,
              0,
            ) / activeLibraries.length,
          ),
  }
}

export async function getDashboard() {
  await delay()

  const ownerResponse = await getOwners({ page: 1, pageSize: 100 })
  const totals = getPlatformTotals(ownerResponse.summary)

  return createSuccessResponse('Super Admin dashboard fetched successfully.', {
    totals,
    libraryStatus: getStatusDistribution(
      libraries,
      Object.values(LIBRARY_STATUSES),
    ),
    ownerStatus: Object.values(OWNER_STATUSES).map((status) => ({
      status,
      count: ownerResponse.summary[status] || 0,
    })),
    topLibraries: [...libraries]
      .filter((library) => library.status === LIBRARY_STATUSES.ACTIVE)
      .sort((first, second) => second.studentCount - first.studentCount)
      .slice(0, 5),
    trend: clone(platformTrendMock),
    recentActivity: activity.slice(0, 6),
    attention: [
      {
        id: 'pending-libraries',
        label: 'Pending library approvals',
        value: totals.pendingLibraries,
        routeName: 'superAdminLibraries',
        tone: 'warning',
      },
      {
        id: 'invited-owners',
        label: 'Owner invitations pending',
        value: totals.invitedOwners,
        routeName: 'superAdminOwners',
        tone: 'info',
      },
      {
        id: 'suspended-libraries',
        label: 'Suspended libraries',
        value: totals.suspendedLibraries,
        routeName: 'superAdminLibraries',
        tone: 'danger',
      },
    ],
    lastUpdated: new Date().toISOString(),
  })
}

export function buildPlatformLibraryParams(filters = {}) {
  return {
    page: filters.page || 1,
    pageSize: filters.pageSize || 10,
    search: filters.search?.trim() || undefined,
    status: filters.status || undefined,
    ownerId: filters.ownerId || undefined,
    state: filters.state || undefined,
    sortBy: filters.sortBy || 'createdAt',
    sortOrder: filters.sortOrder || 'desc',
  }
}

function mapPlatformLibrary(library = {}) {
  return {
    ...library,
    ownerId: library.owner?.id || '',
    ownerName: library.owner?.name || '',
    joinedAt: library.createdAt,
  }
}

function createLibraryPayload(payload = {}) {
  return {
    name: payload.name,
    code: payload.code,
    contactEmail: payload.contactEmail,
    contactPhone: payload.contactPhone || null,
    addressLine: payload.addressLine || null,
    city: payload.city || null,
    state: payload.state || null,
    postalCode: payload.postalCode || null,
    timezone: payload.timezone || 'Asia/Kolkata',
    ownerId: payload.ownerId || null,
  }
}

function updateLibraryPayload(payload = {}) {
  const result = {}
  const fields = [
    'name',
    'contactEmail',
    'contactPhone',
    'addressLine',
    'city',
    'state',
    'postalCode',
    'timezone',
    'expectedUpdatedAt',
  ]
  fields.forEach((field) => {
    if (Object.hasOwn(payload, field)) result[field] = payload[field]
  })
  return result
}

export async function getLibraries(filters = {}) {
  const response = await apiClient.get('/platform/libraries', {
    params: buildPlatformLibraryParams(filters),
  })
  return {
    ...response.data,
    data: response.data.data.map(mapPlatformLibrary),
  }
}

export async function getLibrary(libraryId) {
  const response = await apiClient.get(`/platform/libraries/${libraryId}`)
  return {
    ...response.data,
    data: mapPlatformLibrary(response.data.data),
  }
}

export async function createLibrary(payload = {}) {
  const response = await apiClient.post(
    '/platform/libraries',
    createLibraryPayload(payload),
  )
  return {
    ...response.data,
    data: mapPlatformLibrary(response.data.data),
  }
}

export async function updateLibrary(libraryId, payload = {}) {
  const response = await apiClient.patch(
    `/platform/libraries/${libraryId}`,
    updateLibraryPayload(payload),
  )
  return {
    ...response.data,
    data: mapPlatformLibrary(response.data.data),
  }
}

export async function setLibraryStatus(libraryId, payload = {}) {
  const response = await apiClient.patch(
    `/platform/libraries/${libraryId}/status`,
    {
      status: payload.status,
      reason: payload.reason || null,
      expectedUpdatedAt: payload.expectedUpdatedAt || null,
    },
  )
  return {
    ...response.data,
    data: mapPlatformLibrary(response.data.data),
  }
}

export async function getLibraryOwnerOptions() {
  const response = await apiClient.get('/platform/libraries/owner-options')
  return response.data
}

export async function assignLibraryOwner(libraryId, payload = {}) {
  const response = await apiClient.patch(
    `/platform/libraries/${libraryId}/owner`,
    {
      ownerId: payload.ownerId,
      expectedUpdatedAt: payload.expectedUpdatedAt || null,
    },
  )
  return {
    ...response.data,
    data: mapPlatformLibrary(response.data.data),
  }
}

export function buildPlatformOwnerParams(filters = {}) {
  return {
    page: filters.page || 1,
    pageSize: filters.pageSize || 10,
    search: filters.search?.trim() || undefined,
    status: filters.status || undefined,
    libraryId: filters.libraryId || undefined,
    invitationStatus: filters.invitationStatus || undefined,
    sortBy: filters.sortBy || 'createdAt',
    sortOrder: filters.sortOrder || 'desc',
  }
}

function mapPlatformOwner(owner = {}) {
  const assignment = owner.assignments?.[0] || null
  return {
    ...owner,
    libraryId: assignment?.id || '',
    libraryName: assignment?.name || '',
    libraryStatus: assignment?.status || '',
    isInvitation: !owner.userId,
  }
}

export async function getOwners(filters = {}) {
  const response = await apiClient.get('/platform/owners', {
    params: buildPlatformOwnerParams(filters),
  })
  return {
    ...response.data,
    data: response.data.data.map(mapPlatformOwner),
  }
}

export async function getOwner(ownerId) {
  const response = await apiClient.get(`/platform/owners/${ownerId}`)
  return {
    ...response.data,
    data: mapPlatformOwner(response.data.data),
  }
}

export async function createOwner(payload = {}) {
  const response = await apiClient.post('/platform/owners/invitations', {
    name: payload.name,
    email: payload.email,
    phone: payload.phone || null,
    libraryId: payload.libraryId,
  })
  return {
    ...response.data,
    data: {
      ...response.data.data,
      owner: mapPlatformOwner(response.data.data.owner),
    },
  }
}

export async function updateOwner(ownerId, payload = {}) {
  const body = {}
  if (Object.hasOwn(payload, 'name')) body.name = payload.name
  if (Object.hasOwn(payload, 'phone')) body.phone = payload.phone || null
  if (payload.expectedUpdatedAt) body.expectedUpdatedAt = payload.expectedUpdatedAt
  const response = await apiClient.patch(`/platform/owners/${ownerId}`, body)
  return {
    ...response.data,
    data: mapPlatformOwner(response.data.data),
  }
}

export async function assignOwner(ownerId, payload = {}) {
  const response = await apiClient.patch(
    `/platform/owners/${ownerId}/assignment`,
    {
      libraryId: payload.libraryId,
      expectedUpdatedAt: payload.expectedUpdatedAt || null,
    },
  )
  return {
    ...response.data,
    data: mapPlatformOwner(response.data.data),
  }
}

export async function setOwnerStatus(ownerId, payload = {}) {
  const response = await apiClient.patch(
    `/platform/owners/${ownerId}/status`,
    {
      status: payload.status,
      reason: payload.reason || null,
      expectedUpdatedAt: payload.expectedUpdatedAt || null,
    },
  )
  return {
    ...response.data,
    data: mapPlatformOwner(response.data.data),
  }
}

export async function getAnalytics() {
  await delay()

  const ownerResponse = await getOwners({ page: 1, pageSize: 100 })
  const totals = getPlatformTotals(ownerResponse.summary)
  const stateGroups = libraries.reduce((groups, library) => {
    const current = groups.get(library.state) || {
      state: library.state,
      libraryCount: 0,
      studentCount: 0,
    }

    current.libraryCount += 1
    current.studentCount += library.studentCount
    groups.set(library.state, current)

    return groups
  }, new Map())

  return createSuccessResponse('Platform analytics fetched successfully.', {
    totals,
    trend: clone(platformTrendMock),
    regionalDistribution: [...stateGroups.values()].sort(
      (first, second) => second.studentCount - first.studentCount,
    ),
    libraryPerformance: [...libraries]
      .filter((library) => library.status === LIBRARY_STATUSES.ACTIVE)
      .sort((first, second) => second.occupancyRate - first.occupancyRate),
    generatedAt: new Date().toISOString(),
  })
}

export async function getSettings() {
  await delay()

  return createSuccessResponse('Platform settings fetched successfully.', {
    settings,
  })
}

export async function updateSettings(payload = {}) {
  await delay()

  const platformName = String(payload.platformName || '').trim()
  const supportEmail = String(payload.supportEmail || '').trim()
  const sessionTimeoutMinutes = Number(payload.sessionTimeoutMinutes)

  if (!platformName || !/^\S+@\S+\.\S+$/.test(supportEmail)) {
    throw createServiceError(
      'Platform name and a valid support email are required.',
      422,
      'SETTINGS_VALIDATION_ERROR',
    )
  }

  if (!Number.isInteger(sessionTimeoutMinutes) || sessionTimeoutMinutes < 15) {
    throw createServiceError(
      'Session timeout must be at least 15 minutes.',
      422,
      'SESSION_TIMEOUT_INVALID',
    )
  }

  settings = {
    ...settings,
    ...clone(payload),
    platformName,
    supportEmail,
    sessionTimeoutMinutes,
    updatedAt: new Date().toISOString(),
  }

  addActivity('settings', 'Platform settings updated', platformName)

  return createSuccessResponse('Platform settings updated successfully.', {
    settings,
  })
}
