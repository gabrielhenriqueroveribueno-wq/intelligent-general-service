import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { api } from '../api/client'

interface User {
  id: string
  email: string
  full_name: string
  role: string
  tenant_id: string | null
  must_change_password?: boolean
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (email: string, password: string) => Promise<{ must_change_password: boolean }>
  logout: () => void
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | null>(null)

// DEMO MODE: set to true to bypass auth and show demo data
const DEMO_MODE = true

const DEMO_USER: User = {
  id: 'demo-001',
  email: 'gestor@anchieta.edu.br',
  full_name: 'Gabriel Bueno',
  role: 'admin',
  tenant_id: 'tenant-001',
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(DEMO_MODE ? DEMO_USER : null)
  const [token, setToken] = useState<string | null>(DEMO_MODE ? 'demo-token' : localStorage.getItem('access_token'))
  const [isLoading, setIsLoading] = useState(DEMO_MODE ? false : true)

  useEffect(() => {
    if (DEMO_MODE) return
    const savedToken = localStorage.getItem('access_token')
    if (savedToken) {
      api.defaults.headers.common['Authorization'] = `Bearer ${savedToken}`
      fetchMe()
    } else {
      setIsLoading(false)
    }
  }, [])

  const fetchMe = async () => {
    try {
      const res = await api.get('/api/v1/auth/me')
      setUser(res.data)
    } catch (_e) {
      localStorage.removeItem('access_token')
      setToken(null)
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (email: string, password: string) => {
    const res = await api.post('/api/v1/auth/login', { email, password })
    const { access_token, refresh_token, must_change_password } = res.data
    localStorage.setItem('access_token', access_token)
    localStorage.setItem('refresh_token', refresh_token)
    api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
    setToken(access_token)
    await fetchMe()
    return { must_change_password: must_change_password ?? false }
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    delete api.defaults.headers.common['Authorization']
    setUser(null)
    setToken(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
