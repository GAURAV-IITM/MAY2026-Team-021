import axios from 'axios'

// src/api: Shared HTTP clients and API adapters for future backend integration.
const apiClient = axios.create({
  baseURL: '/api',
})

// TODO: Add authentication headers when the auth token strategy is finalized.
// TODO: Add request and response interceptors when FastAPI integration begins.

export default apiClient
