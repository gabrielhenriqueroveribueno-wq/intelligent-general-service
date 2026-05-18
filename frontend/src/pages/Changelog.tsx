import { Link } from 'react-router-dom'
import { Zap, Shield, Bug, Package, ArrowLeft } from 'lucide-react'

interface ChangeEntry {
  version: string
  date: string
  items: { type: 'feature' | 'fix' | 'improvement' | 'security'; text: string }[]
}

const CHANGELOG: ChangeEntry[] = [
  {
    version: '1.4.0',
    date: '2026-05-14',
    items: [
      { type: 'feature', text: 'Assinatura recorrente via Mercado Pago (pre_approval) — cobrança automática mensal' },
      { type: 'feature', text: 'Banner de trial com contagem regressiva e modal de paywall' },
      { type: 'feature', text: 'Formulário de captação de leads no site — substituindo mailto' },
      { type: 'feature', text: 'Página de status pública com SLA e disponibilidade por componente' },
      { type: 'improvement', text: 'Handlers de WhatsApp (recurso de nota, transferência, bolsa, estágio, evento) agora criam tickets reais no painel' },
      { type: 'improvement', text: 'Busca de livros na biblioteca via WhatsApp com disponibilidade em tempo real' },
      { type: 'improvement', text: 'SEO completo: Open Graph, Twitter Card, JSON-LD, sitemap.xml, robots.txt' },
      { type: 'feature', text: 'Botão de acesso demo na tela de login' },
    ],
  },
  {
    version: '1.3.0',
    date: '2026-05-12',
    items: [
      { type: 'feature', text: 'Pitch deck de investidores em /pitch (público, sem login)' },
      { type: 'feature', text: 'Contrato SaaS completo com DPA e LGPD em docs/CONTRATO_SAAS.md' },
      { type: 'feature', text: 'Recuperação de senha via email (forgot-password / reset-password)' },
      { type: 'feature', text: 'Cache de respostas de IA no Redis (TTL 5min) para intents repetidos' },
      { type: 'improvement', text: 'Service Worker PWA — estratégia NetworkFirst para navegação e cache de assets' },
      { type: 'improvement', text: 'Log rotation no Caddy (10MiB, 5 rotações, 30 dias)' },
      { type: 'improvement', text: 'AI budget alert diário — email quando gasto supera 80% do limite' },
      { type: 'security', text: 'Adicionado keys/, *.key, *.pem ao .gitignore para prevenir exposição de chaves SSH' },
    ],
  },
  {
    version: '1.2.0',
    date: '2026-04-30',
    items: [
      { type: 'feature', text: 'Conector SQL genérico para integração com sistemas acadêmicos' },
      { type: 'feature', text: 'Logs de sincronização com ERP/SIS no painel de integrações' },
      { type: 'feature', text: 'Script de instalação automatizado para novos clientes' },
      { type: 'improvement', text: 'Dashboard com estatísticas animadas e modo apresentação' },
      { type: 'improvement', text: 'Onboarding em etapas (tour guiado para novos tenants)' },
      { type: 'feature', text: 'Sistema de billing SaaS com planos Starter/Pro' },
    ],
  },
  {
    version: '1.1.0',
    date: '2026-04-15',
    items: [
      { type: 'feature', text: 'Agendamento de atendimento presencial via WhatsApp' },
      { type: 'feature', text: 'OCR de documentos via foto no WhatsApp' },
      { type: 'feature', text: 'Tutor acadêmico: responde dúvidas com base no material do professor' },
      { type: 'feature', text: 'Renovação de empréstimos de biblioteca via WhatsApp' },
      { type: 'improvement', text: 'Circuit breaker para providers de IA (Groq, Gemini, Anthropic)' },
      { type: 'fix', text: 'Corrigido loop de refresh token em tabs múltiplas' },
    ],
  },
  {
    version: '1.0.0',
    date: '2026-04-01',
    items: [
      { type: 'feature', text: 'Lançamento — IGS em produção na Faculdade Anchieta' },
      { type: 'feature', text: 'Atendimento via WhatsApp: notas, frequência, boletos, holerite' },
      { type: 'feature', text: 'Painel admin com dashboard, conversas, tickets, base de conhecimento' },
      { type: 'feature', text: 'Multi-tenant com isolamento por tenant_id' },
      { type: 'feature', text: 'Autenticação JWT com refresh token e must_change_password' },
      { type: 'security', text: 'Criptografia Fernet para CPF e tokens sensíveis no banco' },
    ],
  },
]

const typeConfig = {
  feature: { icon: Zap, color: 'text-blue-600', bg: 'bg-blue-50', label: 'Novo' },
  fix: { icon: Bug, color: 'text-red-600', bg: 'bg-red-50', label: 'Correção' },
  improvement: { icon: Package, color: 'text-green-600', bg: 'bg-green-50', label: 'Melhoria' },
  security: { icon: Shield, color: 'text-purple-600', bg: 'bg-purple-50', label: 'Segurança' },
}

export default function Changelog() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <div>
            <Link to="/" className="text-xl font-bold text-gray-900 hover:text-blue-600">IGS</Link>
            <p className="text-sm text-gray-500">Changelog — novidades e correções</p>
          </div>
          <Link to="/" className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-900">
            <ArrowLeft size={14} /> Voltar ao site
          </Link>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-6 py-10 space-y-10">
        {CHANGELOG.map((entry) => (
          <div key={entry.version}>
            <div className="flex items-baseline gap-3 mb-5">
              <h2 className="text-xl font-bold text-gray-900">v{entry.version}</h2>
              <span className="text-sm text-gray-400">
                {new Date(entry.date).toLocaleDateString('pt-BR', { year: 'numeric', month: 'long', day: 'numeric' })}
              </span>
            </div>
            <div className="space-y-2">
              {entry.items.map((item, i) => {
                const cfg = typeConfig[item.type]
                const Icon = cfg.icon
                return (
                  <div key={i} className="flex items-start gap-3 bg-white rounded-xl border border-gray-100 p-4">
                    <div className={`${cfg.bg} ${cfg.color} p-1.5 rounded-lg shrink-0`}>
                      <Icon size={14} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <span className={`text-xs font-medium ${cfg.color} mr-2`}>{cfg.label}</span>
                      <span className="text-sm text-gray-700">{item.text}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
