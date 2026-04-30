import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  CheckCircle2,
  ExternalLink,
  Phone,
  KeyRound,
  Sparkles,
  Send,
  Loader2,
  AlertCircle,
} from 'lucide-react'
import toast from 'react-hot-toast'
import { api } from '../api/client'

interface SettingsResponse {
  bot_name?: string
  welcome_message?: string | null
  business_hours_start?: string | null
  business_hours_end?: string | null
  out_of_hours_message?: string | null
  has_whatsapp_config: boolean
  has_ai_key: boolean
}

interface SettingsForm {
  whatsapp_phone_number_id: string
  whatsapp_token: string
  claude_api_key: string
}

export default function WhatsAppSetup() {
  const qc = useQueryClient()
  const [form, setForm] = useState<SettingsForm>({
    whatsapp_phone_number_id: '',
    whatsapp_token: '',
    claude_api_key: '',
  })
  const [testPhone, setTestPhone] = useState('')

  const { data: settings, isLoading } = useQuery({
    queryKey: ['tenant-settings'],
    queryFn: () =>
      api
        .get('/api/v1/tenants/settings/current')
        .then((r) => r.data as SettingsResponse),
  })

  const saveMutation = useMutation({
    mutationFn: (payload: Partial<SettingsForm>) =>
      api.put('/api/v1/tenants/settings/current', payload).then((r) => r.data),
    onSuccess: () => {
      toast.success('Configuracoes salvas!')
      qc.invalidateQueries({ queryKey: ['tenant-settings'] })
      setForm({
        whatsapp_phone_number_id: '',
        whatsapp_token: '',
        claude_api_key: '',
      })
    },
    onError: () => toast.error('Erro ao salvar configuracoes'),
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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Configurar WhatsApp Business</h1>
        <p className="text-sm text-gray-500">
          Conecte sua conta do WhatsApp Business API para a Billie comecar a atender
        </p>
      </div>

      {/* Status atual */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <StatusCard
          label="WhatsApp Business API"
          isOk={settings?.has_whatsapp_config ?? false}
          loading={isLoading}
        />
        <StatusCard
          label="Chave da IA (Claude)"
          isOk={settings?.has_ai_key ?? false}
          loading={isLoading}
        />
      </div>

      {/* Tutorial passo a passo */}
      <div className="card">
        <h2 className="font-semibold text-lg mb-4 flex items-center gap-2">
          <Sparkles className="text-blue-600" size={20} />
          Tutorial: Como obter as credenciais
        </h2>
        <div className="space-y-4 text-sm">
          <Step number={1} title="Crie uma conta Meta for Developers">
            Acesse{' '}
            <a
              href="https://developers.facebook.com/"
              target="_blank"
              rel="noreferrer"
              className="text-blue-600 hover:underline inline-flex items-center gap-1"
            >
              developers.facebook.com <ExternalLink size={12} />
            </a>{' '}
            e crie uma conta usando seu Facebook pessoal. Eh gratuito.
          </Step>
          <Step number={2} title="Crie um App do tipo Business">
            No painel, clique em <b>"Meus Apps"</b> &rarr; <b>"Criar App"</b> &rarr;
            selecione <b>"Negocios"</b>. De um nome (ex: "IGS Anchieta") e use seu
            email comercial.
          </Step>
          <Step number={3} title="Adicione o produto WhatsApp Business Platform">
            Na pagina do app, role ate <b>"Adicionar produtos"</b> e clique em{' '}
            <b>"Configurar"</b> dentro do card <b>"WhatsApp"</b>.
          </Step>
          <Step number={4} title="Pegue o Phone Number ID e o Access Token">
            Em <b>"WhatsApp" &rarr; "Configuracao da API"</b>, voce vera:
            <ul className="list-disc list-inside ml-2 mt-1 space-y-1">
              <li>
                <span className="font-mono bg-gray-100 px-1 rounded">
                  phone_number_id
                </span>{' '}
                (numero longo) &rarr; cole no campo <b>Phone Number ID</b> abaixo
              </li>
              <li>
                <span className="font-mono bg-gray-100 px-1 rounded">
                  Temporary access token
                </span>{' '}
                &rarr; cole no campo <b>Access Token</b>
              </li>
            </ul>
            <p className="mt-2 text-yellow-700 bg-yellow-50 border border-yellow-200 p-2 rounded text-xs">
              <AlertCircle className="inline mr-1" size={12} />O token temporario
              expira em 24h. Para producao, gere um <b>System User token permanente</b>{' '}
              no Business Manager.
            </p>
          </Step>
          <Step number={5} title="Configure o Webhook (callback) na Meta">
            Em <b>"WhatsApp" &rarr; "Configuration"</b>, edite o <b>Callback URL</b> com:
            <div className="font-mono bg-gray-100 p-2 rounded mt-1 break-all">
              https://SEU-DOMINIO.com.br/api/v1/webhook/whatsapp
            </div>
            <p className="mt-1 text-xs">
              Verify Token: use o mesmo valor da variavel{' '}
              <span className="font-mono">WHATSAPP_VERIFY_TOKEN</span> do seu .env
            </p>
            <p className="mt-1 text-xs">
              Marque os campos: <b>messages</b>, <b>message_status</b>
            </p>
          </Step>
          <Step number={6} title="Adicione um numero de telefone">
            No mesmo painel, em <b>"Numeros de telefone"</b>, adicione um numero
            comercial. Voce pode usar um teste gratuito da Meta antes de migrar pro
            seu numero oficial.
          </Step>
          <Step number={7} title="Configure a chave da Claude (Anthropic)">
            Acesse{' '}
            <a
              href="https://console.anthropic.com/"
              target="_blank"
              rel="noreferrer"
              className="text-blue-600 hover:underline inline-flex items-center gap-1"
            >
              console.anthropic.com <ExternalLink size={12} />
            </a>
            , crie uma conta, adicione credito ($5 ja eh suficiente para comecar) e
            gere uma <b>API Key</b> em <b>"API Keys"</b>. Cole no campo abaixo.
          </Step>
        </div>
      </div>

      {/* Formulario de configuracao */}
      <div className="card">
        <h2 className="font-semibold text-lg mb-4 flex items-center gap-2">
          <KeyRound className="text-blue-600" size={20} />
          Salvar credenciais
        </h2>
        <p className="text-xs text-gray-500 mb-4">
          As credenciais sao criptografadas e armazenadas com seguranca. Deixe em
          branco para manter o valor atual.
        </p>
        <form
          onSubmit={(e) => {
            e.preventDefault()
            const payload: Partial<SettingsForm> = {}
            if (form.whatsapp_phone_number_id)
              payload.whatsapp_phone_number_id = form.whatsapp_phone_number_id
            if (form.whatsapp_token) payload.whatsapp_token = form.whatsapp_token
            if (form.claude_api_key) payload.claude_api_key = form.claude_api_key
            if (Object.keys(payload).length === 0) {
              toast.error('Preencha pelo menos um campo para salvar')
              return
            }
            saveMutation.mutate(payload)
          }}
          className="space-y-3"
        >
          <div>
            <label className="text-xs font-medium text-gray-600">
              Phone Number ID (WhatsApp)
            </label>
            <input
              type="text"
              value={form.whatsapp_phone_number_id}
              onChange={(e) =>
                setForm((f) => ({ ...f, whatsapp_phone_number_id: e.target.value }))
              }
              placeholder="1142668418921479"
              className="input w-full mt-1 font-mono"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-600">
              WhatsApp Access Token
            </label>
            <input
              type="password"
              value={form.whatsapp_token}
              onChange={(e) =>
                setForm((f) => ({ ...f, whatsapp_token: e.target.value }))
              }
              placeholder="EAAxxxxxx..."
              className="input w-full mt-1 font-mono"
              autoComplete="new-password"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-600">
              Claude API Key (Anthropic)
            </label>
            <input
              type="password"
              value={form.claude_api_key}
              onChange={(e) =>
                setForm((f) => ({ ...f, claude_api_key: e.target.value }))
              }
              placeholder="sk-ant-xxxxxx..."
              className="input w-full mt-1 font-mono"
              autoComplete="new-password"
            />
          </div>
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={saveMutation.isPending}
              className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              {saveMutation.isPending && <Loader2 className="animate-spin" size={16} />}
              Salvar credenciais
            </button>
          </div>
        </form>
      </div>

      {/* Teste de envio */}
      <div className="card">
        <h2 className="font-semibold text-lg mb-4 flex items-center gap-2">
          <Phone className="text-blue-600" size={20} />
          Testar envio
        </h2>
        <p className="text-xs text-gray-500 mb-3">
          Envie uma mensagem de teste para validar a integracao. O numero deve estar
          adicionado como destinatario de teste no painel da Meta.
        </p>
        <div className="flex gap-2">
          <input
            type="tel"
            value={testPhone}
            onChange={(e) => setTestPhone(e.target.value)}
            placeholder="11999999999"
            className="input flex-1 font-mono"
          />
          <button
            onClick={() =>
              testPhone.length >= 10
                ? testMutation.mutate(testPhone)
                : toast.error('Digite um telefone valido')
            }
            disabled={testMutation.isPending}
            className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-50"
          >
            {testMutation.isPending ? (
              <Loader2 className="animate-spin" size={16} />
            ) : (
              <Send size={16} />
            )}
            Enviar teste
          </button>
        </div>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────

function StatusCard({
  label,
  isOk,
  loading,
}: {
  label: string
  isOk: boolean
  loading: boolean
}) {
  return (
    <div className="card flex items-center justify-between">
      <span className="text-sm font-medium">{label}</span>
      {loading ? (
        <Loader2 className="animate-spin text-gray-400" size={18} />
      ) : isOk ? (
        <span className="flex items-center gap-1 text-green-700 text-sm font-medium">
          <CheckCircle2 size={16} /> Configurado
        </span>
      ) : (
        <span className="flex items-center gap-1 text-orange-600 text-sm font-medium">
          <AlertCircle size={16} /> Pendente
        </span>
      )}
    </div>
  )
}

function Step({
  number,
  title,
  children,
}: {
  number: number
  title: string
  children: React.ReactNode
}) {
  return (
    <div className="flex gap-3">
      <div className="flex-shrink-0 w-7 h-7 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center text-sm font-bold">
        {number}
      </div>
      <div className="flex-1">
        <p className="font-medium mb-1">{title}</p>
        <div className="text-gray-600">{children}</div>
      </div>
    </div>
  )
}
