import api from './axios';

export const auditApi = {
  getLogs:   (params) => api.get('/audit', { params }),
  getById:   (id)     => api.get(`/audit/${id}`),
};