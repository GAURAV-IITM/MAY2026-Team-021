import {
  LIBRARY_STATUSES,
  OWNER_STATUSES,
  SUPER_ADMIN_NETWORK_DELAY_MS,
  libraryMock,
  ownerMock,
  platformActivityMock,
  platformSettingsMock,
  platformTrendMock,
} from '../mocks/superAdminMock.js'

let libraries = clone(libraryMock)
let owners = clone(ownerMock)
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

function findLibrary(libraryId) {
  const library = libraries.find((item) => item.id === String(libraryId))

  if (!library) {
    throw createServiceError('Library was not found.', 404, 'LIBRARY_NOT_FOUND')
  }

  return library
}

function findOwner(ownerId) {
  const owner = owners.find((item) => item.id === String(ownerId))

  if (!owner) {
    throw createServiceError('Library owner was not found.', 404, 'OWNER_NOT_FOUND')
  }

  return owner
}

function generateCode(name, city) {
  const nameToken = String(name || '')
    .split(/\s+/)
    .filter(Boolean)
    .map((word) => word[0])
    .join('')
    .slice(0, 3)
    .toUpperCase()
  const cityToken = String(city || '').replace(/[^a-z0-9]/gi, '').slice(0, 3).toUpperCase()

  return `${nameToken || 'LIB'}-${cityToken || 'NEW'}`
}

function ensureUniqueLibraryName(name, ignoredLibraryId = '') {
  const normalizedName = String(name || '').trim().toLowerCase()
  const duplicate = libraries.some((library) => {
    return library.id !== ignoredLibraryId && library.name.toLowerCase() === normalizedName
  })

  if (duplicate) {
    throw createServiceError(
      'A library with this name already exists.',
      409,
      'LIBRARY_NAME_DUPLICATE',
    )
  }
}

function ensureUniqueOwnerEmail(email, ignoredOwnerId = '') {
  const normalizedEmail = String(email || '').trim().toLowerCase()
  const duplicate = owners.some((owner) => {
    return owner.id !== ignoredOwnerId && owner.email.toLowerCase() === normalizedEmail
  })

  if (duplicate) {
    throw createServiceError(
      'An owner with this email already exists.',
      409,
      'OWNER_EMAIL_DUPLICATE',
    )
  }
}

function getValidStatus(status, allowedStatuses, entityLabel) {
  const normalizedStatus = String(status || '').trim().toLowerCase()

  if (!allowedStatuses.includes(normalizedStatus)) {
    throw createServiceError(
      `Select a valid ${entityLabel} status.`,
      422,
      'STATUS_INVALID',
    )
  }

  return normalizedStatus
}

function normalizeLibraryPayload(payload = {}, existingLibrary = {}) {
  const name = String(payload.name ?? existingLibrary.name ?? '').trim()
  const city = String(payload.city ?? existingLibrary.city ?? '').trim()
  const state = String(payload.state ?? existingLibrary.state ?? '').trim()
  const contactEmail = String(
    payload.contactEmail ?? existingLibrary.contactEmail ?? '',
  ).trim()
  const contactPhone = String(
    payload.contactPhone ?? existingLibrary.contactPhone ?? '',
  ).trim()
  const seatCount = Number(payload.seatCount ?? existingLibrary.seatCount ?? 0)
  const status = getValidStatus(
    payload.status ?? existingLibrary.status ?? LIBRARY_STATUSES.PENDING,
    Object.values(LIBRARY_STATUSES),
    'library',
  )

  if (!name || !city || !state || !contactEmail) {
    throw createServiceError(
      'Library name, city, state, and contact email are required.',
      422,
      'LIBRARY_VALIDATION_ERROR',
    )
  }

  if (!/^\S+@\S+\.\S+$/.test(contactEmail)) {
    throw createServiceError('Enter a valid library email.', 422, 'EMAIL_INVALID')
  }

  if (!Number.isInteger(seatCount) || seatCount < 0) {
    throw createServiceError(
      'Seat capacity must be a non-negative whole number.',
      422,
      'SEAT_COUNT_INVALID',
    )
  }

  return { name, city, state, contactEmail, contactPhone, seatCount, status }
}

function normalizeOwnerPayload(payload = {}, existingOwner = {}) {
  const name = String(payload.name ?? existingOwner.name ?? '').trim()
  const email = String(payload.email ?? existingOwner.email ?? '').trim()
  const phone = String(payload.phone ?? existingOwner.phone ?? '').trim()
  const libraryId = String(payload.libraryId ?? existingOwner.libraryId ?? '').trim()
  const status = getValidStatus(
    payload.status ?? existingOwner.status ?? OWNER_STATUSES.INVITED,
    Object.values(OWNER_STATUSES),
    'owner',
  )

  if (!name || !email) {
    throw createServiceError(
      'Owner name and email are required.',
      422,
      'OWNER_VALIDATION_ERROR',
    )
  }

  if (!/^\S+@\S+\.\S+$/.test(email)) {
    throw createServiceError('Enter a valid owner email.', 422, 'EMAIL_INVALID')
  }

  return { name, email, phone, libraryId, status }
}

function assignOwnerToLibrary(ownerId, libraryId) {
  const owner = findOwner(ownerId)
  const library = libraryId ? findLibrary(libraryId) : null

  if (library?.ownerId && library.ownerId !== ownerId) {
    throw createServiceError(
      `${library.name} already has an assigned owner.`,
      409,
      'LIBRARY_OWNER_ALREADY_ASSIGNED',
    )
  }

  if (owner.libraryId && owner.libraryId !== libraryId) {
    const previousLibrary = findLibrary(owner.libraryId)
    previousLibrary.ownerId = null
    previousLibrary.ownerName = null
  }

  if (library) {
    owner.libraryId = library.id
    owner.libraryName = library.name
    library.ownerId = owner.id
    library.ownerName = owner.name
    return
  }

  owner.libraryId = ''
  owner.libraryName = ''
}

function getStatusDistribution(source, statusValues) {
  return statusValues.map((status) => ({
    status,
    count: source.filter((item) => item.status === status).length,
  }))
}

function getPlatformTotals() {
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
    totalOwners: owners.length,
    activeOwners: owners.filter((owner) => owner.status === OWNER_STATUSES.ACTIVE).length,
    invitedOwners: owners.filter((owner) => owner.status === OWNER_STATUSES.INVITED).length,
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

  const totals = getPlatformTotals()

  return createSuccessResponse('Super Admin dashboard fetched successfully.', {
    totals,
    libraryStatus: getStatusDistribution(
      libraries,
      Object.values(LIBRARY_STATUSES),
    ),
    ownerStatus: getStatusDistribution(owners, Object.values(OWNER_STATUSES)),
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

export async function getLibraries() {
  await delay()

  return createSuccessResponse('Libraries fetched successfully.', {
    libraries: [...libraries].sort((first, second) =>
      second.joinedAt.localeCompare(first.joinedAt),
    ),
  })
}

export async function createLibrary(payload = {}) {
  await delay()

  const normalizedPayload = normalizeLibraryPayload(payload)
  ensureUniqueLibraryName(normalizedPayload.name)

  const now = new Date().toISOString()
  const library = {
    id: `library-${Date.now()}`,
    code: generateCode(normalizedPayload.name, normalizedPayload.city),
    ...normalizedPayload,
    ownerId: null,
    ownerName: null,
    studentCount: 0,
    occupancyRate: 0,
    joinedAt: now,
    lastActivityAt: now,
  }

  libraries.push(library)

  if (payload.ownerId) {
    assignOwnerToLibrary(String(payload.ownerId), library.id)
  }

  addActivity('library', `${library.name} registered`, `${library.city}, ${library.state}`)

  return createSuccessResponse('Library created successfully.', {
    library,
    libraries,
    owners,
  })
}

export async function updateLibrary(libraryId, payload = {}) {
  await delay()

  const library = findLibrary(libraryId)
  const normalizedPayload = normalizeLibraryPayload(payload, library)
  ensureUniqueLibraryName(normalizedPayload.name, library.id)
  Object.assign(library, normalizedPayload, {
    code: generateCode(normalizedPayload.name, normalizedPayload.city),
    lastActivityAt: new Date().toISOString(),
  })

  if (payload.ownerId && payload.ownerId !== library.ownerId) {
    assignOwnerToLibrary(String(payload.ownerId), library.id)
  }

  if (library.ownerId) {
    const owner = findOwner(library.ownerId)
    owner.libraryName = library.name
    library.ownerName = owner.name
  }

  addActivity('library', `${library.name} updated`, `${library.city}, ${library.state}`)

  return createSuccessResponse('Library updated successfully.', {
    library,
    libraries,
    owners,
  })
}

export async function setLibraryStatus(libraryId, status) {
  const library = findLibrary(libraryId)

  return updateLibrary(libraryId, {
    ...library,
    status,
  })
}

export async function getOwners() {
  await delay()

  return createSuccessResponse('Library owners fetched successfully.', {
    owners: [...owners].sort((first, second) =>
      second.createdAt.localeCompare(first.createdAt),
    ),
  })
}

export async function createOwner(payload = {}) {
  await delay()

  const normalizedPayload = normalizeOwnerPayload(payload)
  ensureUniqueOwnerEmail(normalizedPayload.email)

  const owner = {
    id: `platform-owner-${Date.now()}`,
    ...normalizedPayload,
    libraryId: '',
    libraryName: '',
    createdAt: new Date().toISOString(),
    lastLoginAt: null,
  }

  owners.push(owner)

  if (normalizedPayload.libraryId) {
    assignOwnerToLibrary(owner.id, normalizedPayload.libraryId)
  }

  addActivity('owner', `Owner invitation sent to ${owner.name}`, owner.libraryName)

  return createSuccessResponse('Owner created successfully.', {
    owner,
    owners,
    libraries,
  })
}

export async function updateOwner(ownerId, payload = {}) {
  await delay()

  const owner = findOwner(ownerId)
  const normalizedPayload = normalizeOwnerPayload(payload, owner)
  ensureUniqueOwnerEmail(normalizedPayload.email, owner.id)
  const requestedLibraryId = normalizedPayload.libraryId
  const shouldUpdateLibrary = Object.hasOwn(payload, 'libraryId')

  Object.assign(owner, normalizedPayload, {
    libraryId: owner.libraryId || '',
    libraryName: owner.libraryName || '',
  })

  if (shouldUpdateLibrary && requestedLibraryId !== owner.libraryId) {
    assignOwnerToLibrary(owner.id, requestedLibraryId)
  }

  if (owner.libraryId) {
    const library = findLibrary(owner.libraryId)
    library.ownerName = owner.name
  }

  addActivity('owner', `${owner.name} updated`, owner.libraryName)

  return createSuccessResponse('Owner updated successfully.', {
    owner,
    owners,
    libraries,
  })
}

export async function setOwnerStatus(ownerId, status) {
  const owner = findOwner(ownerId)

  return updateOwner(ownerId, {
    ...owner,
    status,
  })
}

export async function getAnalytics() {
  await delay()

  const totals = getPlatformTotals()
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
