import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Users, DollarSign, Palmtree, ClipboardList } from 'lucide-react'
import { api } from '../api/client'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import clsx from 'clsx'

const hrStatusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-700',
  approved: 'bg-green-100 text-green-700',
  rejected: 'bg-red-100 text-red-700',
  in_progress: 'bg-blue-100 text-blue-700',
}

export default function EmployeeDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data: employee, isLoading } = useQuery({
    queryKey: ['employee', id],
    queryFn: () => api.get(`/api/v1/employees/${id}`).then((r) => r.data),
    enabled: !!id,
  })

  const { data: payslips } = useQuery({
    queryKey: ['employee-payslips', id],
    queryFn: () => api.get(`/api/v1/employees/${id}/payslips`).then((r) => r.data),
    enabled: !!id,
  })

  const { data: vacation } = useQuery({
    queryKey: ['employee-vacation', id],
    queryFn: () => api.get(`/api/v1/employees/${id}/vacation`).then((r) => r.data),
    enabled: !!id,
  })

  const { data: hrRequests } = useQuery({
    queryKey: ['employee-hr-requests', id],
    queryFn: () => api.get(`/api/v1/employees/${id}/requests`).then((r) => r.data),
    enabled: !!id,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    )
  }

  if (!employee) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>Funcionário não encontrado</p>
        <Link to="/employees" className="text-blue-600 hover:underline mt-2 block">Voltar</Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button onClick={() => navigate('/employees')} className="p-1.5 rounded-lg text-gray-500 hover:bg-gray-100">
          <ArrowLeft size={18} />
        </button>
        <div className="bg-purple-100 p-3 rounded-full">
          <Users size={22} className="text-purple-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{employee.full_name}</h1>
          <p className="text-sm text-gray-500">Matrícula: {employee.employee_number}</p>
        </div>
        <span className={clsx(
          'badge ml-2 px-2.5 py-1 rounded-full text-xs font-medium',
          employee.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600',
        )}>
          {employee.status === 'active' ? 'Ativo' : employee.status}
        </span>
      </div>

      {/* Dados básicos */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Departamento', value: employee.department || '—' },
          { label: 'Cargo', value: employee.position || '—' },
          { label: 'Admissão', value: employee.hire_date ? format(new Date(employee.hire_date), 'dd/MM/yyyy', { locale: ptBR }) : '—' },
          { label: 'E-mail', value: employee.email || '—' },
        ].map(({ label, value }) => (
          <div key={label} className="card p-4">
            <p className="text-xs text-gray-500">{label}</p>
            <p className="font-medium text-gray-900 mt-0.5 truncate">{value}</p>
          </div>
        ))}
      </div>

      {/* Saldo de Férias */}
      {vacation && (
        <div className="card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Palmtree size={16} className="text-green-600" />
            <h2 className="font-semibold text-gray-800">Saldo de Férias</h2>
          </div>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <p className="text-2xl font-bold text-gray-900">{vacation.total_days}</p>
              <p className="text-xs text-gray-500 mt-1">Dias totais</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-orange-600">{vacation.used_days}</p>
              <p className="text-xs text-gray-500 mt-1">Utilizados</p>
            </div>
            <div>
              <p className="text-2xl font-bold text-green-600">{vacation.remaining_days}</p>
              <p className="text-xs text-gray-500 mt-1">Disponíveis</p>
            </div>
          </div>
          {vacation.deadline_date && (
            <p className="text-xs text-gray-400 mt-3 text-center">
              Prazo limite: {format(new Date(vacation.deadline_date), 'dd/MM/yyyy', { locale: ptBR })}
            </p>
          )}
        </div>
      )}

      {/* Holerites */}
      <div className="card p-0 overflow-hidden">
        <div className="px-4 py-3 border-b flex items-center gap-2">
          <DollarSign size={16} className="text-gray-500" />
          <h2 className="font-semibold text-gray-800">Holerites</h2>
        </div>
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Competência</th>
              <th className="text-right text-xs font-medium text-gray-500 px-4 py-3">Salário Bruto</th>
              <th className="text-right text-xs font-medium text-gray-500 px-4 py-3">Descontos</th>
              <th className="text-right text-xs font-medium text-gray-500 px-4 py-3">Salário Líquido</th>
              <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">PDF</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {payslips?.map((p: any) => (
              <tr key={p.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm font-medium">{p.reference_month}</td>
                <td className="px-4 py-3 text-sm text-right font-mono">
                  R$ {Number(p.gross_salary).toFixed(2)}
                </td>
                <td className="px-4 py-3 text-sm text-right font-mono text-red-600">
                  R$ {(Number(p.gross_salary) - Number(p.net_salary)).toFixed(2)}
                </td>
                <td className="px-4 py-3 text-sm text-right font-mono font-bold text-green-700">
                  R$ {Number(p.net_salary).toFixed(2)}
                </td>
                <td className="px-4 py-3 text-sm">
                  {p.pdf_url ? (
                    <a href={p.pdf_url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline text-xs">
                      Baixar
                    </a>
                  ) : (
                    <span className="text-gray-400 text-xs">—</span>
                  )}
                </td>
              </tr>
            ))}
            {!payslips?.length && (
              <tr><td colSpan={5} className="text-center py-6 text-gray-400 text-sm">Sem holerites</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Solicitações RH */}
      <div className="card p-0 overflow-hidden">
        <div className="px-4 py-3 border-b flex items-center gap-2">
          <ClipboardList size={16} className="text-gray-500" />
          <h2 className="font-semibold text-gray-800">Solicitações de RH</h2>
        </div>
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Tipo</th>
              <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Data</th>
              <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Status</th>
              <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Resposta</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {hrRequests?.map((r: any) => (
              <tr key={r.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm font-medium capitalize">{r.request_type}</td>
                <td className="px-4 py-3 text-sm text-gray-600">
                  {format(new Date(r.created_at), 'dd/MM/yyyy', { locale: ptBR })}
                </td>
                <td className="px-4 py-3">
                  <span className={clsx('badge px-2 py-0.5 rounded text-xs font-medium', hrStatusColors[r.status] || 'bg-gray-100')}>
                    {r.status === 'pending' ? 'Pendente' : r.status === 'approved' ? 'Aprovado' : r.status === 'rejected' ? 'Rejeitado' : r.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-600 max-w-xs truncate">
                  {r.response_text || '—'}
                </td>
              </tr>
            ))}
            {!hrRequests?.length && (
              <tr><td colSpan={4} className="text-center py-6 text-gray-400 text-sm">Sem solicitações</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
