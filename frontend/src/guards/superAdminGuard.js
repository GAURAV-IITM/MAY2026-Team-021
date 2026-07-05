import { SUPER_ADMIN } from '../constants/roles'
import { ensureRequiredRole } from './authGuard'

// src/guards: Super Admin authorization check.
// TODO: Replace role string checks with backend permission claims when authorization APIs are ready.
export default function superAdminGuard() {
  return ensureRequiredRole(SUPER_ADMIN)
}
