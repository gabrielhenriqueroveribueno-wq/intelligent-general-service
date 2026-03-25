import { Settings as SettingsIcon, Bot, MessageSquare, Clock, Key } from 'lucide-react'

export default function Settings() {
  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Configurações</h1>
        <p className="text-sm text-gray-500">Configure o sistema e integrações</p>
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
              <input className="input" placeholder="Ex: Assistente Anchieta" defaultValue="Assistente IGS" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Mensagem de boas-vindas</label>
              <textarea className="input resize-none" rows={3} placeholder="Olá! Como posso ajudar?" />
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
                <input className="input" type="time" defaultValue="08:00" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Fechamento</label>
                <input className="input" type="time" defaultValue="22:00" />
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Mensagem fora do horário</label>
              <textarea className="input resize-none" rows={2} placeholder="Estamos fora do horário..." />
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
              <label className="block text-xs font-medium text-gray-600 mb-1">WhatsApp Phone Number ID</label>
              <input className="input" placeholder="Ex: 123456789012345" type="password" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">WhatsApp Access Token</label>
              <input className="input" placeholder="EAAxxxxxxxxxx..." type="password" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Claude API Key</label>
              <input className="input" placeholder="sk-ant-..." type="password" />
            </div>
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
              <span>🔴 Crítico</span><span>Resposta: 15min / Resolução: 1h</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b">
              <span>🟠 Alto</span><span>Resposta: 30min / Resolução: 4h</span>
            </div>
            <div className="flex justify-between items-center py-2 border-b">
              <span>🔵 Médio</span><span>Resposta: 1h / Resolução: 8h</span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span>⚪ Baixo</span><span>Resposta: 2h / Resolução: 24h</span>
            </div>
            <p className="text-xs text-gray-400">Configure via API ou banco de dados</p>
          </div>
        </div>
      </div>

      <button className="btn-primary">Salvar Configurações</button>
    </div>
  )
}
