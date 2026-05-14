import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Bot, Loader2, Mail, ArrowLeft, CheckCircle2 } from 'lucide-react'
import { api } from '../api/client'
import toast from 'react-hot-toast'

export default function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [sent, setSent] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    try {
      await api.post('/api/v1/auth/forgot-password', { email })
      setSent(true)
    } catch {
      toast.error('Erro ao processar solicitação. Tente novamente.')
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

        {sent ? (
          <div className="text-center">
            <div className="flex justify-center mb-4">
              <CheckCircle2 size={48} className="text-green-500" />
            </div>
            <h1 className="text-xl font-bold text-gray-900 mb-2">Email enviado!</h1>
            <p className="text-gray-500 text-sm mb-6">
              Se o endereço <strong>{email}</strong> estiver cadastrado, você receberá
              as instruções de redefinição em breve. Verifique também a pasta de spam.
            </p>
            <Link
              to="/login"
              className="inline-flex items-center gap-2 text-blue-600 hover:underline text-sm"
            >
              <ArrowLeft size={16} />
              Voltar ao login
            </Link>
          </div>
        ) : (
          <>
            <h1 className="text-2xl font-bold text-gray-900 mb-1">Esqueceu a senha?</h1>
            <p className="text-gray-500 text-sm mb-7">
              Digite seu e-mail e enviaremos um link para redefinir sua senha.
            </p>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">E-mail</label>
                <div className="relative">
                  <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                  <input
                    type="email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    required
                    placeholder="seu@email.com.br"
                    className="w-full border rounded-lg pl-9 pr-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full btn-primary py-3 flex items-center justify-center gap-2 disabled:opacity-60"
              >
                {loading ? <Loader2 size={18} className="animate-spin" /> : null}
                {loading ? 'Enviando...' : 'Enviar link de redefinição'}
              </button>
            </form>

            <p className="text-sm text-gray-600 mt-5 text-center">
              Lembrou a senha?{' '}
              <Link to="/login" className="text-blue-600 hover:underline font-medium">Entrar</Link>
            </p>
          </>
        )}
      </div>
    </div>
  )
}
