// src/utils: Framework-agnostic helpers and constants shared across the frontend.
// TODO: Add form validators when forms are implemented.
export function isRequired(value) {
  return value !== null && value !== undefined && value !== ''
}
