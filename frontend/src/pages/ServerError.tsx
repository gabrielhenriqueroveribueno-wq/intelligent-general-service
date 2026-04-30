import { AlertTriangle, RefreshCw, Home } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

interface Props {
  error?: Error
  resetError?: () => void
}

export default function ServerError({ error, resetError }: Props) {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center space-y-6">
        <div className="flex justify-center">
          <div className="rounded-full bg-red-100 p-6">
            <AlertTriangle size={48} className="text-red-500" />
          </div>
        </div>

        <div>
          <p className="text-sm font-semibold text-red-500 uppercase tracking-wide mb-2">Erro 500</p>
          <h1 className="text-3xl font-bold text-gray-900 mb-3">Algo deu errado</h1>
          <p className="text-gray-500">
            Ocorreu um erro inesperado no servidor. Nossa equipe foi notificada automaticamente.
          </p>
          {error?.message && (
            <p className="mt-3 text-xs font-mono bg-gray-100 rounded px-3 py-2 text-gray-600 text-left break-all">
              {error.message}
            </p>
          )}
        </div>

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          {resetError && (
            <button
              onClick={resetError}
              className="btn-primary flex items-center gap-2 justify-center"
            >
              <RefreshCw size={16} />
              Tentar novamente
            </button>
          )}
          <button
            onClick={() => navigate('/app/dashboard')}
            className="btn-secondary flex items-center gap-2 justify-center"
          >
            <Home size={16} />
            Ir ao painel
          </button>
        </div>
      </div>
    </div>
  )
}
