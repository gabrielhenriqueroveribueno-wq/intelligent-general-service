import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { Bell, Bot, Clock, Copy, ExternalLink, Key, MessageSquare, Loader2, Check, Send, Webhook, Shield, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { usePushNotifications } from '../hooks/usePushNotifications'

interface SettingsData {
  bot_name: string
  welcome_message: string | null
  business_hours_start: string | null
  business_hours_end: string | null
  out_of_hours_message: string | null
  has_whatsapp_config: boolean
  has_ai_key: boolean
}

function CopyField({ label, value }: { label: string; value: string }) {
  const [copied, setCopied] = useState(false)
  function copy() {
    navigator.clipboard.writeText(value)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  return (
    <div>
      <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
      <div className="flex items-center gap-2">
        <input
          readOnly
          className="input flex-1 font-mono text-xs bg-gray-50"
          value={value}
        />
        <button
          onClick={copy}
          className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors"
          title="Copiar"
        >
          {copied ? <Check size={14} className="text-green-600" /> : <Copy size={14} className="text-gray-500" />}
        </button>
      </div>
    </div>
  )
}

export default function Settings() {
  const push = usePushNotifications()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [data, setData] = useState<SettingsData>({
    bot_name: 'Assistente IGS',
    welcome_message: '',
    business_hours_start: '08:00',
    business_hours_end: '22:00',
    out_of_hours_message: '',
    has_whatsapp_config: false,
    has_ai_key: false,
  })

  const [waPhoneId, setWaPhoneId] = useState('')
  const [waToken, setWaToken] = useState('')
  const [aiKey, setAiKey] = useState('')
  const [testPhone, setTestPhone] = useState('')
  const [testing, setTesting] = useState(false)

  const apiBase = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : `https://${window.location.hostname}`
  const webhookUrl = `${apiBase}/api/v1/webhook/whatsapp`

  useEffect(() => {
    loadSettings()
  }, [])

  async function loadSettings() {
    try {
      const res = await api.get('/api/v1/tenants/settings/current')
      setData(res.data)
    } catch {
      /* interceptor handles */
    }
    setLoading(false)
  }

  async function handleSave() {
    setSaving(true)
    try {
      const body: Record<string, unknown> = {
        bot_name: data.bot_name,
        welcome_message: data.welcome_message,
        business_hours_start: data.business_hours_start,
        business_hours_end: data.business_hours_end,
        out_of_hours_message: data.out_of_hours_message,
      }
      if (waPhoneId) body.whatsapp_phone_number_id = waPhoneId
      if (waToken) body.whatsapp_token = waToken
      if (aiKey) body.claude_api_key = aiKey

      const res = await api.put('/api/v1/tenants/settings/current', body)
      setData(res.data)
      setWaPhoneId('')
      setWaToken('')
      setAiKey('')
      toast.success('Configurações salvas com sucesso!')
    } catch {
      /* interceptor handles */
    }
    setSaving(false)
  }

  async function handleTestWhatsApp() {
    if (!testPhone.trim()) {
      toast.error('Digite um número de telefone para teste')
      return
    }
    setTesting(true)
    try {
      const res = await api.post('/api/v1/tenants/whatsapp/test', {
        phone_number: testPhone.trim(),
      })
      toast.success(res.data.message || 'Mensagem de teste enviada!')
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } }
      toast.error(error?.response?.data?.detail || 'Erro ao enviar teste')
    }
    setTesting(false)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-blue-600" size={32} />
      </div>
    )
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Configurações</h1>
        <p className="text-sm text-gray-500">Configure o sistema e integrações</p>
      </div>

      {/* Webhook URL — seção destacada para facilitar setup do WhatsApp */}
      <div className="card border-blue-100 bg-blue-50">
        <div className="flex items-center gap-3 mb-4">
          <div className="bg-blue-600 p-2 rounded-lg">
            <Webhook size={18} className="text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-blue-900">URL do Webhook WhatsApp</h3>
            <p className="text-xs text-blue-600">Cole esta URL no painel Meta Developer para receber mensagens</p>
          </div>
        </div>
        <div className="space-y-3">
          <CopyField label="URL do Callback" value={webhookUrl} />
          <CopyField label="Token de Verificação" value={import.meta.env.VITE_WHATSAPP_VERIFY_TOKEN || 'igs-verify-token'} />
          <div className="flex items-center gap-2 pt-1">
            <a
              href="https://developers.facebook.com/apps"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-blue-600 hover:underline flex items-center gap-1"
            >
              <ExternalLink size={12} />
              Abrir Meta Developer Console
            </a>
            <span className="text-gray-300">·</span>
            <span className="text-xs text-gray-500">
              Configure em: WhatsApp → Configuração → Webhook
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-blue-100 p-2 rounded-lg">
              <Bot size={18} className="text-blue-600" />
            </div>
            <h3 className="font-semibold">Bot WhatsApp</h3>
          </div>
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Nome do bot</label>
              <input
                className="input"
                value={data.bot_name}
                onChange={(e) => setData({ ...data, bot_name: e.target.value })}
                placeholder="Ex: Assistente Anchieta"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Mensagem de boas-vindas
              </label>
              <textarea
                className="input resize-none"
                rows={3}
                value={data.welcome_message || ''}
                onChange={(e) => setData({ ...data, welcome_message: e.target.value })}
                placeholder="Olá! Sou o assistente virtual. Como posso ajudar?"
              />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-green-100 p-2 rounded-lg">
              <Clock size={18} className="text-green-600" />
            </div>
            <h3 className="font-semibold">Horário de Funcionamento</h3>
          </div>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Abertura</label>
                <input
                  className="input"
                  type="time"
                  value={data.business_hours_start || '08:00'}
                  onChange={(e) => setData({ ...data, business_hours_start: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Fechamento</label>
                <input
                  className="input"
                  type="time"
                  value={data.business_hours_end || '22:00'}
                  onChange={(e) => setData({ ...data, business_hours_end: e.target.value })}
                />
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Mensagem fora do horário
              </label>
              <textarea
                className="input resize-none"
                rows={2}
                value={data.out_of_hours_message || ''}
                onChange={(e) => setData({ ...data, out_of_hours_message: e.target.value })}
                placeholder="Estamos fora do horário de atendimento. Retornaremos em breve!"
              />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-purple-100 p-2 rounded-lg">
              <Key size={18} className="text-purple-600" />
            </div>
            <h3 className="font-semibold">Integrações</h3>
          </div>
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                WhatsApp Phone Number ID
                {data.has_whatsapp_config && (
                  <span className="ml-2 text-green-600 inline-flex items-center gap-1">
                    <Check size={12} /> Configurado
                  </span>
                )}
              </label>
              <input
                className="input"
                placeholder="Ex: 123456789012345"
                type="password"
                value={waPhoneId}
                onChange={(e) => setWaPhoneId(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                WhatsApp Access Token
              </label>
              <input
                className="input"
                placeholder="EAAxxxxxxxxxx..."
                type="password"
                value={waToken}
                onChange={(e) => setWaToken(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Claude API Key
                {data.has_ai_key && (
                  <span className="ml-2 text-green-600 inline-flex items-center gap-1">
                    <Check size={12} /> Configurado
                  </span>
                )}
              </label>
              <input
                className="input"
                placeholder="sk-ant-..."
                type="password"
                value={aiKey}
                onChange={(e) => setAiKey(e.target.value)}
              />
            </div>
            <p className="text-xs text-gray-400">
              Deixe em branco para manter o valor atual
            </p>
            {data.has_whatsapp_config && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Testar conexão WhatsApp
                </label>
                <div className="flex gap-2">
                  <input
                    className="input flex-1"
                    placeholder="11999998888"
                    value={testPhone}
                    onChange={(e) => setTestPhone(e.target.value)}
                  />
                  <button
                    onClick={handleTestWhatsApp}
                    disabled={testing}
                    className="btn-primary flex items-center gap-1 text-sm px-3"
                  >
                    {testing ? (
                      <Loader2 className="animate-spin" size={14} />
                    ) : (
                      <Send size={14} />
                    )}
                    Testar
                  </button>
                </div>
                <p className="text-xs text-gray-400 mt-1">
                  Envia uma mensagem de teste para validar a configuração
                </p>
              </div>
            )}
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-orange-100 p-2 rounded-lg">
              <MessageSquare size={18} className="text-orange-600" />
            </div>
            <h3 className="font-semibold">SLA Padrão</h3>
          </div>
          <div className="space-y-3 text-sm text-gray-600">
            <div className="flex justify-between items-center py-2 border-b">
              <span>Crítico</span>
              <span className="text-xs">Resposta: 15min / Resolução: 1h</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b">
              <span>Alto</span>
              <span className="text-xs">Resposta: 30min / Resolução: 4h</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b">
              <span>Médio</span>
              <span className="text-xs">Resposta: 1h / Resolução: 8h</span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span>Baixo</span>
              <span className="text-xs">Resposta: 2h / Resolução: 24h</span>
            </div>
            <p className="text-xs text-gray-400">
              SLA configurável por prioridade via banco de dados
            </p>
          </div>
        </div>
      </div>

      {push.state !== 'unsupported' && (
        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-purple-100 p-2 rounded-lg">
              <Bell size={18} className="text-purple-600" />
            </div>
            <div>
              <h3 className="font-semibold">Notificações Push</h3>
              <p className="text-xs text-gray-500">Receba alertas no navegador mesmo sem ter o painel aberto</p>
            </div>
          </div>
          {push.state === 'denied' && (
            <p className="text-sm text-red-500">Notificações bloqueadas pelo navegador. Habilite nas configurações do navegador.</p>
          )}
          {push.state === 'subscribed' && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-green-600 font-medium">Notificações ativas neste dispositivo</span>
              <button
                onClick={push.unsubscribe}
                disabled={push.loading}
                className="text-sm text-red-500 hover:underline disabled:opacity-50"
              >
                {push.loading ? 'Aguarde...' : 'Desativar'}
              </button>
            </div>
          )}
          {push.state === 'unsubscribed' && (
            <button
              onClick={push.subscribe}
              disabled={push.loading}
              className="btn-primary flex items-center gap-2 text-sm"
            >
              {push.loading ? <Loader2 className="animate-spin" size={14} /> : <Bell size={14} />}
              {push.loading ? 'Ativando...' : 'Ativar Notificações'}
            </button>
          )}
        </div>
      )}

      <button
        onClick={handleSave}
        disabled={saving}
        className="btn-primary flex items-center gap-2"
      >
        {saving ? <Loader2 className="animate-spin" size={16} /> : <Check size={16} />}
        {saving ? 'Salvando...' : 'Salvar Configurações'}
      </button>

      {/* LGPD */}
      <div className="card border-red-100 bg-red-50/30">
        <div className="flex items-center gap-2 mb-3">
          <Shield size={18} className="text-red-600" />
          <h3 className="font-semibold text-gray-900">Privacidade e LGPD</h3>
        </div>
        <p className="text-sm text-gray-600 mb-4">
          Conforme a Lei Geral de Proteção de Dados (Lei 13.709/2018), você tem o direito de
          solicitar a exclusão dos seus dados pessoais.{' '}
          <Link to="/legal" className="text-blue-600 hover:underline">
            Leia nossa Política de Privacidade
          </Link>
          .
        </p>
        <button
          onClick={async () => {
            if (!confirm('Tem certeza? Esta ação é irreversível e sua conta será removida.')) return
            try {
              await api.delete('/api/v1/auth/me')
              toast.success('Conta removida.')
              localStorage.clear()
              window.location.href = '/login'
            } catch {
              toast.error('Erro ao remover conta')
            }
          }}
          className="flex items-center gap-2 text-sm text-red-600 hover:text-red-700 font-medium"
        >
          <Trash2 size={14} />
          Solicitar exclusão da minha conta
        </button>
      </div>
    </div>
  )
}
