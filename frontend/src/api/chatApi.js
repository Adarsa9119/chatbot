import api from './axios';

export const chatApi = {
  ask:            (data)      => api.post('/chat/ask', data),
  getHistory:     (sessionId) => api.get(`/chat/history/${sessionId}`),
};