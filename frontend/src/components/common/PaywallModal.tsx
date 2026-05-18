import { useNavigate } from 'react-router-dom'
import { useTrial } from '../../hooks/useTrial'

export default function PaywallModal() {
  const { isExpired } = useTrial()
  const navigate = useNavigate()

  if (!isExpired) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl p-8 max-w-md w-full mx-4 text-center">
        <div className="text-5xl mb-4">⏰</div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Seu período de trial encerrou
        </h2>
        <p className="text-gray-500 dark:text-gray-400 mb-6">
          Para continuar usando o IGS e não perder seus dados, escolha um plano. Leva menos de 2 minutos.
        </p>

        <div className="flex flex-col gap-3">
          <button
            onClick={() => navigate('/app/billing')}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-xl transition-colors"
          >
            Ver planos e assinar
          </button>
          <a
            href="https://wa.me/5511999999999?text=Quero+contratar+o+IGS"
            target="_blank"
            rel="noopener noreferrer"
            className="w-full border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 font-medium py-3 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
          >
            Falar com a equipe comercial
          </a>
        </div>

        <p className="text-xs text-gray-400 mt-4">
          Seus dados ficam salvos por 30 dias após o encerramento do trial.
        </p>
      </div>
    </div>
  )
}
