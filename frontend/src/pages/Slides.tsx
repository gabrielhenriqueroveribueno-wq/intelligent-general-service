import { useState, useEffect } from 'react'
import { api } from '../api/client'
import {
  Presentation,
  Plus,
  Download,
  Eye,
  RefreshCw,
  ChevronLeft,
  FileText,
  Loader2,
} from 'lucide-react'

interface SlideItem {
  slide_number: number
  title: string
  content: string[]
  notes?: string
  layout: string
}

interface PresentationItem {
  id: string
  title: string
  subject: string
  prompt_used: string
  slides_content: SlideItem[]
  status: string
  version: number
  total_slides: number
  created_at: string
  updated_at: string
  template_id?: string
}

interface TemplateItem {
  id: string
  name: string
  description?: string
  is_default: boolean
}

export default function Slides() {
  const [presentations, setPresentations] = useState<PresentationItem[]>([])
  const [templates, setTemplates] = useState<TemplateItem[]>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<PresentationItem | null>(null)
  const [showGenerate, setShowGenerate] = useState(false)
  const [generating, setGenerating] = useState(false)

  // Form state
  const [prompt, setPrompt] = useState('')
  const [subject, setSubject] = useState('')
  const [templateId, setTemplateId] = useState('')
  const [numSlides, setNumSlides] = useState<number | ''>('')

  // Update state
  const [updatePrompt, setUpdatePrompt] = useState('')
  const [updating, setUpdating] = useState(false)

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    setLoading(true)
    try {
      const [presRes, tmplRes] = await Promise.all([
        api.get('/api/v1/slides/presentations'),
        api.get('/api/v1/slides/templates'),
      ])
      setPresentations(presRes.data.items || [])
      setTemplates(tmplRes.data || [])
    } catch {
      /* handled by interceptor */
    }
    setLoading(false)
  }

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault()
    setGenerating(true)
    try {
      const body: Record<string, unknown> = { prompt, subject }
      if (templateId) body.template_id = templateId
      if (numSlides) body.num_slides = numSlides
      const res = await api.post('/api/v1/slides/generate', body)
      setPresentations((prev) => [res.data, ...prev])
      setSelected(res.data)
      setShowGenerate(false)
      setPrompt('')
      setSubject('')
      setNumSlides('')
    } catch {
      /* handled by interceptor */
    }
    setGenerating(false)
  }

  async function handleUpdate(e: React.FormEvent) {
    e.preventDefault()
    if (!selected) return
    setUpdating(true)
    try {
      const res = await api.patch(`/api/v1/slides/presentations/${selected.id}`, {
        prompt: updatePrompt,
      })
      setSelected(res.data)
      setPresentations((prev) => prev.map((p) => (p.id === res.data.id ? res.data : p)))
      setUpdatePrompt('')
    } catch {
      /* handled by interceptor */
    }
    setUpdating(false)
  }

  async function handleDownload(id: string, title: string) {
    try {
      const res = await api.get(`/api/v1/slides/presentations/${id}/download`, {
        responseType: 'blob',
      })
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.download = `${title.replace(/\s+/g, '_').slice(0, 50)}.pptx`
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch {
      /* handled by interceptor */
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-blue-600" size={32} />
      </div>
    )
  }

  // Detail view
  if (selected) {
    return (
      <div className="space-y-5">
        <div className="flex items-center gap-3">
          <button onClick={() => setSelected(null)} className="btn-secondary flex items-center gap-1">
            <ChevronLeft size={16} /> Voltar
          </button>
          <h1 className="text-2xl font-bold text-gray-900 flex-1">{selected.title}</h1>
          <button
            onClick={() => handleDownload(selected.id, selected.title)}
            className="btn-primary flex items-center gap-2"
          >
            <Download size={16} /> Baixar PPTX
          </button>
        </div>

        <div className="grid grid-cols-3 gap-3 text-sm">
          <div className="card text-center">
            <p className="text-gray-500">Disciplina</p>
            <p className="font-semibold">{selected.subject}</p>
          </div>
          <div className="card text-center">
            <p className="text-gray-500">Slides</p>
            <p className="font-semibold">{selected.total_slides}</p>
          </div>
          <div className="card text-center">
            <p className="text-gray-500">Versao</p>
            <p className="font-semibold">v{selected.version}</p>
          </div>
        </div>

        {/* Slide preview */}
        <div className="space-y-3">
          {selected.slides_content.map((slide, idx) => (
            <div key={idx} className="card border-l-4 border-blue-500">
              <div className="flex items-center gap-2 mb-2">
                <span className="bg-blue-100 text-blue-700 text-xs font-bold px-2 py-0.5 rounded">
                  {slide.slide_number || idx + 1}
                </span>
                <h3 className="font-semibold">{slide.title}</h3>
                <span className="text-xs text-gray-400 ml-auto">{slide.layout}</span>
              </div>
              <ul className="list-disc list-inside text-sm text-gray-700 space-y-1">
                {slide.content.map((item, i) => (
                  <li key={i}>{item}</li>
                ))}
              </ul>
              {slide.notes && (
                <p className="mt-2 text-xs text-gray-400 italic">Notas: {slide.notes}</p>
              )}
            </div>
          ))}
        </div>

        {/* Update form */}
        <form onSubmit={handleUpdate} className="card">
          <h3 className="font-semibold mb-2 flex items-center gap-2">
            <RefreshCw size={16} /> Atualizar Slides via IA
          </h3>
          <textarea
            value={updatePrompt}
            onChange={(e) => setUpdatePrompt(e.target.value)}
            className="input resize-none"
            rows={3}
            placeholder="Ex: Adicione um slide sobre o ciclo de Calvin apos o slide 4"
            required
            minLength={5}
          />
          <button
            type="submit"
            disabled={updating || updatePrompt.length < 5}
            className="btn-primary mt-2 flex items-center gap-2"
          >
            {updating ? <Loader2 className="animate-spin" size={16} /> : <RefreshCw size={16} />}
            {updating ? 'Atualizando...' : 'Atualizar'}
          </button>
        </form>
      </div>
    )
  }

  // Generate form
  if (showGenerate) {
    return (
      <div className="space-y-5">
        <div className="flex items-center gap-3">
          <button onClick={() => setShowGenerate(false)} className="btn-secondary flex items-center gap-1">
            <ChevronLeft size={16} /> Voltar
          </button>
          <h1 className="text-2xl font-bold text-gray-900">Gerar Apresentacao</h1>
        </div>

        <form onSubmit={handleGenerate} className="card space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Disciplina *</label>
            <input
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="input"
              placeholder="Ex: Biologia"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Prompt *</label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              className="input resize-none"
              rows={4}
              placeholder="Ex: Crie uma aula sobre fotossintese para o 3o ano do ensino medio"
              required
              minLength={10}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Template</label>
              <select
                value={templateId}
                onChange={(e) => setTemplateId(e.target.value)}
                className="input"
              >
                <option value="">Padrao</option>
                {templates.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name} {t.is_default ? '(padrao)' : ''}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Num. Slides</label>
              <input
                type="number"
                value={numSlides}
                onChange={(e) => setNumSlides(e.target.value ? Number(e.target.value) : '')}
                className="input"
                min={3}
                max={30}
                placeholder="Auto"
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={generating || prompt.length < 10 || !subject}
            className="btn-primary flex items-center gap-2"
          >
            {generating ? (
              <Loader2 className="animate-spin" size={16} />
            ) : (
              <Presentation size={16} />
            )}
            {generating ? 'Gerando com IA...' : 'Gerar Apresentacao'}
          </button>
        </form>
      </div>
    )
  }

  // List view
  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Slides IA</h1>
          <p className="text-sm text-gray-500">Gere e gerencie apresentacoes via IA</p>
        </div>
        <button onClick={() => setShowGenerate(true)} className="btn-primary flex items-center gap-2">
          <Plus size={16} /> Nova Apresentacao
        </button>
      </div>

      {presentations.length === 0 ? (
        <div className="card text-center py-12">
          <FileText size={48} className="mx-auto text-gray-300 mb-3" />
          <p className="text-gray-500">Nenhuma apresentacao gerada ainda</p>
          <button
            onClick={() => setShowGenerate(true)}
            className="btn-primary mt-4 inline-flex items-center gap-2"
          >
            <Plus size={16} /> Criar Primeira Apresentacao
          </button>
        </div>
      ) : (
        <div className="grid gap-3">
          {presentations.map((p) => (
            <div key={p.id} className="card hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900">{p.title}</h3>
                  <p className="text-sm text-gray-500">
                    {p.subject} — {p.total_slides} slides — v{p.version}
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    {new Date(p.created_at).toLocaleDateString('pt-BR')}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setSelected(p)}
                    className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg"
                    title="Visualizar"
                  >
                    <Eye size={18} />
                  </button>
                  <button
                    onClick={() => handleDownload(p.id, p.title)}
                    className="p-2 text-green-600 hover:bg-green-50 rounded-lg"
                    title="Baixar PPTX"
                  >
                    <Download size={18} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
