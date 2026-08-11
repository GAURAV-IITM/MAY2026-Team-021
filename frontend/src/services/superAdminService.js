import apiClient from '../api/axios.js'

export function buildPlatformDashboardParams(filters = {}) {
  return {
    startMonth: filters.startMonth || undefined,
    endMonth: filters.endMonth || undefined,
  }
}

export async function getDashboard(filters = {}) {
  const response = await apiClient.get('/platform/dashboard', {
    params: buildPlatformDashboardParams(filters),
  })
  return response.data
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
  const response = await apiClient.post('/platform/libraries', createLibraryPayload(payload))
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
  const response = await apiClient.patch(`/platform/libraries/${libraryId}/status`, {
    status: payload.status,
    reason: payload.reason || null,
    expectedUpdatedAt: payload.expectedUpdatedAt || null,
  })
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
  const response = await apiClient.patch(`/platform/libraries/${libraryId}/owner`, {
    ownerId: payload.ownerId,
    expectedUpdatedAt: payload.expectedUpdatedAt || null,
  })
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
  const response = await apiClient.patch(`/platform/owners/${ownerId}/assignment`, {
    libraryId: payload.libraryId,
    expectedUpdatedAt: payload.expectedUpdatedAt || null,
  })
  return {
    ...response.data,
    data: mapPlatformOwner(response.data.data),
  }
}

export async function setOwnerStatus(ownerId, payload = {}) {
  const response = await apiClient.patch(`/platform/owners/${ownerId}/status`, {
    status: payload.status,
    reason: payload.reason || null,
    expectedUpdatedAt: payload.expectedUpdatedAt || null,
  })
  return {
    ...response.data,
    data: mapPlatformOwner(response.data.data),
  }
}

export async function getSettings() {
  const response = await apiClient.get('/platform/settings')
  return response.data
}

export async function updateSettings(payload = {}) {
  const body = { version: payload.version }
  const editableKeys = [
    'allowLibraryRegistrations',
    'sessionTimeoutMinutes',
    'defaultTimezone',
  ]
  editableKeys.forEach((key) => {
    if (Object.hasOwn(payload, key)) body[key] = payload[key]
  })
  const response = await apiClient.patch('/platform/settings', body)
  return response.data
}
