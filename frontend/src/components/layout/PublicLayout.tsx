import { Link, Outlet, useLocation } from 'react-router-dom'
import { Bot } from 'lucide-react'

export default function PublicLayout() {
  const location = useLocation()
  const isHome = location.pathname === '/'
  return (
    <div className="min-h-screen flex flex-col bg-white">
      {/* Header */}
      <header className="border-b border-gray-200 sticky top-0 z-40 bg-white/95 backdrop-blur">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <div className="bg-blue-600 p-2 rounded-lg">
              <Bot className="text-white" size={20} />
            </div>
            <div>
              <p className="font-bold text-sm leading-tight">IGS</p>
              <p className="text-xs text-gray-500 leading-tight">Atendimento Inteligente</p>
            </div>
          </Link>
          <nav className="flex items-center gap-6 text-sm">
            <Link to="/case-study" className="text-gray-700 hover:text-gray-900 hidden sm:inline">
              Caso de uso
            </Link>
            {isHome ? (
              <a href="#funcionalidades" className="text-gray-700 hover:text-gray-900 hidden sm:inline">
                Funcionalidades
              </a>
            ) : null}
            <Link to="/pricing" className="text-gray-700 hover:text-gray-900 hidden sm:inline">
              Preços
            </Link>
            <Link to="/demo" className="text-gray-700 hover:text-gray-900 hidden md:inline">
              Demo
            </Link>
            <Link
              to="/login"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
            >
              Entrar
            </Link>
          </nav>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-gray-50">
        <div className="max-w-6xl mx-auto px-6 py-8 text-sm text-gray-600 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <div className="bg-blue-600 p-1.5 rounded">
                <Bot className="text-white" size={14} />
              </div>
              <span className="font-bold text-gray-900">IGS</span>
            </div>
            <p>Atendimento inteligente via WhatsApp para instituições de ensino.</p>
          </div>
          <div>
            <h4 className="font-semibold text-gray-900 mb-2">Produto</h4>
            <ul className="space-y-1">
              <li>
                <Link to="/demo" className="hover:text-gray-900">Demonstração</Link>
              </li>
              <li>
                <Link to="/case-study" className="hover:text-gray-900">Caso de uso</Link>
              </li>
              <li>
                <Link to="/pricing" className="hover:text-gray-900">Preços</Link>
              </li>
              <li>
                <Link to="/tour" className="hover:text-gray-900">Tour guiado</Link>
              </li>
              <li>
                <Link to="/status" className="hover:text-gray-900">Status</Link>
              </li>
              <li>
                <Link to="/changelog" className="hover:text-gray-900">Changelog</Link>
              </li>
              <li>
                <Link to="/legal" className="hover:text-gray-900">Termos & Privacidade</Link>
              </li>
            </ul>
          </div>
          <div>
            <h4 className="font-semibold text-gray-900 mb-2">Contato & Recursos</h4>
            <ul className="space-y-1">
              <li>contato@igs.com.br</li>
              <li>WhatsApp: (11) 99999-9999</li>
              <li className="mt-2">
                <a
                  href="/api/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-gray-900"
                >
                  Documentação da API →
                </a>
              </li>
            </ul>
          </div>
        </div>
        <div className="border-t border-gray-200 py-4 text-center text-xs text-gray-500">
          © {new Date().getFullYear()} IGS — Intelligent General Service. Todos os direitos
          reservados.
        </div>
      </footer>
    </div>
  )
}
