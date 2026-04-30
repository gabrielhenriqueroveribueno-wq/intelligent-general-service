import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, GraduationCap, BookOpen, Calendar, FileText, AlertTriangle } from 'lucide-react'
import { api } from '../api/client'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import clsx from 'clsx'

const riskColors: Record<string, string> = {
  critical: 'bg-red-50 border-red-200 text-red-700',
  high: 'bg-orange-50 border-orange-200 text-orange-700',
  medium: 'bg-yellow-50 border-yellow-200 text-yellow-700',
  low: 'bg-green-50 border-green-200 text-green-700',
}

const riskLabels: Record<string, string> = {
  critical: 'Risco Crítico de Evasão',
  high: 'Risco Alto de Evasão',
  medium: 'Risco Médio de Evasão',
  low: 'Risco Baixo',
}

const enrollmentLabels: Record<string, string> = {
  active: 'Ativo',
  locked: 'Bloqueado',
  graduated: 'Formado',
  dropped: 'Evadido',
}
const enrollmentColors: Record<string, string> = {
  active: 'bg-green-100 text-green-700',
  locked: 'bg-red-100 text-red-700',
  graduated: 'bg-blue-100 text-blue-700',
  dropped: 'bg-gray-100 text-gray-600',
}

const gradeStatusColors: Record<string, string> = {
  approved: 'text-green-600',
  failed: 'text-red-600',
  in_progress: 'text-blue-600',
}

const boletoStatusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-700',
  paid: 'bg-green-100 text-green-700',
  overdue: 'bg-red-100 text-red-700',
  cancelled: 'bg-gray-100 text-gray-500',
}

export default function StudentDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()

  const { data: student, isLoading } = useQuery({
    queryKey: ['student', id],
    queryFn: () => api.get(`/api/v1/students/${id}`).then((r) => r.data),
    enabled: !!id,
  })

  const { data: grades } = useQuery({
    queryKey: ['student-grades', id],
    queryFn: () => api.get(`/api/v1/students/${id}/grades`).then((r) => r.data),
    enabled: !!id,
  })

  const { data: attendance } = useQuery({
    queryKey: ['student-attendance', id],
    queryFn: () => api.get(`/api/v1/students/${id}/attendance`).then((r) => r.data),
    enabled: !!id,
  })

  const { data: boletos } = useQuery({
    queryKey: ['student-boletos', id],
    queryFn: () => api.get(`/api/v1/students/${id}/boletos`).then((r) => r.data),
    enabled: !!id,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    )
  }

  if (!student) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>Aluno não encontrado</p>
        <Link to="/app/students" className="text-blue-600 hover:underline mt-2 block">Voltar</Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center gap-3">
        <button onClick={() => navigate('/app/students')} className="p-1.5 rounded-lg text-gray-500 hover:bg-gray-100 shrink-0">
          <ArrowLeft size={18} />
        </button>
        <div className="bg-blue-100 p-3 rounded-full shrink-0">
          <GraduationCap size={22} className="text-blue-600" />
        </div>
        <div className="min-w-0">
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900 truncate">{student.full_name}</h1>
          <p className="text-sm text-gray-500">RA: {student.registration_number}</p>
        </div>
        <span className={clsx('badge px-2.5 py-1 rounded-full text-xs font-medium shrink-0', enrollmentColors[student.enrollment_status] || 'bg-gray-100')}>
          {enrollmentLabels[student.enrollment_status] || student.enrollment_status}
        </span>
      </div>

      {/* Card de dados */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Curso', value: student.course || '—' },
          { label: 'Semestre', value: student.semester ? `${student.semester}º` : '—' },
          { label: 'E-mail', value: student.email || '—' },
          { label: 'Telefone', value: student.phone || '—' },
        ].map(({ label, value }) => (
          <div key={label} className="card p-4">
            <p className="text-xs text-gray-500">{label}</p>
            <p className="font-medium text-gray-900 mt-0.5 truncate">{value}</p>
          </div>
        ))}
      </div>

      {/* Risco de Evasão */}
      {student.evasion_risk_level && student.evasion_risk_level !== 'low' && (
        <div className={clsx('rounded-xl border p-4', riskColors[student.evasion_risk_level])}>
          <div className="flex items-start gap-3">
            <AlertTriangle size={20} className="flex-shrink-0 mt-0.5" />
            <div className="flex-1 min-w-0">
              <p className="font-semibold">
                {riskLabels[student.evasion_risk_level]} — Score: {student.evasion_risk_score}/100
              </p>
              {student.evasion_factors && (() => {
                try {
                  const factors: string[] = JSON.parse(student.evasion_factors)
                  return (
                    <ul className="mt-1 text-sm space-y-0.5 opacity-80">
                      {factors.map((f: string, i: number) => <li key={i}>· {f}</li>)}
                    </ul>
                  )
                } catch { return null }
              })()}
            </div>
          </div>
        </div>
      )}

      {/* Notas */}
      <div className="card p-0 overflow-hidden">
        <div className="px-4 py-3 border-b flex items-center gap-2">
          <BookOpen size={16} className="text-gray-500" />
          <h2 className="font-semibold text-gray-800">Notas</h2>
        </div>
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Disciplina</th>
              <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Período</th>
              <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Tipo</th>
              <th className="text-right text-xs font-medium text-gray-500 px-4 py-3">Nota</th>
              <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {grades?.map((g: any) => (
              <tr key={g.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm font-medium">{g.subject_name}</td>
                <td className="px-4 py-3 text-sm text-gray-600">{g.academic_period}</td>
                <td className="px-4 py-3 text-sm text-gray-600 capitalize">{g.grade_type}</td>
                <td className={clsx('px-4 py-3 text-sm font-bold text-right', gradeStatusColors[g.status] || 'text-gray-800')}>
                  {g.grade_value ?? '—'}
                </td>
                <td className="px-4 py-3">
                  <span className={clsx('text-xs font-medium capitalize', gradeStatusColors[g.status])}>
                    {g.status === 'approved' ? 'Aprovado' : g.status === 'failed' ? 'Reprovado' : 'Em andamento'}
                  </span>
                </td>
              </tr>
            ))}
            {!grades?.length && (
              <tr><td colSpan={5} className="text-center py-6 text-gray-400 text-sm">Sem notas registradas</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Frequência */}
      <div className="card p-0 overflow-hidden">
        <div className="px-4 py-3 border-b flex items-center gap-2">
          <Calendar size={16} className="text-gray-500" />
          <h2 className="font-semibold text-gray-800">Frequência</h2>
        </div>
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Disciplina</th>
              <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Período</th>
              <th className="text-right text-xs font-medium text-gray-500 px-4 py-3">Presentes</th>
              <th className="text-right text-xs font-medium text-gray-500 px-4 py-3">Total</th>
              <th className="text-right text-xs font-medium text-gray-500 px-4 py-3">Faltas %</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {attendance?.map((a: any) => (
              <tr key={a.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm font-medium">{a.subject_name}</td>
                <td className="px-4 py-3 text-sm text-gray-600">{a.academic_period}</td>
                <td className="px-4 py-3 text-sm text-right">{a.attended}</td>
                <td className="px-4 py-3 text-sm text-right">{a.total_classes}</td>
                <td className={clsx(
                  'px-4 py-3 text-sm font-bold text-right',
                  a.absence_pct > 25 ? 'text-red-600' : a.absence_pct > 15 ? 'text-yellow-600' : 'text-green-600',
                )}>
                  {a.absence_pct?.toFixed(1)}%
                </td>
              </tr>
            ))}
            {!attendance?.length && (
              <tr><td colSpan={5} className="text-center py-6 text-gray-400 text-sm">Sem registros de frequência</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Boletos */}
      <div className="card p-0 overflow-hidden">
        <div className="px-4 py-3 border-b flex items-center gap-2">
          <FileText size={16} className="text-gray-500" />
          <h2 className="font-semibold text-gray-800">Boletos</h2>
        </div>
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Referência</th>
              <th className="text-right text-xs font-medium text-gray-500 px-4 py-3">Valor</th>
              <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Vencimento</th>
              <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {boletos?.map((b: any) => (
              <tr key={b.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm font-medium">{b.reference_month}</td>
                <td className="px-4 py-3 text-sm text-right font-mono">
                  R$ {Number(b.amount).toFixed(2)}
                </td>
                <td className="px-4 py-3 text-sm text-gray-600">
                  {b.due_date ? format(new Date(b.due_date), 'dd/MM/yyyy', { locale: ptBR }) : '—'}
                </td>
                <td className="px-4 py-3">
                  <span className={clsx('badge px-2 py-0.5 rounded text-xs font-medium', boletoStatusColors[b.status] || 'bg-gray-100')}>
                    {b.status === 'pending' ? 'Pendente' : b.status === 'paid' ? 'Pago' : b.status === 'overdue' ? 'Vencido' : b.status}
                  </span>
                </td>
              </tr>
            ))}
            {!boletos?.length && (
              <tr><td colSpan={4} className="text-center py-6 text-gray-400 text-sm">Sem boletos</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
