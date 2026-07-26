import apiClient from '../api/axios.js'

let currentSettings = {
  receiptPrefix: 'REC',
  whatsappRemindersEnabled: true,
  defaultMonthlyFee: 0,
  allowSeatChangeRequests: true,
  requireSeatRequestReason: true,
}

function normalizeSettings(settings) {
  currentSettings = {
    ...currentSettings,
    ...settings,
    openingTime: String(settings.openingTime || '').slice(0, 5),
    closingTime: String(settings.closingTime || '').slice(0, 5),
  }
  return currentSettings
}

export async function getLibrarySettings() {
  const response = await apiClient.get('/settings/library')
  return {
    ...response.data,
    data: { settings: normalizeSettings(response.data.data) },
  }
}

export async function updateLibrarySettings(payload = {}) {
  const response = await apiClient.patch('/settings/library', payload)
  return {
    ...response.data,
    data: { settings: normalizeSettings(response.data.data) },
  }
}

export function getCurrentLibrarySettings() {
  return { ...currentSettings }
}
