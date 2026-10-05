import request from '@/utils/request'

export function getServiceCatalog() {
  return request.get('/services/catalog')
}

export function getAdminServiceCatalog(params) {
  return request.get('/admin/services/catalog', { params })
}

export function createServiceCatalog(data) {
  return request.post('/admin/services/catalog', data)
}

export function updateServiceCatalog(id, data) {
  return request.put(`/admin/services/catalog/${id}`, data)
}

export function getServiceSlots(params) {
  return request.get('/services/slots', { params })
}

export function createBooking(data) {
  return request.post('/services/bookings', data)
}

export function getMyBookings(params) {
  return request.get('/services/bookings', { params })
}

export function getAdminBookings(params) {
  return request.get('/admin/services/bookings', { params })
}

export function updateBooking(id, data) {
  return request.put(`/admin/services/bookings/${id}`, data)
}
