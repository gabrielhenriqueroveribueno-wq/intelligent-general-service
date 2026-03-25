import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Ticket as TicketIcon, AlertCircle, Clock } from 'lucide-react'
import { api } from '../api/client'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import clsx from 'clsx'

const priorityColors: Record<string, string> = {
  low: 'bg-gray-100 text-gray-600',
  medium: 'bg-blue-100 text-blue-700',
  high: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700',
}

const statusColors: Record<string, string> = {
  open: 'bg-yellow-100 text-yellow-700',
  in_progress: 'bg-blue-100 text-blue-700',
  resolved: 'bg-green-100 text-green-700',
  closed: 'bg-gray-100 text-gray-600',
}

export default function Tickets() {
  const [status, setStatus] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['tickets', status, page],
    queryFn: () =>
      api.get('/api/v1/tickets', { params: { status: status || undefined, page, size: 20 } }).then((r) => r.data),
  })

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Tickets</h1>
          <p className="text-sm text-gray-500">Gerenciamento de solicitações</p>
        </div>
        <div className="flex gap-2">
          {['', 'open', 'in_progress', 'resolved', 'closed'].map((s) => (
            <button
              key={s}
              onClick={() => { setStatus(s); setPage(1) }}
              className={clsx(
                'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
                status === s ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 border hover:bg-gray-50',
              )}
            >
              {s === '' ? 'Todos' : s.replace('_', ' ')}
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
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Protocolo</th>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Assunto</th>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Prioridade</th>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Status</th>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">SLA</th>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Criado</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data?.items?.map((ticket: any) => {
                const isBreached = ticket.sla_deadline && new Date(ticket.sla_deadline) < new Date() && ticket.status !== 'closed'
                return (
                  <tr key={ticket.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <span className="text-sm font-mono font-medium text-blue-600">{ticket.protocol_number}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm">{ticket.subject}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={clsx('badge', priorityColors[ticket.priority])}>
                        {ticket.priority}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={clsx('badge', statusColors[ticket.status])}>
                        {ticket.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {ticket.sla_deadline ? (
                        <div className={clsx('flex items-center gap-1 text-xs', isBreached ? 'text-red-600' : 'text-gray-500')}>
                          {isBreached ? <AlertCircle size={12} /> : <Clock size={12} />}
                          {format(new Date(ticket.sla_deadline), "dd/MM HH:mm", { locale: ptBR })}
                        </div>
                      ) : '—'}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500">
                      {format(new Date(ticket.created_at), "dd/MM/yyyy", { locale: ptBR })}
                    </td>
                  </tr>
                )
              })}
              {!data?.items?.length && (
                <tr>
                  <td colSpan={6} className="text-center py-8 text-gray-400">
                    <TicketIcon className="mx-auto mb-2 opacity-30" size={32} />
                    <p>Nenhum ticket encontrado</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
