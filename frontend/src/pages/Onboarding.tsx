import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Bot,
  CheckCircle2,
  ChevronRight,
  Phone,
  KeyRound,
  GraduationCap,
  Sparkles,
  ArrowRight,
  Upload,
} from 'lucide-react'
import toast from 'react-hot-toast'
import clsx from 'clsx'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

type Step = 'welcome' | 'whatsapp' | 'bot' | 'import' | 'done'

const STEPS: { id: Step; label: string }[] = [
  { id: 'welcome', label: 'Boas-vindas' },
  { id: 'whatsapp', label: 'WhatsApp' },
  { id: 'bot', label: 'Personalizar bot' },
  { id: 'import', label: 'Importar dados' },
  { id: 'done', label: 'Pronto!' },
]

export default function Onboarding() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const { user } = useAuth()
  const [step, setStep] = useState<Step>('welcome')
  const [waForm, setWaForm] = useState({ phone_number_id: '', token: '' })
  const [botForm, setBotForm] = useState({
    bot_name: 'IGS Assistant',
    welcome_message: 'Olá! Sou o assistente virtual da sua instituição. Como posso ajudar?',
  })
  const [importFile, setImportFile] = useState<File | null>(null)
  const [importResult, setImportResult] = useState<{
    created: number; skipped: number; errors: string[]
  } | null>(null)

  const tenantId = user?.tenant_id

  const saveMutation = useMutation({
    mutationFn: (payload: Record<string, string>) =>
      api.put('/api/v1/tenants/settings/current', payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['tenant-settings'] }),
  })

  const importMutation = useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData()
      form.append('file', file)
      const res = await api.post(
        `/api/v1/onboarding/tenants/${tenantId}/import-students`,
        form,
        { headers: { 'Content-Type': 'multipart/form-data' } },
      )
      return res.data
    },
    onSuccess: (data) => {
      setImportResult(data)
      toast.success(`${data.created} alunos importados!`)
    },
    onError: () => toast.error('Erro ao importar arquivo'),
  })

  const currentIdx = STEPS.findIndex((s) => s.id === step)

  const next = () => {
    const nextStep = STEPS[currentIdx + 1]
    if (nextStep) setStep(nextStep.id)
  }

  const handleSaveWhatsApp = async () => {
    if (!waForm.phone_number_id || !waForm.token) {
      toast.error('Preencha o Phone Number ID e o token de acesso')
      return
    }
    try {
      await saveMutation.mutateAsync({
        whatsapp_phone_number_id: waForm.phone_number_id,
        whatsapp_token: waForm.token,
      })
      toast.success('WhatsApp configurado!')
      next()
    } catch {
      toast.error('Erro ao salvar configurações do WhatsApp')
    }
  }

  const handleSaveBot = async () => {
    try {
      await saveMutation.mutateAsync({
        bot_name: botForm.bot_name,
        welcome_message: botForm.welcome_message,
      })
      toast.success('Bot personalizado!')
      next()
    } catch {
      toast.error('Erro ao salvar configurações do bot')
    }
  }

  const handleImport = async () => {
    if (!importFile) return
    await importMutation.mutateAsync(importFile)
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        {/* Header */}
        <div className="flex items-center gap-3 mb-8">
          <div className="bg-blue-600 p-2 rounded-xl">
            <Bot size={24} className="text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">Configuração inicial — IGS</h1>
            <p className="text-sm text-gray-500">Siga os passos abaixo para começar a atender</p>
          </div>
        </div>

        {/* Steps progress */}
        <div className="flex items-center gap-2 mb-8 overflow-x-auto pb-2">
          {STEPS.map((s, i) => (
            <div key={s.id} className="flex items-center gap-2 shrink-0">
              <div
                className={clsx(
                  'flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold',
                  i < currentIdx
                    ? 'bg-green-500 text-white'
                    : i === currentIdx
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-500',
                )}
              >
                {i < currentIdx ? <CheckCircle2 size={14} /> : i + 1}
              </div>
              <span
                className={clsx(
                  'text-xs font-medium',
                  i === currentIdx ? 'text-blue-700' : 'text-gray-400',
                )}
              >
                {s.label}
              </span>
              {i < STEPS.length - 1 && (
                <ChevronRight size={14} className="text-gray-300" />
              )}
            </div>
          ))}
        </div>

        {/* Step content */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          {/* WELCOME */}
          {step === 'welcome' && (
            <div className="text-center">
              <div className="bg-blue-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <Sparkles size={32} className="text-blue-600" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Bem-vindo ao IGS!</h2>
              <p className="text-gray-500 mb-6 max-w-md mx-auto">
                Vamos configurar seu atendimento inteligente via WhatsApp em menos de 5 minutos.
              </p>
              <div className="grid grid-cols-3 gap-4 mb-8 text-left">
                {[
                  { icon: Phone, label: 'WhatsApp', desc: 'Conecte seu número verificado' },
                  { icon: Bot, label: 'Bot IA', desc: 'Personalize o assistente' },
                  { icon: GraduationCap, label: 'Alunos', desc: 'Importe sua base de dados' },
                ].map(({ icon: Icon, label, desc }) => (
                  <div key={label} className="bg-gray-50 rounded-xl p-4">
                    <Icon size={20} className="text-blue-600 mb-2" />
                    <p className="text-sm font-semibold text-gray-800">{label}</p>
                    <p className="text-xs text-gray-500">{desc}</p>
                  </div>
                ))}
              </div>
              <button onClick={next} className="btn-primary px-8 py-3 inline-flex items-center gap-2">
                Começar <ArrowRight size={16} />
              </button>
            </div>
          )}

          {/* WHATSAPP */}
          {step === 'whatsapp' && (
            <div>
              <div className="flex items-center gap-3 mb-6">
                <Phone size={24} className="text-green-600" />
                <div>
                  <h2 className="text-lg font-bold text-gray-900">Conectar WhatsApp</h2>
                  <p className="text-sm text-gray-500">
                    Você precisará de uma conta no Meta Business Suite com WhatsApp Business API
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Phone Number ID
                  </label>
                  <input
                    className="input"
                    placeholder="Ex: 1142668418921479"
                    value={waForm.phone_number_id}
                    onChange={(e) => setWaForm((f) => ({ ...f, phone_number_id: e.target.value }))}
                  />
                  <p className="text-xs text-gray-400 mt-1">
                    Encontrado em: Meta Business → WhatsApp → API Setup → Phone Number ID
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Token de Acesso Permanente
                  </label>
                  <input
                    className="input"
                    type="password"
                    placeholder="EAAxxxxxxxxxxxxxx..."
                    value={waForm.token}
                    onChange={(e) => setWaForm((f) => ({ ...f, token: e.target.value }))}
                  />
                  <p className="text-xs text-gray-400 mt-1">
                    Gere um token permanente em: Meta Business → System Users → Generate Token
                  </p>
                </div>

                <div className="bg-blue-50 rounded-xl p-4 text-sm text-blue-800">
                  <p className="font-semibold mb-1">URL do Webhook para o Meta:</p>
                  <code className="text-xs bg-blue-100 px-2 py-1 rounded break-all">
                    {window.location.origin}/api/v1/webhook/whatsapp
                  </code>
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => next()}
                  className="text-sm text-gray-500 hover:text-gray-700 px-4 py-2"
                >
                  Pular por agora
                </button>
                <button
                  onClick={handleSaveWhatsApp}
                  disabled={saveMutation.isPending}
                  className="btn-primary flex items-center gap-2"
                >
                  {saveMutation.isPending ? 'Salvando...' : 'Salvar e continuar'}
                  <ArrowRight size={16} />
                </button>
              </div>
            </div>
          )}

          {/* BOT */}
          {step === 'bot' && (
            <div>
              <div className="flex items-center gap-3 mb-6">
                <Bot size={24} className="text-blue-600" />
                <div>
                  <h2 className="text-lg font-bold text-gray-900">Personalizar o bot</h2>
                  <p className="text-sm text-gray-500">
                    Configure o nome e a mensagem de boas-vindas
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nome do assistente
                  </label>
                  <input
                    className="input"
                    value={botForm.bot_name}
                    onChange={(e) => setBotForm((f) => ({ ...f, bot_name: e.target.value }))}
                    placeholder="Ex: Assistente Anchieta"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Mensagem de boas-vindas
                  </label>
                  <textarea
                    className="input h-24 resize-none"
                    value={botForm.welcome_message}
                    onChange={(e) => setBotForm((f) => ({ ...f, welcome_message: e.target.value }))}
                    placeholder="Olá! Sou o assistente virtual da sua instituição..."
                  />
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button onClick={() => next()} className="text-sm text-gray-500 px-4 py-2">
                  Pular
                </button>
                <button
                  onClick={handleSaveBot}
                  disabled={saveMutation.isPending}
                  className="btn-primary flex items-center gap-2"
                >
                  {saveMutation.isPending ? 'Salvando...' : 'Salvar e continuar'}
                  <ArrowRight size={16} />
                </button>
              </div>
            </div>
          )}

          {/* IMPORT */}
          {step === 'import' && (
            <div>
              <div className="flex items-center gap-3 mb-6">
                <GraduationCap size={24} className="text-purple-600" />
                <div>
                  <h2 className="text-lg font-bold text-gray-900">Importar alunos</h2>
                  <p className="text-sm text-gray-500">
                    Faça upload de um arquivo CSV com sua base de alunos
                  </p>
                </div>
              </div>

              {!importResult ? (
                <div className="space-y-4">
                  <div
                    onClick={() => document.getElementById('onboarding-file-input')?.click()}
                    className={clsx(
                      'border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors',
                      importFile
                        ? 'border-green-400 bg-green-50'
                        : 'border-gray-300 hover:border-blue-400',
                    )}
                  >
                    <input
                      id="onboarding-file-input"
                      type="file"
                      accept=".csv"
                      className="hidden"
                      onChange={(e) => {
                        const f = e.target.files?.[0]
                        if (f) setImportFile(f)
                      }}
                    />
                    <Upload
                      size={32}
                      className={clsx('mx-auto mb-2', importFile ? 'text-green-500' : 'text-gray-400')}
                    />
                    {importFile ? (
                      <p className="text-sm font-medium text-green-700">{importFile.name}</p>
                    ) : (
                      <>
                        <p className="text-sm font-medium">Clique para selecionar o arquivo CSV</p>
                        <p className="text-xs text-gray-400 mt-1">
                          Colunas: registration_number, full_name, course, semester...
                        </p>
                      </>
                    )}
                  </div>

                  <div className="flex gap-3">
                    <button onClick={() => next()} className="text-sm text-gray-500 px-4 py-2">
                      Pular por agora
                    </button>
                    <button
                      onClick={handleImport}
                      disabled={!importFile || importMutation.isPending}
                      className="btn-primary flex items-center gap-2 disabled:opacity-50"
                    >
                      {importMutation.isPending ? 'Importando...' : 'Importar e continuar'}
                      <ArrowRight size={16} />
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-3">
                    <div className="bg-green-50 rounded-xl p-4 text-center">
                      <p className="text-2xl font-bold text-green-700">{importResult.created}</p>
                      <p className="text-xs text-green-600">Criados</p>
                    </div>
                    <div className="bg-yellow-50 rounded-xl p-4 text-center">
                      <p className="text-2xl font-bold text-yellow-700">{importResult.skipped}</p>
                      <p className="text-xs text-yellow-600">Ignorados</p>
                    </div>
                    <div className="bg-red-50 rounded-xl p-4 text-center">
                      <p className="text-2xl font-bold text-red-700">{importResult.errors.length}</p>
                      <p className="text-xs text-red-600">Erros</p>
                    </div>
                  </div>
                  <button onClick={next} className="btn-primary w-full flex items-center justify-center gap-2">
                    Continuar <ArrowRight size={16} />
                  </button>
                </div>
              )}
            </div>
          )}

          {/* DONE */}
          {step === 'done' && (
            <div className="text-center">
              <div className="bg-green-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle2 size={32} className="text-green-600" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Tudo pronto!</h2>
              <p className="text-gray-500 mb-8 max-w-md mx-auto">
                Seu IGS está configurado. Acesse o painel para acompanhar as conversas e métricas.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <button
                  onClick={() => navigate('/app/dashboard')}
                  className="btn-primary px-8 py-3"
                >
                  Ir para o Dashboard
                </button>
                <button
                  onClick={() => navigate('/app/whatsapp-setup')}
                  className="px-8 py-3 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 text-sm font-medium"
                >
                  Configurar mais detalhes
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Skip all */}
        {step !== 'done' && (
          <div className="text-center mt-4">
            <button
              onClick={() => navigate('/app/dashboard')}
              className="text-xs text-gray-400 hover:text-gray-600"
            >
              Pular configuração e ir para o painel →
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
