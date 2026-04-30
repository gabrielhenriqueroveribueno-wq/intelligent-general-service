import { Link } from 'react-router-dom'
import { CheckCircle2, ArrowRight, MessageSquare, Users, BarChart3, Zap, Shield, Headphones } from 'lucide-react'
import clsx from 'clsx'

const plans = [
  {
    id: 'starter',
    name: 'Starter',
    price: 297,
    period: '/mês',
    description: 'Para instituições que estão começando com atendimento automatizado.',
    highlight: false,
    cta: 'Começar grátis',
    ctaTo: '/signup',
    features: [
      'Até 500 alunos ativos',
      'Bot WhatsApp 24/7 (Billie)',
      'Notas, boletos e frequência',
      'Painel admin completo',
      'Tickets e SLA básico',
      'Relatórios semanais por email',
      'Base de conhecimento',
      '1 número de WhatsApp',
      'Suporte por email',
    ],
    missing: [
      'Funcionários & holerite',
      'Múltiplos canais',
      'API de integração',
    ],
  },
  {
    id: 'pro',
    name: 'Pro',
    price: 497,
    period: '/mês',
    description: 'Para instituições que precisam de atendimento completo para alunos e funcionários.',
    highlight: true,
    cta: 'Começar grátis',
    ctaTo: '/signup',
    badge: 'Mais popular',
    features: [
      'Alunos ilimitados',
      'Bot WhatsApp 24/7 (Billie)',
      'Notas, boletos e frequência',
      'Funcionários, holerite e férias',
      'Painel admin completo',
      'Tickets e SLA avançado',
      'Relatórios semanais e mensais',
      'Base de conhecimento ilimitada',
      'Alertas de evasão com IA',
      'Dashboard de métricas',
      'Até 3 números de WhatsApp',
      'Suporte prioritário',
    ],
    missing: [],
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: null,
    period: '',
    description: 'Para redes de ensino e grandes instituições com necessidades customizadas.',
    highlight: false,
    cta: 'Falar com vendas',
    ctaTo: 'mailto:contato@igs.com.br?subject=Enterprise IGS',
    ctaExternal: true,
    features: [
      'Tudo do plano Pro',
      'Múltiplas unidades / CNPJ',
      'Integração com sistemas legados (API)',
      'SLA customizado com suporte 24/7',
      'Treinamento e onboarding dedicado',
      'Deploy on-premise disponível',
      'Relatórios customizados',
      'Gerente de conta dedicado',
    ],
    missing: [],
  },
]

const faqs = [
  {
    q: 'Preciso de cartão de crédito para o trial?',
    a: 'Não. O trial de 14 dias é gratuito e não exige dados de pagamento. Você só paga se decidir continuar.',
  },
  {
    q: 'Como funciona o limite de alunos?',
    a: 'Contamos alunos com status "ativo" no sistema. Alunos formados ou evadidos não contam.',
  },
  {
    q: 'Posso mudar de plano depois?',
    a: 'Sim, a qualquer momento. O upgrade é imediato e o downgrade acontece no próximo ciclo de cobrança.',
  },
  {
    q: 'Qual WhatsApp posso usar?',
    a: 'A Billie usa a Meta Business API (WhatsApp Business oficial). Você precisa de um número verificado pela Meta.',
  },
  {
    q: 'Como é feita a cobrança?',
    a: 'Cobrança mensal via PIX, cartão de crédito ou boleto, processada pelo Mercado Pago.',
  },
]

export default function Pricing() {
  return (
    <div className="bg-white">
      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 pt-16 pb-8 text-center">
        <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
          Preços simples e transparentes
        </h1>
        <p className="text-lg text-gray-500 max-w-2xl mx-auto">
          Comece grátis por 14 dias. Sem cartão de crédito. Cancele quando quiser.
        </p>
      </section>

      {/* Plans */}
      <section className="max-w-6xl mx-auto px-6 py-8">
        <div className="grid md:grid-cols-3 gap-6 items-start">
          {plans.map((plan) => (
            <div
              key={plan.id}
              className={clsx(
                'rounded-2xl border p-6 flex flex-col',
                plan.highlight
                  ? 'border-blue-500 shadow-xl shadow-blue-100 ring-1 ring-blue-500'
                  : 'border-gray-200',
              )}
            >
              {plan.badge && (
                <div className="inline-flex self-start bg-blue-600 text-white text-xs font-semibold px-2.5 py-1 rounded-full mb-3">
                  {plan.badge}
                </div>
              )}
              <h2 className="text-xl font-bold text-gray-900">{plan.name}</h2>
              <p className="text-sm text-gray-500 mt-1 mb-4">{plan.description}</p>

              <div className="mb-6">
                {plan.price !== null ? (
                  <div className="flex items-end gap-1">
                    <span className="text-4xl font-bold text-gray-900">
                      R$ {plan.price}
                    </span>
                    <span className="text-gray-500 mb-1">{plan.period}</span>
                  </div>
                ) : (
                  <p className="text-2xl font-bold text-gray-900">Personalizado</p>
                )}
              </div>

              {plan.ctaExternal ? (
                <a
                  href={plan.ctaTo}
                  className={clsx(
                    'w-full py-3 rounded-lg font-semibold text-center mb-6 inline-flex items-center justify-center gap-2',
                    plan.highlight
                      ? 'bg-blue-600 text-white hover:bg-blue-700'
                      : 'border border-gray-300 text-gray-700 hover:bg-gray-50',
                  )}
                >
                  {plan.cta} <ArrowRight size={16} />
                </a>
              ) : (
                <Link
                  to={plan.ctaTo}
                  className={clsx(
                    'w-full py-3 rounded-lg font-semibold text-center mb-6 inline-flex items-center justify-center gap-2',
                    plan.highlight
                      ? 'bg-blue-600 text-white hover:bg-blue-700'
                      : 'border border-gray-300 text-gray-700 hover:bg-gray-50',
                  )}
                >
                  {plan.cta} <ArrowRight size={16} />
                </Link>
              )}

              <ul className="space-y-2 flex-1">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-gray-700">
                    <CheckCircle2 size={16} className="text-green-500 shrink-0 mt-0.5" />
                    {f}
                  </li>
                ))}
                {plan.missing.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-gray-400 line-through">
                    <CheckCircle2 size={16} className="text-gray-300 shrink-0 mt-0.5" />
                    {f}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      {/* Value props */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <h2 className="text-2xl font-bold text-gray-900 text-center mb-10">
          Todos os planos incluem
        </h2>
        <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-6">
          {[
            { icon: MessageSquare, title: 'WhatsApp 24/7', desc: 'A Billie responde em segundos, mesmo de madrugada.' },
            { icon: Zap, title: 'Setup em 1 hora', desc: 'Importe alunos via CSV e configure o bot rapidamente.' },
            { icon: Shield, title: 'LGPD compliance', desc: 'Dados armazenados no Brasil, criptografados, com DPA.' },
            { icon: BarChart3, title: 'Relatórios automáticos', desc: 'Relatórios semanais chegam no seu email toda segunda.' },
            { icon: Users, title: 'Multi-tenancy', desc: 'Cada unidade tem painel isolado com dados independentes.' },
            { icon: Headphones, title: 'Suporte em português', desc: 'Time brasileiro disponível para ajudar na sua implantação.' },
          ].map(({ icon: Icon, title, desc }) => (
            <div key={title} className="flex gap-4">
              <div className="bg-blue-50 p-2.5 rounded-lg h-fit">
                <Icon size={20} className="text-blue-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 text-sm">{title}</h3>
                <p className="text-sm text-gray-500 mt-0.5">{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* FAQ */}
      <section className="bg-gray-50 py-16">
        <div className="max-w-3xl mx-auto px-6">
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-8">
            Perguntas frequentes
          </h2>
          <div className="space-y-4">
            {faqs.map(({ q, a }) => (
              <div key={q} className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="font-semibold text-gray-900 mb-2">{q}</h3>
                <p className="text-sm text-gray-600">{a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-6xl mx-auto px-6 py-16 text-center">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          Pronto para começar?
        </h2>
        <p className="text-gray-500 mb-8">14 dias grátis. Sem cartão. Cancele quando quiser.</p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            to="/signup"
            className="bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 inline-flex items-center gap-2"
          >
            Criar conta grátis <ArrowRight size={18} />
          </Link>
          <Link
            to="/demo"
            className="border border-gray-300 text-gray-700 px-8 py-3 rounded-lg font-semibold hover:bg-gray-50"
          >
            Ver demonstração
          </Link>
        </div>
      </section>
    </div>
  )
}
