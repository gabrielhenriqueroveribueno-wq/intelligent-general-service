import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  CheckCircle2,
  Circle,
  ExternalLink,
  Phone,
  KeyRound,
  Send,
  Loader2,
  AlertCircle,
  Rocket,
  Copy,
  ChevronDown,
  ChevronUp,
  Wifi,
} from 'lucide-react'
import toast from 'react-hot-toast'
import clsx from 'clsx'
import { api } from '../api/client'

interface SettingsResponse {
  has_whatsapp_config: boolean
  has_ai_key: boolean
}

interface SettingsForm {
  whatsapp_phone_number_id: string
  whatsapp_token: string
  claude_api_key: string
}

const WEBHOOK_URL = `${window.location.origin}/api/v1/webhook/whatsapp`
const VERIFY_TOKEN_PLACEHOLDER = 'igs-verify-token'

const STEPS = [
  {
    id: 'meta-account',
    title: 'Criar conta Meta for Developers',
    description: 'Acesse developers.facebook.com e crie um app do tipo "Negócios".',
    link: { href: 'https://developers.facebook.com/', label: 'Abrir Meta for Developers' },
    detail: (
      <ol className="list-decimal list-inside space-y-1.5 text-gray-600">
        <li>Acesse <a href="https://developers.facebook.com/" target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">developers.facebook.com</a></li>
        <li>Clique em <b>Meus Apps</b> → <b>Criar App</b></li>
        <li>Selecione o tipo <b>Negócios</b></li>
        <li>Dê um nome (ex: "IGS Anchieta") e use o email institucional</li>
      </ol>
    ),
  },
  {
    id: 'whatsapp-product',
    title: 'Adicionar produto WhatsApp ao app',
    description: 'Na página do app, role até "Adicionar produtos" e configure o WhatsApp.',
    detail: (
      <ol className="list-decimal list-inside space-y-1.5 text-gray-600">
        <li>Na página do app recém-criado, role até <b>Adicionar produtos</b></li>
        <li>Clique em <b>Configurar</b> dentro do card <b>WhatsApp</b></li>
        <li>Em <b>WhatsApp → Configuração da API</b>, você verá o <code className="bg-gray-100 px-1 rounded text-xs">phone_number_id</code> e o <code className="bg-gray-100 px-1 rounded text-xs">Temporary access token</code></li>
        <li className="text-yellow-700">⚠️ O token temporário expira em 24h. Para produção, gere um <b>System User token permanente</b> no Meta Business Manager.</li>
      </ol>
    ),
  },
  {
    id: 'credentials',
    title: 'Salvar Phone Number ID e Access Token',
    description: 'Cole as credenciais do WhatsApp no formulário abaixo.',
    isForm: true,
  },
  {
    id: 'webhook',
    title: 'Configurar Webhook no Meta',
    description: 'Registre a URL de callback para o IGS receber as mensagens.',
    detail: (
      <div className="space-y-3 text-gray-600">
        <p>Em <b>WhatsApp → Configuration</b>, clique em <b>Edit</b> no campo Webhook:</p>
        <div>
          <p className="text-xs font-medium text-gray-500 mb-1">Callback URL</p>
          <CopyBox value={WEBHOOK_URL} />
        </div>
        <div>
          <p className="text-xs font-medium text-gray-500 mb-1">Verify Token</p>
          <CopyBox value={VERIFY_TOKEN_PLACEHOLDER} />
        </div>
        <p>Marque os campos de assinatura: <b>messages</b> e <b>message_status</b></p>
      </div>
    ),
  },
  {
    id: 'ai-key',
    title: 'Configurar chave de IA (Groq)',
    description: 'O IGS usa Groq (llama-3.3-70b) como IA padrão — gratuito para começar.',
    link: { href: 'https://console.groq.com/', label: 'Abrir Groq Console' },
    detail: (
      <ol className="list-decimal list-inside space-y-1.5 text-gray-600">
        <li>Acesse <a href="https://console.groq.com/" target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">console.groq.com</a> e crie uma conta gratuita</li>
        <li>Vá em <b>API Keys</b> → <b>Create API Key</b></li>
        <li>Copie a chave e cole no formulário acima (campo "Chave de IA")</li>
        <li>Plano gratuito: 14.400 req/dia — suficiente para começar</li>
      </ol>
    ),
    isAiForm: true,
  },
  {
    id: 'test',
    title: 'Testar conexão',
    description: 'Envie uma mensagem de teste para validar a integração.',
    isTest: true,
  },
]

export default function WhatsAppSetup() {
  const qc = useQueryClient()
  const [activeStep, setActiveStep] = useState(0)
  const [form, setForm] = useState<SettingsForm>({
    whatsapp_phone_number_id: '',
    whatsapp_token: '',
    claude_api_key: '',
  })
  const [testPhone, setTestPhone] = useState('')

  const { data: settings, isLoading } = useQuery({
    queryKey: ['tenant-settings'],
    queryFn: () =>
      api.get('/api/v1/tenants/settings/current').then((r) => r.data as SettingsResponse),
  })

  const saveMutation = useMutation({
    mutationFn: (payload: Partial<SettingsForm>) =>
      api.put('/api/v1/tenants/settings/current', payload).then((r) => r.data),
    onSuccess: () => {
      toast.success('Credenciais salvas!')
      qc.invalidateQueries({ queryKey: ['tenant-settings'] })
      setForm({ whatsapp_phone_number_id: '', whatsapp_token: '', claude_api_key: '' })
      setActiveStep((s) => Math.min(s + 1, STEPS.length - 1))
    },
    onError: () => toast.error('Erro ao salvar credenciais'),
  })

  const testMutation = useMutation({
    mutationFn: (phone: string) =>
      api.post('/api/v1/tenants/whatsapp/test', { phone_number: phone }),
    onSuccess: () => toast.success('Mensagem de teste enviada! Verifique seu WhatsApp.'),
    onError: (err: any) => {
      const detail = err?.response?.data?.detail || 'Erro ao enviar teste'
      toast.error(typeof detail === 'string' ? detail : 'Falha no teste')
    },
  })

  const stepDone = (stepId: string) => {
    if (stepId === 'credentials') return settings?.has_whatsapp_config ?? false
    if (stepId === 'ai-key') return settings?.has_ai_key ?? false
    if (stepId === 'test') return false
    return false
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Configurar WhatsApp Business</h1>
        <p className="text-sm text-gray-500 mt-1">
          Siga os passos abaixo para conectar o WhatsApp. Leva cerca de 30 minutos na primeira vez.
        </p>
      </div>

      {/* Status badges */}
      <div className="flex gap-3 flex-wrap">
        <StatusBadge
          label="WhatsApp API"
          ok={settings?.has_whatsapp_config ?? false}
          loading={isLoading}
        />
        <StatusBadge
          label="IA (Groq)"
          ok={settings?.has_ai_key ?? false}
          loading={isLoading}
        />
      </div>

      {/* Steps */}
      <div className="space-y-3">
        {STEPS.map((step, i) => {
          const done = stepDone(step.id)
          const isOpen = activeStep === i

          return (
            <div
              key={step.id}
              className={clsx(
                'rounded-xl border transition-all',
                done ? 'border-green-200 bg-green-50/30' :
                isOpen ? 'border-blue-300 bg-blue-50/20 shadow-sm' :
                'border-gray-200 bg-white',
              )}
            >
              <button
                className="w-full flex items-center gap-4 px-5 py-4 text-left"
                onClick={() => setActiveStep(isOpen ? -1 : i)}
              >
                <div className={clsx(
                  'w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-sm font-bold',
                  done ? 'bg-green-500 text-white' :
                  isOpen ? 'bg-blue-600 text-white' :
                  'bg-gray-100 text-gray-500',
                )}>
                  {done ? <CheckCircle2 size={16} /> : i + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <p className={clsx('font-medium text-sm', done ? 'text-green-800' : 'text-gray-900')}>
                    {step.title}
                  </p>
                  <p className="text-xs text-gray-500 truncate">{step.description}</p>
                </div>
                {isOpen ? <ChevronUp size={16} className="text-gray-400 shrink-0" /> : <ChevronDown size={16} className="text-gray-400 shrink-0" />}
              </button>

              {isOpen && (
                <div className="px-5 pb-5 border-t border-gray-100 pt-4 space-y-4">
                  {step.detail && <div className="text-sm">{step.detail}</div>}

                  {step.link && (
                    <a
                      href={step.link.href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 text-sm text-blue-600 font-medium hover:underline"
                    >
                      <ExternalLink size={14} />
                      {step.link.label}
                    </a>
                  )}

                  {step.isForm && (
                    <form
                      onSubmit={(e) => {
                        e.preventDefault()
                        const payload: Partial<SettingsForm> = {}
                        if (form.whatsapp_phone_number_id)
                          payload.whatsapp_phone_number_id = form.whatsapp_phone_number_id
                        if (form.whatsapp_token) payload.whatsapp_token = form.whatsapp_token
                        if (Object.keys(payload).length === 0) {
                          toast.error('Preencha pelo menos um campo')
                          return
                        }
                        saveMutation.mutate(payload)
                      }}
                      className="space-y-3"
                    >
                      <div>
                        <label className="text-xs font-medium text-gray-600">Phone Number ID</label>
                        <input
                          type="text"
                          value={form.whatsapp_phone_number_id}
                          onChange={(e) => setForm((f) => ({ ...f, whatsapp_phone_number_id: e.target.value }))}
                          placeholder="1142668418921479"
                          className="input w-full mt-1 font-mono text-sm"
                        />
                      </div>
                      <div>
                        <label className="text-xs font-medium text-gray-600">Access Token</label>
                        <input
                          type="password"
                          value={form.whatsapp_token}
                          onChange={(e) => setForm((f) => ({ ...f, whatsapp_token: e.target.value }))}
                          placeholder="EAAxxxxxx..."
                          className="input w-full mt-1 font-mono text-sm"
                          autoComplete="new-password"
                        />
                      </div>
                      <button
                        type="submit"
                        disabled={saveMutation.isPending}
                        className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
                      >
                        {saveMutation.isPending && <Loader2 className="animate-spin" size={14} />}
                        <KeyRound size={14} />
                        Salvar credenciais WhatsApp
                      </button>
                    </form>
                  )}

                  {step.isAiForm && (
                    <form
                      onSubmit={(e) => {
                        e.preventDefault()
                        if (!form.claude_api_key) {
                          toast.error('Cole a chave da IA')
                          return
                        }
                        saveMutation.mutate({ claude_api_key: form.claude_api_key })
                      }}
                      className="space-y-3"
                    >
                      <div>
                        <label className="text-xs font-medium text-gray-600">
                          Groq API Key <span className="text-gray-400">(ou Anthropic/Gemini)</span>
                        </label>
                        <input
                          type="password"
                          value={form.claude_api_key}
                          onChange={(e) => setForm((f) => ({ ...f, claude_api_key: e.target.value }))}
                          placeholder="gsk_xxxxxx... ou sk-ant-xxxxxx..."
                          className="input w-full mt-1 font-mono text-sm"
                          autoComplete="new-password"
                        />
                      </div>
                      <button
                        type="submit"
                        disabled={saveMutation.isPending}
                        className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
                      >
                        {saveMutation.isPending && <Loader2 className="animate-spin" size={14} />}
                        <KeyRound size={14} />
                        Salvar chave de IA
                      </button>
                    </form>
                  )}

                  {step.isTest && (
                    <div className="space-y-3">
                      <p className="text-sm text-gray-600">
                        Digite um número WhatsApp que esteja na lista de destinatários de teste do seu app Meta.
                      </p>
                      <div className="flex gap-2">
                        <input
                          type="tel"
                          value={testPhone}
                          onChange={(e) => setTestPhone(e.target.value)}
                          placeholder="11999999999"
                          className="input flex-1 font-mono text-sm"
                        />
                        <button
                          onClick={() =>
                            testPhone.length >= 10
                              ? testMutation.mutate(testPhone)
                              : toast.error('Digite um número válido')
                          }
                          disabled={testMutation.isPending || !settings?.has_whatsapp_config}
                          className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50"
                        >
                          {testMutation.isPending ? (
                            <Loader2 className="animate-spin" size={14} />
                          ) : (
                            <Send size={14} />
                          )}
                          Enviar teste
                        </button>
                      </div>
                      {!settings?.has_whatsapp_config && (
                        <p className="text-xs text-orange-600 flex items-center gap-1">
                          <AlertCircle size={12} />
                          Configure o WhatsApp no passo 3 antes de testar.
                        </p>
                      )}
                    </div>
                  )}

                  {/* Next step button */}
                  {!step.isForm && !step.isAiForm && !step.isTest && (
                    <button
                      onClick={() => setActiveStep((s) => Math.min(s + 1, STEPS.length - 1))}
                      className="text-sm text-blue-600 font-medium hover:underline"
                    >
                      Próximo passo →
                    </button>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Meta checklist */}
      <div className="rounded-xl border border-orange-200 bg-orange-50/30 p-5">
        <div className="flex items-center gap-3 mb-4">
          <Rocket size={18} className="text-orange-600" />
          <div>
            <h3 className="font-semibold text-sm text-gray-900">Publicar App no Meta (produção)</h3>
            <p className="text-xs text-gray-500">Necessário para atender além dos números de teste</p>
          </div>
        </div>
        <div className="space-y-2">
          {[
            { done: settings?.has_whatsapp_config, label: 'Número WhatsApp verificado e token configurado' },
            { done: false, label: 'Política de Privacidade publicada e linkada no app Meta' },
            { done: false, label: 'App revisado e aprovado pela Meta (Live Mode)' },
            { done: false, label: 'Número de telefone real adicionado ao sistema' },
          ].map((item, i) => (
            <div key={i} className="flex items-center gap-2.5">
              {item.done ? (
                <CheckCircle2 size={14} className="text-green-600 shrink-0" />
              ) : (
                <Circle size={14} className="text-gray-300 shrink-0" />
              )}
              <span className={clsx('text-xs', item.done ? 'line-through text-gray-400' : 'text-gray-700')}>
                {item.label}
              </span>
            </div>
          ))}
        </div>
        <div className="mt-4 bg-white border border-orange-100 rounded-lg p-3">
          <p className="text-xs font-medium text-gray-700 mb-1 flex items-center gap-1">
            <Wifi size={12} /> URL do Webhook
          </p>
          <CopyBox value={WEBHOOK_URL} />
        </div>
      </div>
    </div>
  )
}

function CopyBox({ value }: { value: string }) {
  const copy = () => {
    navigator.clipboard.writeText(value)
    toast.success('Copiado!')
  }
  return (
    <div className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2">
      <code className="text-xs flex-1 break-all font-mono text-gray-700">{value}</code>
      <button onClick={copy} className="text-gray-400 hover:text-gray-700 shrink-0">
        <Copy size={14} />
      </button>
    </div>
  )
}

function StatusBadge({ label, ok, loading }: { label: string; ok: boolean; loading: boolean }) {
  return (
    <div className={clsx(
      'inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium',
      loading ? 'bg-gray-100 text-gray-500' :
      ok ? 'bg-green-100 text-green-700' : 'bg-orange-100 text-orange-700',
    )}>
      {loading ? (
        <Loader2 size={12} className="animate-spin" />
      ) : ok ? (
        <CheckCircle2 size={12} />
      ) : (
        <AlertCircle size={12} />
      )}
      {label}: {loading ? '...' : ok ? 'Configurado' : 'Pendente'}
    </div>
  )
}
