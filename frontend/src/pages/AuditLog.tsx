import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import { Shield, Search } from 'lucide-react'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import clsx from 'clsx'

interface AuditEntry {
  id: string
  user_id: string | null
  action: string
  entity_type: string | null
  entity_id: string | null
  details: Record<string, unknown> | null
  ip_address: string | null
  created_at: string
}

const ACTION_COLORS: Record<string, string> = {
  login: 'bg-blue-100 text-blue-700',
  logout: 'bg-gray-100 text-gray-600',
  lgpd_anonymize: 'bg-purple-100 text-purple-700',
  delete: 'bg-red-100 text-red-700',
  create: 'bg-green-100 text-green-700',
  update: 'bg-yellow-100 text-yellow-700',
}

export default function AuditLog() {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['audit-logs', page, search],
    queryFn: () =>
      api.get('/api/v1/admin/audit-logs', {
        params: { page, size: 30, action: search || undefined },
      }).then(r => r.data),
  })

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Shield size={22} className="text-blue-600" />
            Log de Auditoria
          </h1>
          <p className="text-sm text-gray-500">Histórico de ações sensíveis no sistema</p>
        </div>
        <div className="relative">
          <Search size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            className="pl-8 pr-3 py-2 border rounded-lg text-sm w-48 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Filtrar por ação..."
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1) }}
          />
        </div>
      </div>

      <div className="card p-0 overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-40">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Data/Hora</th>
                  <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Ação</th>
                  <th className="text-left text-xs font-medium text-gray-500 px-4 py-3 hidden sm:table-cell">Entidade</th>
                  <th className="text-left text-xs font-medium text-gray-500 px-4 py-3 hidden md:table-cell">IP</th>
                  <th className="text-left text-xs font-medium text-gray-500 px-4 py-3 hidden lg:table-cell">Detalhes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data?.items?.map((entry: AuditEntry) => (
                  <tr key={entry.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap">
                      {format(new Date(entry.created_at), "dd/MM/yy HH:mm:ss", { locale: ptBR })}
                    </td>
                    <td className="px-4 py-3">
                      <span className={clsx(
                        'px-2 py-0.5 rounded text-xs font-medium',
                        ACTION_COLORS[entry.action] || 'bg-gray-100 text-gray-700',
                      )}>
                        {entry.action}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-600 hidden sm:table-cell">
                      {entry.entity_type && (
                        <span>{entry.entity_type}{entry.entity_id && ` · ${entry.entity_id.substring(0, 8)}…`}</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500 hidden md:table-cell">
                      {entry.ip_address || '—'}
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-500 hidden lg:table-cell max-w-xs truncate">
                      {entry.details ? JSON.stringify(entry.details).substring(0, 80) : '—'}
                    </td>
                  </tr>
                ))}
                {!data?.items?.length && (
                  <tr>
                    <td colSpan={5} className="text-center py-10 text-gray-400">
                      <Shield className="mx-auto mb-2 opacity-30" size={32} />
                      <p>Nenhum log encontrado</p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {data?.total > 30 && (
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>Total: {data.total}</span>
          <div className="flex gap-2">
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
              className="btn-secondary px-3 py-1.5 text-sm disabled:opacity-50">Anterior</button>
            <span className="px-3 py-1.5">Página {page}</span>
            <button onClick={() => setPage(p => p + 1)} disabled={page * 30 >= data.total}
              className="btn-secondary px-3 py-1.5 text-sm disabled:opacity-50">Próxima</button>
          </div>
        </div>
      )}
    </div>
  )
}
