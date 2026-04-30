import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { BookOpen, Plus, Search, Trash2 } from 'lucide-react'
import { api } from '../api/client'
import toast from 'react-hot-toast'

export default function KnowledgeBase() {
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ title: '', content: '', applies_to: 'all' })

  const { data: articles, isLoading } = useQuery({
    queryKey: ['kb-articles', search],
    queryFn: () =>
      api.get('/api/v1/kb/articles', { params: { search: search || undefined } }).then((r) => r.data),
  })

  const createMutation = useMutation({
    mutationFn: () => api.post('/api/v1/kb/articles', form),
    onSuccess: () => {
      toast.success('Artigo criado!')
      qc.invalidateQueries({ queryKey: ['kb-articles'] })
      setShowForm(false)
      setForm({ title: '', content: '', applies_to: 'all' })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/api/v1/kb/articles/${id}`),
    onSuccess: () => {
      toast.success('Artigo removido')
      qc.invalidateQueries({ queryKey: ['kb-articles'] })
    },
  })

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Base de Conhecimento</h1>
          <p className="text-sm text-gray-500">Gerencie respostas automáticas e FAQs</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary gap-2">
          <Plus size={16} /> Novo Artigo
        </button>
      </div>

      {showForm && (
        <div className="card">
          <h3 className="font-medium mb-4">Novo Artigo</h3>
          <div className="space-y-3">
            <input
              className="input"
              placeholder="Título"
              value={form.title}
              onChange={(e) => setForm(f => ({ ...f, title: e.target.value }))}
            />
            <textarea
              className="input resize-none"
              rows={4}
              placeholder="Conteúdo da resposta..."
              value={form.content}
              onChange={(e) => setForm(f => ({ ...f, content: e.target.value }))}
            />
            <select
              className="input"
              value={form.applies_to}
              onChange={(e) => setForm(f => ({ ...f, applies_to: e.target.value }))}
            >
              <option value="all">Todos</option>
              <option value="student">Alunos</option>
              <option value="employee">Funcionários</option>
            </select>
            <div className="flex gap-2">
              <button onClick={() => createMutation.mutate()} className="btn-primary" disabled={createMutation.isPending}>
                Salvar
              </button>
              <button onClick={() => setShowForm(false)} className="btn-secondary">Cancelar</button>
            </div>
          </div>
        </div>
      )}

      <div className="relative max-w-sm">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input className="input pl-9" placeholder="Buscar artigos..." value={search} onChange={(e) => setSearch(e.target.value)} />
      </div>

      <div className="space-y-3">
        {isLoading ? (
          <div className="flex items-center justify-center h-24">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600" />
          </div>
        ) : articles?.length ? (
          articles.map((art: any) => (
            <div key={art.id} className="card flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <BookOpen size={14} className="text-blue-600" />
                  <h4 className="font-medium text-sm">{art.title}</h4>
                  <span className="badge bg-gray-100 text-gray-600">{art.applies_to}</span>
                </div>
                <p className="text-sm text-gray-600 line-clamp-2">{art.content}</p>
                <p className="text-xs text-gray-400 mt-1">Usado {art.usage_count}x</p>
              </div>
              <button
                onClick={() => deleteMutation.mutate(art.id)}
                className="text-gray-400 hover:text-red-500 transition-colors"
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))
        ) : (
          <div className="text-center py-8 text-gray-400">
            <BookOpen className="mx-auto mb-2 opacity-30" size={32} />
            <p>Nenhum artigo encontrado</p>
          </div>
        )}
      </div>
    </div>
  )
}
