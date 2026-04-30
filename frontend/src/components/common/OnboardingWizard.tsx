import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

const STORAGE_KEY = 'igs_onboarding_done'

interface Step {
  title: string
  description: string
  tip: string
  icon: string
  action?: { label: string; path: string }
}

const STEPS: Step[] = [
  {
    title: 'Configure o WhatsApp',
    description:
      'Conecte seu número WhatsApp Business ao IGS. Você vai precisar de uma conta Meta Business e de um número de telefone dedicado.',
    tip: 'Dica: Use um número exclusivo para o bot. Números pessoais não podem ser usados na API oficial.',
    icon: '📱',
    action: { label: 'Ir para configuração', path: '/app/whatsapp-setup' },
  },
  {
    title: 'Importe seus alunos e funcionários',
    description:
      'Faça upload de planilhas CSV com os dados dos seus alunos e funcionários. O IGS vai usá-los para identificar e responder usuários no WhatsApp.',
    tip: 'Baixe o modelo CSV na página de importação para garantir o formato correto.',
    icon: '👥',
    action: { label: 'Importar dados', path: '/app/import-data' },
  },
  {
    title: 'Teste a Billie',
    description:
      'Envie uma mensagem para o número configurado e veja a Billie responder em tempo real. Experimente perguntar sobre notas, horários ou boletos.',
    tip: 'Na primeira mensagem, o usuário precisa se identificar com o RA ou matrícula.',
    icon: '🤖',
    action: { label: 'Ver conversas', path: '/app/conversations' },
  },
  {
    title: 'Convide sua equipe',
    description:
      'Adicione agentes e gestores ao painel. Eles poderão acompanhar conversas, gerenciar tickets e personalizar respostas da IA.',
    tip: 'Agentes recebem alertas quando a Billie não consegue resolver sozinha (handoff humano).',
    icon: '🏫',
    action: { label: 'Gerenciar usuários', path: '/app/users' },
  },
]

export function useOnboardingWizard() {
  const isDone = () => localStorage.getItem(STORAGE_KEY) === 'done'
  const markDone = () => localStorage.setItem(STORAGE_KEY, 'done')
  return { isDone, markDone }
}

export default function OnboardingWizard({ onClose }: { onClose: () => void }) {
  const [step, setStep] = useState(0)
  const navigate = useNavigate()
  const { markDone } = useOnboardingWizard()

  const current = STEPS[step]
  const isLast = step === STEPS.length - 1

  const handleClose = () => {
    markDone()
    onClose()
  }

  const handleAction = () => {
    if (current.action) {
      handleClose()
      navigate(current.action.path)
    }
  }

  const handleNext = () => {
    if (isLast) {
      handleClose()
    } else {
      setStep((s) => s + 1)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 pt-6 pb-8 text-white">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold uppercase tracking-wide opacity-80">
              Primeiros passos
            </span>
            <button
              onClick={handleClose}
              className="text-white/60 hover:text-white text-lg leading-none"
              aria-label="Fechar"
            >
              ✕
            </button>
          </div>

          {/* Progress bar */}
          <div className="flex gap-1.5 mb-5">
            {STEPS.map((_, i) => (
              <div
                key={i}
                className={`h-1 flex-1 rounded-full transition-all duration-300 ${
                  i <= step ? 'bg-white' : 'bg-white/30'
                }`}
              />
            ))}
          </div>

          <div className="flex items-center gap-3">
            <span className="text-4xl">{current.icon}</span>
            <div>
              <p className="text-xs opacity-70 mb-0.5">
                Passo {step + 1} de {STEPS.length}
              </p>
              <h2 className="text-xl font-bold">{current.title}</h2>
            </div>
          </div>
        </div>

        {/* Body */}
        <div className="px-6 py-5 space-y-4">
          <p className="text-gray-700 text-sm leading-relaxed">{current.description}</p>

          <div className="bg-blue-50 border border-blue-100 rounded-xl px-4 py-3 text-sm text-blue-700">
            <span className="font-semibold">💡 </span>
            {current.tip}
          </div>

          {current.action && (
            <button
              onClick={handleAction}
              className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl py-2.5 text-sm transition-colors"
            >
              {current.action.label} →
            </button>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 pb-5 flex items-center justify-between gap-3">
          <button
            onClick={handleClose}
            className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
          >
            Pular configuração inicial
          </button>

          <div className="flex gap-2">
            {step > 0 && (
              <button
                onClick={() => setStep((s) => s - 1)}
                className="px-4 py-2 border border-gray-200 text-gray-600 rounded-xl text-sm hover:bg-gray-50 transition-colors"
              >
                Voltar
              </button>
            )}
            <button
              onClick={handleNext}
              className="px-5 py-2 bg-gray-900 text-white rounded-xl text-sm font-medium hover:bg-gray-700 transition-colors"
            >
              {isLast ? 'Concluir' : 'Próximo'}
            </button>
          </div>
        </div>

        {/* Step dots */}
        <div className="pb-4 flex justify-center gap-1.5">
          {STEPS.map((_, i) => (
            <button
              key={i}
              onClick={() => setStep(i)}
              className={`w-2 h-2 rounded-full transition-all ${
                i === step ? 'bg-indigo-600 w-4' : 'bg-gray-300 hover:bg-gray-400'
              }`}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
