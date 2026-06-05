import api from './axios';

export const adminApi = {
  getUsers:       (params) => api.get('/admin/users', { params }),
  getUserById:    (id)     => api.get(`/admin/users/${id}`),
  updateUserRole: (id, data) => api.patch(`/admin/users/${id}/role`, data),
  deleteUser:     (id)     => api.delete(`/admin/users/${id}`),
  getDashboard:   ()       => api.get('/admin/dashboard'),
  uploadDocument: (formData) => api.post('/admin/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  deleteDocument: (id)     => api.delete(`/admin/documents/${id}`),
  reprocessDocument: (id)  => api.post(`/admin/documents/${id}/reprocess`),
};