import { useState, useEffect } from 'react'
import {
  BarChart2,
  DollarSign,
  Clock,
  TrendingUp,
  Users,
  Bot,
  Phone,
  Zap,
  ArrowRight,
  Frown,
  Smile,
} from 'lucide-react'
import { api } from '../api/client'
import toast from 'react-hot-toast'
import AnimatedCounter from '../components/common/AnimatedCounter'

interface ComparisonData {
  by_responder_type: Record<
    string,
    {
      avg_response_time_seconds: number
      total_interactions: number
      resolution_rate: number
      avg_satisfaction?: number
    }
  >
}

interface ROIData {
  bot_interactions: number
  human_interactions: number
  ai_monthly_cost: number
  human_monthly_cost: number
  hypothetical_full_human_cost: number
  monthly_savings: number
  savings_percentage: number
  avg_time_saved_per_interaction_seconds: number
}

interface DashboardData {
  total_interactions: number
  comparison: { by_responder_type: ComparisonData['by_responder_type'] }
  roi: ROIData
}

interface MonitoredAccount {
  id: string
  account_name: string
  phone_number: string
  account_type: string
  is_active: boolean
  notes: string | null
}

export default function MetricsDashboard() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [accounts, setAccounts] = useState<MonitoredAccount[]>([])
  const [loading, setLoading] = useState(true)
  const [newAccount, setNewAccount] = useState({
    account_name: '',
    phone_number: '',
    account_type: 'mixed',
    notes: '',
  })
  const [showForm, setShowForm] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const [dashRes, accRes] = await Promise.all([
        api.get('/api/v1/metrics/dashboard'),
        api.get('/api/v1/metrics/monitored-accounts'),
      ])
      setDashboard(dashRes.data)
      setAccounts(accRes.data)
    } catch {
      toast.error('Erro ao carregar métricas')
    } finally {
      setLoading(false)
    }
  }

  const addAccount = async () => {
    try {
      await api.post('/api/v1/metrics/monitored-accounts', newAccount)
      toast.success('Conta adicionada!')
      setShowForm(false)
      setNewAccount({ account_name: '', phone_number: '', account_type: 'mixed', notes: '' })
      loadData()
    } catch {
      toast.error('Erro ao adicionar conta')
    }
  }

  const botData = dashboard?.comparison?.by_responder_type?.bot
  const humanData = dashboard?.comparison?.by_responder_type?.human
  const roi = dashboard?.roi

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    )
  }

  // Estimativas pra demonstrativos visuais
  const botRespSec = botData?.avg_response_time_seconds ?? 3
  const humanRespSec = humanData?.avg_response_time_seconds ?? 240
  const speedMultiplier = humanRespSec > 0 ? humanRespSec / Math.max(botRespSec, 1) : 1
  const savings = roi?.monthly_savings ?? 0
  const savingsPct = roi?.savings_percentage ?? 0

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Métricas IA vs Humano</h1>
        <p className="text-sm text-gray-500">Comparativo de desempenho e ROI</p>
      </div>

      {/* HERO: Antes vs Depois */}
      <div className="rounded-2xl overflow-hidden shadow-lg">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-px bg-gray-200">
          {/* ANTES */}
          <div className="bg-navy-750 p-7 text-white relative overflow-hidden">
            <div className="absolute top-0 right-0 opacity-10">
              <Frown size={140} />
            </div>
            <div className="relative">
              <div className="flex items-center gap-2 mb-2">
                <span className="px-2 py-0.5 rounded-full text-[10px] uppercase tracking-wider font-bold bg-white/20 backdrop-blur">
                  Antes do IGS
                </span>
              </div>
              <h3 className="text-lg font-semibold text-gray-300 mb-4">Atendimento manual</h3>

              <div className="space-y-4">
                <div>
                  <p className="text-xs text-gray-400 mb-1">Tempo médio de resposta</p>
                  <p className="text-5xl font-extrabold text-gray-100">
                    <AnimatedCounter
                      value={Math.round(humanRespSec / 60)}
                      suffix=" min"
                      duration={1500}
                    />
                  </p>
                </div>

                <div>
                  <p className="text-xs text-gray-400 mb-1">Custo mensal estimado</p>
                  <p className="text-3xl font-bold text-gray-100">
                    R${' '}
                    <AnimatedCounter
                      value={roi?.hypothetical_full_human_cost ?? 0}
                      duration={1800}
                      decimals={0}
                    />
                  </p>
                </div>

                <ul className="text-sm text-gray-400 space-y-1 mt-3">
                  <li>· Sem cobertura 24/7</li>
                  <li>· Filas e mensagens não respondidas</li>
                  <li>· Equipe sobrecarregada com perguntas repetitivas</li>
                </ul>
              </div>
            </div>
          </div>

          {/* DEPOIS */}
          <div className="bg-green-600 p-7 text-white relative overflow-hidden">
            <div className="absolute top-0 right-0 opacity-10">
              <Smile size={140} />
            </div>
            <div className="relative">
              <div className="flex items-center gap-2 mb-2">
                <span className="px-2 py-0.5 rounded-full text-[10px] uppercase tracking-wider font-bold bg-white/30 backdrop-blur flex items-center gap-1">
                  <Bot size={10} /> Com IGS
                </span>
              </div>
              <h3 className="text-lg font-semibold text-white/90 mb-4">Atendimento com a Billie</h3>

              <div className="space-y-4">
                <div>
                  <p className="text-xs text-white/80 mb-1">Tempo médio de resposta</p>
                  <p className="text-5xl font-extrabold">
                    <AnimatedCounter value={botRespSec} decimals={1} suffix=" s" duration={1500} />
                  </p>
                </div>

                <div>
                  <p className="text-xs text-white/80 mb-1">Custo mensal IGS</p>
                  <p className="text-3xl font-bold">
                    R${' '}
                    <AnimatedCounter
                      value={(roi?.ai_monthly_cost ?? 0) + (roi?.human_monthly_cost ?? 0)}
                      duration={1800}
                      decimals={0}
                    />
                  </p>
                </div>

                <ul className="text-sm text-white/90 space-y-1 mt-3">
                  <li>· Atendimento 24/7</li>
                  <li>· Resposta em segundos</li>
                  <li>· Equipe foca em casos complexos</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Faixa de economia */}
        <div className="bg-white px-7 py-5 flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-gray-100">
          <div className="flex items-center gap-3">
            <div className="bg-green-100 p-3 rounded-xl">
              <ArrowRight className="text-green-600" size={22} />
            </div>
            <div>
              <p className="text-xs uppercase tracking-wider text-gray-500 font-semibold">
                Economia mensal
              </p>
              <p className="text-3xl font-extrabold text-green-600">
                R${' '}
                <AnimatedCounter value={savings} duration={1800} decimals={0} />
                <span className="text-lg text-green-500 ml-2">
                  (<AnimatedCounter value={savingsPct} suffix="%" duration={1500} />)
                </span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="bg-blue-100 p-3 rounded-xl">
              <Zap className="text-blue-600" size={22} />
            </div>
            <div>
              <p className="text-xs uppercase tracking-wider text-gray-500 font-semibold">
                Velocidade
              </p>
              <p className="text-2xl font-bold text-blue-600">
                <AnimatedCounter value={Math.round(speedMultiplier)} suffix="x" duration={1500} />
                <span className="text-sm text-gray-500 ml-2">mais rápido</span>
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          icon={BarChart2}
          color="text-primary-500"
          label="Total Atendimentos"
          value={dashboard?.total_interactions ?? 0}
        />
        <KPICard
          icon={Bot}
          color="text-purple-400"
          label="Atendimentos pela IA"
          value={roi?.bot_interactions ?? 0}
        />
        <KPICard
          icon={Users}
          color="text-orange-400"
          label="Atendimentos por Humano"
          value={roi?.human_interactions ?? 0}
        />
        <KPICard
          icon={Clock}
          color="text-green-400"
          label="Tempo Economizado/Atend."
          value={roi?.avg_time_saved_per_interaction_seconds ?? 0}
          decimals={1}
          suffix="s"
        />
      </div>

      {/* Comparison Table */}
      <div className="card">
        <h3 className="font-medium mb-4 flex items-center gap-2">
          <BarChart2 size={16} className="text-blue-600" />
          Comparativo detalhado
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-gray-500">
                <th className="pb-2">Métrica</th>
                <th className="pb-2">
                  <Bot size={14} className="inline mr-1 text-purple-600" />
                  IA (Bot)
                </th>
                <th className="pb-2">
                  <Users size={14} className="inline mr-1 text-orange-600" />
                  Humano
                </th>
              </tr>
            </thead>
            <tbody className="divide-y">
              <tr>
                <td className="py-2 text-gray-600">Tempo Médio de Resposta</td>
                <td className="py-2 font-medium text-purple-600">
                  {botData?.avg_response_time_seconds?.toFixed(2) ?? '-'}s
                </td>
                <td className="py-2 font-medium text-orange-600">
                  {humanData?.avg_response_time_seconds?.toFixed(2) ?? '-'}s
                </td>
              </tr>
              <tr>
                <td className="py-2 text-gray-600">Total de Interações</td>
                <td className="py-2 font-medium">{botData?.total_interactions ?? 0}</td>
                <td className="py-2 font-medium">{humanData?.total_interactions ?? 0}</td>
              </tr>
              <tr>
                <td className="py-2 text-gray-600">Taxa de Resolução</td>
                <td className="py-2 font-medium">{botData?.resolution_rate ?? 0}%</td>
                <td className="py-2 font-medium">{humanData?.resolution_rate ?? 0}%</td>
              </tr>
              <tr>
                <td className="py-2 text-gray-600">Satisfação Média</td>
                <td className="py-2 font-medium">{botData?.avg_satisfaction?.toFixed(1) ?? '-'}/5</td>
                <td className="py-2 font-medium">{humanData?.avg_satisfaction?.toFixed(1) ?? '-'}/5</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Cost Breakdown */}
      <div className="card">
        <h3 className="font-medium mb-4 flex items-center gap-2">
          <DollarSign size={16} className="text-green-600" />
          Análise de custos
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 rounded-xl p-4 text-center border border-blue-100">
            <p className="text-xs text-gray-500 mb-1">Custo Mensal IA</p>
            <p className="text-xl font-bold text-blue-600">
              R$ {roi?.ai_monthly_cost?.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) ?? '0,00'}
            </p>
          </div>
          <div className="bg-orange-50 rounded-xl p-4 text-center border border-orange-100">
            <p className="text-xs text-gray-500 mb-1">Custo Mensal Humano</p>
            <p className="text-xl font-bold text-orange-600">
              R$ {roi?.human_monthly_cost?.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) ?? '0,00'}
            </p>
          </div>
          <div className="bg-red-50 rounded-xl p-4 text-center border border-red-100">
            <p className="text-xs text-gray-500 mb-1">Hipotético (100% Humano)</p>
            <p className="text-xl font-bold text-red-600">
              R${' '}
              {roi?.hypothetical_full_human_cost?.toLocaleString('pt-BR', {
                minimumFractionDigits: 2,
              }) ?? '0,00'}
            </p>
          </div>
        </div>
      </div>

      {/* Monitored Accounts */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-medium">Contas WhatsApp Monitoradas</h3>
          <button className="btn-primary text-sm" onClick={() => setShowForm(!showForm)}>
            <Phone size={14} className="mr-1" />
            Adicionar Conta
          </button>
        </div>

        {showForm && (
          <div className="bg-gray-50 rounded-lg p-4 mb-4 grid grid-cols-1 md:grid-cols-2 gap-3">
            <input
              className="input"
              placeholder="Nome da conta"
              value={newAccount.account_name}
              onChange={(e) => setNewAccount({ ...newAccount, account_name: e.target.value })}
            />
            <input
              className="input"
              placeholder="Número (+5511...)"
              value={newAccount.phone_number}
              onChange={(e) => setNewAccount({ ...newAccount, phone_number: e.target.value })}
            />
            <select
              className="input"
              value={newAccount.account_type}
              onChange={(e) => setNewAccount({ ...newAccount, account_type: e.target.value })}
            >
              <option value="ai_bot">IA Bot</option>
              <option value="human_agent">Humano</option>
              <option value="mixed">Misto</option>
            </select>
            <input
              className="input"
              placeholder="Observações"
              value={newAccount.notes}
              onChange={(e) => setNewAccount({ ...newAccount, notes: e.target.value })}
            />
            <button className="btn-primary col-span-full" onClick={addAccount}>
              Salvar
            </button>
          </div>
        )}

        {accounts.length === 0 ? (
          <p className="text-sm text-gray-500">Nenhuma conta monitorada.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-500">
                  <th className="pb-2">Nome</th>
                  <th className="pb-2">Número</th>
                  <th className="pb-2">Tipo</th>
                  <th className="pb-2">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {accounts.map((acc) => (
                  <tr key={acc.id}>
                    <td className="py-2">{acc.account_name}</td>
                    <td className="py-2">{acc.phone_number}</td>
                    <td className="py-2">
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs ${
                          acc.account_type === 'ai_bot'
                            ? 'bg-blue-100 text-blue-700'
                            : acc.account_type === 'human_agent'
                              ? 'bg-orange-100 text-orange-700'
                              : 'bg-gray-100 text-gray-700'
                        }`}
                      >
                        {acc.account_type === 'ai_bot'
                          ? 'IA'
                          : acc.account_type === 'human_agent'
                            ? 'Humano'
                            : 'Misto'}
                      </span>
                    </td>
                    <td className="py-2">
                      <span
                        className={`w-2 h-2 rounded-full inline-block mr-1 ${
                          acc.is_active ? 'bg-green-500' : 'bg-gray-400'
                        }`}
                      />
                      {acc.is_active ? 'Ativo' : 'Inativo'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

function KPICard({
  icon: Icon,
  color,
  label,
  value,
  decimals = 0,
  suffix,
}: {
  icon: React.ElementType
  color: string
  label: string
  value: number
  decimals?: number
  suffix?: string
}) {
  return (
    <div className="card hover:shadow-md transition-shadow">
      <div className="flex items-center gap-3">
        <div className="p-2.5 rounded-xl bg-navy-700">
          <Icon className={color} size={20} />
        </div>
        <div className="min-w-0">
          <p className="text-xs text-gray-500">{label}</p>
          <p className="text-xl font-bold">
            <AnimatedCounter value={value} decimals={decimals} suffix={suffix} />
          </p>
        </div>
      </div>
    </div>
  )
}
