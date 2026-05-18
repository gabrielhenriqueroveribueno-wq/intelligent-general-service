import { useState } from 'react'
import { api } from '../../api/client'
import { Loader2, CheckCircle2, Send } from 'lucide-react'

interface LeadFormProps {
  source?: string
  onSuccess?: () => void
  compact?: boolean
}

export default function LeadForm({ source = 'landing', onSuccess, compact = false }: LeadFormProps) {
  const [form, setForm] = useState({ name: '', email: '', phone: '', institution: '', message: '' })
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.name || !form.email) {
      setError('Nome e email são obrigatórios.')
      return
    }
    setLoading(true)
    setError('')
    try {
      const params = new URLSearchParams(window.location.search)
      await api.post('/api/v1/leads', {
        ...form,
        source,
        utm_source: params.get('utm_source') || undefined,
        utm_medium: params.get('utm_medium') || undefined,
        utm_campaign: params.get('utm_campaign') || undefined,
      })
      setDone(true)
      onSuccess?.()
    } catch {
      setError('Erro ao enviar. Tente novamente ou escreva para contato@igs.com.br')
    } finally {
      setLoading(false)
    }
  }

  if (done) {
    return (
      <div className="flex flex-col items-center gap-3 py-6 text-center">
        <CheckCircle2 size={40} className="text-green-500" />
        <p className="font-semibold text-gray-900 text-lg">Mensagem enviada!</p>
        <p className="text-gray-500 text-sm">Nossa equipe entrará em contato em até 1 dia útil.</p>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className={`space-y-3 ${compact ? '' : 'max-w-lg w-full'}`}>
      <div className={`grid gap-3 ${compact ? 'grid-cols-1' : 'grid-cols-1 sm:grid-cols-2'}`}>
        <input
          type="text"
          placeholder="Seu nome *"
          value={form.name}
          onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
          required
          className="px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <input
          type="email"
          placeholder="Email institucional *"
          value={form.email}
          onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
          required
          className="px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <input
          type="tel"
          placeholder="WhatsApp"
          value={form.phone}
          onChange={e => setForm(f => ({ ...f, phone: e.target.value }))}
          className="px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <input
          type="text"
          placeholder="Nome da instituição"
          value={form.institution}
          onChange={e => setForm(f => ({ ...f, institution: e.target.value }))}
          className="px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      {!compact && (
        <textarea
          placeholder="Mensagem (opcional)"
          value={form.message}
          onChange={e => setForm(f => ({ ...f, message: e.target.value }))}
          rows={3}
          className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
        />
      )}
      {error && <p className="text-red-500 text-xs">{error}</p>}
      <button
        type="submit"
        disabled={loading}
        className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg flex items-center justify-center gap-2 transition-colors disabled:opacity-60"
      >
        {loading ? <Loader2 size={18} className="animate-spin" /> : <Send size={16} />}
        {loading ? 'Enviando...' : 'Falar com vendas'}
      </button>
    </form>
  )
}
