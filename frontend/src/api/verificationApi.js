import api from './axios';

export const verificationApi = {
  verifyEmail:  (token) => api.post('/auth/verify-email', { token }),
  resendEmail:  ()      => api.post('/auth/resend-verification'),
};