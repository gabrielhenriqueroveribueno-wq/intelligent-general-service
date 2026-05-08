import { Fragment, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Plug,
  Plus,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Trash2,
  X,
  Pause,
  Play,
  History,
  ChevronDown,
  ChevronUp,
  Database,
} from 'lucide-react'
import toast from 'react-hot-toast'
import clsx from 'clsx'
import { api } from '../api/client'

type ProviderType = 'sophia' | 'totvs' | 'generic_rest' | 'generic_sql'
type StatusType = 'pending' | 'active' | 'paused' | 'error'

interface SyncLog {
  id: string
  started_at: string
  finished_at: string | null
  status: 'success' | 'error' | 'partial' | 'running'
  records_synced: number
  students_created: number
  students_updated: number
  employees_created: number
  employees_updated: number
  duration_ms: number | null
  error_summary: string | null
}

interface Integration {
  id: string
  name: string
  provider_type: ProviderType
  config: Record<string, any>
  has_credentials: boolean
  status: StatusType
  sync_cron: string
  last_sync_at: string | null
  last_sync_duration_ms: number | null
  last_sync_records_synced: number | null
  last_sync_error: string | null
  created_at: string
}

interface ProviderField {
  name: string
  label: string
  type: string
  required?: boolean
  placeholder?: string
  options?: string[]
  default?: string
}

interface Provider {
  type: ProviderType
  label: string
  description: string
  config_fields: ProviderField[]
  credential_fields: ProviderField[]
}

const STATUS_BADGE: Record<StatusType, { label: string; cls: string }> = {
  pending: { label: 'Pendente', cls: 'bg-gray-100 text-gray-700' },
  active: { label: 'Ativa', cls: 'bg-green-100 text-green-700' },
  paused: { label: 'Pausada', cls: 'bg-yellow-100 text-yellow-700' },
  error: { label: 'Erro', cls: 'bg-red-100 text-red-700' },
}

export default function Integrations() {
  const qc = useQueryClient()
  const [showWizard, setShowWizard] = useState(false)
  const [expandedLogs, setExpandedLogs] = useState<string | null>(null)

  const { data: integrations, isLoading } = useQuery({
    queryKey: ['integrations'],
    queryFn: () => api.get('/api/v1/integrations').then((r) => r.data as Integration[]),
  })

  const { data: providers } = useQuery({
    queryKey: ['integrations-providers'],
    queryFn: () =>
      api.get('/api/v1/integrations/providers').then((r) => r.data as Provider[]),
  })

  const testMutation = useMutation({
    mutationFn: (id: string) =>
      api.post(`/api/v1/integrations/${id}/test`, {}).then((r) => r.data),
    onSuccess: (data: any) => {
      if (data.success) toast.success(`Conexão OK: ${data.message}`)
      else toast.error(`Falhou: ${data.message}`)
    },
    onError: () => toast.error('Erro ao testar conexão'),
  })

  const syncMutation = useMutation({
    mutationFn: (id: string) =>
      api.post(`/api/v1/integrations/${id}/sync-now`, {}).then((r) => r.data),
    onSuccess: () => {
      toast.success('Sincronização agendada — atualize em alguns segundos')
      setTimeout(() => qc.invalidateQueries({ queryKey: ['integrations'] }), 3000)
    },
    onError: () => toast.error('Erro ao agendar sync'),
  })

  const togglePauseMutation = useMutation({
    mutationFn: (integ: Integration) =>
      api
        .patch(`/api/v1/integrations/${integ.id}`, {
          status: integ.status === 'active' ? 'paused' : 'active',
        })
        .then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['integrations'] })
    },
    onError: () => toast.error('Erro ao alterar status'),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/integrations/${id}`),
    onSuccess: () => {
      toast.success('Integração removida')
      qc.invalidateQueries({ queryKey: ['integrations'] })
    },
    onError: () => toast.error('Erro ao remover'),
  })

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Integrações</h1>
          <p className="text-sm text-gray-500">
            Conecte o IGS ao Sophia, TOTVS, SQL direto ou qualquer sistema com API REST
          </p>
        </div>
        <button
          onClick={() => setShowWizard(true)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
        >
          <Plus size={16} /> Nova Integração
        </button>
      </div>

      {/* Lista */}
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
                  Sistema
                </th>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">
                  Última sync
                </th>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">
                  Registros
                </th>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">
                  Status
                </th>
                <th></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {integrations?.map((integ) => (
                <Fragment key={integ.id}>
                <tr className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-medium">{integ.name}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 capitalize">
                    {providers?.find((p) => p.type === integ.provider_type)?.label ||
                      integ.provider_type}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {integ.last_sync_at ? (
                      <>
                        {new Date(integ.last_sync_at).toLocaleString('pt-BR')}
                        {integ.last_sync_duration_ms && (
                          <span className="text-xs text-gray-400 ml-2">
                            ({(integ.last_sync_duration_ms / 1000).toFixed(1)}s)
                          </span>
                        )}
                      </>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {integ.last_sync_records_synced ?? '—'}
                  </td>
                  <td className="px-4 py-3">
                    <span className={clsx('badge', STATUS_BADGE[integ.status].cls)}>
                      {STATUS_BADGE[integ.status].label}
                    </span>
                    {integ.last_sync_error && (
                      <p className="text-xs text-red-600 mt-1 max-w-xs truncate" title={integ.last_sync_error}>
                        {integ.last_sync_error}
                      </p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right whitespace-nowrap">
                    <button
                      onClick={() => testMutation.mutate(integ.id)}
                      disabled={testMutation.isPending}
                      title="Testar conexão"
                      className="text-blue-600 hover:bg-blue-50 p-1.5 rounded disabled:opacity-50"
                    >
                      {testMutation.isPending ? (
                        <Loader2 className="animate-spin" size={16} />
                      ) : (
                        <CheckCircle2 size={16} />
                      )}
                    </button>
                    <button
                      onClick={() => syncMutation.mutate(integ.id)}
                      disabled={syncMutation.isPending}
                      title="Sincronizar agora"
                      className="text-blue-600 hover:bg-blue-50 p-1.5 rounded ml-1 disabled:opacity-50"
                    >
                      {syncMutation.isPending ? (
                        <Loader2 className="animate-spin" size={16} />
                      ) : (
                        <RefreshCw size={16} />
                      )}
                    </button>
                    <button
                      onClick={() => togglePauseMutation.mutate(integ)}
                      title={integ.status === 'active' ? 'Pausar' : 'Ativar'}
                      className="text-yellow-600 hover:bg-yellow-50 p-1.5 rounded ml-1"
                    >
                      {integ.status === 'active' ? <Pause size={16} /> : <Play size={16} />}
                    </button>
                    <button
                      onClick={() =>
                        setExpandedLogs(expandedLogs === integ.id ? null : integ.id)
                      }
                      title="Ver histórico de syncs"
                      className="text-gray-500 hover:bg-gray-100 p-1.5 rounded ml-1"
                    >
                      {expandedLogs === integ.id ? (
                        <ChevronUp size={16} />
                      ) : (
                        <History size={16} />
                      )}
                    </button>
                    <button
                      onClick={() => {
                        if (confirm(`Remover integração "${integ.name}"?`))
                          deleteMutation.mutate(integ.id)
                      }}
                      title="Remover"
                      className="text-red-600 hover:bg-red-50 p-1.5 rounded ml-1"
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
                {expandedLogs === integ.id && (
                  <tr>
                    <td colSpan={6} className="bg-gray-50 px-4 pb-3">
                      <SyncLogPanel integrationId={integ.id} />
                    </td>
                  </tr>
                )}
                </Fragment>
              ))}
              {!integrations?.length && (
                <tr>
                  <td colSpan={6} className="text-center py-12 text-gray-400">
                    <Plug className="mx-auto mb-2 opacity-30" size={32} />
                    <p>Nenhuma integração configurada</p>
                    <p className="text-xs mt-1">
                      Conecte o IGS ao seu sistema acadêmico para sincronizar alunos
                      e funcionários automaticamente
                    </p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-900">
        <div className="flex items-start gap-2">
          <CheckCircle2 className="text-blue-600 mt-0.5 flex-shrink-0" size={16} />
          <div>
            <p className="font-semibold mb-1">Como funciona?</p>
            <p>
              Configure uma integração para que o IGS sincronize automaticamente os
              dados de alunos e funcionários do seu sistema acadêmico (Sophia, TOTVS
              ou qualquer sistema com API REST). A sincronização roda no horário
              definido (padrão: a cada 6h). Credenciais ficam criptografadas.
            </p>
          </div>
        </div>
      </div>

      {showWizard && providers && (
        <Wizard
          providers={providers}
          onClose={() => setShowWizard(false)}
          onCreated={() => {
            setShowWizard(false)
            qc.invalidateQueries({ queryKey: ['integrations'] })
          }}
        />
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Wizard
// ─────────────────────────────────────────────────────────────────────────────

function Wizard({
  providers,
  onClose,
  onCreated,
}: {
  providers: Provider[]
  onClose: () => void
  onCreated: () => void
}) {
  const [step, setStep] = useState<'select' | 'configure'>('select')
  const [selected, setSelected] = useState<Provider | null>(null)
  const [name, setName] = useState('')
  const [config, setConfig] = useState<Record<string, any>>({})
  const [credentials, setCredentials] = useState<Record<string, any>>({})
  const [syncCron, setSyncCron] = useState('0 */6 * * *')

  const createMutation = useMutation({
    mutationFn: (payload: any) =>
      api.post('/api/v1/integrations', payload).then((r) => r.data),
    onSuccess: () => {
      toast.success('Integração criada! Teste a conexão antes de ativar.')
      onCreated()
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail || 'Erro ao criar'
      toast.error(typeof detail === 'string' ? detail : 'Erro de validação')
    },
  })

  const setNested = (target: 'config' | 'credentials', path: string, value: any) => {
    const setter = target === 'config' ? setConfig : setCredentials
    const obj = target === 'config' ? config : credentials
    const parts = path.split('.')
    const newObj = JSON.parse(JSON.stringify(obj))
    let cur = newObj
    for (let i = 0; i < parts.length - 1; i++) {
      if (!cur[parts[i]]) cur[parts[i]] = {}
      cur = cur[parts[i]]
    }
    cur[parts[parts.length - 1]] = value
    setter(newObj)
  }

  const getNested = (target: 'config' | 'credentials', path: string): any => {
    const obj = target === 'config' ? config : credentials
    const parts = path.split('.')
    let cur: any = obj
    for (const p of parts) {
      if (cur == null) return ''
      cur = cur[p]
    }
    return cur ?? ''
  }

  const handleCreate = () => {
    if (!selected || !name.trim()) {
      toast.error('Preencha nome e selecione provider')
      return
    }
    createMutation.mutate({
      name: name.trim(),
      provider_type: selected.type,
      config,
      credentials,
      sync_cron: syncCron,
    })
  }

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-5 border-b">
          <h2 className="text-lg font-bold">Nova Integração</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X size={20} />
          </button>
        </div>

        {step === 'select' && (
          <div className="p-5 space-y-3">
            <p className="text-sm text-gray-600 mb-3">
              Escolha o sistema acadêmico que sua escola usa:
            </p>
            {providers.map((p) => (
              <button
                key={p.type}
                onClick={() => {
                  setSelected(p)
                  setStep('configure')
                }}
                className="w-full text-left p-4 border border-gray-200 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition"
              >
                <div className="font-semibold">{p.label}</div>
                <p className="text-xs text-gray-500 mt-1">{p.description}</p>
              </button>
            ))}
          </div>
        )}

        {step === 'configure' && selected && (
          <div className="p-5 space-y-4">
            <div>
              <button
                onClick={() => setStep('select')}
                className="text-xs text-blue-600 hover:underline mb-2"
              >
                ← Trocar provider
              </button>
              <p className="text-sm">
                Configurando <b>{selected.label}</b>
              </p>
            </div>

            <div>
              <label className="text-xs font-medium text-gray-600">
                Nome da integração *
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Ex: Sophia Produção"
                className="input w-full mt-1"
                required
              />
            </div>

            <section className="border-t pt-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">Configuração</h3>
              <div className="space-y-3">
                {selected.config_fields.map((field) => (
                  <DynamicField
                    key={field.name}
                    field={field}
                    value={getNested('config', field.name)}
                    onChange={(v) => setNested('config', field.name, v)}
                  />
                ))}
              </div>
            </section>

            <section className="border-t pt-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">
                Credenciais (criptografadas)
              </h3>
              <div className="space-y-3">
                {selected.credential_fields.map((field) => (
                  <DynamicField
                    key={field.name}
                    field={field}
                    value={getNested('credentials', field.name)}
                    onChange={(v) => setNested('credentials', field.name, v)}
                  />
                ))}
              </div>
            </section>

            <section className="border-t pt-4">
              <label className="text-xs font-medium text-gray-600">
                Frequência de sync (cron)
              </label>
              <select
                value={syncCron}
                onChange={(e) => setSyncCron(e.target.value)}
                className="input w-full mt-1"
              >
                <option value="0 */1 * * *">A cada hora</option>
                <option value="0 */3 * * *">A cada 3 horas</option>
                <option value="0 */6 * * *">A cada 6 horas (recomendado)</option>
                <option value="0 */12 * * *">A cada 12 horas</option>
                <option value="0 6 * * *">Diário (06:00 UTC)</option>
              </select>
            </section>

            <div className="flex justify-end gap-2 border-t pt-4">
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                onClick={handleCreate}
                disabled={createMutation.isPending}
                className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
              >
                {createMutation.isPending && (
                  <Loader2 className="animate-spin" size={16} />
                )}
                Criar integração
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Sync Log Panel
// ─────────────────────────────────────────────────────────────────────────────

const LOG_STATUS: Record<string, { label: string; cls: string }> = {
  success: { label: 'OK', cls: 'text-green-700 bg-green-100' },
  partial: { label: 'Parcial', cls: 'text-yellow-700 bg-yellow-100' },
  error: { label: 'Erro', cls: 'text-red-700 bg-red-100' },
  running: { label: 'Rodando', cls: 'text-blue-700 bg-blue-100' },
}

function SyncLogPanel({ integrationId }: { integrationId: string }) {
  const { data: logs, isLoading } = useQuery({
    queryKey: ['sync-logs', integrationId],
    queryFn: () =>
      api
        .get(`/api/v1/integrations/${integrationId}/logs?limit=10`)
        .then((r) => r.data as SyncLog[]),
    refetchInterval: 10_000,
  })

  if (isLoading)
    return (
      <div className="flex items-center gap-2 py-3 text-sm text-gray-400">
        <Loader2 className="animate-spin" size={14} /> Carregando histórico...
      </div>
    )

  if (!logs?.length)
    return (
      <p className="py-3 text-sm text-gray-400">Nenhuma sync realizada ainda.</p>
    )

  return (
    <div className="mt-2">
      <p className="text-xs font-semibold text-gray-500 mb-2 flex items-center gap-1">
        <History size={12} /> Histórico das últimas syncs
      </p>
      <div className="space-y-1.5">
        {logs.map((log) => {
          const st = LOG_STATUS[log.status] || LOG_STATUS.error
          const dur = log.duration_ms ? `${(log.duration_ms / 1000).toFixed(1)}s` : '—'
          return (
            <div
              key={log.id}
              className="flex items-start gap-3 text-xs bg-white rounded border border-gray-100 px-3 py-2"
            >
              <span className={clsx('px-1.5 py-0.5 rounded font-semibold shrink-0', st.cls)}>
                {st.label}
              </span>
              <span className="text-gray-500 shrink-0">
                {new Date(log.started_at).toLocaleString('pt-BR')}
              </span>
              <span className="text-gray-400 shrink-0">{dur}</span>
              <span className="text-gray-700">
                {log.records_synced} registros
                {log.students_created > 0 && ` · ${log.students_created} alunos criados`}
                {log.students_updated > 0 && ` · ${log.students_updated} atualizados`}
                {log.employees_created > 0 && ` · ${log.employees_created} funcs criados`}
              </span>
              {log.error_summary && (
                <span className="text-red-600 truncate max-w-xs" title={log.error_summary}>
                  {log.error_summary}
                </span>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function DynamicField({
  field,
  value,
  onChange,
}: {
  field: ProviderField
  value: any
  onChange: (v: any) => void
}) {
  if (field.type === 'select' && field.options) {
    return (
      <div>
        <label className="text-xs font-medium text-gray-600">{field.label}</label>
        <select
          value={value || field.default || ''}
          onChange={(e) => onChange(e.target.value)}
          className="input w-full mt-1"
        >
          {field.options.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
      </div>
    )
  }

  return (
    <div>
      <label className="text-xs font-medium text-gray-600">
        {field.label} {field.required && '*'}
      </label>
      <input
        type={field.type === 'password' ? 'password' : field.type === 'url' ? 'url' : 'text'}
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        placeholder={field.placeholder || ''}
        className="input w-full mt-1 font-mono text-sm"
        autoComplete={field.type === 'password' ? 'new-password' : 'off'}
      />
    </div>
  )
}
