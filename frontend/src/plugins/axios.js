import apiClient from '../api/axios'

// src/plugins: Vue plugin setup helpers used by the application bootstrap.
export function setupAxios(app) {
  // TODO: Register Axios globally only if components need direct access to the API client.
  app.config.globalProperties.$axios = apiClient
}
