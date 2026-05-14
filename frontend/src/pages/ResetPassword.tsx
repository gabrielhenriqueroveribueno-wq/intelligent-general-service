import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { Bot, Loader2, Eye, EyeOff, CheckCircle2 } from 'lucide-react'
import { api } from '../api/client'
import toast from 'react-hot-toast'

export default function ResetPassword() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token') || ''

  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [showPass, setShowPass] = useState(false)
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)

  if (!token) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 to-gray-900 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
          <p className="text-red-500 font-medium mb-4">Link inválido ou expirado.</p>
          <Link to="/forgot-password" className="text-blue-600 hover:underline text-sm">
            Solicitar novo link
          </Link>
        </div>
      </div>
    )
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (password !== confirm) {
      toast.error('As senhas não coincidem')
      return
    }
    if (password.length < 8) {
      toast.error('Senha deve ter pelo menos 8 caracteres')
      return
    }
    setLoading(true)
    try {
      await api.post('/api/v1/auth/reset-password', { token, new_password: password })
      setDone(true)
      setTimeout(() => navigate('/login'), 3000)
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Token inválido ou expirado. Solicite um novo link.'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 to-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl p-8">
        <div className="flex items-center gap-2 mb-6">
          <div className="bg-blue-100 p-2 rounded-xl">
            <Bot size={22} className="text-blue-600" />
          </div>
          <span className="font-bold text-gray-900">IGS</span>
        </div>

        {done ? (
          <div className="text-center">
            <CheckCircle2 size={48} className="text-green-500 mx-auto mb-4" />
            <h1 className="text-xl font-bold text-gray-900 mb-2">Senha redefinida!</h1>
            <p className="text-gray-500 text-sm">Redirecionando para o login...</p>
          </div>
        ) : (
          <>
            <h1 className="text-2xl font-bold text-gray-900 mb-1">Nova senha</h1>
            <p className="text-gray-500 text-sm mb-7">
              Escolha uma senha forte com pelo menos 8 caracteres.
            </p>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nova senha *</label>
                <div className="relative">
                  <input
                    type={showPass ? 'text' : 'password'}
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    required
                    placeholder="Mínimo 8 caracteres"
                    className="w-full border rounded-lg px-3 pr-10 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPass(p => !p)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Confirmar senha *</label>
                <input
                  type="password"
                  value={confirm}
                  onChange={e => setConfirm(e.target.value)}
                  required
                  placeholder="Repita a senha"
                  className="w-full border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full btn-primary py-3 flex items-center justify-center gap-2 disabled:opacity-60"
              >
                {loading ? <Loader2 size={18} className="animate-spin" /> : null}
                {loading ? 'Salvando...' : 'Redefinir senha'}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  )
}
