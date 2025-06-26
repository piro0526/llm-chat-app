import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle token expiration
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      window.location.href = '/'
    }
    return Promise.reject(error)
  }
)

// Auth endpoints
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  register: (email: string, password: string) =>
    api.post('/auth/register', { email, password }),
  me: () => api.get('/auth/me'),
}

// Projects endpoints
export const projectsApi = {
  getAll: () => api.get('/projects'),
  getById: (id: string) => api.get(`/projects/${id}`),
  create: (data: { title: string; description?: string }) =>
    api.post('/projects', data),
  update: (id: string, data: { title?: string; description?: string }) =>
    api.put(`/projects/${id}`, data),
  delete: (id: string) => api.delete(`/projects/${id}`),
}

// Chat Sessions endpoints
export const chatSessionsApi = {
  create: (projectId: string, data: { title?: string }) =>
    api.post(`/projects/${projectId}/sessions`, data),
  getAll: (projectId: string) =>
    api.get(`/projects/${projectId}/sessions`),
  getById: (projectId: string, sessionId: string) =>
    api.get(`/projects/${projectId}/sessions/${sessionId}`),
  update: (projectId: string, sessionId: string, data: { title?: string }) =>
    api.put(`/projects/${projectId}/sessions/${sessionId}`, data),
  delete: (projectId: string, sessionId: string) =>
    api.delete(`/projects/${projectId}/sessions/${sessionId}`),
}

// Chat endpoints
export const chatApi = {
  send: (data: {
    message: string
    session_id: string
    provider: string
    model?: string
  }) => api.post('/chat', data),
  getHistory: (sessionId: string) => api.get(`/chat/sessions/${sessionId}/history`),
  clearHistory: (sessionId: string) => api.delete(`/chat/sessions/${sessionId}/history`),
}

// LLM Settings endpoints
export const llmSettingsApi = {
  getAll: () => api.get('/llm-settings'),
  getByProvider: (provider: string) => api.get(`/llm-settings/${provider}`),
  create: (data: { provider: string; api_key: string; model: string }) =>
    api.post('/llm-settings', data),
  update: (provider: string, data: { api_key?: string; model?: string }) =>
    api.put(`/llm-settings/${provider}`, data),
  delete: (provider: string) => api.delete(`/llm-settings/${provider}`),
}