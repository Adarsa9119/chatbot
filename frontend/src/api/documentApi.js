import api from './axios';

export const documentApi = {
  getAll:    (params) => api.get('/documents', { params }),
  getById:   (id)     => api.get(`/documents/${id}`),
  getReady:  ()       => api.get('/documents/ready'),
};