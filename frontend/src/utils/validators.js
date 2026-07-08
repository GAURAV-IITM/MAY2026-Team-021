// src/utils: Framework-agnostic validation helpers shared across frontend forms.

export function isRequired(value) {
  if (typeof value === 'string') {
    return value.trim() !== ''
  }

  return value !== null && value !== undefined && value !== ''
}

export function isValidEmail(value) {
  if (!isRequired(value)) return false

  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

  return emailPattern.test(String(value).trim())
}

export function hasMinLength(value, minLength) {
  if (!isRequired(value)) return false

  return String(value).length >= minLength
}

export function isValidIndianPhone(value) {
  if (!isRequired(value)) return false

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

export function validateLoginForm({ email, password }) {
  const errors = {
    email: '',
    password: '',
  }

  if (!isRequired(email)) {
    errors.email = 'Email is required.'
  } else if (!isValidEmail(email)) {
    errors.email = 'Enter a valid email address.'
  }

  if (!isRequired(password)) {
    errors.password = 'Password is required.'
  } else if (!hasMinLength(password, 8)) {
    errors.password = 'Password must be at least 8 characters.'
  }

  return errors
}

export function hasValidationErrors(errors) {
  return Object.values(errors).some(Boolean)
}