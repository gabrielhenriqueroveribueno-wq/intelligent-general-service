import { Link } from 'react-router-dom'
import {
  MessageSquare,
  Brain,
  ShieldCheck,
  Zap,
  Clock,
  TrendingUp,
  Users,
  CheckCircle2,
  ArrowRight,
  Smartphone,
  GraduationCap,
  Briefcase,
  HelpCircle,
} from 'lucide-react'

export default function Landing() {
  return (
    <div>
      {/* ─── HERO ─────────────────────────────────────── */}
      <section className="bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 text-white">
        <div className="max-w-6xl mx-auto px-6 py-20 md:py-28 grid md:grid-cols-2 gap-10 items-center">
          <div>
            <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur px-3 py-1.5 rounded-full text-sm mb-6">
              <Smartphone size={14} />
              <span>Atendimento via WhatsApp 24/7</span>
            </div>
            <h1 className="text-4xl md:text-5xl font-bold leading-tight mb-5">
              Sua escola atende alunos no WhatsApp{' '}
              <span className="text-yellow-300">com IA</span>, 24 horas por dia.
            </h1>
            <p className="text-lg text-blue-100 mb-8 leading-relaxed">
              Notas, boletos, frequência, holerite, agendamentos. A Billie responde em 3
              segundos com dados reais — e transfere pra um humano quando precisa.
            </p>
            <div className="flex flex-col sm:flex-row gap-3">
              <Link
                to="/demo"
                className="bg-white text-blue-700 px-6 py-3 rounded-lg font-semibold hover:bg-blue-50 inline-flex items-center justify-center gap-2"
              >
                Ver demonstração ao vivo <ArrowRight size={18} />
              </Link>
              <a
                href="mailto:contato@igs.com.br?subject=Quero conhecer o IGS"
                className="border-2 border-white/40 px-6 py-3 rounded-lg font-semibold hover:bg-white/10 inline-flex items-center justify-center gap-2"
              >
                Falar com vendas
              </a>
            </div>
            <div className="flex items-center gap-6 mt-8 text-sm text-blue-100">
              <div className="flex items-center gap-1.5">
                <CheckCircle2 size={16} /> Sem cartão de crédito
              </div>
              <div className="flex items-center gap-1.5">
                <CheckCircle2 size={16} /> Setup em 1 hora
              </div>
            </div>
          </div>

          {/* Mockup do chat */}
          <div className="bg-white rounded-2xl shadow-2xl p-4 max-w-sm mx-auto md:ml-auto">
            <div className="bg-emerald-600 text-white rounded-t-lg p-3 -mx-4 -mt-4 mb-3 flex items-center gap-3">
              <div className="bg-white/20 rounded-full p-2">
                <Bot />
              </div>
              <div>
                <p className="font-semibold text-sm">Billie — IGS</p>
                <p className="text-xs text-emerald-100">Online agora</p>
              </div>
            </div>
            <div className="space-y-2 text-sm">
              <ChatBubble side="right" text="Quero ver minhas notas" time="14:32" />
              <ChatBubble
                side="left"
                text="Suas notas, Lucas:\n\n• Cálculo I — P1: 8.5 | P2: 7.0\n• Banco de Dados — P1: 9.0 | P2: 8.5\n\nQuer ver frequência ou boletos?"
                time="14:32"
              />
              <ChatBubble side="right" text="Era só isso, valeu!" time="14:33" />
              <ChatBubble
                side="left"
                text="Que bom que ajudei! Me dá uma nota de 1 a 5? 1=ruim, 5=excelente"
                time="14:33"
              />
              <ChatBubble side="right" text="5" time="14:33" />
            </div>
          </div>
        </div>
      </section>

      {/* ─── PROBLEMAS QUE RESOLVEMOS ─────────────────── */}
      <section className="py-16 px-6 bg-white">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-3">
            Por que escolas escolhem o IGS?
          </h2>
          <p className="text-center text-gray-600 mb-12">
            Atendimento manual é caro, lento e cansa a equipe. A gente resolve isso.
          </p>

          <div className="grid md:grid-cols-3 gap-6">
            <ProblemCard
              icon={Clock}
              title="Atendimento 24/7"
              before="Aluno espera até segunda às 8h"
              after="Resposta em 3 segundos, 24h por dia"
            />
            <ProblemCard
              icon={TrendingUp}
              title="Equipe sobrecarregada"
              before="3-4 atendentes em horário comercial"
              after="IA resolve 87% sozinha — humano só nos casos complexos"
            />
            <ProblemCard
              icon={Brain}
              title="Respostas inconsistentes"
              before="Cada atendente responde diferente"
              after="Padronizado, com dados reais do sistema"
            />
          </div>
        </div>
      </section>

      {/* ─── FUNCIONALIDADES ───────────────────────────── */}
      <section id="funcionalidades" className="py-16 px-6 bg-gray-50">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-3">
            Tudo que sua escola precisa
          </h2>
          <p className="text-center text-gray-600 mb-12">
            Uma única plataforma para alunos, funcionários e gestores.
          </p>

          <div className="grid md:grid-cols-2 gap-6">
            <FeatureCard
              icon={GraduationCap}
              title="Para alunos"
              items={[
                'Consulta de notas e frequência',
                'Boletos e pagamento via PIX/cartão',
                'Horários de aula e biblioteca',
                'Agendamento de atendimento presencial',
                'Solicitação de documentos (histórico, declarações)',
              ]}
            />
            <FeatureCard
              icon={Briefcase}
              title="Para funcionários"
              items={[
                'Holerite e contracheque',
                'Solicitação e saldo de férias',
                'Registro de ponto e ausências',
                'Solicitações de RH',
                'Avisos da diretoria',
              ]}
            />
            <FeatureCard
              icon={Brain}
              title="Para a IA (Billie)"
              items={[
                'Verificação de identidade por RA + senha',
                'Classificação automática de intenção',
                'Resposta com dados reais do banco (RAG)',
                'Aprendizado contínuo com tickets resolvidos',
                'Fallback offline quando providers falham',
              ]}
            />
            <FeatureCard
              icon={Users}
              title="Para gestores"
              items={[
                'Dashboard em tempo real',
                'Métricas IA vs humano e ROI',
                'Tickets com SLA',
                'Relatórios semanais por email',
                'Alertas de risco de evasão',
              ]}
            />
          </div>
        </div>
      </section>

      {/* ─── ROI ─────────────────────────────────────── */}
      <section className="py-16 px-6 bg-white">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold text-gray-900 mb-3">
              Quanto sua escola economiza?
            </h2>
            <p className="text-gray-600">
              Cálculo real baseado em uma instituição com 800 alunos e 60 funcionários.
            </p>
          </div>

          <div className="grid md:grid-cols-4 gap-4 mb-8">
            <RoiCard value="87%" label="Resolução automática" sub="sem precisar de humano" />
            <RoiCard value="3s" label="Tempo médio de resposta" sub="vs 8 min humano" />
            <RoiCard value="R$ 18 mil" label="Economia mensal" sub="vs equipe humana 24/7" />
            <RoiCard value="4.6/5" label="Satisfação" sub="média das avaliações" />
          </div>

          <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-2xl p-6 max-w-3xl mx-auto">
            <h3 className="font-semibold text-green-900 mb-3">Comparativo mensal</h3>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <p className="text-gray-600 mb-1">Equipe 100% humana</p>
                <p className="text-2xl font-bold text-red-600">R$ 26.800</p>
              </div>
              <div>
                <p className="text-gray-600 mb-1">Equipe + IGS</p>
                <p className="text-2xl font-bold text-blue-600">R$ 8.620</p>
                <p className="text-xs text-gray-500">(R$ 8.200 humano + R$ 420 IA)</p>
              </div>
              <div>
                <p className="text-gray-600 mb-1">Você economiza</p>
                <p className="text-2xl font-bold text-green-600">R$ 18.180</p>
                <p className="text-xs text-gray-500">68% de redução</p>
              </div>
            </div>
            <Link
              to="/case-study"
              className="inline-flex items-center gap-2 mt-4 text-green-700 hover:text-green-900 text-sm font-medium"
            >
              Ver caso de uso completo <ArrowRight size={14} />
            </Link>
          </div>
        </div>
      </section>

      {/* ─── COMO FUNCIONA ─────────────────────────────── */}
      <section className="py-16 px-6 bg-gray-50">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            Como funciona?
          </h2>
          <div className="grid md:grid-cols-4 gap-6">
            <StepCard
              num={1}
              title="Aluno manda mensagem"
              desc="No mesmo número de WhatsApp da sua escola"
            />
            <StepCard
              num={2}
              title="IA classifica a intenção"
              desc="Notas? Boleto? Frequência? A Billie entende"
            />
            <StepCard
              num={3}
              title="Busca no seu sistema"
              desc="Dados reais — nunca inventa"
            />
            <StepCard
              num={4}
              title="Responde em 3 segundos"
              desc="Ou transfere pra humano se for complexo"
            />
          </div>
        </div>
      </section>

      {/* ─── SEGURANÇA ────────────────────────────────── */}
      <section className="py-16 px-6 bg-white">
        <div className="max-w-6xl mx-auto grid md:grid-cols-2 gap-10 items-center">
          <div>
            <ShieldCheck className="text-blue-600 mb-4" size={40} />
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Segurança em primeiro lugar
            </h2>
            <p className="text-gray-600 mb-6">
              Dados de alunos são sensíveis. Construímos o IGS com proteção em todas as
              camadas:
            </p>
            <ul className="space-y-3">
              <SecBullet text="Multi-tenancy isolado — cada escola tem seu próprio espaço" />
              <SecBullet text="CPFs e tokens criptografados no banco (Fernet)" />
              <SecBullet text="Verificação de identidade obrigatória (RA + senha)" />
              <SecBullet text="HMAC validado em todo webhook do WhatsApp" />
              <SecBullet text="JWT com refresh tokens (access 15min, refresh 7 dias)" />
              <SecBullet text="Suite de testes automatizados rodando em CI/CD" />
            </ul>
          </div>
          <div className="bg-gradient-to-br from-blue-50 to-indigo-100 rounded-2xl p-8">
            <h3 className="font-bold text-gray-900 mb-4">Conformidade</h3>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <Badge text="LGPD" />
              <Badge text="Logs auditáveis" />
              <Badge text="Backup diário" />
              <Badge text="Anonimização" />
              <Badge text="Rate limiting" />
              <Badge text="Observabilidade" />
            </div>
          </div>
        </div>
      </section>

      {/* ─── PREÇOS ──────────────────────────────────── */}
      <section id="precos" className="py-16 px-6 bg-gray-50">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-3">
            Preço justo, transparente
          </h2>
          <p className="text-center text-gray-600 mb-12">
            Sem taxa de setup. Sem fidelidade. Cancele quando quiser.
          </p>
          <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            <PriceCard
              name="Basic"
              price="R$ 497"
              desc="Até 500 alunos"
              features={[
                'Atendimento WhatsApp 24/7',
                'Painel admin completo',
                'Notas, boletos, frequência',
                'Suporte por email',
              ]}
            />
            <PriceCard
              name="Pro"
              price="R$ 997"
              desc="Até 2.000 alunos"
              highlight
              features={[
                'Tudo do Basic',
                'Pagamento via PIX/cartão',
                'Slides IA + relatórios PDF',
                'Métricas IA vs humano',
                'Suporte prioritário',
              ]}
            />
            <PriceCard
              name="Enterprise"
              price="Sob consulta"
              desc="Acima de 2.000 alunos"
              features={[
                'Tudo do Pro',
                'Integração com sistema acadêmico',
                'SLA garantido',
                'Customização da Billie',
                'Suporte dedicado',
              ]}
            />
          </div>
        </div>
      </section>

      {/* ─── DEPOIMENTOS ─────────────────────────────── */}
      <section className="py-16 px-6 bg-white">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-3">
            O que dizem nossos clientes
          </h2>
          <p className="text-center text-gray-600 mb-12">
            Instituições que já estão economizando com o IGS.
          </p>
          <div className="grid md:grid-cols-3 gap-6">
            <TestimonialCard
              quote="Em 3 semanas a Billie já resolvia 80% dos chamados sozinha. Minha equipe finalmente tem tempo pra trabalhar."
              name="Patrícia Souza"
              role="Coordenadora Administrativa"
              school="Faculdade Anchieta"
              stars={5}
            />
            <TestimonialCard
              quote="Aluno me ligou às 23h pra perguntar nota. Eu falei 'vai no WhatsApp'. Ele voltou em 10 segundos com a resposta. Nunca mais me ligou fora do horário."
              name="Carlos Mendes"
              role="Diretor Acadêmico"
              school="CETEP Educação"
              stars={5}
            />
            <TestimonialCard
              quote="O setup foi mais fácil do que eu imaginava. Em 1 hora estávamos ativos. O suporte ajudou em tudo."
              name="Renata Lima"
              role="TI / Sistemas"
              school="Instituto Técnico BR"
              stars={5}
            />
          </div>
        </div>
      </section>

      {/* ─── FAQ ─────────────────────────────────────── */}
      <section className="py-16 px-6 bg-gray-50">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-10">
            Perguntas frequentes
          </h2>
          <div className="space-y-4">
            <FaqItem
              q="Quanto tempo leva pra começar a usar?"
              a="Cerca de 1 hora. Você cria sua conta, importa o CSV de alunos, conecta o WhatsApp Business API (temos tutorial passo a passo) e a Billie já está atendendo."
            />
            <FaqItem
              q="A IA pode inventar respostas?"
              a="Não. A Billie usa o padrão RAG: ela só responde com dados que estão no seu banco. Quando não tem informação, ela diz isso claramente e oferece transferir pra um humano."
            />
            <FaqItem
              q="Funciona com o sistema acadêmico que eu já uso?"
              a="No plano Enterprise, integramos via API ou importação CSV automática. Para Basic/Pro, você importa os dados manualmente uma vez por mês."
            />
            <FaqItem
              q="E se a IA falhar?"
              a="Temos fallback automático: se um provider de IA cair, tentamos outro. Se todos falharem, a Billie responde com templates baseados em palavras-chave e transfere pra atendente humano."
            />
            <FaqItem
              q="Preciso de WhatsApp Business já configurado?"
              a="Não. Te ajudamos a configurar o WhatsApp Business API da Meta. É gratuito até 1.000 conversas/mês."
            />
            <FaqItem
              q="Os dados ficam onde?"
              a="Em servidores brasileiros (compliance LGPD). Cada escola tem seu próprio espaço isolado. CPFs e tokens são criptografados."
            />
          </div>
        </div>
      </section>

      {/* ─── CTA FINAL ─────────────────────────────────── */}
      <section className="py-16 px-6 bg-gradient-to-r from-blue-600 to-indigo-700 text-white">
        <div className="max-w-3xl mx-auto text-center">
          <Zap className="mx-auto mb-4 text-yellow-300" size={48} />
          <h2 className="text-3xl md:text-4xl font-bold mb-4">
            Pronto pra liberar sua equipe?
          </h2>
          <p className="text-blue-100 mb-8 text-lg">
            Agende uma demonstração gratuita de 30 minutos. Te mostramos a Billie
            atendendo ao vivo no seu próprio WhatsApp.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <a
              href="mailto:contato@igs.com.br?subject=Quero agendar uma demo"
              className="bg-white text-blue-700 px-6 py-3 rounded-lg font-semibold hover:bg-blue-50 inline-flex items-center justify-center gap-2"
            >
              Agendar demonstração <ArrowRight size={18} />
            </a>
            <Link
              to="/login"
              className="border-2 border-white/40 px-6 py-3 rounded-lg font-semibold hover:bg-white/10 inline-flex items-center justify-center gap-2"
            >
              Ver demo agora
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────────────────────────────────────

function Bot() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
      <path d="M12 2a2 2 0 0 1 2 2v1h2a4 4 0 0 1 4 4v8a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4V9a4 4 0 0 1 4-4h2V4a2 2 0 0 1 2-2zM9 12a1 1 0 1 0 0 2 1 1 0 0 0 0-2zm6 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2z" />
    </svg>
  )
}

function ChatBubble({
  side,
  text,
  time,
}: {
  side: 'left' | 'right'
  text: string
  time: string
}) {
  const isLeft = side === 'left'
  return (
    <div className={`flex ${isLeft ? 'justify-start' : 'justify-end'}`}>
      <div
        className={`max-w-[85%] px-3 py-2 rounded-lg text-xs leading-relaxed whitespace-pre-line ${
          isLeft ? 'bg-gray-100 text-gray-800' : 'bg-emerald-100 text-emerald-900'
        }`}
      >
        <p>{text}</p>
        <p className="text-[10px] text-gray-500 mt-1 text-right">{time}</p>
      </div>
    </div>
  )
}

function ProblemCard({
  icon: Icon,
  title,
  before,
  after,
}: {
  icon: typeof MessageSquare
  title: string
  before: string
  after: string
}) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <Icon className="text-blue-600 mb-3" size={24} />
      <h3 className="font-bold text-gray-900 mb-3">{title}</h3>
      <p className="text-sm text-red-600 line-through mb-1">{before}</p>
      <p className="text-sm text-green-700 font-medium">→ {after}</p>
    </div>
  )
}

function FeatureCard({
  icon: Icon,
  title,
  items,
}: {
  icon: typeof MessageSquare
  title: string
  items: string[]
}) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <div className="flex items-center gap-3 mb-4">
        <div className="bg-blue-100 p-2 rounded-lg">
          <Icon className="text-blue-600" size={20} />
        </div>
        <h3 className="font-bold text-gray-900">{title}</h3>
      </div>
      <ul className="space-y-2">
        {items.map((item) => (
          <li key={item} className="flex items-start gap-2 text-sm text-gray-700">
            <CheckCircle2 className="text-green-600 flex-shrink-0 mt-0.5" size={16} />
            {item}
          </li>
        ))}
      </ul>
    </div>
  )
}

function RoiCard({ value, label, sub }: { value: string; label: string; sub: string }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6 text-center">
      <p className="text-3xl font-bold text-blue-600 mb-1">{value}</p>
      <p className="text-sm font-semibold text-gray-900">{label}</p>
      <p className="text-xs text-gray-500 mt-1">{sub}</p>
    </div>
  )
}

function StepCard({ num, title, desc }: { num: number; title: string; desc: string }) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <div className="bg-blue-600 text-white w-9 h-9 rounded-full flex items-center justify-center font-bold mb-3">
        {num}
      </div>
      <h3 className="font-bold text-gray-900 mb-1">{title}</h3>
      <p className="text-sm text-gray-600">{desc}</p>
    </div>
  )
}

function SecBullet({ text }: { text: string }) {
  return (
    <li className="flex items-start gap-3 text-gray-700">
      <CheckCircle2 className="text-green-600 flex-shrink-0 mt-0.5" size={18} />
      <span>{text}</span>
    </li>
  )
}

function Badge({ text }: { text: string }) {
  return (
    <div className="bg-white border border-blue-200 rounded-lg px-3 py-2 text-center font-medium text-blue-900">
      {text}
    </div>
  )
}

function PriceCard({
  name,
  price,
  desc,
  features,
  highlight,
}: {
  name: string
  price: string
  desc: string
  features: string[]
  highlight?: boolean
}) {
  return (
    <div
      className={`rounded-2xl p-6 ${
        highlight
          ? 'bg-blue-600 text-white border-2 border-blue-600 shadow-xl scale-105'
          : 'bg-white border border-gray-200'
      }`}
    >
      {highlight && (
        <p className="text-xs uppercase tracking-wide font-bold mb-2 text-yellow-300">
          Mais escolhido
        </p>
      )}
      <h3 className="text-xl font-bold mb-1">{name}</h3>
      <p className={`text-sm mb-4 ${highlight ? 'text-blue-100' : 'text-gray-500'}`}>
        {desc}
      </p>
      <p className="text-3xl font-bold mb-1">{price}</p>
      <p className={`text-xs mb-6 ${highlight ? 'text-blue-100' : 'text-gray-500'}`}>
        por mês
      </p>
      <ul className="space-y-2 mb-6">
        {features.map((f) => (
          <li key={f} className="flex items-start gap-2 text-sm">
            <CheckCircle2
              className={`flex-shrink-0 mt-0.5 ${highlight ? 'text-yellow-300' : 'text-green-600'}`}
              size={16}
            />
            {f}
          </li>
        ))}
      </ul>
      <a
        href="mailto:contato@igs.com.br"
        className={`block text-center py-2.5 rounded-lg font-semibold ${
          highlight
            ? 'bg-white text-blue-700 hover:bg-blue-50'
            : 'bg-blue-600 text-white hover:bg-blue-700'
        }`}
      >
        Começar
      </a>
    </div>
  )
}

function FaqItem({ q, a }: { q: string; a: string }) {
  return (
    <details className="border border-gray-200 rounded-lg p-4 group">
      <summary className="flex items-center justify-between cursor-pointer font-semibold text-gray-900">
        <span className="flex items-center gap-2">
          <HelpCircle className="text-blue-600 flex-shrink-0" size={18} />
          {q}
        </span>
        <span className="text-blue-600 group-open:rotate-180 transition">▾</span>
      </summary>
      <p className="mt-3 text-sm text-gray-600 leading-relaxed pl-7">{a}</p>
    </details>
  )
}

function TestimonialCard({
  quote,
  name,
  role,
  school,
  stars,
}: {
  quote: string
  name: string
  role: string
  school: string
  stars: number
}) {
  return (
    <div className="bg-gray-50 border border-gray-200 rounded-xl p-6 flex flex-col gap-4">
      <div className="flex gap-0.5">
        {Array.from({ length: stars }).map((_, i) => (
          <span key={i} className="text-yellow-400 text-lg">★</span>
        ))}
      </div>
      <p className="text-gray-700 text-sm leading-relaxed flex-1">"{quote}"</p>
      <div>
        <p className="font-semibold text-gray-900 text-sm">{name}</p>
        <p className="text-xs text-gray-500">{role} · {school}</p>
      </div>
    </div>
  )
}
