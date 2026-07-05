import { ADMIN } from '../constants/roles'
import { ensureRequiredRole } from './authGuard'

// src/guards: Library Owner/Admin authorization check.
// TODO: Replace role string checks with backend permission claims when authorization APIs are ready.
export default function adminGuard() {
  return ensureRequiredRole(ADMIN)
}
