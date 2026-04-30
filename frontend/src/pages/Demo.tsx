import { useState, useRef, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Bot, User, ArrowLeft, RefreshCw, Send } from 'lucide-react'
import { DEMO_CONVERSATIONS, type DemoMessage } from '../api/demo-mock'

type ConvKey = keyof typeof DEMO_CONVERSATIONS

const PERSONAS: { key: ConvKey; label: string; description: string; emoji: string }[] = [
  {
    key: 'student',
    label: 'Aluno',
    description: 'João Silva — pergunta sobre notas e boleto',
    emoji: '🎓',
  },
  {
    key: 'employee',
    label: 'Funcionário',
    description: 'Ana Costa — consulta holerite e férias',
    emoji: '👔',
  },
]

function Bubble({ msg }: { msg: DemoMessage }) {
  const isUser = msg.sender === 'user'
  return (
    <div className={`flex gap-2 ${isUser ? 'flex-row-reverse' : ''}`}>
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

export default function Demo() {
  const [persona, setPersona] = useState<ConvKey | null>(null)
  const [displayed, setDisplayed] = useState<DemoMessage[]>([])
  const [isTyping, setIsTyping] = useState(false)
  const [step, setStep] = useState(0)
  const [inputValue, setInputValue] = useState('')
  const endRef = useRef<HTMLDivElement>(null)

  const messages = persona ? DEMO_CONVERSATIONS[persona] : []

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [displayed, isTyping])

  useEffect(() => {
    if (!persona || step >= messages.length) return

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
  }, [persona, step, messages])

  const handlePersona = (key: ConvKey) => {
    setPersona(key)
    setDisplayed([])
    setStep(0)
    setIsTyping(false)
    setInputValue('')
  }

  const handleReset = () => {
    if (persona) handlePersona(persona)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-4 py-3 flex items-center justify-between max-w-3xl mx-auto">
        <Link to="/" className="flex items-center gap-2 text-gray-600 hover:text-gray-900 text-sm">
          <ArrowLeft size={16} />
          Voltar ao site
        </Link>
        <div className="flex items-center gap-2">
          <div className="bg-blue-600 p-1.5 rounded-lg">
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

      <div className="max-w-3xl mx-auto px-4 py-6">
        {!persona ? (
          /* Tela de seleção de persona */
          <div className="space-y-6">
            <div className="text-center">
              <h1 className="text-2xl font-bold text-gray-900 mb-2">
                Veja a Billie em ação
              </h1>
              <p className="text-gray-500">
                Escolha quem você quer ser nessa simulação de atendimento real.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {PERSONAS.map((p) => (
                <button
                  key={p.key}
                  onClick={() => handlePersona(p.key)}
                  className="card p-6 text-left hover:shadow-md hover:border-blue-300 transition-all border-2 border-transparent"
                >
                  <div className="text-3xl mb-3">{p.emoji}</div>
                  <h3 className="font-semibold text-gray-900 mb-1">{p.label}</h3>
                  <p className="text-sm text-gray-500">{p.description}</p>
                </button>
              ))}
            </div>

            <div className="card p-4 bg-blue-50 border-blue-100">
              <p className="text-sm text-blue-700">
                <strong>Demo simulada</strong> — Todas as respostas são pré-roteirizadas para demonstração.
                No produto real, a Billie usa dados reais da sua instituição via banco de dados.
              </p>
            </div>

            <div className="text-center">
              <Link
                to="/signup"
                className="btn-primary inline-flex items-center gap-2"
              >
                Experimentar grátis por 14 dias
              </Link>
              <p className="text-xs text-gray-400 mt-2">Sem cartão de crédito</p>
            </div>
          </div>
        ) : (
          /* Chat */
          <div className="space-y-4">
            {/* Info banner */}
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-500">
                Simulando como:{' '}
                <strong className="text-gray-800">
                  {PERSONAS.find((p) => p.key === persona)?.description}
                </strong>
              </div>
              <div className="flex gap-2">
                {PERSONAS.map((p) => (
                  <button
                    key={p.key}
                    onClick={() => handlePersona(p.key)}
                    className={`text-xs px-3 py-1 rounded-full border transition-colors ${
                      persona === p.key
                        ? 'bg-blue-600 text-white border-blue-600'
                        : 'bg-white text-gray-600 border-gray-200 hover:border-blue-300'
                    }`}
                  >
                    {p.emoji} {p.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Chat window */}
            <div className="bg-gray-100 rounded-2xl overflow-hidden">
              {/* Chat header (WhatsApp-like) */}
              <div className="bg-green-600 px-4 py-3 flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center">
                  <Bot size={16} className="text-white" />
                </div>
                <div>
                  <p className="text-white text-sm font-medium">Billie — Fac. Anchieta</p>
                  <p className="text-green-200 text-xs">Online</p>
                </div>
              </div>

              {/* Messages */}
              <div className="p-4 space-y-3 min-h-[400px] max-h-[500px] overflow-y-auto bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0naHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmcnIHdpZHRoPScyMCcgaGVpZ2h0PScyMCc+PHJlY3Qgd2lkdGg9JzIwJyBoZWlnaHQ9JzIwJyBmaWxsPScjZjBmNGY4Jy8+PC9zdmc+')] bg-repeat">
                {displayed.map((msg, i) => (
                  <Bubble key={i} msg={msg} />
                ))}
                {isTyping && (
                  <div className="flex gap-2">
                    <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center shrink-0">
                      <Bot size={14} className="text-white" />
                    </div>
                    <div className="bg-white rounded-2xl rounded-tl-none px-4 py-2 shadow-sm border border-gray-100">
                      <div className="flex gap-1 items-center h-4">
                        <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                        <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                        <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                    </div>
                  </div>
                )}
                {step >= messages.length && !isTyping && (
                  <div className="text-center pt-4">
                    <p className="text-xs text-gray-400 mb-3">Fim da simulação</p>
                    <div className="flex flex-col sm:flex-row gap-2 justify-center">
                      <button onClick={handleReset} className="btn-secondary text-xs">
                        <RefreshCw size={12} className="inline mr-1" />
                        Replay
                      </button>
                      <Link to="/signup" className="btn-primary text-xs">
                        Começar grátis
                      </Link>
                    </div>
                  </div>
                )}
                <div ref={endRef} />
              </div>

              {/* Input (decorativo — demo não é interativa) */}
              <div className="bg-white px-3 py-2 flex items-center gap-2 border-t">
                <input
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Digite uma mensagem... (demo simulada)"
                  className="flex-1 text-sm bg-gray-50 rounded-full px-4 py-2 border border-gray-200 outline-none focus:border-green-400"
                  disabled
                />
                <button className="w-9 h-9 bg-green-600 rounded-full flex items-center justify-center opacity-50 cursor-not-allowed">
                  <Send size={14} className="text-white" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
