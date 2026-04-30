import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Mail,
  Plus,
  Trash2,
  Send,
  Eye,
  X,
  Loader2,
  CheckCircle2,
  Clock,
  Calendar,
} from 'lucide-react'
import toast from 'react-hot-toast'
import clsx from 'clsx'
import { api } from '../api/client'

type Period = 'daily' | 'weekly' | 'monthly'

interface Subscription {
  id: string
  name: string
  period: Period
  recipients: string[]
  is_active: boolean
  send_hour_utc: number
  last_sent_at: string | null
  created_at: string
}

interface FormState {
  name: string
  period: Period
  recipients: string
  send_hour_utc: number
  is_active: boolean
}

const EMPTY_FORM: FormState = {
  name: '',
  period: 'weekly',
  recipients: '',
  send_hour_utc: 11,
  is_active: true,
}

const PERIOD_LABEL: Record<Period, string> = {
  daily: 'Diário',
  weekly: 'Semanal (segundas)',
  monthly: 'Mensal (dia 1)',
}

export default function ReportSubscriptions() {
  const qc = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState<FormState>(EMPTY_FORM)
  const [previewHtml, setPreviewHtml] = useState<string | null>(null)

  const { data: subs, isLoading } = useQuery({
    queryKey: ['report-subscriptions'],
    queryFn: () =>
      api.get('/api/v1/report-subscriptions').then((r) => r.data as Subscription[]),
  })

  const saveMutation = useMutation({
    mutationFn: (payload: {
      id?: string
      body: {
        name: string
        period: Period
        recipients: string[]
        is_active: boolean
        send_hour_utc: number
      }
    }) => {
      if (payload.id) {
        return api
          .patch(`/api/v1/report-subscriptions/${payload.id}`, payload.body)
          .then((r) => r.data)
      }
      return api.post('/api/v1/report-subscriptions', payload.body).then((r) => r.data)
    },
    onSuccess: () => {
      toast.success(editingId ? 'Subscrição atualizada' : 'Subscrição criada')
      qc.invalidateQueries({ queryKey: ['report-subscriptions'] })
      closeForm()
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail || 'Erro ao salvar'
      toast.error(typeof detail === 'string' ? detail : 'Erro de validação')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/report-subscriptions/${id}`),
    onSuccess: () => {
      toast.success('Subscrição removida')
      qc.invalidateQueries({ queryKey: ['report-subscriptions'] })
    },
    onError: () => toast.error('Erro ao remover'),
  })

  const sendNowMutation = useMutation({
    mutationFn: (id: string) =>
      api
        .post(`/api/v1/report-subscriptions/${id}/send-now`, {})
        .then((r) => r.data),
    onSuccess: (data: any) => {
      toast.success(`Relatório enviado para ${data.sent} destinatário(s)`)
      qc.invalidateQueries({ queryKey: ['report-subscriptions'] })
    },
    onError: () => toast.error('Erro ao enviar relatório'),
  })

  const previewMutation = useMutation({
    mutationFn: (period: Period) =>
      api
        .post('/api/v1/report-subscriptions/preview', { period })
        .then((r) => r.data as { html: string; subject: string; kpis: any }),
    onSuccess: (data) => {
      setPreviewHtml(data.html)
    },
    onError: () => toast.error('Erro ao gerar preview'),
  })

  const handleEdit = (sub: Subscription) => {
    setEditingId(sub.id)
    setForm({
      name: sub.name,
      period: sub.period,
      recipients: sub.recipients.join(', '),
      send_hour_utc: sub.send_hour_utc,
      is_active: sub.is_active,
    })
    setShowForm(true)
  }

  const closeForm = () => {
    setShowForm(false)
    setEditingId(null)
    setForm(EMPTY_FORM)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const recipients = form.recipients
      .split(/[,;\n]/)
      .map((r) => r.trim())
      .filter(Boolean)

    if (!form.name.trim() || recipients.length === 0) {
      toast.error('Preencha o nome e pelo menos um email')
      return
    }

    saveMutation.mutate({
      id: editingId ?? undefined,
      body: {
        name: form.name.trim(),
        period: form.period,
        recipients,
        is_active: form.is_active,
        send_hour_utc: form.send_hour_utc,
      },
    })
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Relatórios por Email</h1>
          <p className="text-sm text-gray-500">
            Configure envios automáticos de KPIs para gestores, diretores ou
            stakeholders
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => previewMutation.mutate('weekly')}
            disabled={previewMutation.isPending}
            className="flex items-center gap-2 bg-white border border-gray-200 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-50"
          >
            {previewMutation.isPending ? (
              <Loader2 className="animate-spin" size={16} />
            ) : (
              <Eye size={16} />
            )}
            Preview
          </button>
          <button
            onClick={() => {
              setForm(EMPTY_FORM)
              setEditingId(null)
              setShowForm(true)
            }}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
          >
            <Plus size={16} />
            Nova Subscrição
          </button>
        </div>
      </div>

      {/* Lista de subscricoes */}
      <div className="card p-0 overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <Loader2 className="animate-spin text-blue-600" size={20} />
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">
                  Nome
                </th>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">
                  Frequência
                </th>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">
                  Destinatários
                </th>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">
                  Último envio
                </th>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">
                  Status
                </th>
                <th></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {subs?.map((sub) => (
                <tr key={sub.id} className="hover:bg-gray-50">
                  <td
                    className="px-4 py-3 text-sm font-medium text-gray-900 cursor-pointer"
                    onClick={() => handleEdit(sub)}
                  >
                    {sub.name}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    <span className="inline-flex items-center gap-1">
                      <Calendar size={12} />
                      {PERIOD_LABEL[sub.period]}
                    </span>
                    <span className="ml-2 text-xs text-gray-400">
                      <Clock size={10} className="inline" /> {String(sub.send_hour_utc).padStart(2, '0')}:00 UTC
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {sub.recipients.length === 1 ? (
                      sub.recipients[0]
                    ) : (
                      <span title={sub.recipients.join(', ')}>
                        {sub.recipients[0]} +{sub.recipients.length - 1}
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {sub.last_sent_at
                      ? new Date(sub.last_sent_at).toLocaleDateString('pt-BR')
                      : '—'}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={clsx(
                        'badge',
                        sub.is_active
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-600',
                      )}
                    >
                      {sub.is_active ? 'Ativa' : 'Pausada'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right whitespace-nowrap">
                    <button
                      onClick={() => sendNowMutation.mutate(sub.id)}
                      disabled={sendNowMutation.isPending}
                      title="Enviar agora"
                      className="text-blue-600 hover:text-blue-700 p-1.5 rounded hover:bg-blue-50 disabled:opacity-50"
                    >
                      {sendNowMutation.isPending ? (
                        <Loader2 className="animate-spin" size={16} />
                      ) : (
                        <Send size={16} />
                      )}
                    </button>
                    <button
                      onClick={() => {
                        if (confirm(`Remover subscrição "${sub.name}"?`))
                          deleteMutation.mutate(sub.id)
                      }}
                      title="Remover"
                      className="text-red-600 hover:text-red-700 p-1.5 rounded hover:bg-red-50 ml-1"
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))}
              {!subs?.length && (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-gray-400">
                    <Mail className="mx-auto mb-2 opacity-30" size={32} />
                    <p>Nenhuma subscrição configurada</p>
                    <p className="text-xs mt-1">
                      Crie uma subscrição para receber relatórios automáticos
                    </p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* Info box */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-900">
        <div className="flex items-start gap-2">
          <CheckCircle2 className="text-blue-600 mt-0.5 flex-shrink-0" size={16} />
          <div>
            <p className="font-semibold mb-1">Como funciona?</p>
            <p>
              Subscrições ativas recebem email automático com KPIs do período
              (conversas, taxa de resolução automática, satisfação, tickets pendentes,
              top assuntos). Semanais enviam nas segundas; mensais no dia 1.
            </p>
          </div>
        </div>
      </div>

      {/* Modal form */}
      {showForm && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-xl w-full">
            <div className="flex items-center justify-between p-5 border-b">
              <h2 className="text-lg font-bold">
                {editingId ? 'Editar' : 'Nova'} Subscrição
              </h2>
              <button
                onClick={closeForm}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-5 space-y-4">
              <div>
                <label className="text-xs font-medium text-gray-600">Nome *</label>
                <input
                  type="text"
                  value={form.name}
                  onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                  placeholder="Ex: Relatório do Diretor"
                  className="input w-full mt-1"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-medium text-gray-600">
                    Frequência *
                  </label>
                  <select
                    value={form.period}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, period: e.target.value as Period }))
                    }
                    className="input w-full mt-1"
                  >
                    <option value="daily">Diário</option>
                    <option value="weekly">Semanal (segundas)</option>
                    <option value="monthly">Mensal (dia 1)</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-medium text-gray-600">
                    Horário envio (UTC)
                  </label>
                  <select
                    value={form.send_hour_utc}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, send_hour_utc: Number(e.target.value) }))
                    }
                    className="input w-full mt-1"
                  >
                    {Array.from({ length: 24 }).map((_, h) => (
                      <option key={h} value={h}>
                        {String(h).padStart(2, '0')}:00 UTC ({brtLabel(h)})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="text-xs font-medium text-gray-600">
                  Destinatários * (separados por vírgula)
                </label>
                <textarea
                  value={form.recipients}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, recipients: e.target.value }))
                  }
                  rows={3}
                  placeholder="diretor@escola.com, coordenador@escola.com"
                  className="input w-full mt-1 font-mono text-sm"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  Máximo 20 emails. Não precisa ser usuário do sistema.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <input
                  id="is_active"
                  type="checkbox"
                  checked={form.is_active}
                  onChange={(e) =>
                    setForm((f) => ({ ...f, is_active: e.target.checked }))
                  }
                  className="rounded"
                />
                <label htmlFor="is_active" className="text-sm">
                  Ativa (enviar automaticamente)
                </label>
              </div>

              <div className="flex justify-end gap-2 border-t pt-4">
                <button
                  type="button"
                  onClick={closeForm}
                  className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={saveMutation.isPending}
                  className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
                >
                  {saveMutation.isPending && (
                    <Loader2 className="animate-spin" size={16} />
                  )}
                  {editingId ? 'Salvar alterações' : 'Criar subscrição'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Preview modal */}
      {previewHtml && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="font-bold">Preview do Relatório</h2>
              <button
                onClick={() => setPreviewHtml(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={20} />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-4 bg-gray-50">
              <div
                className="bg-white rounded-lg shadow"
                dangerouslySetInnerHTML={{ __html: previewHtml }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function brtLabel(utcHour: number): string {
  const brt = (utcHour - 3 + 24) % 24
  return `${String(brt).padStart(2, '0')}:00 BRT`
}
