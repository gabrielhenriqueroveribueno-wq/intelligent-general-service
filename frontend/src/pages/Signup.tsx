import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Bot, CheckCircle2, Loader2 } from 'lucide-react'
import { api } from '../api/client'
import toast from 'react-hot-toast'

interface SignupForm {
  institution_name: string
  slug: string
  admin_name: string
  admin_email: string
  admin_password: string
  admin_password_confirm: string
  phone: string
}

const PLAN_FEATURES = [
  'Atendimento WhatsApp 24/7 com IA',
  'Painel admin completo',
  'Notas, boletos, frequência, holerite',
  'Tickets e SLA',
  'Relatórios semanais',
]

export default function Signup() {
  const navigate = useNavigate()
  const [form, setForm] = useState<SignupForm>({
    institution_name: '',
    slug: '',
    admin_name: '',
    admin_email: '',
    admin_password: '',
    admin_password_confirm: '',
    phone: '',
  })
  const [loading, setLoading] = useState(false)
  const [termsAccepted, setTermsAccepted] = useState(false)

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const { name, value } = e.target
    const updated: Partial<SignupForm> = { [name]: value }
    // Auto-gera slug a partir do nome da instituição
    if (name === 'institution_name') {
      updated.slug = value
        .toLowerCase()
        .normalize('NFD')
        .replace(/[̀-ͯ]/g, '')
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-|-$/g, '')
    }
    setForm(prev => ({ ...prev, ...updated }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!termsAccepted) {
      toast.error('Você precisa aceitar os Termos de Uso e a Política de Privacidade')
      return
    }
    if (form.admin_password !== form.admin_password_confirm) {
      toast.error('As senhas não coincidem')
      return
    }
    if (form.admin_password.length < 8) {
      toast.error('Senha deve ter pelo menos 8 caracteres')
      return
    }
    setLoading(true)
    try {
      await api.post('/api/v1/auth/signup', {
        institution_name: form.institution_name,
        slug: form.slug,
        admin_name: form.admin_name,
        admin_email: form.admin_email,
        admin_password: form.admin_password,
        phone: form.phone,
      })
      toast.success('Conta criada! Faça login para continuar.')
      navigate('/login?next=/onboarding')
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Erro ao criar conta. Tente novamente.'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Left panel */}
      <div className="hidden lg:flex w-1/2 bg-gradient-to-br from-blue-600 to-indigo-800 text-white flex-col justify-center px-16">
        <div className="flex items-center gap-3 mb-10">
          <div className="bg-white/20 p-2.5 rounded-xl">
            <Bot size={28} />
          </div>
          <span className="text-2xl font-bold">IGS</span>
        </div>
        <h2 className="text-3xl font-bold mb-4">
          Sua escola atendendo 24h em 1 hora de setup
        </h2>
        <p className="text-blue-100 mb-10 leading-relaxed">
          14 dias grátis, sem cartão de crédito. Cancele quando quiser.
        </p>
        <ul className="space-y-3">
          {PLAN_FEATURES.map(f => (
            <li key={f} className="flex items-center gap-3 text-blue-100">
              <CheckCircle2 size={18} className="text-green-300 flex-shrink-0" />
              {f}
            </li>
          ))}
        </ul>
      </div>

      {/* Right panel */}
      <div className="flex-1 flex items-center justify-center px-6 py-10">
        <div className="w-full max-w-md">
          <div className="lg:hidden flex items-center gap-2 mb-6">
            <Bot size={22} className="text-blue-600" />
            <span className="font-bold text-gray-900">IGS</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-1">Criar conta grátis</h1>
          <p className="text-gray-500 mb-7 text-sm">14 dias de trial. Sem cartão.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nome da instituição *
              </label>
              <input
                name="institution_name"
                value={form.institution_name}
                onChange={handleChange}
                required
                placeholder="Faculdade Exemplo"
                className="w-full border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Identificador único (slug)
              </label>
              <div className="flex items-center border rounded-lg overflow-hidden focus-within:ring-2 focus-within:ring-blue-500">
                <span className="px-3 py-2.5 bg-gray-50 text-gray-500 text-sm border-r">igs.com.br/</span>
                <input
                  name="slug"
                  value={form.slug}
                  onChange={handleChange}
                  required
                  placeholder="faculdade-exemplo"
                  className="flex-1 px-3 py-2.5 text-sm focus:outline-none"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Seu nome *</label>
                <input
                  name="admin_name"
                  value={form.admin_name}
                  onChange={handleChange}
                  required
                  placeholder="Ana Silva"
                  className="w-full border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">WhatsApp</label>
                <input
                  name="phone"
                  value={form.phone}
                  onChange={handleChange}
                  placeholder="(11) 99999-9999"
                  className="w-full border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">E-mail *</label>
              <input
                type="email"
                name="admin_email"
                value={form.admin_email}
                onChange={handleChange}
                required
                placeholder="ana@faculdade.edu.br"
                className="w-full border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Senha *</label>
                <input
                  type="password"
                  name="admin_password"
                  value={form.admin_password}
                  onChange={handleChange}
                  required
                  placeholder="Mínimo 8 caracteres"
                  className="w-full border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Confirmar *</label>
                <input
                  type="password"
                  name="admin_password_confirm"
                  value={form.admin_password_confirm}
                  onChange={handleChange}
                  required
                  placeholder="Repita a senha"
                  className="w-full border rounded-lg px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <label className="flex items-start gap-3 cursor-pointer select-none">
              <input
                type="checkbox"
                checked={termsAccepted}
                onChange={e => setTermsAccepted(e.target.checked)}
                className="mt-0.5 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 flex-shrink-0"
              />
              <span className="text-xs text-gray-600 leading-relaxed">
                Li e aceito os{' '}
                <a href="/legal" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                  Termos de Uso
                </a>
                {' '}e a{' '}
                <a href="/legal#privacidade" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                  Política de Privacidade
                </a>
                , incluindo o tratamento dos meus dados conforme a LGPD.
              </span>
            </label>

            <button
              type="submit"
              disabled={loading || !termsAccepted}
              className="w-full btn-primary py-3 flex items-center justify-center gap-2 disabled:opacity-60"
            >
              {loading ? <Loader2 size={18} className="animate-spin" /> : null}
              {loading ? 'Criando conta...' : 'Criar conta grátis'}
            </button>
          </form>
          <p className="text-sm text-gray-600 mt-3 text-center">
            Já tem conta?{' '}
            <Link to="/login" className="text-blue-600 hover:underline font-medium">Entrar</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
