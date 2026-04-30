import { Link, useNavigate } from 'react-router-dom'
import { Home, ArrowLeft, Bot } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export default function NotFound() {
  const navigate = useNavigate()
  const { user } = useAuth()

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center px-4">
      <div className="text-center max-w-md">
        <div className="flex justify-center mb-6">
          <div className="bg-blue-100 p-4 rounded-2xl">
            <Bot size={48} className="text-blue-600" />
          </div>
        </div>

        <h1 className="text-8xl font-black text-gray-200 leading-none mb-2">404</h1>
        <h2 className="text-2xl font-bold text-gray-800 mb-3">Página não encontrada</h2>
        <p className="text-gray-500 mb-8">
          A página que você tentou acessar não existe ou foi movida.
        </p>

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button
            onClick={() => navigate(-1)}
            className="btn-secondary flex items-center justify-center gap-2"
          >
            <ArrowLeft size={16} />
            Voltar
          </button>
          <Link
            to={user ? '/app/dashboard' : '/'}
            className="btn-primary flex items-center justify-center gap-2"
          >
            <Home size={16} />
            {user ? 'Ir ao Dashboard' : 'Página inicial'}
          </Link>
        </div>
      </div>
    </div>
  )
}
