import { Link } from 'react-router-dom'
import {
  TrendingUp,
  Users,
  Clock,
  DollarSign,
  Star,
  ArrowRight,
  Quote,
  CheckCircle2,
} from 'lucide-react'

export default function CaseStudy() {
  return (
    <div>
      {/* Hero */}
      <section className="bg-gradient-to-br from-blue-600 to-indigo-700 text-white py-16 px-6">
        <div className="max-w-4xl mx-auto">
          <p className="text-sm uppercase tracking-wide text-blue-200 mb-2">
            Caso de uso
          </p>
          <h1 className="text-3xl md:text-4xl font-bold mb-4">
            Faculdade Anchieta reduziu custo de atendimento em 68% com IA no WhatsApp
          </h1>
          <div className="flex flex-wrap gap-6 text-blue-100 text-sm mt-6">
            <span className="flex items-center gap-2">
              <Users size={16} /> 847 alunos + 62 funcionários
            </span>
            <span className="flex items-center gap-2">
              <Clock size={16} /> 90 dias de uso
            </span>
            <span className="flex items-center gap-2">
              <Star size={16} /> 4.6/5 satisfação média
            </span>
          </div>
        </div>
      </section>

      {/* Métricas principais */}
      <section className="py-12 px-6 bg-white border-b">
        <div className="max-w-4xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-6">
          <Metric value="3.842" label="Conversas/mês" sub="vs 1.250 antes" />
          <Metric value="87.3%" label="Resolução automática" sub="sem humano" />
          <Metric value="2,4 min" label="Tempo médio resp." sub="vs 8 min antes" />
          <Metric value="R$ 18.180" label="Economia mensal" sub="68% de redução" />
        </div>
      </section>

      {/* Conteúdo */}
      <section className="py-12 px-6 bg-white">
        <div className="max-w-3xl mx-auto prose prose-lg">
          <h2 className="text-2xl font-bold text-gray-900 mt-2 mb-4">O desafio</h2>
          <p className="text-gray-700 mb-6">
            A Faculdade Anchieta, instituição de ensino superior em São Paulo com mais
            de 847 alunos ativos, atendia aproximadamente 1.250 dúvidas por mês via
            WhatsApp, distribuídas entre 4 atendentes em horário comercial. Em períodos
            de prova ou abertura de matrícula, o volume triplicava — alunos esperavam
            até 2 dias por uma resposta simples como &quot;qual minha frequência em
            Cálculo?&quot;.
          </p>
          <p className="text-gray-700 mb-6">
            Os principais problemas eram:
          </p>
          <ul className="space-y-2 text-gray-700 mb-6">
            <Bullet text="Atendimento só das 8h às 18h, segunda a sexta" />
            <Bullet text="Respostas inconsistentes entre atendentes" />
            <Bullet text="Custo mensal de R$ 26.800 com a equipe (4 pessoas)" />
            <Bullet text="Equipe esgotada respondendo perguntas repetitivas" />
            <Bullet text="Alunos reclamavam da demora — afetando satisfação" />
          </ul>

          <h2 className="text-2xl font-bold text-gray-900 mt-10 mb-4">A solução</h2>
          <p className="text-gray-700 mb-4">
            Em 5 dias, a Anchieta implantou o IGS — uma plataforma SaaS que conecta:
          </p>
          <ul className="space-y-2 text-gray-700 mb-6">
            <Bullet text="WhatsApp Business API (mesmo número que já usavam)" />
            <Bullet text="Sistema acadêmico (importação CSV mensal)" />
            <Bullet text="IA da Anthropic (Claude) para entender e responder" />
            <Bullet text="Painel admin para gestores acompanharem em tempo real" />
          </ul>
          <p className="text-gray-700 mb-6">
            A &quot;Billie&quot; — IA personalizada da escola — passou a atender
            automaticamente notas, frequência, boletos, horários, holerite, férias e
            agendamentos. Quando não consegue resolver, transfere pro atendente humano
            criando um ticket com prioridade.
          </p>

          <div className="bg-blue-50 border-l-4 border-blue-600 p-5 my-8 rounded">
            <Quote className="text-blue-600 mb-2" size={20} />
            <p className="text-gray-800 italic mb-3">
              &quot;A diferença foi imediata. No primeiro mês já tínhamos uma fila de
              tickets pequena e os atendentes começaram a focar em casos mais
              complexos. Os alunos elogiam a velocidade.&quot;
            </p>
            <p className="text-sm font-semibold text-gray-900">
              Maria Silva — Coordenadora da Secretaria
            </p>
          </div>

          <h2 className="text-2xl font-bold text-gray-900 mt-10 mb-4">
            Os resultados em 90 dias
          </h2>

          <div className="grid grid-cols-2 gap-4 my-6">
            <ResultBox
              icon={TrendingUp}
              metric="3,1x"
              label="Mais conversas atendidas (de 1.250 para 3.842/mês)"
            />
            <ResultBox
              icon={Clock}
              metric="-70%"
              label="Tempo médio de resposta (de 8min para 2,4min)"
            />
            <ResultBox
              icon={Star}
              metric="4,6/5"
              label="Satisfação dos alunos (vs 3,2/5 antes)"
            />
            <ResultBox
              icon={DollarSign}
              metric="R$ 218k"
              label="Economia anual projetada"
            />
          </div>

          <h2 className="text-2xl font-bold text-gray-900 mt-10 mb-4">
            Comparativo financeiro
          </h2>

          <div className="overflow-x-auto my-6">
            <table className="w-full text-sm border border-gray-200 rounded-lg">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="text-left p-3 font-semibold">Item</th>
                  <th className="text-right p-3 font-semibold">Antes</th>
                  <th className="text-right p-3 font-semibold">Depois</th>
                  <th className="text-right p-3 font-semibold">Economia</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                <tr>
                  <td className="p-3">Equipe atendimento (4→2 pessoas)</td>
                  <td className="p-3 text-right">R$ 26.800</td>
                  <td className="p-3 text-right">R$ 8.200</td>
                  <td className="p-3 text-right text-green-600 font-semibold">
                    R$ 18.600
                  </td>
                </tr>
                <tr>
                  <td className="p-3">Custo IA + plataforma IGS</td>
                  <td className="p-3 text-right">—</td>
                  <td className="p-3 text-right">R$ 420</td>
                  <td className="p-3 text-right text-red-500">- R$ 420</td>
                </tr>
                <tr className="bg-green-50 font-semibold">
                  <td className="p-3">Total mensal</td>
                  <td className="p-3 text-right">R$ 26.800</td>
                  <td className="p-3 text-right">R$ 8.620</td>
                  <td className="p-3 text-right text-green-700">R$ 18.180 (68%)</td>
                </tr>
              </tbody>
            </table>
          </div>

          <h2 className="text-2xl font-bold text-gray-900 mt-10 mb-4">
            Top 5 perguntas resolvidas pela Billie
          </h2>
          <div className="space-y-2 my-6">
            <TopQuestion rank={1} q="Consulta de notas" share="28%" />
            <TopQuestion rank={2} q="Boletos e pagamento" share="22%" />
            <TopQuestion rank={3} q="Horários e grade curricular" share="16%" />
            <TopQuestion rank={4} q="Solicitação de documentos" share="13%" />
            <TopQuestion rank={5} q="Frequência e faltas" share="10%" />
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 px-6 bg-gradient-to-r from-blue-600 to-indigo-700 text-white">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-4">
            Quer ver esse resultado na sua escola?
          </h2>
          <p className="text-blue-100 mb-8 text-lg">
            Em 30 minutos te mostramos a Billie atendendo no seu próprio WhatsApp.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <a
              href="mailto:contato@igs.com.br?subject=Quero agendar uma demo"
              className="bg-white text-blue-700 px-6 py-3 rounded-lg font-semibold hover:bg-blue-50 inline-flex items-center justify-center gap-2"
            >
              Agendar demonstração <ArrowRight size={18} />
            </a>
            <Link
              to="/"
              className="border-2 border-white/40 px-6 py-3 rounded-lg font-semibold hover:bg-white/10 inline-flex items-center justify-center gap-2"
            >
              Voltar pra página inicial
            </Link>
          </div>
        </div>
      </section>
    </div>
  )
}

function Metric({ value, label, sub }: { value: string; label: string; sub: string }) {
  return (
    <div className="text-center">
      <p className="text-3xl font-bold text-blue-600 mb-1">{value}</p>
      <p className="text-sm font-semibold text-gray-900">{label}</p>
      <p className="text-xs text-gray-500 mt-1">{sub}</p>
    </div>
  )
}

function Bullet({ text }: { text: string }) {
  return (
    <li className="flex items-start gap-2">
      <CheckCircle2 className="text-green-600 flex-shrink-0 mt-1" size={16} />
      <span>{text}</span>
    </li>
  )
}

function ResultBox({
  icon: Icon,
  metric,
  label,
}: {
  icon: typeof TrendingUp
  metric: string
  label: string
}) {
  return (
    <div className="bg-blue-50 border border-blue-100 rounded-xl p-5">
      <Icon className="text-blue-600 mb-2" size={22} />
      <p className="text-2xl font-bold text-blue-900 mb-1">{metric}</p>
      <p className="text-sm text-blue-800 leading-snug">{label}</p>
    </div>
  )
}

function TopQuestion({ rank, q, share }: { rank: number; q: string; share: string }) {
  return (
    <div className="flex items-center justify-between bg-gray-50 rounded-lg p-3 border">
      <div className="flex items-center gap-3">
        <span className="bg-blue-600 text-white w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold">
          {rank}
        </span>
        <span className="font-medium text-gray-900">{q}</span>
      </div>
      <span className="text-blue-700 font-semibold">{share}</span>
    </div>
  )
}
