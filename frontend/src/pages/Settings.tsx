import { useState, useEffect } from 'react'
import { api } from '../api/client'
import { Bell, Bot, Clock, Key, MessageSquare, Loader2, Check, Send } from 'lucide-react'
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

  // Integration fields (not returned by GET for security)
  const [waPhoneId, setWaPhoneId] = useState('')
  const [waToken, setWaToken] = useState('')
  const [aiKey, setAiKey] = useState('')
  const [testPhone, setTestPhone] = useState('')
  const [testing, setTesting] = useState(false)

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
      toast.success('Configuracoes salvas com sucesso!')
    } catch {
      /* interceptor handles */
    }
    setSaving(false)
  }

  async function handleTestWhatsApp() {
    if (!testPhone.trim()) {
      toast.error('Digite um numero de telefone para teste')
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
        <h1 className="text-2xl font-bold text-gray-900">Configuracoes</h1>
        <p className="text-sm text-gray-500">Configure o sistema e integracoes</p>
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
                placeholder="Ola! Como posso ajudar?"
              />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-green-100 p-2 rounded-lg">
              <Clock size={18} className="text-green-600" />
            </div>
            <h3 className="font-semibold">Horario de Funcionamento</h3>
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
                Mensagem fora do horario
              </label>
              <textarea
                className="input resize-none"
                rows={2}
                value={data.out_of_hours_message || ''}
                onChange={(e) => setData({ ...data, out_of_hours_message: e.target.value })}
                placeholder="Estamos fora do horario..."
              />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <div className="bg-purple-100 p-2 rounded-lg">
              <Key size={18} className="text-purple-600" />
            </div>
            <h3 className="font-semibold">Integracoes</h3>
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
                  Testar conexao WhatsApp
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
                  Envia uma mensagem de teste para validar a configuracao
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
            <h3 className="font-semibold">SLA Padrao</h3>
          </div>
          <div className="space-y-3 text-sm text-gray-600">
            <div className="flex justify-between items-center py-2 border-b">
              <span>Critico</span>
              <span>Resposta: 15min / Resolucao: 1h</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b">
              <span>Alto</span>
              <span>Resposta: 30min / Resolucao: 4h</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b">
              <span>Medio</span>
              <span>Resposta: 1h / Resolucao: 8h</span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span>Baixo</span>
              <span>Resposta: 2h / Resolucao: 24h</span>
            </div>
            <p className="text-xs text-gray-400">
              SLA configuravel por prioridade via banco de dados
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
              <h3 className="font-semibold">Notificacoes Push</h3>
              <p className="text-xs text-gray-500">Receba alertas no navegador mesmo sem ter o painel aberto</p>
            </div>
          </div>
          {push.state === 'denied' && (
            <p className="text-sm text-red-500">Notificacoes bloqueadas pelo navegador. Habilite nas configuracoes do navegador.</p>
          )}
          {push.state === 'subscribed' && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-green-600 font-medium">Notificacoes ativas neste dispositivo</span>
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
              {push.loading ? 'Ativando...' : 'Ativar Notificacoes'}
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
        {saving ? 'Salvando...' : 'Salvar Configuracoes'}
      </button>
    </div>
  )
}
