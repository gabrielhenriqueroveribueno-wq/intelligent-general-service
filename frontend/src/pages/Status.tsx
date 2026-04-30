import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import { CheckCircle2, XCircle, AlertTriangle, RefreshCw, Clock } from 'lucide-react'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import clsx from 'clsx'

interface CheckResult {
  status: 'ok' | 'error' | 'degraded' | 'warning' | 'unknown'
  latency_ms?: number
  version?: string
  error?: string
  queue_depth?: number
  circuits?: Record<string, string>
  active_provider?: string
  free_pct?: number
  free_gb?: number
}

interface HealthData {
  status: 'healthy' | 'degraded' | 'critical'
  checks: Record<string, CheckResult>
  timestamp: number
}

const CHECK_LABELS: Record<string, string> = {
  postgres: 'PostgreSQL',
  redis: 'Redis',
  celery: 'Celery Workers',
  ai_providers: 'Provedores de IA',
  disk: 'Disco',
}

function StatusBadge({ status }: { status: CheckResult['status'] }) {
  if (status === 'ok') return (
    <span className="flex items-center gap-1.5 text-green-600 text-sm font-medium">
      <CheckCircle2 size={16} /> Operacional
    </span>
  )
  if (status === 'error') return (
    <span className="flex items-center gap-1.5 text-red-600 text-sm font-medium">
      <XCircle size={16} /> Erro
    </span>
  )
  if (status === 'degraded' || status === 'warning') return (
    <span className="flex items-center gap-1.5 text-yellow-600 text-sm font-medium">
      <AlertTriangle size={16} /> Degradado
    </span>
  )
  return (
    <span className="flex items-center gap-1.5 text-gray-500 text-sm font-medium">
      <Clock size={16} /> Desconhecido
    </span>
  )
}

export default function Status() {
  const { data, isLoading, refetch, dataUpdatedAt } = useQuery<HealthData>({
    queryKey: ['health-detailed'],
    queryFn: () => api.get('/api/v1/health/detailed').then(r => r.data),
    refetchInterval: 30_000,
    retry: false,
  })

  const overallColor = {
    healthy: 'bg-green-50 border-green-200 text-green-800',
    degraded: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    critical: 'bg-red-50 border-red-200 text-red-800',
  }[data?.status || 'healthy']

  const overallLabel = {
    healthy: '✓ Todos os sistemas operacionais',
    degraded: '⚠ Alguns sistemas com degradação',
    critical: '✕ Falha crítica detectada',
  }[data?.status || 'healthy']

  return (
    <div className="space-y-5 max-w-3xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Status do Sistema</h1>
          <p className="text-sm text-gray-500">Saúde dos componentes em tempo real</p>
        </div>
        <button
          onClick={() => refetch()}
          className="btn-secondary flex items-center gap-2 text-sm"
          disabled={isLoading}
        >
          <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} />
          Atualizar
        </button>
      </div>

      {/* Overall status banner */}
      {data && (
        <div className={clsx('border rounded-xl p-4 font-semibold', overallColor)}>
          {overallLabel}
        </div>
      )}

      {/* Component cards */}
      <div className="card p-0 overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-40">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600" />
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Componente</th>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Status</th>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3 hidden sm:table-cell">Detalhes</th>
                <th className="text-right text-xs font-medium text-gray-500 px-4 py-3 hidden md:table-cell">Latência</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {Object.entries(data?.checks || {}).map(([key, check]) => (
                <tr key={key}>
                  <td className="px-4 py-3 font-medium text-sm text-gray-800">
                    {CHECK_LABELS[key] || key}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={check.status} />
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-500 hidden sm:table-cell">
                    {check.version && `v${check.version}`}
                    {check.queue_depth !== undefined && `Fila: ${check.queue_depth} tarefas`}
                    {check.active_provider && `Provider: ${check.active_provider}`}
                    {check.free_pct !== undefined && `${check.free_gb}GB livres (${check.free_pct}%)`}
                    {check.error && (
                      <span className="text-red-500">{check.error}</span>
                    )}
                    {check.circuits && Object.entries(check.circuits).map(([p, s]) => (
                      <span key={p} className={clsx('mr-2', s === 'open' ? 'text-red-500' : 'text-green-600')}>
                        {p}: {s}
                      </span>
                    ))}
                  </td>
                  <td className="px-4 py-3 text-right text-xs text-gray-500 hidden md:table-cell">
                    {check.latency_ms !== undefined ? `${check.latency_ms}ms` : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {dataUpdatedAt > 0 && (
        <p className="text-xs text-gray-400 text-right">
          Última atualização: {format(new Date(dataUpdatedAt), "HH:mm:ss", { locale: ptBR })}
          {' · '}atualiza a cada 30s
        </p>
      )}
    </div>
  )
}
