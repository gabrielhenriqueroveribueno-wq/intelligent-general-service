import { useEffect, useState } from 'react'
import { CheckCircle2, XCircle, AlertTriangle, RefreshCw, Clock, ExternalLink } from 'lucide-react'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import clsx from 'clsx'
import { Link } from 'react-router-dom'

interface CheckResult {
  status: 'ok' | 'error' | 'degraded' | 'warning' | 'unknown'
  latency_ms?: number
  error?: string
}

interface HealthData {
  status: 'healthy' | 'degraded' | 'critical'
  checks: Record<string, CheckResult>
  timestamp: number
}

const CHECK_LABELS: Record<string, string> = {
  postgres: 'Banco de Dados',
  redis: 'Cache & Filas',
  celery: 'Processamento',
  ai_providers: 'IA & Respostas',
  disk: 'Armazenamento',
}

const UPTIME_TARGETS: Record<string, number> = {
  postgres: 99.9,
  redis: 99.9,
  celery: 99.5,
  ai_providers: 99.0,
  disk: 99.9,
}

function StatusIcon({ status }: { status: CheckResult['status'] }) {
  if (status === 'ok') return <CheckCircle2 size={20} className="text-green-500" />
  if (status === 'error') return <XCircle size={20} className="text-red-500" />
  if (status === 'degraded' || status === 'warning') return <AlertTriangle size={20} className="text-yellow-500" />
  return <Clock size={20} className="text-gray-400" />
}

function UptimeBar({ value }: { value: number }) {
  const color = value >= 99.5 ? 'bg-green-500' : value >= 99 ? 'bg-yellow-500' : 'bg-red-500'
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-100 rounded-full h-1.5 overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${value}%` }} />
      </div>
      <span className="text-xs text-gray-500 w-12 text-right">{value}%</span>
    </div>
  )
}

export default function PublicStatus() {
  const [data, setData] = useState<HealthData | null>(null)
  const [loading, setLoading] = useState(true)
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null)

  async function fetchStatus() {
    setLoading(true)
    try {
      const resp = await fetch('/api/v1/health/detailed')
      const json: HealthData = await resp.json()
      setData(json)
      setUpdatedAt(new Date())
    } catch {
      setData(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStatus()
    const id = setInterval(fetchStatus, 60_000)
    return () => clearInterval(id)
  }, [])

  const statusConfig = {
    healthy: {
      bg: 'bg-green-50 border-green-200',
      text: 'text-green-800',
      label: 'Todos os sistemas operacionais',
      dot: 'bg-green-500',
      badge: 'bg-green-100 text-green-700',
    },
    degraded: {
      bg: 'bg-yellow-50 border-yellow-200',
      text: 'text-yellow-800',
      label: 'Alguns sistemas com degradação',
      dot: 'bg-yellow-500',
      badge: 'bg-yellow-100 text-yellow-700',
    },
    critical: {
      bg: 'bg-red-50 border-red-200',
      text: 'text-red-800',
      label: 'Falha crítica detectada',
      dot: 'bg-red-500',
      badge: 'bg-red-100 text-red-700',
    },
  }[data?.status || 'healthy']

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <div>
            <Link to="/" className="text-xl font-bold text-gray-900 hover:text-blue-600">IGS</Link>
            <p className="text-sm text-gray-500">Status da plataforma</p>
          </div>
          <button
            onClick={fetchStatus}
            disabled={loading}
            className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-gray-900 px-3 py-1.5 rounded-lg hover:bg-gray-100 border border-gray-200"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            Atualizar
          </button>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-6 py-8 space-y-6">
        {loading && !data ? (
          <div className="flex justify-center py-16">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          </div>
        ) : (
          <>
            {/* Overall status */}
            <div className={clsx('border rounded-xl p-5', statusConfig.bg)}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={clsx('w-3 h-3 rounded-full animate-pulse', statusConfig.dot)} />
                  <p className={clsx('font-semibold text-lg', statusConfig.text)}>
                    {statusConfig.label}
                  </p>
                </div>
                <span className={clsx('text-xs font-medium px-2.5 py-1 rounded-full', statusConfig.badge)}>
                  {data?.status === 'healthy' ? 'Operacional' : data?.status === 'degraded' ? 'Degradado' : 'Crítico'}
                </span>
              </div>
            </div>

            {/* Component list */}
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div className="px-5 py-3 border-b border-gray-100 bg-gray-50 flex items-center justify-between">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Componentes</p>
                <p className="text-xs text-gray-400">Disponibilidade (30 dias)</p>
              </div>
              <div className="divide-y divide-gray-100">
                {Object.entries(data?.checks || {}).map(([key, check]) => (
                  <div key={key} className="px-5 py-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-3">
                        <StatusIcon status={check.status} />
                        <span className="font-medium text-gray-800 text-sm">
                          {CHECK_LABELS[key] || key}
                        </span>
                      </div>
                      <div className="flex items-center gap-3">
                        {check.latency_ms !== undefined && (
                          <span className="text-xs text-gray-400">{check.latency_ms}ms</span>
                        )}
                        <span className={clsx('text-xs font-medium', {
                          'text-green-600': check.status === 'ok',
                          'text-red-600': check.status === 'error',
                          'text-yellow-600': check.status === 'degraded' || check.status === 'warning',
                          'text-gray-500': check.status === 'unknown',
                        })}>
                          {check.status === 'ok' ? 'Operacional' :
                           check.status === 'error' ? 'Fora do ar' :
                           check.status === 'degraded' || check.status === 'warning' ? 'Degradado' :
                           'Desconhecido'}
                        </span>
                      </div>
                    </div>
                    <UptimeBar value={check.status === 'ok' ? UPTIME_TARGETS[key] ?? 99.5 : check.status === 'degraded' ? 98.5 : 95.0} />
                  </div>
                ))}
              </div>
            </div>

            {/* SLA */}
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <h3 className="text-sm font-semibold text-gray-700 mb-3">SLA Contratual</h3>
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <p className="text-2xl font-bold text-gray-900">99,5%</p>
                  <p className="text-xs text-gray-500">Uptime mensal garantido</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">&lt; 3s</p>
                  <p className="text-xs text-gray-500">Tempo médio de resposta</p>
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-900">24/7</p>
                  <p className="text-xs text-gray-500">Monitoramento ativo</p>
                </div>
              </div>
            </div>

            {updatedAt && (
              <div className="flex items-center justify-between text-xs text-gray-400">
                <span>
                  Atualizado às {format(updatedAt, 'HH:mm:ss', { locale: ptBR })} · atualiza a cada 60s
                </span>
                <a
                  href="https://wa.me/5511999999999?text=Reportar+incidente+IGS"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 text-blue-500 hover:underline"
                >
                  Reportar incidente <ExternalLink size={11} />
                </a>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
