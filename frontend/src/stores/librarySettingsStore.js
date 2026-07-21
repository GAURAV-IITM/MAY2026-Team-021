import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import * as librarySettingsService from '../services/librarySettingsService.js'

export const useLibrarySettingsStore = defineStore('librarySettings', () => {
  const settings = ref(null)
  const isLoading = ref(false)
  const isSaving = ref(false)
  const error = ref(null)

  const errorMessage = computed(() => {
    if (!error.value) return ''
    return error.value?.response?.data?.message || error.value?.message || 'An unexpected settings service error occurred.'
  })

  async function fetchSettings() {
    isLoading.value = true
    error.value = null
    try {
      const response = await librarySettingsService.getLibrarySettings()
      settings.value = response.data.settings
      return response
    } catch (requestError) {
      error.value = requestError
      throw requestError
    } finally {
      isLoading.value = false
    }
  }

  async function updateSettings(payload) {
    isSaving.value = true
    error.value = null
    try {
      const response = await librarySettingsService.updateLibrarySettings(payload)
      settings.value = response.data.settings
      return response
    } catch (requestError) {
      error.value = requestError
      throw requestError
    } finally {
      isSaving.value = false
    }
  }

  return { settings, isLoading, isSaving, error, errorMessage, fetchSettings, updateSettings }
})

