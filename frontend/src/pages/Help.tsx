import { useState } from 'react'
import { ChevronDown, ChevronUp, HelpCircle, ExternalLink, MessageSquare } from 'lucide-react'

interface FaqItem {
  q: string
  a: string
  category: string
}

const FAQ: FaqItem[] = [
  // Billie / Atendimento
  {
    category: 'Atendimento',
    q: 'Como o aluno inicia o atendimento?',
    a: 'O aluno envia qualquer mensagem para o número WhatsApp cadastrado. Na primeira interação, a Billie pede o RA (Registro Acadêmico) para identificação. Nas próximas mensagens, o aluno já é reconhecido automaticamente.',
  },
  {
    category: 'Atendimento',
    q: 'Quais informações a Billie consegue responder?',
    a: 'Notas e frequência, boletos pendentes, calendário acadêmico, horários de aula, holerite (para funcionários), saldo de férias, ponto eletrônico, e qualquer conteúdo publicado na Base de Conhecimento.',
  },
  {
    category: 'Atendimento',
    q: 'O que acontece quando a Billie não sabe responder?',
    a: 'A Billie informa ao usuário que não encontrou a resposta e cria um ticket automaticamente. Se um atendente humano estiver disponível no horário configurado, o atendimento é transferido em tempo real.',
  },
  {
    category: 'Atendimento',
    q: 'É possível personalizar as respostas da Billie?',
    a: 'Sim. Você pode adicionar artigos na Base de Conhecimento para cobrir perguntas específicas da sua instituição. Também é possível configurar a mensagem de boas-vindas e o tom das respostas em Configurações.',
  },
  // Dados
  {
    category: 'Dados',
    q: 'Como importo dados de alunos e funcionários?',
    a: 'Em Importar Dados, faça upload de arquivo CSV. O sistema valida o formato antes de importar. Você pode baixar o template de exemplo na própria página.',
  },
  {
    category: 'Dados',
    q: 'Os dados são atualizados em tempo real?',
    a: 'O sistema funciona com importações periódicas (manual ou agendada). Para integrações em tempo real com ERPs ou sistemas acadêmicos, entre em contato com o suporte para configurar a API de integração.',
  },
  {
    category: 'Dados',
    q: 'Qual é a política de retenção de dados?',
    a: 'De acordo com a LGPD, mantemos dados de alunos/funcionários inativos por até 5 anos. Após esse prazo, os dados pessoais são anonimizados automaticamente. Você também pode solicitar anonimização manual em Admin → LGPD.',
  },
  // Planos e cobrança
  {
    category: 'Planos',
    q: 'O que acontece quando atinjo o limite de mensagens do meu plano?',
    a: 'As mensagens recebidas serão bloqueadas até o início do próximo mês ou até você fazer upgrade. Você receberá alertas por e-mail ao atingir 80% e 100% do limite.',
  },
  {
    category: 'Planos',
    q: 'Posso testar antes de contratar?',
    a: 'Sim. O período de trial dura 14 dias com até 300 mensagens e 3 usuários. Não é necessário cartão de crédito para iniciar.',
  },
  {
    category: 'Planos',
    q: 'Como faço upgrade de plano?',
    a: 'Entre em contato com nossa equipe de vendas pelo e-mail comercial@igs.com.br ou WhatsApp. O upgrade é ativado imediatamente após a confirmação do pagamento.',
  },
  // Técnico
  {
    category: 'Técnico',
    q: 'O sistema fica fora do ar para manutenção?',
    a: 'Manutenções programadas ocorrem geralmente às madrugadas de domingo (entre 01h e 04h BRT). Avisamos com antecedência de 48h por e-mail. Acompanhe o status em tempo real em Status do Sistema.',
  },
  {
    category: 'Técnico',
    q: 'Onde ficam armazenados meus dados?',
    a: 'Os dados são armazenados em servidores na região de São Paulo (Brasil), em conformidade com a LGPD. Utilizamos criptografia em repouso e em trânsito.',
  },
  {
    category: 'Técnico',
    q: 'Posso usar minha própria chave da API do Claude?',
    a: 'Sim. No plano Pro e Enterprise, você pode configurar sua própria chave Anthropic em Configurações → Integrações. Isso permite faturamento direto e maior controle de custos.',
  },
]

const CATEGORIES = ['Todos', ...Array.from(new Set(FAQ.map((f) => f.category)))]

export default function Help() {
  const [openIndex, setOpenIndex] = useState<number | null>(null)
  const [category, setCategory] = useState('Todos')
  const [search, setSearch] = useState('')

  const filtered = FAQ.filter((item) => {
    const matchCat = category === 'Todos' || item.category === category
    const matchSearch =
      !search ||
      item.q.toLowerCase().includes(search.toLowerCase()) ||
      item.a.toLowerCase().includes(search.toLowerCase())
    return matchCat && matchSearch
  })

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Central de Ajuda</h1>
        <p className="text-sm text-gray-500">Perguntas frequentes e documentação</p>
      </div>

      {/* Links rápidos */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <a
          href="/docs/ADMIN_MANUAL.md"
          target="_blank"
          rel="noopener noreferrer"
          className="card p-4 flex items-center gap-3 hover:shadow-md transition-shadow"
        >
          <HelpCircle size={20} className="text-blue-600 shrink-0" />
          <div>
            <p className="font-medium text-sm">Manual do Admin</p>
            <p className="text-xs text-gray-500">Guia completo do painel</p>
          </div>
          <ExternalLink size={14} className="text-gray-400 ml-auto" />
        </a>
        <a
          href="mailto:suporte@igs.com.br"
          className="card p-4 flex items-center gap-3 hover:shadow-md transition-shadow"
        >
          <MessageSquare size={20} className="text-green-600 shrink-0" />
          <div>
            <p className="font-medium text-sm">Abrir chamado</p>
            <p className="text-xs text-gray-500">suporte@igs.com.br</p>
          </div>
          <ExternalLink size={14} className="text-gray-400 ml-auto" />
        </a>
        <a
          href="/app/status"
          className="card p-4 flex items-center gap-3 hover:shadow-md transition-shadow"
        >
          <div className="w-3 h-3 rounded-full bg-green-500 shrink-0" />
          <div>
            <p className="font-medium text-sm">Status do Sistema</p>
            <p className="text-xs text-gray-500">Uptime e incidentes</p>
          </div>
        </a>
      </div>

      {/* FAQ */}
      <div className="card p-6 space-y-4">
        <h2 className="font-semibold text-gray-800">Perguntas Frequentes</h2>

        <div className="flex flex-col sm:flex-row gap-3">
          <input
            className="input flex-1"
            placeholder="Buscar pergunta..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setOpenIndex(null) }}
          />
          <div className="flex gap-2 flex-wrap">
            {CATEGORIES.map((cat) => (
              <button
                key={cat}
                onClick={() => { setCategory(cat); setOpenIndex(null) }}
                className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
                  category === cat
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white text-gray-600 border-gray-200 hover:border-blue-300'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {filtered.length === 0 && (
          <p className="text-center text-gray-400 py-8">Nenhuma pergunta encontrada.</p>
        )}

        <div className="divide-y divide-gray-100">
          {filtered.map((item, idx) => (
            <div key={idx} className="py-3">
              <button
                className="w-full flex items-start justify-between gap-3 text-left"
                onClick={() => setOpenIndex(openIndex === idx ? null : idx)}
              >
                <div>
                  <span className="text-xs font-medium text-blue-600 mr-2">{item.category}</span>
                  <span className="text-sm font-medium text-gray-800">{item.q}</span>
                </div>
                {openIndex === idx ? (
                  <ChevronUp size={16} className="text-gray-400 shrink-0 mt-0.5" />
                ) : (
                  <ChevronDown size={16} className="text-gray-400 shrink-0 mt-0.5" />
                )}
              </button>
              {openIndex === idx && (
                <p className="mt-2 text-sm text-gray-600 leading-relaxed pl-1">{item.a}</p>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
