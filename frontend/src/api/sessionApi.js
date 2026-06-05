import api from './axios';

export const sessionApi = {
  getAll:    ()   => api.get('/sessions'),
  getById:   (id) => api.get(`/sessions/${id}`),
  create:    ()   => api.post('/sessions'),
  delete:    (id) => api.delete(`/sessions/${id}`),
};