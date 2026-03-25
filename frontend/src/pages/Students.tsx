import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { GraduationCap, Search } from 'lucide-react'
import { api } from '../api/client'
import clsx from 'clsx'

const statusColors: Record<string, string> = {
  active: 'bg-green-100 text-green-700',
  locked: 'bg-red-100 text-red-700',
  graduated: 'bg-blue-100 text-blue-700',
  dropped: 'bg-gray-100 text-gray-600',
}

export default function Students() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['students', search, page],
    queryFn: () =>
      api.get('/api/v1/students', { params: { search: search || undefined, page, size: 20 } }).then((r) => r.data),
  })

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Alunos</h1>
          <p className="text-sm text-gray-500">Consulte dados dos alunos</p>
        </div>
      </div>

      {/* Busca */}
      <div className="relative max-w-sm">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          className="input pl-9"
          placeholder="Buscar por nome ou RA..."
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
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">RA</th>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Nome</th>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Curso</th>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Semestre</th>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Situação</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {data?.items?.map((student: any) => (
                <tr key={student.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-mono">{student.registration_number}</td>
                  <td className="px-4 py-3 text-sm font-medium">{student.full_name}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{student.course || '—'}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{student.semester || '—'}</td>
                  <td className="px-4 py-3">
                    <span className={clsx('badge', statusColors[student.enrollment_status] || 'bg-gray-100')}>
                      {student.enrollment_status}
                    </span>
                  </td>
                </tr>
              ))}
              {!data?.items?.length && (
                <tr>
                  <td colSpan={5} className="text-center py-8 text-gray-400">
                    <GraduationCap className="mx-auto mb-2 opacity-30" size={32} />
                    <p>Nenhum aluno encontrado</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
      <p className="text-sm text-gray-500">Total: {data?.total ?? 0} alunos</p>
    </div>
  )
}
