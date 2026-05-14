import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  ArrowRight,
  Bot,
  Building2,
  CheckCircle2,
  Clock,
  Database,
  DollarSign,
  GraduationCap,
  Heart,
  Lock,
  MessageSquare,
  Rocket,
  Shield,
  Sparkles,
  Target,
  TrendingUp,
  Users,
  Wallet,
  X,
  Zap,
} from 'lucide-react'

/**
 * Pitch Deck — apresentação comercial/investor-style.
 *
 * Diferente da /presentation (que puxa métricas reais do tenant), este pitch
 * é uma narrativa de vendas com problema → solução → tração → ask.
 *
 * Navegação: ← → Espaço PageUp/Down · Esc para sair · Home/End extremos.
 */

interface Slide {
  bg: string
  content: React.ReactNode
  title?: string
}

export default function PitchDeck() {
  const navigate = useNavigate()
  const [slide, setSlide] = useState(0)

  const slides = buildSlides()

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown')
        setSlide(s => Math.min(s + 1, slides.length - 1))
      else if (e.key === 'ArrowLeft' || e.key === 'PageUp')
        setSlide(s => Math.max(s - 1, 0))
      else if (e.key === 'Escape') navigate(-1)
      else if (e.key === 'Home') setSlide(0)
      else if (e.key === 'End') setSlide(slides.length - 1)
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [slides.length, navigate])

  useEffect(() => {
    if (document.fullscreenEnabled && !document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch(() => {})
    }
    return () => {
      if (document.fullscreenElement) document.exitFullscreen().catch(() => {})
    }
  }, [])

  const current = slides[slide] ?? slides[0]

  return (
    <div className={`fixed inset-0 z-50 flex items-center justify-center overflow-hidden ${current.bg}`}>
      <div className="w-full h-full flex items-center justify-center px-8 animate-fade-in" key={slide}>
        {current.content}
      </div>

      <div className="absolute top-4 right-4 flex items-center gap-2">
        <span className="text-white/70 text-sm font-medium px-3 py-1 rounded bg-black/20 backdrop-blur">
          {slide + 1} / {slides.length}
        </span>
        <button
          onClick={() => navigate(-1)}
          className="p-2 rounded-lg bg-white/10 backdrop-blur text-white hover:bg-white/20 transition-colors"
          aria-label="Sair (Esc)"
        >
          <X size={20} />
        </button>
      </div>

      <button
        onClick={() => setSlide(s => Math.max(s - 1, 0))}
        disabled={slide === 0}
        className="absolute left-4 top-1/2 -translate-y-1/2 p-3 rounded-full bg-white/10 backdrop-blur text-white hover:bg-white/20 transition-all disabled:opacity-20"
      >
        <ArrowLeft size={24} />
      </button>
      <button
        onClick={() => setSlide(s => Math.min(s + 1, slides.length - 1))}
        disabled={slide === slides.length - 1}
        className="absolute right-4 top-1/2 -translate-y-1/2 p-3 rounded-full bg-white/10 backdrop-blur text-white hover:bg-white/20 transition-all disabled:opacity-20"
      >
        <ArrowRight size={24} />
      </button>

      <div className="absolute bottom-0 left-0 right-0 h-1 bg-white/10">
        <div
          className="h-full bg-white/60 transition-all duration-500"
          style={{ width: `${((slide + 1) / slides.length) * 100}%` }}
        />
      </div>

      {current.title && (
        <div className="absolute bottom-6 left-8 text-white/40 text-xs uppercase tracking-widest font-semibold">
          {current.title}
        </div>
      )}

      {slide === 0 && (
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 text-white/60 text-sm bg-black/20 backdrop-blur px-4 py-2 rounded-full animate-pulse">
          ← → para navegar · Esc para sair
        </div>
      )}
    </div>
  )
}

function buildSlides(): Slide[] {
  return [
    // ─── 1: Capa ──────────────────────────────────────────────────────
    {
      bg: 'bg-gradient-to-br from-blue-700 via-indigo-700 to-purple-800',
      content: (
        <div className="text-center text-white max-w-5xl">
          <div className="inline-flex items-center justify-center w-32 h-32 bg-white/20 backdrop-blur rounded-3xl mb-8 shadow-2xl">
            <Bot size={64} />
          </div>
          <h1 className="text-8xl md:text-9xl font-extrabold tracking-tight mb-6">IGS</h1>
          <p className="text-3xl md:text-4xl font-light text-white/90 mb-4">
            Intelligent General Service
          </p>
          <p className="text-xl md:text-2xl text-white/70 max-w-3xl mx-auto leading-relaxed">
            A primeira plataforma de IA que resolve o atendimento universitário
            <br />
            de ponta-a-ponta, em tempo real, via WhatsApp.
          </p>
          <div className="mt-12 inline-flex items-center gap-2 text-white/60 text-sm">
            <Sparkles size={14} /> Pitch Deck · 2026
          </div>
        </div>
      ),
    },

    // ─── 2: A dor ────────────────────────────────────────────────────
    {
      bg: 'bg-gradient-to-br from-slate-900 via-slate-800 to-black',
      title: 'O Problema',
      content: (
        <div className="text-center text-white max-w-5xl">
          <p className="text-sm uppercase tracking-widest text-orange-400 font-bold mb-6">
            O problema
          </p>
          <p className="text-6xl md:text-8xl font-bold leading-tight mb-10">
            Secretarias afogadas em
            <br />
            <span className="text-orange-400">200+ WhatsApps/dia</span>
          </p>
          <div className="grid grid-cols-3 gap-8 mt-12 text-left">
            <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur">
              <div className="text-4xl font-bold text-orange-400 mb-2">62%</div>
              <p className="text-sm text-white/70">das mensagens chegam fora do horário comercial</p>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur">
              <div className="text-4xl font-bold text-orange-400 mb-2">85%</div>
              <p className="text-sm text-white/70">são perguntas repetitivas (boleto, nota, frequência)</p>
            </div>
            <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur">
              <div className="text-4xl font-bold text-orange-400 mb-2">4h+</div>
              <p className="text-sm text-white/70">é o tempo médio de resposta humana</p>
            </div>
          </div>
        </div>
      ),
    },

    // ─── 3: Impacto da dor ───────────────────────────────────────────
    {
      bg: 'bg-gradient-to-br from-red-900 via-red-800 to-black',
      title: 'Consequências',
      content: (
        <div className="text-center text-white max-w-5xl">
          <p className="text-sm uppercase tracking-widest text-red-300 font-bold mb-6">
            E o resultado é
          </p>
          <p className="text-5xl md:text-7xl font-bold leading-tight mb-10">
            Alunos frustrados,
            <br />
            <span className="text-red-300">evasão crescente,</span>
            <br />
            equipes esgotadas.
          </p>
          <p className="text-2xl text-white/80 font-light mt-12 max-w-3xl mx-auto">
            E ninguém tem ferramenta dedicada para resolver isso —
            só CRM genérico e bots que &quot;não entendem&quot;.
          </p>
        </div>
      ),
    },

    // ─── 4: A solução ───────────────────────────────────────────────
    {
      bg: 'bg-gradient-to-br from-emerald-600 via-green-600 to-teal-700',
      title: 'A Solução',
      content: (
        <div className="text-center text-white max-w-5xl">
          <p className="text-sm uppercase tracking-widest text-emerald-200 font-bold mb-6">
            A solução
          </p>
          <p className="text-6xl md:text-8xl font-bold leading-tight mb-6">
            A Billie responde
            <br />
            <span className="text-yellow-300">em 2 segundos.</span>
          </p>
          <p className="text-2xl text-white/90 font-light mt-8 max-w-3xl mx-auto leading-relaxed">
            Bot WhatsApp com IA que <strong>entende contexto, consulta dados reais</strong>
            <br />
            e <strong>resolve ações</strong> sem invenção.
          </p>
          <div className="mt-12 grid grid-cols-3 gap-4 text-sm">
            {[
              '40+ intenções classificadas',
              'RAG com dados da instituição',
              'Verificação de identidade',
            ].map(f => (
              <div key={f} className="bg-white/10 backdrop-blur rounded-xl py-3 px-4 border border-white/20">
                <CheckCircle2 size={18} className="inline mr-2" />
                {f}
              </div>
            ))}
          </div>
        </div>
      ),
    },

    // ─── 5: Como funciona ──────────────────────────────────────────
    {
      bg: 'bg-gradient-to-br from-blue-600 via-indigo-700 to-violet-800',
      title: 'Como funciona',
      content: (
        <div className="text-white max-w-6xl w-full">
          <p className="text-center text-sm uppercase tracking-widest text-white/70 font-bold mb-4">
            Em 4 passos
          </p>
          <h2 className="text-center text-5xl md:text-6xl font-bold mb-16">Pipeline da Billie</h2>
          <div className="grid grid-cols-4 gap-6">
            {[
              { n: 1, icon: MessageSquare, title: 'Recebe', desc: 'WhatsApp → Webhook seguro (HMAC)' },
              { n: 2, icon: Sparkles, title: 'Classifica', desc: 'IA identifica 1 de 40+ intenções' },
              { n: 3, icon: Database, title: 'Consulta', desc: 'Dados reais da instituição (RAG)' },
              { n: 4, icon: Zap, title: 'Responde / Age', desc: 'Texto + ação executada (PIX, ticket…)' },
            ].map(({ n, icon: Icon, title, desc }) => (
              <div key={n} className="text-center">
                <div className="relative inline-flex items-center justify-center w-20 h-20 bg-white/15 backdrop-blur rounded-2xl mb-4 border border-white/20">
                  <Icon size={32} />
                  <span className="absolute -top-2 -right-2 w-7 h-7 bg-yellow-300 text-blue-900 rounded-full text-sm font-bold flex items-center justify-center">
                    {n}
                  </span>
                </div>
                <h3 className="font-bold text-lg mb-1">{title}</h3>
                <p className="text-sm text-white/70">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      ),
    },

    // ─── 6: O que faz (capacidades) ────────────────────────────────
    {
      bg: 'bg-gradient-to-br from-slate-800 to-slate-900',
      title: 'Capacidades',
      content: (
        <div className="text-white max-w-6xl">
          <p className="text-center text-sm uppercase tracking-widest text-white/70 font-bold mb-4">
            Não é só FAQ
          </p>
          <h2 className="text-center text-5xl md:text-6xl font-bold mb-12">A Billie executa.</h2>
          <div className="grid grid-cols-3 gap-4 text-sm">
            {[
              { icon: GraduationCap, t: 'Notas & frequência', d: 'consulta em tempo real' },
              { icon: Wallet, t: 'Boletos & PIX', d: 'gera, envia 2ª via, negocia' },
              { icon: Users, t: 'Holerite & férias', d: 'RH self-service para funcionários' },
              { icon: Clock, t: 'Agendamentos', d: 'marca atendimento na secretaria' },
              { icon: Target, t: 'Análise de evasão', d: 'IA prevê risco antes do aluno sair' },
              { icon: Heart, t: 'Sentimento', d: 'detecta insatisfação e prioriza' },
              { icon: Building2, t: 'OCR de documentos', d: 'lê atestados, RG, declarações' },
              { icon: Bot, t: 'Tutor IA', d: 'tira dúvidas acadêmicas' },
              { icon: Shield, t: 'Tickets & SLA', d: 'escalonamento humano automático' },
            ].map(({ icon: Icon, t, d }) => (
              <div key={t} className="bg-white/5 border border-white/10 rounded-xl p-4 backdrop-blur">
                <div className="flex items-start gap-3">
                  <div className="bg-blue-500/20 p-2 rounded-lg">
                    <Icon size={20} className="text-blue-300" />
                  </div>
                  <div>
                    <h4 className="font-semibold mb-0.5">{t}</h4>
                    <p className="text-xs text-white/60">{d}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ),
    },

    // ─── 7: Demo / fluxo de conversa ────────────────────────────────
    {
      bg: 'bg-gradient-to-br from-green-600 via-emerald-700 to-teal-800',
      title: 'Conversa real',
      content: (
        <div className="text-white max-w-3xl">
          <p className="text-center text-sm uppercase tracking-widest text-emerald-200 font-bold mb-4">
            Aluno → Billie · em segundos
          </p>
          <div className="bg-white/95 rounded-3xl shadow-2xl overflow-hidden">
            <div className="bg-green-700 px-4 py-3 flex items-center gap-3">
              <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center">
                <Bot size={22} className="text-green-700" />
              </div>
              <div>
                <p className="text-white font-semibold leading-tight">Billie · IGS</p>
                <p className="text-green-100 text-xs">online · responde em 2s</p>
              </div>
            </div>
            <div className="p-5 space-y-3 bg-[#e5ddd5]">
              <Bubble side="left">
                Oi! Sou a Billie 👋 Me diga seu RA pra continuar.
              </Bubble>
              <Bubble side="right">RA 2024110453</Bubble>
              <Bubble side="left">
                Oi, Marcos! Como posso te ajudar hoje?
              </Bubble>
              <Bubble side="right">2ª via do boleto de março, por favor</Bubble>
              <Bubble side="left">
                Encontrei aqui ✅<br />
                <strong>Março/2026:</strong> R$ 847,00 · vence 10/03<br />
                <br />
                Posso enviar o PIX agora?
              </Bubble>
              <Bubble side="right">Sim, manda o PIX</Bubble>
              <Bubble side="left">
                Pronto! 📲<br />
                <code className="text-xs">00020126360014BR.GOV.BCB.PIX...</code>
                <br />
                Cole no app do seu banco. Qualquer coisa, me avise!
              </Bubble>
            </div>
          </div>
          <p className="text-center text-white/80 text-sm mt-4">
            Tempo total: 11 segundos · 0 humanos envolvidos
          </p>
        </div>
      ),
    },

    // ─── 8: Mercado (TAM) ───────────────────────────────────────────
    {
      bg: 'bg-gradient-to-br from-violet-700 via-purple-700 to-fuchsia-800',
      title: 'Mercado',
      content: (
        <div className="text-white max-w-5xl">
          <p className="text-center text-sm uppercase tracking-widest text-purple-200 font-bold mb-4">
            Tamanho do mercado
          </p>
          <h2 className="text-center text-5xl md:text-6xl font-bold mb-12">Brasil tem fome de IA</h2>
          <div className="grid grid-cols-3 gap-6">
            <MarketCard
              n="2.500+"
              label="instituições de ensino superior privadas"
              footnote="Censo MEC/INEP"
            />
            <MarketCard
              n="42.500+"
              label="escolas privadas (ensino básico)"
              footnote="Censo Escolar 2024"
            />
            <MarketCard
              n="R$ 7,2bi"
              label="movimentados em ed-tech BR/ano"
              footnote="ABED 2025"
            />
          </div>
          <div className="mt-12 bg-white/10 backdrop-blur rounded-2xl p-8 border border-white/20 text-center">
            <p className="text-white/80 text-sm mb-2">Mercado endereçável anual</p>
            <p className="text-5xl font-bold">R$ 178M / ano</p>
            <p className="text-white/60 text-sm mt-2">
              ICP: 5.000 instituições · ticket médio R$ 497/mês · ARR potencial
            </p>
          </div>
        </div>
      ),
    },

    // ─── 9: Produto (Stack técnica) ────────────────────────────────
    {
      bg: 'bg-gradient-to-br from-gray-900 to-slate-950',
      title: 'Produto',
      content: (
        <div className="text-white max-w-5xl">
          <p className="text-center text-sm uppercase tracking-widest text-blue-300 font-bold mb-4">
            Tecnologia
          </p>
          <h2 className="text-center text-5xl md:text-6xl font-bold mb-12">
            Built for scale, day 1
          </h2>
          <div className="grid grid-cols-2 gap-8 text-sm">
            <TechBlock title="Backend & IA">
              <Tech name="FastAPI + Python 3.12" />
              <Tech name="PostgreSQL 16 com Row-Level Security" />
              <Tech name="Redis 7 + Celery (async tasks)" />
              <Tech name="Multi-provider IA: Groq · Gemini · Claude" />
              <Tech name="RAG sem alucinação (resposta = dados reais)" />
            </TechBlock>
            <TechBlock title="Frontend & UX">
              <Tech name="React 18 + TypeScript + Vite" />
              <Tech name="PWA installable + offline-first" />
              <Tech name="WebSocket para conversas em tempo real" />
              <Tech name="Multi-tenant isolation no painel" />
              <Tech name="Push notifications nativas" />
            </TechBlock>
            <TechBlock title="Infra & DevOps">
              <Tech name="Docker Compose · Caddy SSL automático" />
              <Tech name="Prometheus · Grafana · Loki" />
              <Tech name="Backup diário · DLQ para falhas" />
              <Tech name="Health checks + auto-restart" />
              <Tech name="Deploy em &lt; 60 minutos" />
            </TechBlock>
            <TechBlock title="Segurança & LGPD">
              <Tech name="HMAC validation no webhook Meta" />
              <Tech name="JWT 15min access + 7d refresh" />
              <Tech name="Fernet (AES-128) para CPF e tokens" />
              <Tech name="LGPD: export, delete, anonimização auto" />
              <Tech name="Audit log com retenção 90d" />
            </TechBlock>
          </div>
        </div>
      ),
    },

    // ─── 10: Diferenciais ──────────────────────────────────────────
    {
      bg: 'bg-gradient-to-br from-amber-500 via-orange-600 to-red-700',
      title: 'Diferenciais',
      content: (
        <div className="text-white max-w-5xl">
          <p className="text-center text-sm uppercase tracking-widest text-amber-100 font-bold mb-4">
            Por que IGS &gt; concorrência
          </p>
          <h2 className="text-center text-5xl md:text-6xl font-bold mb-12">Não somos só FAQ.</h2>
          <div className="space-y-4">
            <Differentiator
              versus="Zenvia, Take, Tellbio"
              vsLabel="Bots genéricos de varejo"
              winner="IGS"
              winnerLabel="Especializado em ensino: 40+ intenções acadêmicas pré-treinadas"
            />
            <Differentiator
              versus="ChatGPT plugins"
              vsLabel="Alucina (inventa notas/boletos)"
              winner="IGS"
              winnerLabel="RAG: responde só com dados reais da instituição"
            />
            <Differentiator
              versus="CRM educacional (RD, Total Voice)"
              vsLabel="Foca em captação, não em vida acadêmica"
              winner="IGS"
              winnerLabel="Cobre toda a jornada: do candidato ao egresso"
            />
            <Differentiator
              versus="Bot interno desenvolvido"
              vsLabel="6-12 meses, R$ 200k+, mantém aceso"
              winner="IGS"
              winnerLabel="Setup em 1 hora, R$ 297/mês, sem dor de manutenção"
            />
          </div>
        </div>
      ),
    },

    // ─── 11: Modelo de negócio ─────────────────────────────────────
    {
      bg: 'bg-gradient-to-br from-blue-600 to-blue-900',
      title: 'Modelo',
      content: (
        <div className="text-white max-w-5xl w-full">
          <p className="text-center text-sm uppercase tracking-widest text-blue-200 font-bold mb-4">
            Modelo de negócio
          </p>
          <h2 className="text-center text-5xl md:text-6xl font-bold mb-12">
            SaaS recorrente · 3 planos
          </h2>
          <div className="grid grid-cols-3 gap-5">
            <PlanCard
              name="Starter"
              price="R$ 297"
              tagline="até 500 alunos"
              highlight={false}
              features={['Bot WhatsApp 24/7', 'Notas, boletos, frequência', '1 número', 'Email support']}
            />
            <PlanCard
              name="Pro"
              price="R$ 497"
              tagline="alunos ilimitados"
              highlight
              badge="Mais vendido"
              features={[
                'Tudo do Starter',
                'RH/holerite/férias',
                'Evasão IA',
                '3 números WhatsApp',
                'Suporte prioritário',
              ]}
            />
            <PlanCard
              name="Enterprise"
              price="Custom"
              tagline="redes & on-premise"
              highlight={false}
              features={['Multi-CNPJ', 'Integração legados', 'SLA 24/7', 'Gerente dedicado']}
            />
          </div>
          <p className="text-center text-white/70 text-sm mt-8">
            + Custos repassáveis transparentes (WhatsApp Meta · Mercado Pago) — sem markup
          </p>
        </div>
      ),
    },

    // ─── 12: ROI para o cliente ────────────────────────────────────
    {
      bg: 'bg-gradient-to-br from-emerald-600 via-green-700 to-emerald-900',
      title: 'ROI cliente',
      content: (
        <div className="text-white max-w-5xl">
          <p className="text-center text-sm uppercase tracking-widest text-emerald-200 font-bold mb-4">
            O que o cliente economiza
          </p>
          <h2 className="text-center text-5xl md:text-6xl font-bold mb-12">
            Pague R$ 497.<br />Economize R$ 5.000+/mês.
          </h2>
          <div className="grid grid-cols-2 gap-6">
            <div className="bg-white/10 backdrop-blur rounded-2xl p-8 border border-white/20">
              <p className="text-sm uppercase tracking-widest text-red-200 font-bold mb-3">
                Antes do IGS
              </p>
              <ul className="space-y-2 text-white/90">
                <li className="flex justify-between">
                  <span>2 atendentes dedicados</span>
                  <span className="font-bold">R$ 5.400</span>
                </li>
                <li className="flex justify-between">
                  <span>Treinamento e turnover</span>
                  <span className="font-bold">R$ 800</span>
                </li>
                <li className="flex justify-between">
                  <span>Ferramenta CRM</span>
                  <span className="font-bold">R$ 300</span>
                </li>
                <li className="border-t border-white/20 pt-3 mt-3 flex justify-between text-xl font-bold">
                  <span>Total/mês</span>
                  <span>R$ 6.500</span>
                </li>
              </ul>
            </div>
            <div className="bg-emerald-400/20 backdrop-blur rounded-2xl p-8 border border-emerald-300">
              <p className="text-sm uppercase tracking-widest text-emerald-100 font-bold mb-3">
                Com IGS Pro
              </p>
              <ul className="space-y-2 text-white/90">
                <li className="flex justify-between">
                  <span>Mensalidade IGS Pro</span>
                  <span className="font-bold">R$ 497</span>
                </li>
                <li className="flex justify-between">
                  <span>WhatsApp Meta (média)</span>
                  <span className="font-bold">R$ 200</span>
                </li>
                <li className="flex justify-between">
                  <span>1 atendente part-time (handoff)</span>
                  <span className="font-bold">R$ 1.300</span>
                </li>
                <li className="border-t border-white/20 pt-3 mt-3 flex justify-between text-xl font-bold">
                  <span>Total/mês</span>
                  <span>R$ 1.997</span>
                </li>
              </ul>
            </div>
          </div>
          <div className="mt-8 text-center">
            <p className="text-2xl text-white/80">
              Economia: <span className="font-bold text-yellow-300">R$ 4.503/mês</span> · payback em <span className="font-bold text-yellow-300">3 semanas</span>
            </p>
          </div>
        </div>
      ),
    },

    // ─── 13: Tração ────────────────────────────────────────────────
    {
      bg: 'bg-gradient-to-br from-indigo-700 via-blue-700 to-cyan-700',
      title: 'Tração',
      content: (
        <div className="text-white max-w-5xl">
          <p className="text-center text-sm uppercase tracking-widest text-cyan-200 font-bold mb-4">
            Onde estamos
          </p>
          <h2 className="text-center text-5xl md:text-6xl font-bold mb-12">Pronto pra escalar</h2>
          <div className="grid grid-cols-2 gap-6">
            <TractionCard icon={CheckCircle2} label="MVP em produção" value="100%" desc="Live em Oracle Cloud · domínio próprio · SSL automático" />
            <TractionCard icon={Rocket} label="Sprint 1 concluído" value="17 itens" desc="Auth, billing, onboarding, integrações, LGPD" />
            <TractionCard icon={MessageSquare} label="WhatsApp validado" value="end-to-end" desc="Conversas reais respondidas pela Billie" />
            <TractionCard icon={Building2} label="Primeiro piloto" value="em negociação" desc="UniAnchieta — implantação Q3/2026" />
          </div>
          <p className="text-center text-white/70 text-sm mt-8">
            Próximos: 5 escolas no piloto · validar churn · case study público
          </p>
        </div>
      ),
    },

    // ─── 14: Time ──────────────────────────────────────────────────
    {
      bg: 'bg-gradient-to-br from-slate-800 to-slate-950',
      title: 'Time',
      content: (
        <div className="text-white max-w-4xl text-center">
          <p className="text-sm uppercase tracking-widest text-white/70 font-bold mb-4">Time</p>
          <h2 className="text-5xl md:text-6xl font-bold mb-16">Quem está construindo</h2>
          <div className="inline-flex items-center justify-center w-32 h-32 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full mb-6 text-5xl font-bold">
            G
          </div>
          <h3 className="text-3xl font-bold mb-2">Gabriel Roveri</h3>
          <p className="text-xl text-white/70 mb-6">Founder · Full-stack · IA</p>
          <p className="text-lg text-white/60 max-w-2xl mx-auto leading-relaxed">
            Desenvolvedor com foco em sistemas distribuídos, infra cloud e
            integração de modelos de IA em produção. Construiu o IGS do zero —
            backend, frontend, deploy, monetização.
          </p>
          <div className="mt-12 text-sm text-white/50">
            Procuro: co-founder comercial (educação) · 1º dev fullstack júnior
          </div>
        </div>
      ),
    },

    // ─── 15: Roadmap ───────────────────────────────────────────────
    {
      bg: 'bg-gradient-to-br from-purple-700 via-pink-600 to-rose-700',
      title: 'Roadmap',
      content: (
        <div className="text-white max-w-5xl">
          <p className="text-center text-sm uppercase tracking-widest text-pink-200 font-bold mb-4">
            Próximos 12 meses
          </p>
          <h2 className="text-center text-5xl md:text-6xl font-bold mb-12">Roadmap</h2>
          <div className="space-y-4">
            <RoadmapItem
              q="Q2 2026"
              status="now"
              items={['Piloto UniAnchieta (1.500 alunos)', 'Onboarding self-service', 'Stripe (BR) como gateway alternativo']}
            />
            <RoadmapItem
              q="Q3 2026"
              status="next"
              items={['5 instituições pagantes', 'Conector TOTVS RM nativo', 'Voz: Billie atende WhatsApp por áudio']}
            />
            <RoadmapItem
              q="Q4 2026"
              status="next"
              items={['Marketplace de templates por nicho', 'App nativo iOS/Android para gestores', 'Insights preditivos com BI embarcado']}
            />
            <RoadmapItem
              q="Q1 2027"
              status="future"
              items={['Expansão LATAM (Espanhol)', 'Integração SAP / Oracle EBS', 'White-label para grupos educacionais']}
            />
          </div>
        </div>
      ),
    },

    // ─── 16: Ask ───────────────────────────────────────────────────
    {
      bg: 'bg-gradient-to-br from-yellow-400 via-orange-500 to-red-600',
      title: 'Ask',
      content: (
        <div className="text-white max-w-4xl text-center">
          <p className="text-sm uppercase tracking-widest text-yellow-100 font-bold mb-6">O ask</p>
          <h2 className="text-6xl md:text-8xl font-bold mb-12">R$ 350k</h2>
          <p className="text-3xl text-white/90 font-light mb-12 leading-relaxed">
            Seed para validar escalabilidade comercial
            <br />
            e fechar os primeiros 30 contratos.
          </p>
          <div className="grid grid-cols-3 gap-4 text-left">
            <UseOfFunds pct="40%" label="Vendas & marketing" detail="ICP focado: faculdades particulares regionais" />
            <UseOfFunds pct="40%" label="Produto" detail="1 dev pleno · 6 meses de roadmap" />
            <UseOfFunds pct="20%" label="Operação" detail="Infra · jurídico · contabilidade" />
          </div>
          <p className="mt-12 text-white/80">
            Em troca: equity proporcional · diluição ≤ 15% · valuation pre-money R$ 2M
          </p>
        </div>
      ),
    },

    // ─── 17: CTA ──────────────────────────────────────────────────
    {
      bg: 'bg-gradient-to-br from-blue-700 via-indigo-700 to-purple-800',
      content: (
        <div className="text-center text-white max-w-4xl">
          <Sparkles size={64} className="mx-auto mb-8 text-yellow-300" />
          <h2 className="text-6xl md:text-8xl font-bold mb-8">Vamos conversar?</h2>
          <p className="text-2xl text-white/90 font-light mb-12">
            Demo ao vivo · case study · proposta sob medida
          </p>
          <div className="space-y-3 text-lg">
            <p>
              <strong>Email:</strong> gabriel.henrique.roveri.bueno@gmail.com
            </p>
            <p>
              <strong>Demo:</strong> igs-anchieta.duckdns.org
            </p>
          </div>
          <p className="mt-16 text-white/50 text-sm">
            Obrigado · IGS · 2026
          </p>
        </div>
      ),
    },
  ]
}

// ─── Componentes auxiliares ─────────────────────────────────────────

function Bubble({ side, children }: { side: 'left' | 'right'; children: React.ReactNode }) {
  return (
    <div className={`flex ${side === 'right' ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm shadow ${
          side === 'right' ? 'bg-green-100 text-gray-900 rounded-br-md' : 'bg-white text-gray-900 rounded-bl-md'
        }`}
      >
        {children}
      </div>
    </div>
  )
}

function MarketCard({ n, label, footnote }: { n: string; label: string; footnote: string }) {
  return (
    <div className="bg-white/10 backdrop-blur rounded-2xl p-6 border border-white/20 text-center">
      <p className="text-5xl font-bold mb-2">{n}</p>
      <p className="text-sm text-white/80 leading-snug">{label}</p>
      <p className="text-xs text-white/50 mt-3">{footnote}</p>
    </div>
  )
}

function TechBlock({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur">
      <h3 className="font-bold text-blue-300 text-sm uppercase tracking-wider mb-3">{title}</h3>
      <ul className="space-y-2">{children}</ul>
    </div>
  )
}

function Tech({ name }: { name: string }) {
  return (
    <li className="flex items-start gap-2 text-white/85">
      <CheckCircle2 size={14} className="text-blue-400 shrink-0 mt-1" />
      <span dangerouslySetInnerHTML={{ __html: name }} />
    </li>
  )
}

function Differentiator({
  versus,
  vsLabel,
  winner,
  winnerLabel,
}: {
  versus: string
  vsLabel: string
  winner: string
  winnerLabel: string
}) {
  return (
    <div className="bg-white/10 backdrop-blur rounded-xl p-5 border border-white/20 grid grid-cols-[1fr_auto_1fr] items-center gap-4">
      <div>
        <p className="text-xs text-white/50 mb-0.5">{versus}</p>
        <p className="text-sm">{vsLabel}</p>
      </div>
      <div className="text-2xl">→</div>
      <div>
        <p className="text-xs text-yellow-200 mb-0.5 font-bold">{winner}</p>
        <p className="text-sm font-medium">{winnerLabel}</p>
      </div>
    </div>
  )
}

function PlanCard({
  name,
  price,
  tagline,
  features,
  highlight,
  badge,
}: {
  name: string
  price: string
  tagline: string
  features: string[]
  highlight: boolean
  badge?: string
}) {
  return (
    <div
      className={`rounded-2xl p-6 border ${
        highlight
          ? 'bg-white text-gray-900 border-yellow-300 shadow-2xl shadow-yellow-300/40 scale-105'
          : 'bg-white/10 border-white/20 text-white backdrop-blur'
      }`}
    >
      {badge && (
        <span className="inline-block bg-yellow-300 text-blue-900 text-xs font-bold px-2 py-0.5 rounded-full mb-2">
          {badge}
        </span>
      )}
      <h3 className="text-2xl font-bold">{name}</h3>
      <p className={`text-xs ${highlight ? 'text-gray-500' : 'text-white/60'} mb-3`}>{tagline}</p>
      <p className="text-3xl font-bold mb-4">
        {price}
        <span className="text-sm font-normal">/mês</span>
      </p>
      <ul className="space-y-1.5 text-sm">
        {features.map(f => (
          <li key={f} className="flex items-start gap-2">
            <CheckCircle2 size={14} className={`shrink-0 mt-1 ${highlight ? 'text-green-600' : 'text-yellow-300'}`} />
            <span>{f}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function TractionCard({
  icon: Icon,
  label,
  value,
  desc,
}: {
  icon: typeof CheckCircle2
  label: string
  value: string
  desc: string
}) {
  return (
    <div className="bg-white/10 backdrop-blur rounded-2xl p-6 border border-white/20">
      <div className="flex items-center gap-3 mb-3">
        <Icon size={28} className="text-cyan-300" />
        <p className="text-sm uppercase tracking-wider text-white/60 font-semibold">{label}</p>
      </div>
      <p className="text-3xl font-bold mb-1">{value}</p>
      <p className="text-sm text-white/70">{desc}</p>
    </div>
  )
}

function RoadmapItem({
  q,
  status,
  items,
}: {
  q: string
  status: 'now' | 'next' | 'future'
  items: string[]
}) {
  const dotColor = status === 'now' ? 'bg-green-400' : status === 'next' ? 'bg-yellow-300' : 'bg-white/40'
  return (
    <div className="flex gap-5 items-start">
      <div className="flex flex-col items-center pt-1">
        <span className={`w-4 h-4 rounded-full ${dotColor}`} />
      </div>
      <div className="bg-white/10 backdrop-blur rounded-xl p-4 border border-white/20 flex-1">
        <div className="flex items-center gap-3 mb-2">
          <h3 className="font-bold text-lg">{q}</h3>
          <span className="text-xs uppercase tracking-wider text-white/60">
            {status === 'now' ? 'em andamento' : status === 'next' ? 'próximo' : 'futuro'}
          </span>
        </div>
        <ul className="text-sm text-white/85 space-y-0.5">
          {items.map(i => (
            <li key={i}>• {i}</li>
          ))}
        </ul>
      </div>
    </div>
  )
}

function UseOfFunds({ pct, label, detail }: { pct: string; label: string; detail: string }) {
  return (
    <div className="bg-white/15 backdrop-blur rounded-xl p-5 border border-white/30">
      <p className="text-4xl font-bold mb-1">{pct}</p>
      <p className="font-semibold mb-1">{label}</p>
      <p className="text-xs text-white/70">{detail}</p>
    </div>
  )
}
