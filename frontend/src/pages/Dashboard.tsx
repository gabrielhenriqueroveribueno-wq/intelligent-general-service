import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  MessageSquare,
  Ticket,
  AlertTriangle,
  Clock,
  UserX,
  Bot,
  Star,
  Zap,
  Coins,
  ListChecks,
  HeartHandshake,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import OnboardingWizard, { useOnboardingWizard } from '../components/common/OnboardingWizard'
import AnimatedCounter from '../components/common/AnimatedCounter'

interface EvasionSummary {
  critical: number
  high: number
  medium: number
  total_at_risk: number
  students: Array<{
    id: string
    full_name: string
    registration_number: string
    course: string | null
    evasion_risk_score: number
    evasion_risk_level: string
    evasion_factors: string[]
  }>
}

interface DashboardData {
  total_conversations_today: number
  total_conversations_week: number
  total_conversations_month: number
  auto_resolution_rate: number
  avg_response_time_seconds: number
  open_tickets: number
  sla_breached_tickets: number
  active_agents: number
  avg_satisfaction_score: number
}

interface DashboardInsights {
  daily_volume: Array<{ date: string; label: string; count: number }>
  top_intents: Array<{ intent: string; count: number }>
  sentiment: { positive: number; neutral: number; negative: number }
  csat: { avg_score: number; responses: number }
  ai_cost: {
    tokens_month: number
    estimated_cost_usd: number
    budget_usd: number
    budget_used_pct: number
    provider: string
  }
}

const RISK_COLORS: Record<string, string> = {
  critical: 'bg-red-100 text-red-700 border-red-200',
  high: 'bg-orange-100 text-orange-700 border-orange-200',
  medium: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  low: 'bg-green-100 text-green-700 border-green-200',
}

const RISK_LABELS: Record<string, string> = {
  critical: 'Crítico',
  high: 'Alto',
  medium: 'Médio',
  low: 'Baixo',
}

const INTENT_LABELS: Record<string, string> = {
  grade_query: 'Notas',
  attendance_query: 'Frequência',
  schedule_query: 'Horários de aula',
  boleto_query: 'Boletos',
  generate_boleto: '2ª via de boleto',
  generate_pix: 'PIX',
  enrollment_query: 'Matrícula',
  enrollment_request: 'Rematrícula',
  document_request: 'Documentos',
  certificate_request: 'Certificados',
  payslip_query: 'Holerite',
  vacation_query: 'Férias',
  time_record_query: 'Ponto',
  hr_request: 'Solicitações RH',
  medical_certificate: 'Atestados',
  schedule_appointment: 'Agendamentos',
  cancel_appointment: 'Cancelar agendamento',
  open_ticket: 'Chamados',
  facility_ticket: 'Manutenção',
  library_query: 'Biblioteca',
  library_renewal: 'Renovação de livro',
  financial_negotiation: 'Negociação financeira',
  scholarship_query: 'Bolsas',
  internship_query: 'Estágios',
  tutor_question: 'Tutoria',
  faq: 'Dúvidas gerais',
  human_handoff: 'Atendimento humano',
  document_ocr: 'Envio de documentos',
  conversation: 'Conversa geral',
}

const PROVIDER_LABELS: Record<string, string> = {
  groq: 'Groq',
  gemini: 'Gemini',
  anthropic: 'Claude',
  claude: 'Claude',
}

export default function Dashboard() {
  const { isDone } = useOnboardingWizard()
  const [showWizard, setShowWizard] = useState(!isDone())

  const { data, isLoading } = useQuery<DashboardData>({
    queryKey: ['dashboard'],
    queryFn: () => api.get('/api/v1/dashboard/overview').then((r) => r.data),
    refetchInterval: 30_000,
  })

  const { data: insights } = useQuery<DashboardInsights>({
    queryKey: ['dashboard-insights'],
    queryFn: () => api.get('/api/v1/dashboard/insights').then((r) => r.data),
    refetchInterval: 60_000,
  })

  const { data: evasion } = useQuery<EvasionSummary>({
    queryKey: ['evasion-at-risk'],
    queryFn: () => api.get('/api/v1/evasion/at-risk?limit=5').then((r) => r.data),
    refetchInterval: 5 * 60_000,
  })

  if (isLoading && !data) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500" />
      </div>
    )
  }

  const autoRate = data?.auto_resolution_rate ?? 0
  const avgRespMin = data?.avg_response_time_seconds ? data.avg_response_time_seconds / 60 : 0
  const csat = insights?.csat
  const aiCost = insights?.ai_cost
  const sentiment = insights?.sentiment
  const sentimentTotal = sentiment
    ? sentiment.positive + sentiment.neutral + sentiment.negative
    : 0
  const topIntentMax = insights?.top_intents?.[0]?.count ?? 0

  return (
    <>
      {showWizard && <OnboardingWizard onClose={() => setShowWizard(false)} />}
      <div className="space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-100">Dashboard</h1>
            <p className="text-slate-500 text-sm mt-1">Visão geral do atendimento</p>
          </div>
          <span className="hidden sm:flex items-center gap-2 text-xs text-primary-500 bg-navy-700 px-3 py-1.5 rounded-lg">
            <span className="inline-flex h-2 w-2 rounded-full bg-green-400 animate-pulse" />
            Billie online
          </span>
        </div>

        {/* HERO — flat navy, destaque amarelo */}
        <div className="rounded-2xl bg-navy-800 border border-navy-line p-6 lg:p-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-center">
            <div className="lg:col-span-2">
              <div className="flex items-center gap-2 mb-3">
                <div className="bg-accent p-2 rounded-lg">
                  <Bot size={18} className="text-accent-ink" />
                </div>
                <span className="text-xs uppercase tracking-widest text-slate-400 font-semibold">
                  IA atendendo agora
                </span>
              </div>
              <p className="text-6xl md:text-7xl font-extrabold leading-none tracking-tight text-white">
                <AnimatedCounter value={autoRate} suffix="%" duration={1500} />
              </p>
              <p className="text-lg mt-3 text-slate-300 font-medium">
                das conversas resolvidas <span className="text-accent">automaticamente</span>
              </p>
              <p className="text-sm mt-1 text-slate-500">
                A Billie cuida do trivial — sua equipe foca no que importa
              </p>
            </div>

            <div className="grid grid-cols-2 lg:grid-cols-1 gap-3">
              <div className="bg-navy-750 rounded-xl p-4 border border-navy-line">
                <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
                  <Zap size={14} /> Conversas hoje
                </div>
                <p className="text-3xl font-bold text-white">
                  <AnimatedCounter value={data?.total_conversations_today ?? 0} />
                </p>
              </div>
              <div className="bg-navy-750 rounded-xl p-4 border border-navy-line">
                <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
                  <Clock size={14} /> Resp. média
                </div>
                <p className="text-3xl font-bold text-white">
                  <AnimatedCounter value={avgRespMin} decimals={1} suffix="min" />
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* KPIs */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Conversas Hoje"
            value={data?.total_conversations_today ?? 0}
            icon={MessageSquare}
            tone="blue"
            subtitle={`${data?.total_conversations_week ?? 0} esta semana`}
          />
          <StatCard
            label="Satisfação (CSAT)"
            value={csat?.avg_score ?? data?.avg_satisfaction_score ?? 0}
            decimals={1}
            suffix=" / 5"
            icon={Star}
            tone="yellow"
            subtitle={csat ? `${csat.responses} respostas em 30 dias` : 'Últimos 30 dias'}
          />
          <StatCard
            label="Tickets Abertos"
            value={data?.open_tickets ?? 0}
            icon={Ticket}
            tone="orange"
          />
          <StatCard
            label="SLA Violado"
            value={data?.sla_breached_tickets ?? 0}
            icon={AlertTriangle}
            tone={data?.sla_breached_tickets ? 'red' : 'gray'}
            subtitle="Tickets em atraso"
          />
        </div>

        {/* Volume por dia (7d, dados reais) */}
        <div className="rounded-xl bg-navy-800 border border-navy-line p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-semibold text-slate-200">Volume de conversas · 7 dias</h2>
            <span className="text-xs text-slate-500">Atualiza a cada 60s</span>
          </div>
          <ResponsiveContainer width="100%" height={210}>
            <BarChart data={insights?.daily_volume ?? []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e2a40" vertical={false} />
              <XAxis dataKey="label" tick={{ fontSize: 12, fill: '#8294ad' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 12, fill: '#8294ad' }} axisLine={false} tickLine={false} allowDecimals={false} />
              <Tooltip
                cursor={{ fill: '#15223c' }}
                contentStyle={{
                  borderRadius: 8,
                  border: '1px solid #1e2a40',
                  backgroundColor: '#0f1a2e',
                  color: '#e8edf6',
                }}
                labelStyle={{ color: '#8294ad' }}
              />
              <Bar dataKey="count" name="Conversas" fill="#3b82f6" radius={[5, 5, 0, 0]} animationDuration={800} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Custo de IA + Sentimento */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="rounded-xl bg-navy-800 border border-navy-line p-5">
            <div className="flex items-center gap-2 mb-4">
              <div className="bg-navy-700 p-2 rounded-lg">
                <Coins size={16} className="text-accent" />
              </div>
              <h2 className="font-semibold text-slate-200">Custo de IA no mês</h2>
            </div>
            <div className="flex items-baseline gap-3">
              <p className="text-4xl font-bold text-white">
                US$ <AnimatedCounter value={aiCost?.estimated_cost_usd ?? 0} decimals={2} />
              </p>
              <span className="text-xs text-slate-500">
                via {PROVIDER_LABELS[aiCost?.provider ?? 'groq'] ?? aiCost?.provider}
              </span>
            </div>
            <p className="text-sm text-slate-500 mt-1">
              {(aiCost?.tokens_month ?? 0).toLocaleString('pt-BR')} tokens processados
            </p>
            <div className="mt-4">
              <div className="flex justify-between text-xs mb-1.5">
                <span className="text-slate-400">Orçamento mensal</span>
                <span className={aiCost && aiCost.budget_used_pct >= 80 ? 'text-red-400' : 'text-slate-400'}>
                  {aiCost?.budget_used_pct ?? 0}% de US$ {aiCost?.budget_usd ?? 0}
                </span>
              </div>
              <div className="h-2 bg-navy-950 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${
                    (aiCost?.budget_used_pct ?? 0) >= 80 ? 'bg-red-500' : 'bg-accent'
                  }`}
                  style={{ width: `${Math.min(aiCost?.budget_used_pct ?? 0, 100)}%` }}
                />
              </div>
            </div>
          </div>

          <div className="rounded-xl bg-navy-800 border border-navy-line p-5">
            <div className="flex items-center gap-2 mb-4">
              <div className="bg-navy-700 p-2 rounded-lg">
                <HeartHandshake size={16} className="text-primary-500" />
              </div>
              <h2 className="font-semibold text-slate-200">Sentimento dos alunos · 30 dias</h2>
            </div>
            {sentimentTotal > 0 && sentiment ? (
              <>
                <div className="flex h-3 rounded-full overflow-hidden bg-navy-950">
                  <div className="bg-green-500" style={{ width: `${(sentiment.positive / sentimentTotal) * 100}%` }} />
                  <div className="bg-slate-500" style={{ width: `${(sentiment.neutral / sentimentTotal) * 100}%` }} />
                  <div className="bg-red-500" style={{ width: `${(sentiment.negative / sentimentTotal) * 100}%` }} />
                </div>
                <div className="grid grid-cols-3 gap-2 mt-4">
                  <SentimentStat label="Positivo" count={sentiment.positive} total={sentimentTotal} dot="bg-green-500" />
                  <SentimentStat label="Neutro" count={sentiment.neutral} total={sentimentTotal} dot="bg-slate-500" />
                  <SentimentStat label="Negativo" count={sentiment.negative} total={sentimentTotal} dot="bg-red-500" />
                </div>
              </>
            ) : (
              <p className="text-sm text-slate-500">Sem mensagens analisadas no período.</p>
            )}
          </div>
        </div>

        {/* Top assuntos + Evasão */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="rounded-xl bg-navy-800 border border-navy-line p-5">
            <div className="flex items-center gap-2 mb-4">
              <div className="bg-navy-700 p-2 rounded-lg">
                <ListChecks size={16} className="text-primary-500" />
              </div>
              <h2 className="font-semibold text-slate-200">Assuntos mais pedidos · 30 dias</h2>
            </div>
            {insights?.top_intents?.length ? (
              <div className="space-y-3">
                {insights.top_intents.map((it) => (
                  <div key={it.intent}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-300">{INTENT_LABELS[it.intent] ?? it.intent}</span>
                      <span className="text-slate-500">{it.count}</span>
                    </div>
                    <div className="h-1.5 bg-navy-950 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary-500 rounded-full"
                        style={{ width: `${topIntentMax ? (it.count / topIntentMax) * 100 : 0}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-500">Sem demanda classificada no período.</p>
            )}
          </div>

          <div className="rounded-xl bg-navy-800 border border-navy-line p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="bg-navy-700 p-2 rounded-lg">
                  <UserX size={16} className="text-red-400" />
                </div>
                <div>
                  <h2 className="font-semibold text-slate-200">Alunos em risco de evasão</h2>
                  {evasion && (
                    <p className="text-xs text-slate-500">
                      {evasion.critical > 0 && (
                        <span className="text-red-400 font-medium">{evasion.critical} crítico(s) · </span>
                      )}
                      {evasion.high > 0 && (
                        <span className="text-orange-400 font-medium">{evasion.high} alto(s) · </span>
                      )}
                      {evasion.medium > 0 && <span className="text-yellow-500">{evasion.medium} médio(s)</span>}
                    </p>
                  )}
                </div>
              </div>
              <Link to="/app/students?risk=high" className="text-sm text-primary-500 hover:underline">
                Ver todos
              </Link>
            </div>
            {evasion && evasion.total_at_risk > 0 ? (
              <div className="space-y-1">
                {evasion.students.map((s) => (
                  <Link
                    key={s.id}
                    to={`/app/students/${s.id}`}
                    className="flex items-center justify-between p-2 rounded-lg hover:bg-navy-750 transition-colors"
                  >
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-slate-200 truncate">{s.full_name}</p>
                      <p className="text-xs text-slate-500">
                        RA {s.registration_number} · {s.course ?? 'Sem curso'}
                      </p>
                    </div>
                    <span
                      className={`ml-3 text-xs font-medium px-2 py-0.5 rounded-full border flex-shrink-0 ${
                        RISK_COLORS[s.evasion_risk_level] ?? RISK_COLORS.low
                      }`}
                    >
                      {RISK_LABELS[s.evasion_risk_level] ?? s.evasion_risk_level} · {s.evasion_risk_score}
                    </span>
                  </Link>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-500">Nenhum aluno em risco no momento. 🎉</p>
            )}
          </div>
        </div>
      </div>
    </>
  )
}

const TONE_STYLES: Record<string, { box: string; icon: string }> = {
  blue: { box: 'bg-navy-700', icon: 'text-primary-500' },
  yellow: { box: 'bg-navy-700', icon: 'text-accent' },
  orange: { box: 'bg-navy-700', icon: 'text-orange-400' },
  red: { box: 'bg-navy-700', icon: 'text-red-400' },
  gray: { box: 'bg-navy-700', icon: 'text-slate-400' },
}

function StatCard({
  label,
  value,
  suffix,
  decimals,
  icon: Icon,
  tone,
  subtitle,
}: {
  label: string
  value: number
  suffix?: string
  decimals?: number
  icon: React.ElementType
  tone: keyof typeof TONE_STYLES
  subtitle?: string
}) {
  const styles = TONE_STYLES[tone] ?? TONE_STYLES.gray
  return (
    <div className="rounded-xl bg-navy-800 border border-navy-line p-5 hover:border-navy-600 transition-colors">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <p className="text-sm text-slate-400">{label}</p>
          <p className="text-3xl font-bold mt-1 text-white">
            <AnimatedCounter value={value} suffix={suffix} decimals={decimals} />
          </p>
          {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
        </div>
        <div className={`p-3 rounded-xl ${styles.box} shrink-0`}>
          <Icon size={20} className={styles.icon} />
        </div>
      </div>
    </div>
  )
}

function SentimentStat({
  label,
  count,
  total,
  dot,
}: {
  label: string
  count: number
  total: number
  dot: string
}) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0
  return (
    <div className="rounded-lg bg-navy-750 p-3">
      <div className="flex items-center gap-1.5 text-xs text-slate-400">
        <span className={`w-2 h-2 rounded-full ${dot}`} />
        {label}
      </div>
      <p className="text-lg font-semibold text-white mt-1">{pct}%</p>
      <p className="text-xs text-slate-500">{count} msgs</p>
    </div>
  )
}
