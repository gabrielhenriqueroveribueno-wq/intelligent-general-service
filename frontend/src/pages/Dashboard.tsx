import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  MessageSquare,
  Ticket,
  CheckCircle,
  AlertTriangle,
  TrendingUp,
  Clock,
  UserX,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import OnboardingWizard, { useOnboardingWizard } from '../components/common/OnboardingWizard'

interface EvasionSummary {
  critical: number
  high: number
  medium: number
  total_at_risk: number
  students: Array<{
    id: string
    full_name: string
    registration_number: string
    course: string | null
    evasion_risk_score: number
    evasion_risk_level: string
    evasion_factors: string[]
  }>
}

const RISK_COLORS: Record<string, string> = {
  critical: 'bg-red-100 text-red-700 border-red-200',
  high: 'bg-orange-100 text-orange-700 border-orange-200',
  medium: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  low: 'bg-green-100 text-green-700 border-green-200',
}

const RISK_LABELS: Record<string, string> = {
  critical: 'Crítico',
  high: 'Alto',
  medium: 'Médio',
  low: 'Baixo',
}

interface DashboardData {
  total_conversations_today: number
  total_conversations_week: number
  total_conversations_month: number
  auto_resolution_rate: number
  avg_response_time_seconds: number
  open_tickets: number
  sla_breached_tickets: number
  active_agents: number
}

function MetricCard({
  title,
  value,
  icon: Icon,
  color,
  subtitle,
}: {
  title: string
  value: string | number
  icon: React.ElementType
  color: string
  subtitle?: string
}) {
  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-500">{title}</p>
          <p className="text-3xl font-bold mt-1">{value}</p>
          {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-xl ${color}`}>
          <Icon size={20} className="text-white" />
        </div>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { isDone } = useOnboardingWizard()
  const [showWizard, setShowWizard] = useState(!isDone())

  const { data, isLoading } = useQuery<DashboardData>({
    queryKey: ['dashboard'],
    queryFn: () => api.get('/api/v1/dashboard/overview').then((r) => r.data),
    refetchInterval: 30_000,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    )
  }

  const { data: evasion } = useQuery<EvasionSummary>({
    queryKey: ['evasion-at-risk'],
    queryFn: () =>
      api.get('/api/v1/evasion/at-risk?limit=5').then((r) => r.data),
    refetchInterval: 5 * 60_000,
  })

  const chartData = [
    { name: 'Hoje', value: data?.total_conversations_today ?? 0 },
    { name: 'Semana', value: data?.total_conversations_week ?? 0 },
    { name: 'Mês', value: data?.total_conversations_month ?? 0 },
  ]

  return (
    <>
      {showWizard && <OnboardingWizard onClose={() => setShowWizard(false)} />}
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-500 text-sm mt-1">Visão geral do atendimento</p>
      </div>

      {/* Métricas principais */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Conversas Hoje"
          value={data?.total_conversations_today ?? 0}
          icon={MessageSquare}
          color="bg-blue-500"
          subtitle={`${data?.total_conversations_week ?? 0} esta semana`}
        />
        <MetricCard
          title="Resolução Automática"
          value={`${data?.auto_resolution_rate ?? 0}%`}
          icon={CheckCircle}
          color="bg-green-500"
          subtitle="Taxa do mês"
        />
        <MetricCard
          title="Tickets Abertos"
          value={data?.open_tickets ?? 0}
          icon={Ticket}
          color="bg-orange-500"
        />
        <MetricCard
          title="SLA Violado"
          value={data?.sla_breached_tickets ?? 0}
          icon={AlertTriangle}
          color={data?.sla_breached_tickets ? 'bg-red-500' : 'bg-gray-400'}
          subtitle="Tickets em atraso"
        />
      </div>

      {/* Gráfico */}
      <div className="card">
        <h2 className="font-semibold text-gray-800 mb-4">Volume de Conversas</h2>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            <Bar dataKey="value" name="Conversas" fill="#3b82f6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Info cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card">
          <div className="flex items-center gap-3 mb-3">
            <Clock size={18} className="text-blue-600" />
            <h3 className="font-medium text-gray-800">Tempo Médio de Resposta</h3>
          </div>
          <p className="text-2xl font-bold">
            {data?.avg_response_time_seconds
              ? `${(data.avg_response_time_seconds / 60).toFixed(1)}min`
              : '—'}
          </p>
          <p className="text-sm text-gray-400 mt-1">Via Prometheus</p>
        </div>
        <div className="card">
          <div className="flex items-center gap-3 mb-3">
            <TrendingUp size={18} className="text-green-600" />
            <h3 className="font-medium text-gray-800">Conversas no Mês</h3>
          </div>
          <p className="text-2xl font-bold">{data?.total_conversations_month ?? 0}</p>
          <p className="text-sm text-gray-400 mt-1">Últimos 30 dias</p>
        </div>
      </div>

      {/* Widget de Risco de Evasão */}
      {evasion && evasion.total_at_risk > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="bg-red-100 p-2 rounded-lg">
                <UserX size={18} className="text-red-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-800">Alunos em Risco de Evasão</h3>
                <p className="text-xs text-gray-400">
                  {evasion.critical > 0 && <span className="text-red-600 font-medium">{evasion.critical} crítico(s) · </span>}
                  {evasion.high > 0 && <span className="text-orange-600 font-medium">{evasion.high} alto(s) · </span>}
                  {evasion.medium > 0 && <span className="text-yellow-600">{evasion.medium} médio(s)</span>}
                </p>
              </div>
            </div>
            <Link
              to="/app/students?risk=high"
              className="text-sm text-blue-600 hover:underline"
            >
              Ver todos
            </Link>
          </div>
          <div className="space-y-2">
            {evasion.students.map((s) => (
              <Link
                key={s.id}
                to={`/app/students/${s.id}`}
                className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium text-gray-800 truncate">{s.full_name}</p>
                  <p className="text-xs text-gray-400">
                    RA {s.registration_number} · {s.course ?? 'Sem curso'}
                  </p>
                  {s.evasion_factors.length > 0 && (
                    <p className="text-xs text-gray-400 truncate">{s.evasion_factors[0]}</p>
                  )}
                </div>
                <span
                  className={`ml-3 text-xs font-medium px-2 py-0.5 rounded-full border flex-shrink-0 ${RISK_COLORS[s.evasion_risk_level] ?? RISK_COLORS.low}`}
                >
                  {RISK_LABELS[s.evasion_risk_level] ?? s.evasion_risk_level} · {s.evasion_risk_score}
                </span>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
    </>
  )
}
