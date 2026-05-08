import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { MessageSquare, Clock, User, Sparkles } from 'lucide-react'
import { api } from '../api/client'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import clsx from 'clsx'

function SentimentDot({ sentiment }: { sentiment?: string }) {
  if (!sentiment || sentiment === 'neutral')
    return <span className="text-gray-300 text-xs">—</span>
  if (sentiment === 'negative')
    return (
      <span
        title="Sentimento negativo"
        className="inline-block w-2.5 h-2.5 rounded-full bg-red-500"
      />
    )
  return (
    <span
      title="Sentimento positivo"
      className="inline-block w-2.5 h-2.5 rounded-full bg-green-500"
    />
  )
}

const statusColors: Record<string, string> = {
  active: 'bg-green-100 text-green-700',
  waiting_agent: 'bg-yellow-100 text-yellow-700',
  closed: 'bg-gray-100 text-gray-600',
}

const statusLabels: Record<string, string> = {
  active: 'Ativa',
  waiting_agent: 'Aguardando agente',
  closed: 'Encerrada',
}

/** Animação dos 3 pontinhos pulsando — estilo WhatsApp/iMessage. */
function TypingIndicator({ className = '' }: { className?: string }) {
  return (
    <span className={clsx('inline-flex items-center gap-0.5', className)}>
      <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-typing" style={{ animationDelay: '0ms' }} />
      <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-typing" style={{ animationDelay: '150ms' }} />
      <span className="w-1.5 h-1.5 rounded-full bg-green-500 animate-typing" style={{ animationDelay: '300ms' }} />
    </span>
  )
}

/** Conversa "viva" se a última mensagem foi nos últimos 90s. */
function isLive(lastMessageAt?: string | null) {
  if (!lastMessageAt) return false
  const diff = Date.now() - new Date(lastMessageAt).getTime()
  return diff < 90_000
}

export default function Conversations() {
  const navigate = useNavigate()
  const [status, setStatus] = useState<string>('')
  const [page, setPage] = useState(1)
  const [highlightedIds, setHighlightedIds] = useState<Set<string>>(new Set())
  const [knownIds, setKnownIds] = useState<Set<string>>(new Set())

  const { data, isLoading } = useQuery({
    queryKey: ['conversations', status, page],
    queryFn: () =>
      api
        .get('/api/v1/conversations', {
          params: { status: status || undefined, page, size: 20 },
        })
        .then((r) => r.data),
    refetchInterval: 8_000,
  })

  // Detecta conversas novas: animação de highlight verde por 4s
  useEffect(() => {
    if (!data?.items) return
    const currentIds: string[] = data.items.map((c: any) => c.id)
    const newOnes = currentIds.filter((id) => !knownIds.has(id))
    if (newOnes.length && knownIds.size > 0) {
      setHighlightedIds((prev) => new Set([...Array.from(prev), ...newOnes]))
      setTimeout(() => {
        setHighlightedIds((prev) => {
          const next = new Set(prev)
          newOnes.forEach((id) => next.delete(id))
          return next
        })
      }, 4000)
    }
    setKnownIds(new Set(currentIds))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data?.items])

  // Conta conversas aguardando agente para o badge
  const { data: waitingData } = useQuery({
    queryKey: ['conversations-waiting'],
    queryFn: () =>
      api
        .get('/api/v1/conversations', {
          params: { status: 'waiting_agent', page: 1, size: 1 },
        })
        .then((r) => r.data),
    refetchInterval: 15_000,
  })
  const waitingCount: number = waitingData?.total ?? 0

  const liveCount = (data?.items || []).filter((c: any) => isLive(c.last_message_at)).length

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            Conversas
            {liveCount > 0 && (
              <span className="inline-flex items-center gap-1.5 text-xs font-medium px-2 py-1 rounded-full bg-green-100 text-green-700">
                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                {liveCount} ao vivo
              </span>
            )}
          </h1>
          <p className="text-sm text-gray-500">Gerencie os atendimentos via WhatsApp</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {(['', 'active', 'waiting_agent', 'closed'] as const).map((s) => (
            <button
              key={s}
              onClick={() => {
                setStatus(s)
                setPage(1)
              }}
              className={clsx(
                'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5',
                status === s
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-600 border hover:bg-gray-50',
              )}
            >
              {s === '' ? 'Todas' : statusLabels[s]}
              {s === 'waiting_agent' && waitingCount > 0 && (
                <span
                  className={clsx(
                    'text-xs font-bold px-1.5 py-0.5 rounded-full',
                    status === s ? 'bg-white text-orange-600' : 'bg-orange-500 text-white',
                  )}
                >
                  {waitingCount}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      <div className="card p-0 overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Contato</th>
                  <th className="text-left text-xs font-medium text-gray-500 px-4 py-3 hidden md:table-cell">Tipo</th>
                  <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Status</th>
                  <th className="text-left text-xs font-medium text-gray-500 px-4 py-3 hidden sm:table-cell">
                    Última mensagem
                  </th>
                  <th className="text-left text-xs font-medium text-gray-500 px-4 py-3 hidden lg:table-cell">
                    Início
                  </th>
                  <th
                    className="text-left text-xs font-medium text-gray-500 px-4 py-3"
                    title="Sentimento da última mensagem"
                  >
                    Humor
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data?.items?.map((conv: any) => {
                  const live = isLive(conv.last_message_at)
                  const isNew = highlightedIds.has(conv.id)
                  return (
                    <tr
                      key={conv.id}
                      className={clsx(
                        'cursor-pointer transition-colors',
                        isNew ? 'animate-flash-green' : 'hover:bg-gray-50',
                      )}
                      onClick={() => navigate(`/app/conversations/${conv.id}`)}
                    >
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          <div className="relative">
                            <div className="bg-blue-100 p-1.5 rounded-full">
                              <User size={14} className="text-blue-600" />
                            </div>
                            {live && (
                              <span className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-green-500 ring-2 ring-white animate-pulse" />
                            )}
                          </div>
                          <div className="min-w-0">
                            <p className="text-sm font-medium truncate">
                              {conv.contact_name ||
                                conv.contact_phone ||
                                conv.contact_id?.substring(0, 8) + '...'}
                            </p>
                            {live && (
                              <span className="flex items-center gap-1 text-[10px] text-green-600 font-medium">
                                <TypingIndicator /> conversando agora
                              </span>
                            )}
                          </div>
                          {isNew && (
                            <span className="ml-1 inline-flex items-center gap-0.5 text-[10px] font-bold text-green-700 bg-green-100 px-1.5 py-0.5 rounded">
                              <Sparkles size={10} /> NOVA
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 hidden md:table-cell">
                        <span className="text-sm text-gray-600">
                          {conv.context_type || 'Geral'}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className={clsx('badge', statusColors[conv.status] || 'bg-gray-100')}>
                          {statusLabels[conv.status] || conv.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 hidden sm:table-cell">
                        <div className="flex items-center gap-1 text-xs text-gray-500">
                          <Clock size={12} />
                          {conv.last_message_at
                            ? format(new Date(conv.last_message_at), 'dd/MM HH:mm', {
                                locale: ptBR,
                              })
                            : '—'}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-500 hidden lg:table-cell">
                        {format(new Date(conv.started_at), 'dd/MM/yyyy HH:mm', {
                          locale: ptBR,
                        })}
                      </td>
                      <td className="px-4 py-3">
                        <SentimentDot sentiment={conv.last_sentiment} />
                      </td>
                    </tr>
                  )
                })}
                {!data?.items?.length && (
                  <tr>
                    <td colSpan={6} className="text-center py-8 text-gray-400">
                      <MessageSquare className="mx-auto mb-2 opacity-30" size={32} />
                      <p>Nenhuma conversa encontrada</p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Paginação */}
      {data?.total > 20 && (
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>Total: {data.total}</span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="btn-secondary px-3 py-1.5 text-sm disabled:opacity-50"
            >
              Anterior
            </button>
            <span className="px-3 py-1.5">Página {page}</span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={page * 20 >= data.total}
              className="btn-secondary px-3 py-1.5 text-sm disabled:opacity-50"
            >
              Próxima
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
