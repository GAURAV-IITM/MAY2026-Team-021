// src/mocks: Mock authentication data used until FastAPI authentication APIs are available.
// TODO: Remove this file when authService is replaced by real backend integration.

export const AUTH_ROLES = Object.freeze({
  LIBRARY_OWNER: 'admin',
  STUDENT: 'student',
  SUPER_ADMIN: 'superadmin',
})

export const AUTH_STORAGE_KEYS = Object.freeze({
  TOKEN: 'smart_library_fake_jwt',
  SESSION: 'smart_library_auth_session',
})

export const AUTH_NETWORK_DELAY_MS = 500

export const mockUsers = [
  {
    id: 'owner-001',
    name: 'Library Owner',
    email: 'owner@smartlibrary.test',
    phone: '9876543210',
    password: 'Owner@123',
    role: AUTH_ROLES.LIBRARY_OWNER,
    roleLabel: 'Library Owner',
    libraryId: 'library-001',
    libraryName: 'Central Study Library',
    createdAt: '2025-06-01T09:00:00.000Z',
  },
  {
    id: 'student-001',
    name: 'Aarav Sharma',
    email: 'student@smartlibrary.test',
    password: 'Student@123',
    role: AUTH_ROLES.STUDENT,
    roleLabel: 'Student',
    libraryName: 'Central Study Library',
  },
  {
    id: 'superadmin-001',
    name: 'Super Admin',
    email: 'superadmin@smartlibrary.test',
    password: 'Super@123',
    role: AUTH_ROLES.SUPER_ADMIN,
    roleLabel: 'Super Admin',
    libraryName: null,
  },
]

export function toPublicUser(user) {
  if (!user) return null

  const publicUser = { ...user }
  delete publicUser.password

  return publicUser
}

export const authMock = {
  users: mockUsers,
  roles: AUTH_ROLES,
  storageKeys: AUTH_STORAGE_KEYS,
  networkDelayMs: AUTH_NETWORK_DELAY_MS,
}
