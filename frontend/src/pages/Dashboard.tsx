import { useQuery } from '@tanstack/react-query'
import {
  MessageSquare,
  Ticket,
  CheckCircle,
  AlertTriangle,
  TrendingUp,
  Clock,
} from 'lucide-react'
import { api } from '../api/client'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

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

  const chartData = [
    { name: 'Hoje', value: data?.total_conversations_today ?? 0 },
    { name: 'Semana', value: data?.total_conversations_week ?? 0 },
    { name: 'Mês', value: data?.total_conversations_month ?? 0 },
  ]

  return (
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
            <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
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
    </div>
  )
}
