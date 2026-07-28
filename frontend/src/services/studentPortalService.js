import apiClient from '../api/axios.js'

export async function getDashboard() {
  const results = await Promise.allSettled([
    getProfile(),
    getSeat(),
    getFees(),
    getRequests(),
    getAnnouncements()
  ])
  
  const profileRes = results[0]
  const seatRes = results[1]
  const feesRes = results[2]
  const requestsRes = results[3]
  const announcementsRes = results[4]
  
  if (profileRes.status === 'rejected') {
    throw profileRes.reason
  }
  
  const profile = profileRes.value.data.profile
  const seat = seatRes.status === 'fulfilled' ? seatRes.value.data.seat : null
  const allocations = seatRes.status === 'fulfilled' ? seatRes.value.data.allocations : []
  const feeSummary = feesRes.status === 'fulfilled' ? feesRes.value.data.feeSummary : null
  const requestsList = requestsRes.status === 'fulfilled' ? requestsRes.value.data.requests : []
  const announcementsList = announcementsRes.status === 'fulfilled' ? announcementsRes.value.data.announcements : []
  
  const activeRequest = requestsList.find(req => req.status === 'pending') || null
  const recentAnnouncements = announcementsList.slice(0, 3)
  const unreadAnnouncementCount = announcementsList.filter(item => !item.isRead).length
  
  return {
    success: true,
    message: 'Student dashboard fetched successfully.',
    data: {
      profile,
      seat,
      allocations,
      feeSummary,
      recentAnnouncements,
      unreadAnnouncementCount,
      activeRequest,
      lastUpdated: new Date().toISOString()
    }
  }
}

export async function getSeat() {
  const response = await apiClient.get('/seat-allocations/me')
  return response.data
}

export async function getFees() {
  const response = await apiClient.get('/payments/me')
  return response.data
}

export async function getReceipts() {
  const response = await apiClient.get('/payments/receipts/me')
  return {
    ...response.data,
    data: {
      receipts: response.data.data
    }
  }
}

export async function getRequests() {
  const response = await apiClient.get('/seat-requests/me')
  return response.data
}

export async function createSeatRequest(studentId, payload = {}) {
  const response = await apiClient.post('/seat-requests/me', {
    preferredSeatId: payload.preferredSeatId || null,
    preferredFloorId: payload.preferredFloorId || null,
    preferredShiftId: payload.preferredShiftId,
    reason: payload.reason
  })
  
  const freshRequests = await getRequests()
  return {
    success: true,
    message: 'Seat change request submitted successfully.',
    data: {
      request: response.data.data,
      requests: freshRequests.data.requests
    }
  }
}

export async function cancelSeatRequest(studentId, requestId) {
  const response = await apiClient.patch(`/seat-requests/me/${requestId}/cancel`)
  const freshRequests = await getRequests()
  return {
    success: true,
    message: 'Seat change request cancelled successfully.',
    data: {
      request: response.data.data,
      requests: freshRequests.data.requests
    }
  }
}

export async function getAnnouncements() {
  const response = await apiClient.get('/announcements/feed')
  return response.data
}

export async function markAnnouncementRead(studentId, announcementId) {
  const response = await apiClient.post(`/announcements/feed/${announcementId}/read`)
  const freshAnnouncements = await getAnnouncements()
  return {
    success: true,
    message: 'Announcement marked as read.',
    data: {
      announcement: response.data.data,
      announcements: freshAnnouncements.data.announcements
    }
  }
}

export async function getProfile() {
  const response = await apiClient.get('/students/me')
  return {
    ...response.data,
    data: {
      profile: response.data.data
    }
  }
}

export async function updateProfile(studentId, payload = {}) {
  const response = await apiClient.patch('/students/me', {
    phone: payload.phone || null,
    address: payload.address || null,
    guardianName: payload.guardianName || null,
    guardianPhone: payload.guardianPhone || null,
    preferredLanguage: payload.preferredLanguage || null
  })
  return {
    ...response.data,
    data: {
      profile: response.data.data
    }
  }
}
