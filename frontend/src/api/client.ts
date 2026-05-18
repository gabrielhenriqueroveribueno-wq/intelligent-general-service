import axios from 'axios'
import toast from 'react-hot-toast'

export const api = axios.create({
  baseURL: '/',
  headers: { 'Content-Type': 'application/json' },
})

// Interceptor: adiciona token automaticamente
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Interceptor: trata erros globais
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Tenta refresh
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const res = await axios.post('/api/v1/auth/refresh', { refresh_token: refreshToken })
          localStorage.setItem('access_token', res.data.access_token)
          api.defaults.headers.common['Authorization'] = `Bearer ${res.data.access_token}`
          error.config.headers['Authorization'] = `Bearer ${res.data.access_token}`
          return api.request(error.config)
        } catch (_e) {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          window.location.href = '/login'
        }
      }
    }

    const status = error.response?.status
    if (status === 402 || status === 403) {
      const detail = error.response?.data?.detail || ''
      if (detail.includes('trial') || detail.includes('plano') || detail.includes('plan') || status === 402) {
        // Redirect to billing instead of showing a toast for plan limit errors
        window.location.href = '/app/billing'
        return Promise.reject(error)
      }
    }

    const message = error.response?.data?.detail || 'Ocorreu um erro. Tente novamente.'
    if (status !== 401) {
      toast.error(message)
    }

    return Promise.reject(error)
  },
)
