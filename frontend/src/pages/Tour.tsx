import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  ArrowRight, ArrowLeft, LayoutDashboard, MessageSquare, GraduationCap,
  BookOpen, BarChart3, Settings, CheckCircle2, Smartphone, Bot,
} from 'lucide-react'
import clsx from 'clsx'

interface Step {
  id: number
  icon: React.ElementType
  color: string
  title: string
  subtitle: string
  description: string
  tip: string
  link?: { label: string; to: string }
  visual: React.ReactNode
}

const steps: Step[] = [
  {
    id: 1,
    icon: Smartphone,
    color: 'blue',
    title: 'Integre seu WhatsApp',
    subtitle: 'Passo 1 de 6 — Configuração inicial',
    description:
      'Conecte seu número de WhatsApp Business oficial (via Meta). A Billie passa a responder automaticamente qualquer mensagem enviada para esse número, 24 horas por dia.',
    tip: 'Dica: você pode testar com uma conta sandbox antes de ativar o número oficial.',
    link: { label: 'Ir para Configurações → WhatsApp', to: '/app/whatsapp-setup' },
    visual: (
      <div className="bg-gray-900 rounded-2xl p-4 w-full max-w-xs mx-auto">
        <div className="bg-green-500 rounded-xl p-3 mb-3 text-white text-xs font-medium flex items-center gap-2">
          <div className="w-2 h-2 bg-white rounded-full animate-pulse" /> WhatsApp Business Conectado
        </div>
        <div className="space-y-2">
          {['aluno@faculdade.edu.br', 'funcionario@faculdade.edu.br'].map((e) => (
            <div key={e} className="bg-gray-800 rounded-lg px-3 py-2 text-xs text-gray-300 flex items-center gap-2">
              <div className="w-6 h-6 bg-gray-700 rounded-full" />
              {e.split('@')[0]}
            </div>
          ))}
        </div>
      </div>
    ),
  },
  {
    id: 2,
    icon: GraduationCap,
    color: 'indigo',
    title: 'Importe seus alunos',
    subtitle: 'Passo 2 de 6 — Dados',
    description:
      'Carregue sua base de alunos via CSV com nome, RA, curso, e-mail e telefone. A Billie usa esses dados para verificar identidade e responder perguntas sobre notas, boletos e frequência.',
    tip: 'Você também pode importar via API REST se já tiver um sistema de gestão acadêmica.',
    link: { label: 'Ir para Alunos', to: '/app/students' },
    visual: (
      <div className="bg-white rounded-2xl border border-gray-200 p-4 w-full max-w-xs mx-auto shadow-sm">
        <div className="text-xs font-semibold text-gray-500 mb-3">alunos.csv</div>
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b">
              <th className="text-left pb-1 text-gray-400">RA</th>
              <th className="text-left pb-1 text-gray-400">Nome</th>
              <th className="text-left pb-1 text-gray-400">Curso</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {[
              ['2024001', 'Ana Silva', 'ADS'],
              ['2024002', 'João Costa', 'Direito'],
              ['2024003', 'Maria Lima', 'Medicina'],
            ].map(([ra, nome, curso]) => (
              <tr key={ra} className="text-gray-700">
                <td className="py-1 font-mono">{ra}</td>
                <td className="py-1">{nome}</td>
                <td className="py-1">{curso}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="mt-3 text-xs text-green-600 font-medium flex items-center gap-1">
          <CheckCircle2 size={12} /> 3 alunos importados
        </div>
      </div>
    ),
  },
  {
    id: 3,
    icon: MessageSquare,
    color: 'green',
    title: 'Billie responde automaticamente',
    subtitle: 'Passo 3 de 6 — Atendimento',
    description:
      'Quando um aluno manda mensagem, a Billie identifica quem é pelo RA, classifica a intenção (nota? boleto? frequência?) e responde com dados reais do banco em menos de 3 segundos.',
    tip: 'Se a Billie não souber responder, ela cria um ticket e avisa o atendente humano.',
    link: { label: 'Ver Conversas', to: '/app/conversations' },
    visual: (
      <div className="bg-[#075e54] rounded-2xl p-3 w-full max-w-xs mx-auto">
        <div className="space-y-2">
          {[
            { from: 'aluno', text: 'Qual minha nota em Matemática?' },
            { from: 'billie', text: '📊 Sua nota em Matemática (2024.1) é 8,5 — Aprovado ✓' },
            { from: 'aluno', text: 'E o boleto de maio?' },
            { from: 'billie', text: '💳 Boleto Maio/2024: R$ 890,00 · Vence 10/05 · [Link PIX]' },
          ].map((msg, i) => (
            <div
              key={i}
              className={clsx(
                'rounded-xl px-3 py-2 text-xs max-w-[85%]',
                msg.from === 'aluno'
                  ? 'bg-white text-gray-800 self-start'
                  : 'bg-[#dcf8c6] text-gray-800 self-end ml-auto',
              )}
            >
              {msg.text}
            </div>
          ))}
        </div>
      </div>
    ),
  },
  {
    id: 4,
    icon: LayoutDashboard,
    color: 'purple',
    title: 'Monitore pelo painel',
    subtitle: 'Passo 4 de 6 — Gestão',
    description:
      'O painel admin mostra conversas em tempo real, tickets abertos, taxa de resolução automática, alunos em risco de evasão e muito mais. Tudo em um só lugar.',
    tip: 'O dashboard atualiza automaticamente — não precisa recarregar a página.',
    link: { label: 'Abrir Dashboard', to: '/app/dashboard' },
    visual: (
      <div className="grid grid-cols-2 gap-2 w-full max-w-xs mx-auto">
        {[
          { label: 'Conversas hoje', value: '127', color: 'text-blue-600' },
          { label: 'Resolvidas IA', value: '94%', color: 'text-green-600' },
          { label: 'Tickets abertos', value: '8', color: 'text-orange-600' },
          { label: 'Risco evasão', value: '12', color: 'text-red-600' },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-white rounded-xl border border-gray-200 p-3 shadow-sm">
            <p className={clsx('text-2xl font-bold', color)}>{value}</p>
            <p className="text-xs text-gray-500 mt-0.5">{label}</p>
          </div>
        ))}
      </div>
    ),
  },
  {
    id: 5,
    icon: BookOpen,
    color: 'amber',
    title: 'Base de conhecimento',
    subtitle: 'Passo 5 de 6 — Conteúdo',
    description:
      'Adicione artigos sobre processos, regras e FAQs da sua instituição. A Billie consulta essa base automaticamente para responder perguntas que não estão nos dados estruturados.',
    tip: 'Exemplos: "como solicitar segunda via de diploma", "calendário acadêmico 2024".',
    link: { label: 'Ir para Base de Conhecimento', to: '/app/knowledge-base' },
    visual: (
      <div className="bg-white rounded-2xl border border-gray-200 p-4 w-full max-w-xs mx-auto shadow-sm space-y-2">
        {[
          { title: 'Calendário 2024', cat: 'Acadêmico' },
          { title: 'Solicitação de Diploma', cat: 'Secretaria' },
          { title: 'Rematrícula', cat: 'Financeiro' },
        ].map(({ title, cat }) => (
          <div key={title} className="flex items-center gap-3 border border-gray-100 rounded-lg p-2.5">
            <BookOpen size={14} className="text-amber-500 shrink-0" />
            <div>
              <p className="text-xs font-medium text-gray-800">{title}</p>
              <p className="text-xs text-gray-400">{cat}</p>
            </div>
          </div>
        ))}
      </div>
    ),
  },
  {
    id: 6,
    icon: BarChart3,
    color: 'teal',
    title: 'Relatórios automáticos',
    subtitle: 'Passo 6 de 6 — Resultados',
    description:
      'Todo início de semana você recebe um relatório com volume de atendimentos, taxa de resolução, alunos em risco de evasão e satisfação. Sem precisar gerar nada manualmente.',
    tip: 'Configure destinatários adicionais em Configurações → Relatórios.',
    link: { label: 'Ver Relatórios', to: '/app/reports' },
    visual: (
      <div className="bg-white rounded-2xl border border-gray-200 p-4 w-full max-w-xs mx-auto shadow-sm">
        <div className="text-xs font-semibold text-gray-700 mb-3 flex items-center gap-1.5">
          <BarChart3 size={14} className="text-teal-600" />
          Relatório Semanal — Jan/2024
        </div>
        <div className="space-y-2">
          {[
            { label: 'Atendimentos', value: 842, max: 1000, color: 'bg-blue-500' },
            { label: 'IA resolveu', value: 792, max: 1000, color: 'bg-green-500' },
            { label: 'Tickets abertos', value: 50, max: 1000, color: 'bg-orange-400' },
          ].map(({ label, value, max, color }) => (
            <div key={label}>
              <div className="flex justify-between text-xs text-gray-600 mb-0.5">
                <span>{label}</span>
                <span className="font-medium">{value}</span>
              </div>
              <div className="h-1.5 bg-gray-100 rounded-full">
                <div className={clsx('h-full rounded-full', color)} style={{ width: `${(value / max) * 100}%` }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    ),
  },
]

export default function Tour() {
  const [current, setCurrent] = useState(0)
  const step = steps[current]
  const Icon = step.icon

  const colorClasses: Record<string, string> = {
    blue: 'bg-blue-50 text-blue-600',
    indigo: 'bg-indigo-50 text-indigo-600',
    green: 'bg-green-50 text-green-600',
    purple: 'bg-purple-50 text-purple-600',
    amber: 'bg-amber-50 text-amber-600',
    teal: 'bg-teal-50 text-teal-600',
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Progress bar */}
      <div className="h-1 bg-gray-200">
        <div
          className="h-full bg-blue-600 transition-all duration-500"
          style={{ width: `${((current + 1) / steps.length) * 100}%` }}
        />
      </div>

      <div className="flex-1 flex flex-col items-center justify-center px-6 py-12">
        <div className="w-full max-w-2xl">
          {/* Step indicator */}
          <div className="flex items-center justify-center gap-2 mb-8">
            {steps.map((s, i) => (
              <button
                key={s.id}
                onClick={() => setCurrent(i)}
                className={clsx(
                  'w-2 h-2 rounded-full transition-all',
                  i === current ? 'w-6 bg-blue-600' : i < current ? 'bg-blue-300' : 'bg-gray-300',
                )}
              />
            ))}
          </div>

          {/* Card */}
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
            {/* Visual */}
            <div className="bg-gray-50 border-b border-gray-100 p-8 flex justify-center">
              {step.visual}
            </div>

            {/* Content */}
            <div className="p-6 md:p-8">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                {step.subtitle}
              </p>
              <div className="flex items-center gap-3 mb-4">
                <div className={clsx('p-2 rounded-lg', colorClasses[step.color])}>
                  <Icon size={20} />
                </div>
                <h2 className="text-xl font-bold text-gray-900">{step.title}</h2>
              </div>
              <p className="text-gray-600 leading-relaxed mb-4">{step.description}</p>
              <div className="bg-blue-50 rounded-lg px-4 py-3 text-sm text-blue-700 border border-blue-100">
                💡 {step.tip}
              </div>

              {step.link && (
                <Link
                  to={step.link.to}
                  className="mt-4 inline-flex items-center gap-1.5 text-sm text-blue-600 hover:underline font-medium"
                >
                  {step.link.label} <ArrowRight size={14} />
                </Link>
              )}
            </div>

            {/* Navigation */}
            <div className="border-t border-gray-100 px-6 py-4 flex items-center justify-between">
              <button
                onClick={() => setCurrent(Math.max(0, current - 1))}
                disabled={current === 0}
                className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-gray-900 disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <ArrowLeft size={16} /> Anterior
              </button>

              <span className="text-xs text-gray-400">
                {current + 1} / {steps.length}
              </span>

              {current < steps.length - 1 ? (
                <button
                  onClick={() => setCurrent(current + 1)}
                  className="flex items-center gap-1.5 text-sm font-medium text-blue-600 hover:text-blue-700"
                >
                  Próximo <ArrowRight size={16} />
                </button>
              ) : (
                <Link
                  to="/signup"
                  className="flex items-center gap-1.5 text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg"
                >
                  Começar agora <ArrowRight size={16} />
                </Link>
              )}
            </div>
          </div>

          {/* Skip */}
          <div className="text-center mt-4">
            <Link to="/signup" className="text-xs text-gray-400 hover:text-gray-600 underline">
              Pular tour e criar conta
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
