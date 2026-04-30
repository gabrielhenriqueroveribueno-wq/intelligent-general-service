import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { GraduationCap, Search, AlertTriangle } from 'lucide-react'
import { api } from '../api/client'
import clsx from 'clsx'

const statusColors: Record<string, string> = {
  active: 'bg-green-100 text-green-700',
  locked: 'bg-red-100 text-red-700',
  graduated: 'bg-blue-100 text-blue-700',
  dropped: 'bg-gray-100 text-gray-600',
}

const riskColors: Record<string, string> = {
  critical: 'bg-red-100 text-red-700 border border-red-200',
  high: 'bg-orange-100 text-orange-700 border border-orange-200',
  medium: 'bg-yellow-100 text-yellow-700 border border-yellow-200',
  low: '',
}

const riskLabels: Record<string, string> = {
  critical: 'Crítico',
  high: 'Alto',
  medium: 'Médio',
  low: '',
}

export default function Students() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [riskFilter, setRiskFilter] = useState(searchParams.get('risk') || '')

  const { data, isLoading } = useQuery({
    queryKey: ['students', search, page, riskFilter],
    queryFn: () =>
      api
        .get('/api/v1/students', {
          params: {
            search: search || undefined,
            page,
            size: 20,
            evasion_risk_level: riskFilter || undefined,
          },
        })
        .then((r) => r.data),
  })

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Alunos</h1>
          <p className="text-sm text-gray-500">Consulte dados dos alunos</p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="relative max-w-sm flex-1">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            className="input pl-9 w-full"
            placeholder="Buscar por nome ou RA..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value)
              setPage(1)
            }}
          />
        </div>
        <select
          className="input text-sm"
          value={riskFilter}
          onChange={(e) => {
            setRiskFilter(e.target.value)
            setPage(1)
          }}
        >
          <option value="">Todos os riscos</option>
          <option value="critical">Risco Crítico</option>
          <option value="high">Risco Alto</option>
          <option value="medium">Risco Médio</option>
          <option value="low">Risco Baixo</option>
        </select>
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
                  <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">RA</th>
                  <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Nome</th>
                  <th className="text-left text-xs font-medium text-gray-500 px-4 py-3 hidden md:table-cell">Curso</th>
                  <th className="text-left text-xs font-medium text-gray-500 px-4 py-3 hidden md:table-cell">Semestre</th>
                  <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Situação</th>
                  <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Evasão</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data?.items?.map((student: any) => (
                  <tr
                    key={student.id}
                    className="hover:bg-gray-50 cursor-pointer"
                    onClick={() => navigate(`/app/students/${student.id}`)}
                  >
                    <td className="px-4 py-3 text-sm font-mono">{student.registration_number}</td>
                    <td className="px-4 py-3 text-sm font-medium">
                      <div className="flex items-center gap-2">
                        {student.evasion_risk_level === 'critical' && (
                          <AlertTriangle size={14} className="text-red-500 flex-shrink-0" />
                        )}
                        {student.full_name}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 hidden md:table-cell">
                      {student.course || '—'}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 hidden md:table-cell">
                      {student.semester || '—'}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={clsx(
                          'badge',
                          statusColors[student.enrollment_status] || 'bg-gray-100'
                        )}
                      >
                        {student.enrollment_status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {student.evasion_risk_level && student.evasion_risk_level !== 'low' ? (
                        <span
                          className={clsx(
                            'text-xs font-medium px-2 py-0.5 rounded-full',
                            riskColors[student.evasion_risk_level]
                          )}
                        >
                          {riskLabels[student.evasion_risk_level]} · {student.evasion_risk_score}
                        </span>
                      ) : (
                        <span className="text-xs text-gray-400">—</span>
                      )}
                    </td>
                  </tr>
                ))}
                {!data?.items?.length && (
                  <tr>
                    <td colSpan={6} className="text-center py-8 text-gray-400">
                      <GraduationCap className="mx-auto mb-2 opacity-30" size={32} />
                      <p>Nenhum aluno encontrado</p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
      <p className="text-sm text-gray-500">Total: {data?.total ?? 0} alunos</p>
    </div>
  )
}
