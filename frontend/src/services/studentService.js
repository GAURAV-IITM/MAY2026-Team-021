import apiClient from '../api/axios.js'

// Student Management uses the real tenant-scoped FastAPI endpoints.
export async function getStudents(filters = {}) {
  const response = await apiClient.get('/students', {
    params: {
      page: filters.page || 1,
      pageSize: filters.pageSize || 100,
      search: filters.search || undefined,
      status: filters.status || undefined,
    },
  })
  return response.data
}

export async function getStudentById(studentId) {
  const response = await apiClient.get(`/students/${studentId}`)
  return response.data
}

export async function createStudent(studentData = {}) {
  const response = await apiClient.post('/students', studentData)
  return response.data
}

export async function updateStudent(studentId, studentData = {}) {
  const response = await apiClient.patch(`/students/${studentId}`, studentData)
  return response.data
}

export async function updateStudentStatus(studentId, status) {
  const response = await apiClient.patch(`/students/${studentId}/status`, { status })
  return response.data
}

export async function deactivateStudent(studentId) {
  return updateStudentStatus(studentId, 'inactive')
}

export async function deleteStudent(studentId) {
  const response = await apiClient.delete(`/students/${studentId}`)
  return response.data
}

export async function inviteStudent(studentId) {
  const response = await apiClient.post(`/students/${studentId}/invitation`)
  return response.data
}
