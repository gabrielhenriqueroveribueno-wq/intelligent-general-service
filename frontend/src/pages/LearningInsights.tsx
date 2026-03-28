import { useState, useEffect } from 'react'
import { Brain, Star, Clock, Tag, TrendingUp } from 'lucide-react'
import { api } from '../api/client'
import toast from 'react-hot-toast'

interface ResolutionStats {
  total_resolutions: number
  avg_satisfaction: number | null
  avg_resolution_time_seconds: number | null
  top_categories: Array<{ category: string; count: number }>
}

export default function LearningInsights() {
  const [stats, setStats] = useState<ResolutionStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const res = await api.get('/api/v1/metrics/dashboard')
      setStats(res.data.learning_stats ?? null)
    } catch {
      toast.error('Erro ao carregar dados de aprendizado')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600" />
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Aprendizado da IA</h1>
        <p className="text-sm text-gray-500">Insights baseados em tickets resolvidos</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center gap-3">
            <div className="bg-purple-100 p-2 rounded-lg">
              <Brain className="text-purple-600" size={20} />
            </div>
            <div>
              <p className="text-xs text-gray-500">Resoluções Indexadas</p>
              <p className="text-xl font-bold">{stats?.total_resolutions ?? 0}</p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="bg-yellow-100 p-2 rounded-lg">
              <Star className="text-yellow-600" size={20} />
            </div>
            <div>
              <p className="text-xs text-gray-500">Satisfação Média</p>
              <p className="text-xl font-bold">
                {stats?.avg_satisfaction ? `${stats.avg_satisfaction.toFixed(1)}/5` : '-'}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="bg-blue-100 p-2 rounded-lg">
              <Clock className="text-blue-600" size={20} />
            </div>
            <div>
              <p className="text-xs text-gray-500">Tempo Médio Resolução</p>
              <p className="text-xl font-bold">
                {stats?.avg_resolution_time_seconds
                  ? `${Math.round(stats.avg_resolution_time_seconds / 60)}min`
                  : '-'}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3">
            <div className="bg-green-100 p-2 rounded-lg">
              <TrendingUp className="text-green-600" size={20} />
            </div>
            <div>
              <p className="text-xs text-gray-500">Categorias</p>
              <p className="text-xl font-bold">{stats?.top_categories?.length ?? 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Categories */}
      <div className="card">
        <h3 className="font-medium mb-4">Categorias de Problemas Mais Comuns</h3>
        {!stats?.top_categories?.length ? (
          <div className="text-center py-8 text-gray-500">
            <Brain size={40} className="mx-auto mb-2 opacity-50" />
            <p>Nenhuma resolução indexada ainda.</p>
            <p className="text-xs mt-1">As resoluções aparecem conforme tickets são fechados.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {stats.top_categories.map((cat, i) => {
              const maxCount = stats.top_categories[0]?.count || 1
              const pct = (cat.count / maxCount) * 100
              return (
                <div key={cat.category}>
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <Tag size={14} className="text-gray-400" />
                      <span className="text-sm font-medium capitalize">{cat.category}</span>
                    </div>
                    <span className="text-sm text-gray-500">{cat.count} resoluções</span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        i === 0 ? 'bg-purple-500' : i === 1 ? 'bg-blue-500' : 'bg-gray-400'
                      }`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* How it works */}
      <div className="card">
        <h3 className="font-medium mb-3">Como Funciona o Aprendizado</h3>
        <div className="space-y-2 text-sm text-gray-600">
          <p>1. Quando um ticket é resolvido, a IA analisa a conversa e extrai o problema e a solução.</p>
          <p>2. Essas resoluções são indexadas com categorias e tags para busca rápida.</p>
          <p>3. Em novas conversas, a IA busca resoluções similares e usa como referência para sugerir soluções.</p>
          <p>4. Resoluções com melhor avaliação de satisfação são priorizadas.</p>
        </div>
      </div>
    </div>
  )
}
