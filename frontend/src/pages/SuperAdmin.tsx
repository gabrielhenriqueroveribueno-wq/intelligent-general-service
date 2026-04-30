import { useEffect, useState } from 'react'
import { api } from '../api/client'

interface Overview {
  total_tenants: number
  active_tenants: number
  inactive_tenants: number
  new_last_30_days: number
  mrr: number
  arr: number
  churn_rate_30d: number
  churned_last_30_days: number
  plan_breakdown: Record<string, number>
}

interface TenantRow {
  id: string
  name: string
  slug: string
  plan: string
  is_active: boolean
  monthly_revenue: number
  user_count: number
  whatsapp_configured: boolean
  created_at: string | null
}

const PLAN_BADGE: Record<string, string> = {
  trial: 'bg-yellow-100 text-yellow-800',
  starter: 'bg-blue-100 text-blue-800',
  pro: 'bg-purple-100 text-purple-800',
  enterprise: 'bg-green-100 text-green-800',
  basic: 'bg-gray-100 text-gray-700',
}

function fmt(n: number) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(n)
}

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-1">
      <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">{label}</span>
      <span className="text-2xl font-bold text-gray-900">{value}</span>
      {sub && <span className="text-xs text-gray-400">{sub}</span>}
    </div>
  )
}

export default function SuperAdmin() {
  const [overview, setOverview] = useState<Overview | null>(null)
  const [tenants, setTenants] = useState<TenantRow[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [filterPlan, setFilterPlan] = useState('')
  const [filterActive, setFilterActive] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [togglingId, setTogglingId] = useState<string | null>(null)

  const fetchOverview = async () => {
    try {
      const res = await api.get('/api/v1/admin/super/overview')
      setOverview(res.data)
    } catch {
      /* noop */
    }
  }

  const fetchTenants = async (p = 1) => {
    setLoading(true)
    try {
      const params: Record<string, string | number> = { page: p, size: 25 }
      if (search) params.search = search
      if (filterPlan) params.plan = filterPlan
      if (filterActive !== '') params.active = filterActive
      const res = await api.get('/api/v1/admin/super/tenants', { params })
      setTenants(res.data.items)
      setTotal(res.data.total)
    } catch {
      /* noop */
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchOverview()
  }, [])

  useEffect(() => {
    fetchTenants(page)
  }, [page, filterPlan, filterActive])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setPage(1)
    fetchTenants(1)
  }

  const toggleActive = async (tenant: TenantRow) => {
    setTogglingId(tenant.id)
    try {
      await api.patch(`/api/v1/admin/super/tenants/${tenant.id}`, {
        is_active: !tenant.is_active,
      })
      setTenants((prev) =>
        prev.map((t) => (t.id === tenant.id ? { ...t, is_active: !t.is_active } : t))
      )
      fetchOverview()
    } finally {
      setTogglingId(null)
    }
  }

  const totalPages = Math.ceil(total / 25)

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Super Admin</h1>
        <p className="text-sm text-gray-500 mt-1">Visão global de todos os tenants e receita</p>
      </div>

      {/* KPIs */}
      {overview && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="MRR" value={fmt(overview.mrr)} sub={`ARR ${fmt(overview.arr)}`} />
          <StatCard
            label="Tenants ativos"
            value={overview.active_tenants}
            sub={`${overview.total_tenants} total`}
          />
          <StatCard
            label="Novos (30d)"
            value={overview.new_last_30_days}
            sub="novos cadastros"
          />
          <StatCard
            label="Churn (30d)"
            value={`${overview.churn_rate_30d}%`}
            sub={`${overview.churned_last_30_days} cancelamentos`}
          />
        </div>
      )}

      {/* Plan breakdown */}
      {overview && Object.keys(overview.plan_breakdown).length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Distribuição de planos (ativos)</h2>
          <div className="flex flex-wrap gap-3">
            {Object.entries(overview.plan_breakdown).map(([plan, count]) => (
              <div key={plan} className="flex items-center gap-2">
                <span
                  className={`px-2 py-0.5 rounded-full text-xs font-semibold ${PLAN_BADGE[plan] ?? 'bg-gray-100 text-gray-700'}`}
                >
                  {plan}
                </span>
                <span className="text-sm font-medium text-gray-800">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white border border-gray-200 rounded-xl p-4">
        <form onSubmit={handleSearch} className="flex flex-wrap gap-3 items-end">
          <div className="flex-1 min-w-[200px]">
            <label className="block text-xs font-medium text-gray-600 mb-1">Buscar</label>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Nome ou slug..."
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Plano</label>
            <select
              value={filterPlan}
              onChange={(e) => { setFilterPlan(e.target.value); setPage(1) }}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todos</option>
              <option value="trial">Trial</option>
              <option value="starter">Starter</option>
              <option value="pro">Pro</option>
              <option value="enterprise">Enterprise</option>
              <option value="basic">Basic</option>
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Status</label>
            <select
              value={filterActive}
              onChange={(e) => { setFilterActive(e.target.value); setPage(1) }}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todos</option>
              <option value="true">Ativos</option>
              <option value="false">Inativos</option>
            </select>
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700"
          >
            Buscar
          </button>
        </form>
      </div>

      {/* Tenant table */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <div className="px-5 py-3 border-b border-gray-100 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-700">
            Tenants{' '}
            <span className="text-gray-400 font-normal">({total})</span>
          </h2>
        </div>

        {loading ? (
          <div className="p-8 text-center text-gray-400 text-sm">Carregando...</div>
        ) : tenants.length === 0 ? (
          <div className="p-8 text-center text-gray-400 text-sm">Nenhum tenant encontrado.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-left">
                  <th className="px-4 py-3 font-medium text-gray-600">Tenant</th>
                  <th className="px-4 py-3 font-medium text-gray-600">Plano</th>
                  <th className="px-4 py-3 font-medium text-gray-600">MRR</th>
                  <th className="px-4 py-3 font-medium text-gray-600">Usuários</th>
                  <th className="px-4 py-3 font-medium text-gray-600">WhatsApp</th>
                  <th className="px-4 py-3 font-medium text-gray-600">Criado em</th>
                  <th className="px-4 py-3 font-medium text-gray-600">Status</th>
                  <th className="px-4 py-3 font-medium text-gray-600"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {tenants.map((t) => (
                  <tr key={t.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-900">{t.name}</div>
                      <div className="text-xs text-gray-400">{t.slug}</div>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-semibold ${PLAN_BADGE[t.plan] ?? 'bg-gray-100 text-gray-700'}`}
                      >
                        {t.plan}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-medium text-gray-800">
                      {t.monthly_revenue > 0 ? fmt(t.monthly_revenue) : '—'}
                    </td>
                    <td className="px-4 py-3 text-gray-600">{t.user_count}</td>
                    <td className="px-4 py-3">
                      {t.whatsapp_configured ? (
                        <span className="text-green-600 font-medium">Configurado</span>
                      ) : (
                        <span className="text-gray-400">Pendente</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">
                      {t.created_at ? new Date(t.created_at).toLocaleDateString('pt-BR') : '—'}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                          t.is_active
                            ? 'bg-green-100 text-green-700'
                            : 'bg-red-100 text-red-700'
                        }`}
                      >
                        {t.is_active ? 'Ativo' : 'Suspenso'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => toggleActive(t)}
                        disabled={togglingId === t.id}
                        className={`text-xs px-3 py-1 rounded-lg border font-medium transition-colors ${
                          t.is_active
                            ? 'border-red-200 text-red-600 hover:bg-red-50'
                            : 'border-green-200 text-green-600 hover:bg-green-50'
                        } disabled:opacity-40`}
                      >
                        {togglingId === t.id ? '...' : t.is_active ? 'Suspender' : 'Ativar'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-5 py-3 border-t border-gray-100 flex items-center justify-between text-sm text-gray-500">
            <span>
              Página {page} de {totalPages}
            </span>
            <div className="flex gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="px-3 py-1 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40"
              >
                Anterior
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
                className="px-3 py-1 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40"
              >
                Próxima
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
