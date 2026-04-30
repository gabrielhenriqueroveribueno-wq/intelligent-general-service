import { Wrench, RefreshCw } from 'lucide-react'

export default function Maintenance() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center space-y-6">
        <div className="flex justify-center">
          <div className="rounded-full bg-blue-100 p-6">
            <Wrench size={48} className="text-blue-600" />
          </div>
        </div>

        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-3">Em manutenção</h1>
          <p className="text-gray-600">
            O sistema está passando por atualizações programadas. Estaremos de volta em breve.
          </p>
          <p className="mt-2 text-sm text-gray-500">
            Enquanto isso, você pode acompanhar o status em{' '}
            <a
              href="https://status.igs.com.br"
              className="text-blue-600 hover:underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              status.igs.com.br
            </a>
          </p>
        </div>

        <button
          onClick={() => window.location.reload()}
          className="btn-primary flex items-center gap-2 mx-auto"
        >
          <RefreshCw size={16} />
          Recarregar página
        </button>
      </div>
    </div>
  )
}
