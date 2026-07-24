import axios from 'axios'

// src/api: Shared HTTP clients and API adapters for backend integration.
const apiClient = axios.create({
  baseURL: '/api/v1',
})

// Request interceptor: Attach access token if present
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('smart_library_access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor: Handle 401 errors and try token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    
    // If response is 401 and request has not been retried yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      const refreshToken = localStorage.getItem('smart_library_refresh_token')
      
      if (refreshToken) {
        try {
          // Use plain axios instance to request refresh token (avoiding interceptor loop)
          const response = await axios.post('/api/v1/auth/refresh', {
            refresh_token: refreshToken,
          })
          
          const { access_token, refresh_token } = response.data
          localStorage.setItem('smart_library_access_token', access_token)
          localStorage.setItem('smart_library_refresh_token', refresh_token)
          
          // Update authorization header and retry original request
          originalRequest.headers.Authorization = `Bearer ${access_token}`
          return axios(originalRequest)
        } catch (refreshError) {
          // Clear session data if refresh fails and redirect to login page
          localStorage.removeItem('smart_library_access_token')
          localStorage.removeItem('smart_library_refresh_token')
          localStorage.removeItem('smart_library_auth_session')
          window.location.href = '/login'
          return Promise.reject(refreshError)
        }
      }
    }
    
    return Promise.reject(error)
  }
)

export default apiClient
