import { STUDENT } from '../constants/roles'
import { ensureRequiredRole } from './authGuard'

// src/guards: Student authorization check.
// TODO: Replace role string checks with backend permission claims when authorization APIs are ready.
export default function studentGuard() {
  return ensureRequiredRole(STUDENT)
}
