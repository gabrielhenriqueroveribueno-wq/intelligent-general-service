import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { Users, Search } from 'lucide-react'
import { api } from '../api/client'
import clsx from 'clsx'

export default function Employees() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['employees', search, page],
    queryFn: () =>
      api.get('/api/v1/employees', { params: { search: search || undefined, page, size: 20 } }).then((r) => r.data),
  })

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Funcionários</h1>
        <p className="text-sm text-gray-500">Consulte dados dos funcionários</p>
      </div>
      <div className="relative max-w-sm">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          className="input pl-9"
          placeholder="Buscar por nome ou matrícula..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1) }}
        />
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
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Matrícula</th>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Nome</th>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Departamento</th>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Cargo</th>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data?.items?.map((emp: any) => (
                <tr key={emp.id} className="hover:bg-gray-50 cursor-pointer" onClick={() => navigate(`/employees/${emp.id}`)}>
                  <td className="px-4 py-3 text-sm font-mono">{emp.employee_number}</td>
                  <td className="px-4 py-3 text-sm font-medium">{emp.full_name}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{emp.department || '—'}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{emp.position || '—'}</td>
                  <td className="px-4 py-3">
                    <span className={clsx('badge', emp.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600')}>
                      {emp.status}
                    </span>
                  </td>
                </tr>
              ))}
              {!data?.items?.length && (
                <tr>
                  <td colSpan={5} className="text-center py-8 text-gray-400">
                    <Users className="mx-auto mb-2 opacity-30" size={32} />
                    <p>Nenhum funcionário encontrado</p>
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
