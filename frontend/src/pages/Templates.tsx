import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Send, Trash2, MessageSquare, Loader2, X } from 'lucide-react'
import toast from 'react-hot-toast'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

interface Template {
  id: string
  name: string
  meta_template_name: string
  language_code: string
  category: string
  parameters_schema: Record<string, unknown>
}

const CATEGORIES = ['UTILITY', 'MARKETING', 'AUTHENTICATION']

export default function Templates() {
  const qc = useQueryClient()
  const { user } = useAuth()
  const [showCreate, setShowCreate] = useState(false)
  const [sendState, setSendState] = useState<{ id: string; to: string } | null>(null)
  const [form, setForm] = useState({
    name: '',
    meta_template_name: '',
    language_code: 'pt_BR',
    category: 'UTILITY',
  })

  const { data, isLoading } = useQuery({
    queryKey: ['templates'],
    queryFn: () => api.get('/api/v1/templates').then((r) => r.data),
  })

  const createMutation = useMutation({
    mutationFn: (payload: typeof form) => api.post('/api/v1/templates', payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['templates'] })
      setShowCreate(false)
      setForm({ name: '', meta_template_name: '', language_code: 'pt_BR', category: 'UTILITY' })
      toast.success('Template criado!')
    },
    onError: () => toast.error('Erro ao criar template'),
  })

  const sendMutation = useMutation({
    mutationFn: ({ id, to }: { id: string; to: string }) =>
      api.post(`/api/v1/templates/${id}/send`, { to }),
    onSuccess: () => {
      toast.success('Mensagem enviada!')
      setSendState(null)
    },
    onError: () => toast.error('Erro ao enviar mensagem'),
  })

  const canEdit = user?.role === 'admin' || user?.role === 'super_admin'

  const templates: Template[] = data?.items ?? []

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Templates WhatsApp</h1>
          <p className="text-sm text-gray-500">
            Gerencie templates HSM aprovados pelo Meta para envios proativos
          </p>
        </div>
        {canEdit && (
          <button
            onClick={() => setShowCreate(true)}
            className="btn-primary flex items-center gap-2"
          >
            <Plus size={16} /> Novo template
          </button>
        )}
      </div>

      {/* Lista */}
      {isLoading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="animate-spin text-blue-600" size={24} />
        </div>
      ) : templates.length === 0 ? (
        <div className="card text-center py-12">
          <MessageSquare className="mx-auto text-gray-300 mb-3" size={40} />
          <p className="text-gray-500 font-medium">Nenhum template cadastrado</p>
          <p className="text-sm text-gray-400 mt-1">
            Crie templates aprovados pelo Meta para envios proativos via WhatsApp
          </p>
        </div>
      ) : (
        <div className="grid gap-3">
          {templates.map((t) => (
            <div
              key={t.id}
              className="card flex items-center justify-between gap-4"
            >
              <div className="flex items-start gap-3">
                <div className="bg-green-100 p-2 rounded-lg shrink-0">
                  <MessageSquare size={16} className="text-green-700" />
                </div>
                <div>
                  <p className="font-semibold text-gray-900">{t.name}</p>
                  <p className="text-xs text-gray-500 font-mono">{t.meta_template_name}</p>
                  <div className="flex gap-2 mt-1">
                    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
                      {t.category}
                    </span>
                    <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">
                      {t.language_code}
                    </span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <button
                  onClick={() => setSendState({ id: t.id, to: '' })}
                  className="flex items-center gap-1.5 text-sm text-green-700 hover:text-green-800 font-medium"
                >
                  <Send size={14} /> Enviar
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal criar template */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold">Novo template</h2>
              <button onClick={() => setShowCreate(false)}>
                <X size={20} className="text-gray-400" />
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nome interno
                </label>
                <input
                  className="input"
                  placeholder="Ex: Aviso de boleto vencendo"
                  value={form.name}
                  onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nome no Meta (exato)
                </label>
                <input
                  className="input font-mono text-sm"
                  placeholder="Ex: boleto_vencendo_aviso"
                  value={form.meta_template_name}
                  onChange={(e) =>
                    setForm((f) => ({
                      ...f,
                      meta_template_name: e.target.value.toLowerCase().replace(/\s+/g, '_'),
                    }))
                  }
                />
                <p className="text-xs text-gray-400 mt-1">
                  Deve corresponder exatamente ao nome cadastrado no Meta Business
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Idioma</label>
                  <select
                    className="input"
                    value={form.language_code}
                    onChange={(e) => setForm((f) => ({ ...f, language_code: e.target.value }))}
                  >
                    <option value="pt_BR">Português (BR)</option>
                    <option value="en_US">English (US)</option>
                    <option value="es">Español</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Categoria</label>
                  <select
                    className="input"
                    value={form.category}
                    onChange={(e) => setForm((f) => ({ ...f, category: e.target.value }))}
                  >
                    {CATEGORIES.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            <div className="flex gap-3 mt-5">
              <button
                onClick={() => setShowCreate(false)}
                className="flex-1 py-2 border border-gray-200 rounded-lg text-sm text-gray-700 hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                onClick={() => createMutation.mutate(form)}
                disabled={!form.name || !form.meta_template_name || createMutation.isPending}
                className="flex-1 btn-primary disabled:opacity-50"
              >
                {createMutation.isPending ? 'Salvando...' : 'Criar template'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal enviar */}
      {sendState && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold">Enviar template</h2>
              <button onClick={() => setSendState(null)}>
                <X size={20} className="text-gray-400" />
              </button>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Número de destino
              </label>
              <input
                className="input"
                placeholder="5511999999999 (sem + ou espaços)"
                value={sendState.to}
                onChange={(e) =>
                  setSendState((s) => s && { ...s, to: e.target.value.replace(/\D/g, '') })
                }
              />
              <p className="text-xs text-gray-400 mt-1">
                Formato: código do país + DDD + número (ex: 5511999999999)
              </p>
            </div>

            <div className="flex gap-3 mt-5">
              <button
                onClick={() => setSendState(null)}
                className="flex-1 py-2 border border-gray-200 rounded-lg text-sm text-gray-700"
              >
                Cancelar
              </button>
              <button
                onClick={() =>
                  sendMutation.mutate({ id: sendState.id, to: sendState.to })
                }
                disabled={sendState.to.length < 10 || sendMutation.isPending}
                className="flex-1 btn-primary flex items-center justify-center gap-2 disabled:opacity-50"
              >
                {sendMutation.isPending ? (
                  <Loader2 className="animate-spin" size={14} />
                ) : (
                  <Send size={14} />
                )}
                Enviar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
