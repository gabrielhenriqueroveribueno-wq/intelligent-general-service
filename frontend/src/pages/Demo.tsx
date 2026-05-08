import { useState, useRef, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Bot, User, ArrowLeft, RefreshCw, Send, Sparkles, Wand2 } from 'lucide-react'
import { DEMO_CONVERSATIONS, type DemoMessage } from '../api/demo-mock'

type ConvKey = keyof typeof DEMO_CONVERSATIONS
type Mode = 'auto' | 'free'

const PERSONAS: { key: ConvKey; label: string; description: string; emoji: string }[] = [
  {
    key: 'student',
    label: 'Aluno',
    description: 'Ana Carolina — pergunta sobre notas e boleto',
    emoji: '🎓',
  },
  {
    key: 'employee',
    label: 'Funcionário',
    description: 'Carlos Eduardo — consulta holerite e férias',
    emoji: '👔',
  },
]

// ─── Respostas mockadas por keyword (modo livre) ────────────────────────────

interface KeywordResponse {
  keywords: string[]
  text: string
}

const STUDENT_RESPONSES: KeywordResponse[] = [
  {
    keywords: ['nota', 'boletim', 'média'],
    text: 'Suas notas do semestre, *Ana*:\n\n- *Cálculo II* — P1: 7.5 | P2: 8.0\n- *Programação Web* — P1: 9.0 | P2: 9.5\n- *Banco de Dados II* — P1: 6.5 | P2: 5.0 ⚠️\n- *Eng. Software* — P1: 8.0 | P2: 8.5',
  },
  {
    keywords: ['boleto', 'pagar', 'mensalidade'],
    text: 'Seu boleto de *abril/2026*:\n- Valor: R$ 1.890,00\n- Vencimento: 10/04/2026\n- Status: Pendente\n\nQuer o link de pagamento?',
  },
  {
    keywords: ['frequência', 'falta', 'presença'],
    text: 'Sua frequência neste semestre:\n\n- Cálculo II: 92%\n- Prog. Web: 100%\n- Banco de Dados II: 78% ⚠️\n- Eng. Software: 88%\n\nFique atenta na disciplina de Banco de Dados — limite mínimo é 75%.',
  },
  {
    keywords: ['horário', 'aula', 'sala'],
    text: 'Suas aulas de hoje:\n\n- 19h00 — Cálculo II (Sala 304)\n- 20h45 — Banco de Dados II (Lab 12)',
  },
  {
    keywords: ['biblioteca', 'livro', 'empréstimo'],
    text: 'Você tem 1 livro em empréstimo:\n\n- "Estruturas de Dados" — devolução até 12/05/2026',
  },
]

const EMPLOYEE_RESPONSES: KeywordResponse[] = [
  {
    keywords: ['holerite', 'salário', 'contracheque'],
    text: 'Seu holerite de *março/2026*:\n\n- Bruto: R$ 4.800,00\n- INSS: -R$ 432,00\n- IRRF: -R$ 168,00\n- VT: -R$ 288,00\n- *Líquido: R$ 3.912,00*',
  },
  {
    keywords: ['férias', 'recesso'],
    text: 'Saldo de férias:\n\n- Total: 30 dias\n- Usados: 12 dias\n- *Disponíveis: 18 dias*\n- Prazo: até 15/08/2026',
  },
  {
    keywords: ['ponto', 'horário', 'banco de horas'],
    text: 'Seu banco de horas em abril:\n\n- Saldo: +6h30min\n- Última batida: hoje, 08:02',
  },
  {
    keywords: ['solicitação', 'rh', 'pedido'],
    text: 'Você pode solicitar:\n\n1. Férias\n2. Atestado médico\n3. Adiantamento de salário\n4. Mudança de turno\n\nQual você quer abrir?',
  },
]

const FALLBACK_RESPONSES = [
  'Entendi! Estou consultando o sistema...\n\nNão achei essa informação específica. Posso transferir pra um atendente humano se preferir.',
  'Hmm, não encontrei dados sobre isso. Mas posso te ajudar com: notas, boletos, frequência, horário, biblioteca.',
  'Vou repassar para um atendente humano. Em breve alguém da secretaria vai te chamar! 👍',
]

function findResponse(text: string, persona: ConvKey): string {
  const lower = text.toLowerCase()
  const responses = persona === 'student' ? STUDENT_RESPONSES : EMPLOYEE_RESPONSES
  const match = responses.find((r) => r.keywords.some((k) => lower.includes(k)))
  if (match) return match.text
  return FALLBACK_RESPONSES[Math.floor(Math.random() * FALLBACK_RESPONSES.length)]
}

const SUGGESTIONS: Record<ConvKey, string[]> = {
  student: ['Quais minhas notas?', 'Quero pagar o boleto', 'Como está minha frequência?'],
  employee: ['Ver meu holerite', 'Saldo de férias', 'Solicitar atestado'],
}

// ─── Componentes ────────────────────────────────────────────────────────────

function Bubble({ msg }: { msg: DemoMessage }) {
  const isUser = msg.sender === 'user'
  return (
    <div className={`flex gap-2 animate-slide-in-right ${isUser ? 'flex-row-reverse' : ''}`}>
      <div
        className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${
          isUser ? 'bg-green-100' : 'bg-blue-600'
        }`}
      >
        {isUser ? (
          <User size={14} className="text-green-700" />
        ) : (
          <Bot size={14} className="text-white" />
        )}
      </div>
      <div
        className={`max-w-[80%] rounded-2xl px-3 py-2 text-sm leading-relaxed whitespace-pre-wrap ${
          isUser
            ? 'bg-green-100 text-gray-800 rounded-tr-none'
            : 'bg-white text-gray-800 shadow-sm border border-gray-100 rounded-tl-none'
        }`}
      >
        {msg.text}
      </div>
    </div>
  )
}

function TypingBubble() {
  return (
    <div className="flex gap-2 animate-slide-in-right">
      <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center shrink-0">
        <Bot size={14} className="text-white" />
      </div>
      <div className="bg-white rounded-2xl rounded-tl-none px-4 py-2 shadow-sm border border-gray-100">
        <div className="flex gap-1 items-center h-4">
          <div
            className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"
            style={{ animationDelay: '0ms' }}
          />
          <div
            className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"
            style={{ animationDelay: '150ms' }}
          />
          <div
            className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"
            style={{ animationDelay: '300ms' }}
          />
        </div>
      </div>
    </div>
  )
}

export default function Demo() {
  const [persona, setPersona] = useState<ConvKey | null>(null)
  const [mode, setMode] = useState<Mode>('auto')
  const [displayed, setDisplayed] = useState<DemoMessage[]>([])
  const [isTyping, setIsTyping] = useState(false)
  const [step, setStep] = useState(0)
  const [inputValue, setInputValue] = useState('')
  const endRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const messages = persona ? DEMO_CONVERSATIONS[persona] : []

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [displayed, isTyping])

  // Modo auto: roda script
  useEffect(() => {
    if (!persona || mode !== 'auto' || step >= messages.length) return

    const msg = messages[step]
    const delay = step === 0 ? 400 : msg.sender === 'bot' ? 800 : 400

    const timer = setTimeout(() => {
      if (msg.sender === 'bot') {
        setIsTyping(true)
        setTimeout(() => {
          setIsTyping(false)
          setDisplayed((prev) => [...prev, msg])
          setStep((s) => s + 1)
        }, 1200)
      } else {
        setDisplayed((prev) => [...prev, msg])
        setStep((s) => s + 1)
      }
    }, delay)

    return () => clearTimeout(timer)
  }, [persona, step, messages, mode])

  const handlePersona = (key: ConvKey, newMode: Mode = 'auto') => {
    setPersona(key)
    setMode(newMode)
    setDisplayed(
      newMode === 'free'
        ? [
            {
              sender: 'bot',
              text:
                key === 'student'
                  ? 'Oi *Ana*! Sou a Billie 😊 Como posso te ajudar? Pergunte sobre notas, boletos, frequência ou biblioteca.'
                  : 'Oi *Carlos*! Como posso te ajudar? Pode perguntar sobre holerite, férias, ponto ou abrir solicitações.',
            },
          ]
        : [],
    )
    setStep(0)
    setIsTyping(false)
    setInputValue('')
    setTimeout(() => inputRef.current?.focus(), 100)
  }

  const handleReset = () => {
    if (persona) handlePersona(persona, mode)
  }

  const handleSend = (text?: string) => {
    if (!persona || mode !== 'free') return
    const userMsg = (text ?? inputValue).trim()
    if (!userMsg) return

    setInputValue('')
    setDisplayed((prev) => [...prev, { sender: 'user', text: userMsg }])

    setIsTyping(true)
    setTimeout(() => {
      const reply = findResponse(userMsg, persona)
      setIsTyping(false)
      setDisplayed((prev) => [...prev, { sender: 'bot', text: reply }])
    }, 800 + Math.random() * 600)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSend()
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur border-b px-4 py-3 flex items-center justify-between max-w-4xl mx-auto sticky top-0 z-10">
        <Link to="/" className="flex items-center gap-2 text-gray-600 hover:text-gray-900 text-sm">
          <ArrowLeft size={16} />
          Voltar
        </Link>
        <div className="flex items-center gap-2">
          <div className="bg-gradient-to-br from-blue-600 to-indigo-600 p-1.5 rounded-lg">
            <Bot size={16} className="text-white" />
          </div>
          <span className="font-semibold text-sm">Demo — Billie IGS</span>
        </div>
        {persona && (
          <button
            onClick={handleReset}
            className="text-sm text-gray-500 hover:text-gray-800 flex items-center gap-1"
          >
            <RefreshCw size={14} />
            Reiniciar
          </button>
        )}
        {!persona && <div className="w-20" />}
      </div>

      <div className="max-w-4xl mx-auto px-4 py-6">
        {!persona ? (
          /* Tela de seleção de persona */
          <div className="space-y-6">
            <div className="text-center pt-6">
              <div className="inline-flex items-center gap-2 bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-xs font-medium mb-4">
                <Sparkles size={12} /> Demo interativa
              </div>
              <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-3">
                Veja a Billie em ação
              </h1>
              <p className="text-gray-600 max-w-xl mx-auto">
                Escolha quem você quer ser nessa simulação. Você pode rodar o tour guiado
                ou conversar livremente com a IA.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {PERSONAS.map((p) => (
                <div
                  key={p.key}
                  className="card p-6 hover:shadow-lg transition-all border-2 border-transparent hover:border-blue-300"
                >
                  <div className="text-4xl mb-3">{p.emoji}</div>
                  <h3 className="font-semibold text-gray-900 mb-1 text-lg">{p.label}</h3>
                  <p className="text-sm text-gray-500 mb-4">{p.description}</p>
                  <div className="flex flex-col gap-2">
                    <button
                      onClick={() => handlePersona(p.key, 'auto')}
                      className="btn-primary text-sm flex items-center justify-center gap-2"
                    >
                      <Sparkles size={14} /> Tour guiado
                    </button>
                    <button
                      onClick={() => handlePersona(p.key, 'free')}
                      className="btn-secondary text-sm flex items-center justify-center gap-2"
                    >
                      <Wand2 size={14} /> Conversar livremente
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="card p-4 bg-blue-50 border-blue-100">
              <p className="text-sm text-blue-700">
                <strong>Demo simulada</strong> — As respostas são roteirizadas. No produto
                real, a Billie usa dados reais via banco de dados da sua instituição.
              </p>
            </div>

            <div className="text-center">
              <Link to="/signup" className="btn-primary inline-flex items-center gap-2">
                Experimentar grátis por 14 dias
              </Link>
              <p className="text-xs text-gray-400 mt-2">Sem cartão de crédito</p>
            </div>
          </div>
        ) : (
          /* Chat */
          <div className="space-y-4">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="text-sm text-gray-500">
                Como:{' '}
                <strong className="text-gray-800">
                  {PERSONAS.find((p) => p.key === persona)?.description}
                </strong>
              </div>
              <div className="flex gap-1 bg-white rounded-lg border p-1">
                <button
                  onClick={() => handlePersona(persona, 'auto')}
                  className={`text-xs px-3 py-1 rounded transition-colors flex items-center gap-1 ${
                    mode === 'auto' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  <Sparkles size={12} /> Tour
                </button>
                <button
                  onClick={() => handlePersona(persona, 'free')}
                  className={`text-xs px-3 py-1 rounded transition-colors flex items-center gap-1 ${
                    mode === 'free' ? 'bg-blue-600 text-white' : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  <Wand2 size={12} /> Livre
                </button>
              </div>
            </div>

            {/* Mockup de celular */}
            <div className="max-w-md mx-auto bg-gray-900 rounded-[2rem] p-2 shadow-2xl">
              <div className="bg-gray-100 rounded-[1.5rem] overflow-hidden">
                {/* WhatsApp header */}
                <div className="bg-green-600 px-4 py-3 flex items-center gap-3">
                  <ArrowLeft size={18} className="text-white" />
                  <div className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center">
                    <Bot size={18} className="text-white" />
                  </div>
                  <div className="flex-1">
                    <p className="text-white text-sm font-medium">Billie — Anchieta</p>
                    <p className="text-green-200 text-[11px] flex items-center gap-1">
                      <span className="inline-block w-1.5 h-1.5 rounded-full bg-green-300 animate-pulse" />
                      Online
                    </p>
                  </div>
                </div>

                {/* Messages */}
                <div className="p-4 space-y-3 h-[440px] overflow-y-auto bg-[#e5ddd5]">
                  {displayed.map((msg, i) => (
                    <Bubble key={i} msg={msg} />
                  ))}
                  {isTyping && <TypingBubble />}
                  {mode === 'auto' && step >= messages.length && !isTyping && (
                    <div className="text-center pt-4">
                      <p className="text-xs text-gray-500 mb-3 bg-white/80 rounded-full inline-block px-3 py-1">
                        Fim da simulação
                      </p>
                      <div className="flex flex-col sm:flex-row gap-2 justify-center mt-2">
                        <button onClick={handleReset} className="btn-secondary text-xs">
                          <RefreshCw size={12} className="inline mr-1" />
                          Repetir
                        </button>
                        <button
                          onClick={() => handlePersona(persona, 'free')}
                          className="btn-primary text-xs"
                        >
                          <Wand2 size={12} className="inline mr-1" />
                          Conversar livremente
                        </button>
                      </div>
                    </div>
                  )}
                  <div ref={endRef} />
                </div>

                {/* Sugestões + Input */}
                {mode === 'free' && (
                  <>
                    {SUGGESTIONS[persona].length > 0 && displayed.length < 3 && (
                      <div className="bg-white px-3 py-2 border-t flex gap-2 overflow-x-auto">
                        {SUGGESTIONS[persona].map((s) => (
                          <button
                            key={s}
                            onClick={() => handleSend(s)}
                            className="text-xs whitespace-nowrap px-3 py-1 bg-blue-50 text-blue-700 rounded-full border border-blue-100 hover:bg-blue-100 transition-colors"
                          >
                            {s}
                          </button>
                        ))}
                      </div>
                    )}
                    <div className="bg-white px-3 py-2 flex items-center gap-2 border-t">
                      <input
                        ref={inputRef}
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={handleKeyPress}
                        placeholder="Digite uma mensagem..."
                        className="flex-1 text-sm bg-gray-100 rounded-full px-4 py-2 outline-none focus:bg-white focus:ring-2 focus:ring-green-400"
                      />
                      <button
                        onClick={() => handleSend()}
                        disabled={!inputValue.trim()}
                        className="w-9 h-9 bg-green-600 rounded-full flex items-center justify-center disabled:opacity-50 hover:bg-green-700 transition-colors"
                      >
                        <Send size={14} className="text-white" />
                      </button>
                    </div>
                  </>
                )}

                {mode === 'auto' && (
                  <div className="bg-white px-3 py-2 flex items-center gap-2 border-t opacity-50">
                    <input
                      placeholder="Tour guiado em andamento..."
                      className="flex-1 text-sm bg-gray-100 rounded-full px-4 py-2 outline-none cursor-not-allowed"
                      disabled
                    />
                    <button className="w-9 h-9 bg-gray-400 rounded-full flex items-center justify-center cursor-not-allowed">
                      <Send size={14} className="text-white" />
                    </button>
                  </div>
                )}
              </div>
            </div>

            <div className="text-center">
              <Link to="/signup" className="btn-primary inline-flex items-center gap-2 text-sm">
                Experimentar 14 dias grátis
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
