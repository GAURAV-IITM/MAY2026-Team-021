// src/utils: Framework-agnostic validation helpers shared across frontend forms.

export function isRequired(value) {
  if (typeof value === 'string') {
    return value.trim() !== ''
  }

  return value !== null && value !== undefined && value !== ''
}

export function isValidEmail(value) {
  if (!isRequired(value)) return false

  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value).trim())
}

export function isValidIndianPhone(value) {
  return /^[6-9]\d{9}$/.test(String(value).trim())
}

export function isNonNegativeNumber(value) {
  if (!isRequired(value)) return false

  const number = Number(value)

  return Number.isFinite(number) && number >= 0
}

export function isPositiveNumber(value) {
  if (!isRequired(value)) return false

  const number = Number(value)

  return Number.isFinite(number) && number > 0
}