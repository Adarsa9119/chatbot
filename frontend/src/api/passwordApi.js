import api from './axios';

export const passwordApi = {
  forgotPassword: (data) => api.post('/password/forgot', data),
  resetPassword:  (data) => api.post('/password/reset', data),
  changePassword: (data) => api.post('/password/change', data),
};