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
  Bot,
  Sparkles,
  Zap,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import OnboardingWizard, { useOnboardingWizard } from '../components/common/OnboardingWizard'
import AnimatedCounter from '../components/common/AnimatedCounter'

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

export default function Dashboard() {
  const { isDone } = useOnboardingWizard()
  const [showWizard, setShowWizard] = useState(!isDone())

  const { data, isLoading } = useQuery<DashboardData>({
    queryKey: ['dashboard'],
    queryFn: () => api.get('/api/v1/dashboard/overview').then((r) => r.data),
    refetchInterval: 30_000,
  })

  const { data: evasion } = useQuery<EvasionSummary>({
    queryKey: ['evasion-at-risk'],
    queryFn: () => api.get('/api/v1/evasion/at-risk?limit=5').then((r) => r.data),
    refetchInterval: 5 * 60_000,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    )
  }

  const chartData = [
    { name: 'Hoje', value: data?.total_conversations_today ?? 0 },
    { name: 'Semana', value: data?.total_conversations_week ?? 0 },
    { name: 'Mês', value: data?.total_conversations_month ?? 0 },
  ]

  const autoRate = data?.auto_resolution_rate ?? 0
  const avgRespMin = data?.avg_response_time_seconds
    ? data.avg_response_time_seconds / 60
    : 0

  return (
    <>
      {showWizard && <OnboardingWizard onClose={() => setShowWizard(false)} />}
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 text-sm mt-1">Visão geral do atendimento</p>
        </div>

        {/* HERO ─ taxa de resolução automática (numero gigante + glow) */}
        <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-600 p-8 text-white shadow-xl">
          <div className="absolute -top-16 -right-16 w-64 h-64 bg-white/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute -bottom-12 -left-12 w-48 h-48 bg-white/10 rounded-full blur-3xl pointer-events-none" />

          <div className="relative grid grid-cols-1 lg:grid-cols-3 gap-6 items-center">
            <div className="lg:col-span-2">
              <div className="flex items-center gap-2 mb-3">
                <div className="bg-white/20 p-2 rounded-lg backdrop-blur">
                  <Bot size={18} />
                </div>
                <span className="text-xs uppercase tracking-widest text-white/80 font-semibold">
                  IA atendendo agora
                </span>
                <span className="ml-1 inline-flex h-2 w-2 rounded-full bg-green-400 animate-pulse" />
              </div>
              <p className="text-7xl md:text-8xl font-extrabold leading-none tracking-tight">
                <AnimatedCounter value={autoRate} suffix="%" duration={1500} />
              </p>
              <p className="text-xl mt-3 text-white/90 font-medium">
                das conversas resolvidas <span className="text-white">automaticamente</span>
              </p>
              <p className="text-sm mt-1 text-white/70">
                A Billie cuida do trivial — sua equipe foca no que importa
              </p>
            </div>

            <div className="grid grid-cols-2 lg:grid-cols-1 gap-4">
              <div className="bg-white/10 backdrop-blur rounded-xl p-4 border border-white/20">
                <div className="flex items-center gap-2 text-white/80 text-xs mb-1">
                  <Zap size={14} /> Conversas hoje
                </div>
                <p className="text-3xl font-bold">
                  <AnimatedCounter value={data?.total_conversations_today ?? 0} />
                </p>
              </div>
              <div className="bg-white/10 backdrop-blur rounded-xl p-4 border border-white/20">
                <div className="flex items-center gap-2 text-white/80 text-xs mb-1">
                  <Clock size={14} /> Resp. média
                </div>
                <p className="text-3xl font-bold">
                  <AnimatedCounter value={avgRespMin} decimals={1} suffix="min" />
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Grid 4 cards animados */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Conversas Hoje"
            value={data?.total_conversations_today ?? 0}
            icon={MessageSquare}
            color="from-blue-500 to-blue-600"
            subtitle={`${data?.total_conversations_week ?? 0} esta semana`}
          />
          <StatCard
            label="Resolução Automática"
            value={autoRate}
            suffix="%"
            icon={CheckCircle}
            color="from-green-500 to-emerald-600"
            subtitle="Taxa do mês"
          />
          <StatCard
            label="Tickets Abertos"
            value={data?.open_tickets ?? 0}
            icon={Ticket}
            color="from-orange-500 to-amber-600"
          />
          <StatCard
            label="SLA Violado"
            value={data?.sla_breached_tickets ?? 0}
            icon={AlertTriangle}
            color={
              data?.sla_breached_tickets
                ? 'from-red-500 to-rose-600'
                : 'from-gray-400 to-gray-500'
            }
            subtitle="Tickets em atraso"
          />
        </div>

        {/* Gráfico */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-gray-800">Volume de Conversas</h2>
            <span className="flex items-center gap-1 text-xs text-gray-400">
              <Sparkles size={12} /> Atualiza a cada 30s
            </span>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={chartData}>
              <defs>
                <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.95} />
                  <stop offset="100%" stopColor="#6366f1" stopOpacity={0.7} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  borderRadius: 8,
                  border: '1px solid #e5e7eb',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                }}
              />
              <Bar
                dataKey="value"
                name="Conversas"
                fill="url(#barGrad)"
                radius={[6, 6, 0, 0]}
                animationDuration={900}
              />
            </BarChart>
          </ResponsiveContainer>
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
                    {evasion.critical > 0 && (
                      <span className="text-red-600 font-medium">{evasion.critical} crítico(s) · </span>
                    )}
                    {evasion.high > 0 && (
                      <span className="text-orange-600 font-medium">{evasion.high} alto(s) · </span>
                    )}
                    {evasion.medium > 0 && (
                      <span className="text-yellow-600">{evasion.medium} médio(s)</span>
                    )}
                  </p>
                </div>
              </div>
              <Link to="/app/students?risk=high" className="text-sm text-blue-600 hover:underline">
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
                    className={`ml-3 text-xs font-medium px-2 py-0.5 rounded-full border flex-shrink-0 ${
                      RISK_COLORS[s.evasion_risk_level] ?? RISK_COLORS.low
                    }`}
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

function StatCard({
  label,
  value,
  suffix,
  icon: Icon,
  color,
  subtitle,
}: {
  label: string
  value: number
  suffix?: string
  icon: React.ElementType
  color: string
  subtitle?: string
}) {
  return (
    <div className="card hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-sm text-gray-500">{label}</p>
          <p className="text-3xl font-bold mt-1">
            <AnimatedCounter value={value} suffix={suffix} />
          </p>
          {subtitle && <p className="text-xs text-gray-400 mt-1">{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-xl bg-gradient-to-br ${color} shrink-0 shadow-sm`}>
          <Icon size={20} className="text-white" />
        </div>
      </div>
    </div>
  )
}
