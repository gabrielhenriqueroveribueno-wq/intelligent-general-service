import { useEffect, useState } from 'react'
import { CheckCircle2, XCircle, AlertTriangle, RefreshCw, Clock } from 'lucide-react'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import clsx from 'clsx'

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

function StatusIcon({ status }: { status: CheckResult['status'] }) {
  if (status === 'ok') return <CheckCircle2 size={20} className="text-green-500" />
  if (status === 'error') return <XCircle size={20} className="text-red-500" />
  if (status === 'degraded' || status === 'warning') return <AlertTriangle size={20} className="text-yellow-500" />
  return <Clock size={20} className="text-gray-400" />
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
    },
    degraded: {
      bg: 'bg-yellow-50 border-yellow-200',
      text: 'text-yellow-800',
      label: 'Alguns sistemas com degradação',
      dot: 'bg-yellow-500',
    },
    critical: {
      bg: 'bg-red-50 border-red-200',
      text: 'text-red-800',
      label: 'Falha crítica detectada',
      dot: 'bg-red-500',
    },
  }[data?.status || 'healthy']

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900">IGS — Status</h1>
            <p className="text-sm text-gray-500">status.igs.com.br</p>
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
        {/* Overall status */}
        {loading && !data ? (
          <div className="flex justify-center py-16">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          </div>
        ) : (
          <>
            <div className={clsx('border rounded-xl p-5', statusConfig.bg)}>
              <div className="flex items-center gap-3">
                <div className={clsx('w-3 h-3 rounded-full animate-pulse', statusConfig.dot)} />
                <p className={clsx('font-semibold text-lg', statusConfig.text)}>
                  {statusConfig.label}
                </p>
              </div>
            </div>

            {/* Component list */}
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div className="px-5 py-3 border-b border-gray-100 bg-gray-50">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Componentes</p>
              </div>
              <div className="divide-y divide-gray-100">
                {Object.entries(data?.checks || {}).map(([key, check]) => (
                  <div key={key} className="flex items-center justify-between px-5 py-4">
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
                ))}
              </div>
            </div>

            {updatedAt && (
              <p className="text-xs text-gray-400 text-center">
                Atualizado às {format(updatedAt, 'HH:mm:ss', { locale: ptBR })} · atualiza a cada 60s
              </p>
            )}
          </>
        )}
      </div>
    </div>
  )
}
