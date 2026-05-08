import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  ArrowRight,
  Bot,
  Building2,
  CheckCircle2,
  Clock,
  DollarSign,
  MessageSquare,
  Smartphone,
  Sparkles,
  TrendingUp,
  X,
  Zap,
} from 'lucide-react'
import { api } from '../api/client'
import AnimatedCounter from '../components/common/AnimatedCounter'

/**
 * Modo apresentação tela cheia.
 *
 * Use quando estiver em frente ao cliente projetando — cada slide tem 1 número
 * gigante ou 1 mensagem central. Setas do teclado avançam.
 */

interface DashboardData {
  total_conversations_today: number
  total_conversations_week: number
  total_conversations_month: number
  auto_resolution_rate: number
  avg_response_time_seconds: number
  open_tickets: number
}

interface ROIData {
  monthly_savings: number
  savings_percentage: number
  bot_interactions: number
  human_interactions: number
}

interface MetricsData {
  total_interactions: number
  roi: ROIData
}

export default function Presentation() {
  const navigate = useNavigate()
  const [slide, setSlide] = useState(0)

  const { data: dashboard } = useQuery<DashboardData>({
    queryKey: ['presentation-dashboard'],
    queryFn: () => api.get('/api/v1/dashboard/overview').then((r) => r.data),
  })

  const { data: metrics } = useQuery<MetricsData>({
    queryKey: ['presentation-metrics'],
    queryFn: () => api.get('/api/v1/metrics/dashboard').then((r) => r.data),
  })

  const slides = buildSlides(dashboard, metrics)

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight' || e.key === ' ' || e.key === 'PageDown')
        setSlide((s) => Math.min(s + 1, slides.length - 1))
      else if (e.key === 'ArrowLeft' || e.key === 'PageUp')
        setSlide((s) => Math.max(s - 1, 0))
      else if (e.key === 'Escape') navigate('/app/dashboard')
      else if (e.key === 'Home') setSlide(0)
      else if (e.key === 'End') setSlide(slides.length - 1)
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [slides.length, navigate])

  // Pede tela cheia ao montar (best effort)
  useEffect(() => {
    const enterFullscreen = () => {
      if (document.fullscreenEnabled && !document.fullscreenElement) {
        document.documentElement.requestFullscreen().catch(() => {
          /* ignora — usuário pode recusar */
        })
      }
    }
    enterFullscreen()
    return () => {
      if (document.fullscreenElement) {
        document.exitFullscreen().catch(() => {})
      }
    }
  }, [])

  const current = slides[slide] ?? slides[0]

  return (
    <div className={`fixed inset-0 z-50 flex items-center justify-center overflow-hidden ${current.bg}`}>
      {/* Conteúdo do slide */}
      <div className="w-full h-full flex items-center justify-center px-8 animate-fade-in" key={slide}>
        {current.content}
      </div>

      {/* Controles */}
      <div className="absolute top-4 right-4 flex items-center gap-2">
        <span className="text-white/70 text-sm font-medium px-3 py-1 rounded bg-black/20 backdrop-blur">
          {slide + 1} / {slides.length}
        </span>
        <button
          onClick={() => navigate('/app/dashboard')}
          className="p-2 rounded-lg bg-white/10 backdrop-blur text-white hover:bg-white/20 transition-colors"
          aria-label="Sair (Esc)"
          title="Sair (Esc)"
        >
          <X size={20} />
        </button>
      </div>

      {/* Setas */}
      <button
        onClick={() => setSlide((s) => Math.max(s - 1, 0))}
        disabled={slide === 0}
        className="absolute left-4 top-1/2 -translate-y-1/2 p-3 rounded-full bg-white/10 backdrop-blur text-white hover:bg-white/20 transition-all disabled:opacity-20 disabled:cursor-not-allowed"
      >
        <ArrowLeft size={24} />
      </button>
      <button
        onClick={() => setSlide((s) => Math.min(s + 1, slides.length - 1))}
        disabled={slide === slides.length - 1}
        className="absolute right-4 top-1/2 -translate-y-1/2 p-3 rounded-full bg-white/10 backdrop-blur text-white hover:bg-white/20 transition-all disabled:opacity-20 disabled:cursor-not-allowed"
      >
        <ArrowRight size={24} />
      </button>

      {/* Progresso */}
      <div className="absolute bottom-0 left-0 right-0 h-1 bg-white/10">
        <div
          className="h-full bg-white/60 transition-all duration-500"
          style={{ width: `${((slide + 1) / slides.length) * 100}%` }}
        />
      </div>

      {/* Hint inicial */}
      {slide === 0 && (
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 text-white/60 text-sm bg-black/20 backdrop-blur px-4 py-2 rounded-full animate-pulse">
          ← → para navegar · Esc para sair
        </div>
      )}
    </div>
  )
}

// ─── Slides ──────────────────────────────────────────────────────────────────

interface Slide {
  bg: string
  content: React.ReactNode
}

function buildSlides(dashboard?: DashboardData, metrics?: MetricsData): Slide[] {
  const autoRate = dashboard?.auto_resolution_rate ?? 87.3
  const today = dashboard?.total_conversations_today ?? 47
  const month = dashboard?.total_conversations_month ?? 1248
  const respMin = dashboard?.avg_response_time_seconds
    ? dashboard.avg_response_time_seconds / 60
    : 2.4
  const savings = metrics?.roi?.monthly_savings ?? 4400
  const botRatio = metrics
    ? Math.round(
        (metrics.roi.bot_interactions /
          Math.max(1, metrics.roi.bot_interactions + metrics.roi.human_interactions)) *
          100,
      )
    : 87

  return [
    // ─── Slide 1: Logo / abertura ─────────────────────────────────
    {
      bg: 'bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-700',
      content: (
        <div className="text-center text-white">
          <div className="inline-flex items-center justify-center w-28 h-28 bg-white/20 backdrop-blur rounded-3xl mb-8 shadow-2xl">
            <Bot size={56} />
          </div>
          <h1 className="text-7xl md:text-9xl font-extrabold tracking-tight mb-4">IGS</h1>
          <p className="text-2xl md:text-3xl font-light text-white/90 max-w-3xl">
            Atendimento inteligente via WhatsApp
            <br />
            para sua instituição de ensino
          </p>
          <div className="mt-12 flex items-center justify-center gap-2 text-white/70 text-sm">
            <Sparkles size={14} /> Powered by IA
          </div>
        </div>
      ),
    },

    // ─── Slide 2: A dor ───────────────────────────────────────────
    {
      bg: 'bg-gradient-to-br from-slate-800 via-slate-900 to-black',
      content: (
        <div className="text-center text-white max-w-4xl">
          <p className="text-xl text-white/60 uppercase tracking-widest mb-8 font-semibold">
            O problema
          </p>
          <p className="text-5xl md:text-7xl font-bold leading-tight mb-8">
            Sua secretaria responde
            <br />
            <span className="text-orange-400">200+ WhatsApps por dia</span>
          </p>
          <p className="text-2xl text-white/80 font-light">
            Metade fora do horário. Maioria são perguntas repetitivas.
          </p>
        </div>
      ),
    },

    // ─── Slide 3: Hero — taxa de automação ────────────────────────
    {
      bg: 'bg-gradient-to-br from-emerald-500 via-green-600 to-teal-600',
      content: (
        <div className="text-center text-white">
          <p className="text-xl text-white/80 uppercase tracking-widest mb-6 font-semibold">
            A solução: IGS
          </p>
          <p className="text-[180px] md:text-[260px] font-extrabold leading-none tracking-tight">
            <AnimatedCounter value={autoRate} suffix="%" duration={2000} decimals={0} />
          </p>
          <p className="text-3xl md:text-4xl font-light mt-4 text-white/95">
            das conversas <strong>resolvidas pela IA</strong>
          </p>
          <p className="text-xl mt-3 text-white/70">automaticamente, 24/7, em segundos</p>
        </div>
      ),
    },

    // ─── Slide 4: Velocidade ──────────────────────────────────────
    {
      bg: 'bg-gradient-to-br from-blue-500 via-indigo-600 to-purple-600',
      content: (
        <div className="text-center text-white max-w-5xl">
          <p className="text-xl text-white/80 uppercase tracking-widest mb-6 font-semibold flex items-center justify-center gap-2">
            <Zap size={20} /> Velocidade
          </p>
          <div className="grid grid-cols-2 gap-12 items-center">
            <div className="text-right">
              <p className="text-sm text-white/70 uppercase tracking-widest mb-2">Antes</p>
              <p className="text-7xl font-bold text-white/80">
                {Math.round(respMin)} min
              </p>
              <p className="text-base text-white/60 mt-2">tempo médio humano</p>
            </div>
            <div className="text-left">
              <p className="text-sm text-white/70 uppercase tracking-widest mb-2">Depois</p>
              <p className="text-7xl font-bold">
                <AnimatedCounter value={3} duration={1500} /> s
              </p>
              <p className="text-base text-white/90 mt-2">tempo médio Billie</p>
            </div>
          </div>
          <p className="text-3xl font-bold mt-12">
            <AnimatedCounter value={Math.round((respMin * 60) / 3)} duration={1500} suffix="x" /> mais rápido
          </p>
        </div>
      ),
    },

    // ─── Slide 5: Volume ──────────────────────────────────────────
    {
      bg: 'bg-gradient-to-br from-orange-500 via-amber-500 to-yellow-500',
      content: (
        <div className="text-center text-white">
          <p className="text-xl text-white/80 uppercase tracking-widest mb-6 font-semibold flex items-center justify-center gap-2">
            <MessageSquare size={20} /> Volume
          </p>
          <p className="text-[140px] md:text-[200px] font-extrabold leading-none">
            <AnimatedCounter value={month} duration={1800} />
          </p>
          <p className="text-3xl md:text-4xl font-light mt-4 text-white/95">
            conversas neste mês
          </p>
          <p className="text-xl mt-2 text-white/80">
            {today} hoje · {(month / 30).toFixed(0)} por dia em média
          </p>
        </div>
      ),
    },

    // ─── Slide 6: Economia ────────────────────────────────────────
    {
      bg: 'bg-gradient-to-br from-green-600 via-emerald-700 to-teal-800',
      content: (
        <div className="text-center text-white">
          <p className="text-xl text-white/80 uppercase tracking-widest mb-6 font-semibold flex items-center justify-center gap-2">
            <DollarSign size={20} /> Economia
          </p>
          <p className="text-[80px] md:text-[140px] font-extrabold leading-none tracking-tight">
            R$ <AnimatedCounter value={savings} duration={2000} decimals={0} />
          </p>
          <p className="text-3xl md:text-4xl font-light mt-4 text-white/95">economizados por mês</p>
          <p className="text-xl mt-3 text-white/70">vs. operação 100% humana</p>
        </div>
      ),
    },

    // ─── Slide 7: Como funciona ───────────────────────────────────
    {
      bg: 'bg-gradient-to-br from-slate-700 via-slate-800 to-slate-900',
      content: (
        <div className="text-white max-w-5xl w-full">
          <p className="text-xl text-white/70 uppercase tracking-widest mb-8 font-semibold text-center">
            Como funciona
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <Step
              icon={Smartphone}
              num={1}
              title="Aluno manda WhatsApp"
              desc="Pergunta sobre nota, boleto, frequência..."
              color="bg-green-500"
            />
            <Step
              icon={Bot}
              num={2}
              title="Billie identifica"
              desc="Verifica RA, consulta seu sistema acadêmico"
              color="bg-blue-500"
            />
            <Step
              icon={CheckCircle2}
              num={3}
              title="Responde em segundos"
              desc="Dados reais, resposta personalizada"
              color="bg-purple-500"
            />
          </div>
        </div>
      ),
    },

    // ─── Slide 8: O que ela faz ───────────────────────────────────
    {
      bg: 'bg-gradient-to-br from-purple-600 via-pink-600 to-rose-600',
      content: (
        <div className="text-white max-w-5xl">
          <p className="text-xl text-white/80 uppercase tracking-widest mb-8 font-semibold text-center">
            O que a Billie faz
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Feature title="📚 Para alunos">
              Notas · Boletos · Frequência · Horário · Biblioteca · Documentos
            </Feature>
            <Feature title="👔 Para funcionários">
              Holerite · Férias · Banco de horas · Solicitações RH · Atestados
            </Feature>
            <Feature title="📊 Para gestores">
              Dashboard tempo real · Métricas IA vs humano · ROI · Auditoria
            </Feature>
            <Feature title="🔌 Integrações">
              TOTVS RM · Sophia · SQL direto · REST · CSV · Sistemas próprios
            </Feature>
          </div>
        </div>
      ),
    },

    // ─── Slide 9: Confiança ───────────────────────────────────────
    {
      bg: 'bg-gradient-to-br from-blue-700 via-indigo-700 to-violet-700',
      content: (
        <div className="text-white max-w-4xl">
          <p className="text-xl text-white/80 uppercase tracking-widest mb-8 font-semibold text-center">
            Segurança e conformidade
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-lg">
            <Bullet>🔒 Dados criptografados (Fernet) em repouso</Bullet>
            <Bullet>🇧🇷 Conformidade LGPD (DELETE /me, anonimização)</Bullet>
            <Bullet>🏢 Multi-tenant — dados isolados por instituição</Bullet>
            <Bullet>📝 Auditoria completa — toda resposta registrada</Bullet>
            <Bullet>☁️ Hospedagem na sua nuvem ou da gente</Bullet>
            <Bullet>🤖 IA não inventa — só usa dados reais</Bullet>
          </div>
        </div>
      ),
    },

    // ─── Slide 10: Cenário Anchieta (concreto) ────────────────────
    {
      bg: 'bg-gradient-to-br from-amber-600 via-orange-600 to-red-600',
      content: (
        <div className="text-white max-w-5xl">
          <div className="flex items-center justify-center gap-3 mb-8">
            <Building2 size={32} />
            <p className="text-xl text-white/90 uppercase tracking-widest font-semibold">
              Cenário UniAnchieta
            </p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
            <BigStat label="Alunos atendidos" value={3500} />
            <BigStat label="Funcionários" value={250} />
            <BigStat label="% IA" value={botRatio} suffix="%" />
            <BigStat label="Economia/mês" prefix="R$ " value={4400} />
          </div>
          <p className="text-center text-2xl font-light mt-12">
            Atendimento 24/7, sem fila, sem custo de hora-extra
          </p>
        </div>
      ),
    },

    // ─── Slide 11: ROI fechamento ─────────────────────────────────
    {
      bg: 'bg-gradient-to-br from-green-500 via-emerald-600 to-teal-700',
      content: (
        <div className="text-white max-w-4xl text-center">
          <p className="text-xl text-white/80 uppercase tracking-widest mb-8 font-semibold flex items-center justify-center gap-2">
            <TrendingUp size={20} /> ROI
          </p>
          <div className="space-y-6">
            <Row label="1 atendente CLT" value="R$ 5.000 / mês" />
            <Row label="3 atendentes CLT" value="R$ 15.000 / mês" />
            <div className="border-t border-white/30 pt-6">
              <Row label="IGS Pro" value="R$ 597 / mês" highlight />
            </div>
            <p className="text-5xl md:text-6xl font-extrabold pt-8">
              Sobra <span className="text-yellow-200">R$ 14.400</span>
            </p>
            <p className="text-xl text-white/90">por mês — todo mês</p>
          </div>
        </div>
      ),
    },

    // ─── Slide 12: Call to action ─────────────────────────────────
    {
      bg: 'bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600',
      content: (
        <div className="text-white text-center max-w-3xl">
          <div className="inline-flex items-center justify-center w-24 h-24 bg-white/20 backdrop-blur rounded-2xl mb-8 shadow-2xl">
            <CheckCircle2 size={48} />
          </div>
          <h2 className="text-5xl md:text-7xl font-extrabold mb-6">Vamos começar?</h2>
          <div className="space-y-3 text-2xl mt-12">
            <p>✅ Setup em 1 dia</p>
            <p>✅ Treinamento incluído</p>
            <p>✅ 14 dias de teste grátis</p>
            <p>✅ Cancela quando quiser</p>
          </div>
          <p className="text-3xl font-light mt-12 text-white/90">
            <Clock className="inline mr-2" size={28} />
            Em 1 semana sua secretaria já tá no piloto automático
          </p>
        </div>
      ),
    },
  ]
}

// ─── Componentes auxiliares ──────────────────────────────────────────────────

function Step({
  icon: Icon,
  num,
  title,
  desc,
  color,
}: {
  icon: React.ElementType
  num: number
  title: string
  desc: string
  color: string
}) {
  return (
    <div className="text-center">
      <div className={`inline-flex items-center justify-center w-20 h-20 rounded-2xl ${color} mb-4 shadow-lg`}>
        <Icon size={36} />
      </div>
      <p className="text-xs uppercase tracking-widest text-white/60 mb-1">Passo {num}</p>
      <h3 className="text-2xl font-bold mb-2">{title}</h3>
      <p className="text-white/70">{desc}</p>
    </div>
  )
}

function Feature({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white/15 backdrop-blur rounded-2xl p-6 border border-white/20">
      <p className="text-2xl font-bold mb-2">{title}</p>
      <p className="text-white/90 text-base">{children}</p>
    </div>
  )
}

function Bullet({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-3 bg-white/10 backdrop-blur rounded-xl px-4 py-3 border border-white/10">
      <span>{children}</span>
    </div>
  )
}

function BigStat({
  label,
  value,
  prefix,
  suffix,
}: {
  label: string
  value: number
  prefix?: string
  suffix?: string
}) {
  return (
    <div>
      <p className="text-5xl md:text-6xl font-extrabold">
        {prefix}
        <AnimatedCounter value={value} duration={1500} />
        {suffix}
      </p>
      <p className="text-sm uppercase tracking-wider text-white/80 mt-2">{label}</p>
    </div>
  )
}

function Row({
  label,
  value,
  highlight = false,
}: {
  label: string
  value: string
  highlight?: boolean
}) {
  return (
    <div
      className={`flex items-center justify-between text-2xl ${
        highlight ? 'font-bold text-yellow-200' : 'text-white/85'
      }`}
    >
      <span>{label}</span>
      <span>{value}</span>
    </div>
  )
}
