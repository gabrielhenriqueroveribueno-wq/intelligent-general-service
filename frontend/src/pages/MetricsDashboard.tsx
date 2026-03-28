import { useState, useEffect } from 'react'
import { BarChart2, DollarSign, Clock, TrendingUp, Users, Bot, Phone } from 'lucide-react'
import { api } from '../api/client'
import toast from 'react-hot-toast'

interface ComparisonData {
  by_responder_type: Record<string, {
    avg_response_time_seconds: number
    total_interactions: number
    resolution_rate: number
    avg_satisfaction?: number
  }>
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
  const [newAccount, setNewAccount] = useState({ account_name: '', phone_number: '', account_type: 'mixed', notes: '' })
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

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Métricas IA vs Humano</h1>
        <p className="text-sm text-gray-500">Comparativo de desempenho e ROI</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="bg-blue-100 p-2 rounded-lg">
              <BarChart2 className="text-blue-600" size={20} />
            </div>
            <div>
              <p className="text-xs text-gray-500">Total Atendimentos</p>
              <p className="text-xl font-bold">{dashboard?.total_interactions ?? 0}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="bg-green-100 p-2 rounded-lg">
              <DollarSign className="text-green-600" size={20} />
            </div>
            <div>
              <p className="text-xs text-gray-500">Economia Mensal</p>
              <p className="text-xl font-bold text-green-600">
                R$ {roi?.monthly_savings?.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) ?? '0,00'}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="bg-purple-100 p-2 rounded-lg">
              <TrendingUp className="text-purple-600" size={20} />
            </div>
            <div>
              <p className="text-xs text-gray-500">ROI (%)</p>
              <p className="text-xl font-bold text-purple-600">{roi?.savings_percentage ?? 0}%</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="bg-orange-100 p-2 rounded-lg">
              <Clock className="text-orange-600" size={20} />
            </div>
            <div>
              <p className="text-xs text-gray-500">Tempo Economizado/Atend.</p>
              <p className="text-xl font-bold">{roi?.avg_time_saved_per_interaction_seconds?.toFixed(1) ?? 0}s</p>
            </div>
          </div>
        </div>
      </div>

      {/* Comparison Table */}
      <div className="card">
        <h3 className="font-medium mb-4">Comparativo de Desempenho</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-gray-500">
                <th className="pb-2">Métrica</th>
                <th className="pb-2"><Bot size={14} className="inline mr-1" />IA (Bot)</th>
                <th className="pb-2"><Users size={14} className="inline mr-1" />Humano</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              <tr>
                <td className="py-2 text-gray-600">Tempo Médio de Resposta</td>
                <td className="py-2 font-medium">{botData?.avg_response_time_seconds?.toFixed(2) ?? '-'}s</td>
                <td className="py-2 font-medium">{humanData?.avg_response_time_seconds?.toFixed(2) ?? '-'}s</td>
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
        <h3 className="font-medium mb-4">Análise de Custos</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-50 rounded-lg p-4 text-center">
            <p className="text-xs text-gray-500 mb-1">Custo Mensal IA</p>
            <p className="text-lg font-bold text-blue-600">
              R$ {roi?.ai_monthly_cost?.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) ?? '0,00'}
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4 text-center">
            <p className="text-xs text-gray-500 mb-1">Custo Mensal Humano</p>
            <p className="text-lg font-bold text-orange-600">
              R$ {roi?.human_monthly_cost?.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) ?? '0,00'}
            </p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4 text-center">
            <p className="text-xs text-gray-500 mb-1">Custo Hipotético (100% Humano)</p>
            <p className="text-lg font-bold text-red-600">
              R$ {roi?.hypothetical_full_human_cost?.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) ?? '0,00'}
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
            <input className="input" placeholder="Nome da conta" value={newAccount.account_name}
              onChange={(e) => setNewAccount({ ...newAccount, account_name: e.target.value })} />
            <input className="input" placeholder="Número (+5511...)" value={newAccount.phone_number}
              onChange={(e) => setNewAccount({ ...newAccount, phone_number: e.target.value })} />
            <select className="input" value={newAccount.account_type}
              onChange={(e) => setNewAccount({ ...newAccount, account_type: e.target.value })}>
              <option value="ai_bot">IA Bot</option>
              <option value="human_agent">Humano</option>
              <option value="mixed">Misto</option>
            </select>
            <input className="input" placeholder="Observações" value={newAccount.notes}
              onChange={(e) => setNewAccount({ ...newAccount, notes: e.target.value })} />
            <button className="btn-primary col-span-full" onClick={addAccount}>Salvar</button>
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
                      <span className={`px-2 py-0.5 rounded-full text-xs ${
                        acc.account_type === 'ai_bot' ? 'bg-blue-100 text-blue-700' :
                        acc.account_type === 'human_agent' ? 'bg-orange-100 text-orange-700' :
                        'bg-gray-100 text-gray-700'
                      }`}>
                        {acc.account_type === 'ai_bot' ? 'IA' : acc.account_type === 'human_agent' ? 'Humano' : 'Misto'}
                      </span>
                    </td>
                    <td className="py-2">
                      <span className={`w-2 h-2 rounded-full inline-block mr-1 ${acc.is_active ? 'bg-green-500' : 'bg-gray-400'}`} />
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
