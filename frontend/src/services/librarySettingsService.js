import {
  LIBRARY_SETTINGS_NETWORK_DELAY_MS,
  librarySettingsMock,
} from '../mocks/librarySettingsMock.js'

// TODO: Replace with GET/PATCH /api/libraries/{libraryId}/settings.

let settings = structuredClone(librarySettingsMock)

function delay(ms = LIBRARY_SETTINGS_NETWORK_DELAY_MS) {
  return new Promise((resolve) => globalThis.setTimeout(resolve, ms))
}

function clone(value) {
  return structuredClone(value)
}

function createSuccessResponse(message, data) {
  return {
    success: true,
    message,
    data: clone(data),
    meta: {
      source: 'mock-library-settings-service',
      timestamp: new Date().toISOString(),
    },
  }
}

function createSettingsError(message, code = 'LIBRARY_SETTINGS_INVALID') {
  const error = new Error(message)
  error.response = {
    status: 422,
    data: { success: false, message, error: { code } },
  }
  return error
}

function validateSettings(payload = {}) {
  const normalized = {
    ...settings,
    ...clone(payload),
    libraryName: String(payload.libraryName ?? settings.libraryName).trim(),
    contactEmail: String(payload.contactEmail ?? settings.contactEmail).trim(),
    contactPhone: String(payload.contactPhone ?? settings.contactPhone).replace(/\D/g, ''),
    address: String(payload.address ?? settings.address).trim(),
    city: String(payload.city ?? settings.city).trim(),
    state: String(payload.state ?? settings.state).trim(),
    postalCode: String(payload.postalCode ?? settings.postalCode).replace(/\D/g, ''),
    receiptPrefix: String(payload.receiptPrefix ?? settings.receiptPrefix)
      .trim()
      .toUpperCase(),
    defaultMonthlyFee: Number(payload.defaultMonthlyFee),
    feeDueDay: Number(payload.feeDueDay),
    paymentGraceDays: Number(payload.paymentGraceDays),
  }

  if (normalized.libraryName.length < 3) {
    throw createSettingsError('Library name must contain at least 3 characters.')
  }
  if (!/^\S+@\S+\.\S+$/.test(normalized.contactEmail)) {
    throw createSettingsError('Enter a valid library contact email address.')
  }
  if (!/^\d{10}$/.test(normalized.contactPhone)) {
    throw createSettingsError('Contact phone must contain exactly 10 digits.')
  }
  if (!normalized.address || !normalized.city || !normalized.state) {
    throw createSettingsError('Library address, city, and state are required.')
  }
  if (!/^\d{6}$/.test(normalized.postalCode)) {
    throw createSettingsError('Postal code must contain exactly 6 digits.')
  }
  if (!normalized.openingTime || !normalized.closingTime) {
    throw createSettingsError('Opening and closing times are required.')
  }
  if (normalized.openingTime >= normalized.closingTime) {
    throw createSettingsError('Closing time must be later than opening time.')
  }
  if (!Number.isFinite(normalized.defaultMonthlyFee) || normalized.defaultMonthlyFee < 1) {
    throw createSettingsError('Default monthly fee must be greater than zero.')
  }
  if (!Number.isInteger(normalized.feeDueDay) || normalized.feeDueDay < 1 || normalized.feeDueDay > 28) {
    throw createSettingsError('Fee due day must be between 1 and 28.')
  }
  if (!Number.isInteger(normalized.paymentGraceDays) || normalized.paymentGraceDays < 0 || normalized.paymentGraceDays > 30) {
    throw createSettingsError('Payment grace period must be between 0 and 30 days.')
  }
  if (!/^[A-Z0-9]{2,10}$/.test(normalized.receiptPrefix)) {
    throw createSettingsError('Receipt prefix must contain 2 to 10 letters or numbers.')
  }

  return normalized
}

export async function getLibrarySettings() {
  await delay()
  return createSuccessResponse('Library settings fetched successfully.', { settings })
}

export async function updateLibrarySettings(payload = {}) {
  await delay()
  settings = {
    ...validateSettings(payload),
    updatedAt: new Date().toISOString(),
  }
  return createSuccessResponse('Library settings updated successfully.', { settings })
}

export function getCurrentLibrarySettings() {
  return clone(settings)
}
