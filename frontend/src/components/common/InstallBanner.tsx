import { useState } from 'react'
import { Smartphone, X } from 'lucide-react'
import { dismissInstallPrompt, shouldShowInstallBanner, usePWA } from '../../hooks/usePWA'

/**
 * Banner discreto no rodape (mobile) ou canto inferior direito (desktop)
 * convidando o usuario a instalar o IGS como app.
 *
 * Some apos clique em "Depois" (cooldown de 7 dias) ou "Instalar".
 */
export default function InstallBanner() {
  const { isInstallable, promptInstall } = usePWA()
  const [dismissed, setDismissed] = useState(false)

  const visible = !dismissed && shouldShowInstallBanner(isInstallable)
  if (!visible) return null

  const handleInstall = async () => {
    const result = await promptInstall()
    if (result !== 'unsupported') setDismissed(true)
  }

  const handleLater = () => {
    dismissInstallPrompt()
    setDismissed(true)
  }

  return (
    <div className="fixed bottom-4 inset-x-4 md:left-auto md:right-4 md:max-w-sm z-40 bg-white rounded-xl shadow-2xl border border-blue-200 p-4 animate-slide-up">
      <div className="flex items-start gap-3">
        <div className="bg-blue-600 p-2 rounded-lg flex-shrink-0">
          <Smartphone className="text-white" size={20} />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-gray-900 text-sm">Instale o IGS</p>
          <p className="text-xs text-gray-600 mt-0.5">
            Acesso rápido pela tela inicial, sem abrir o navegador.
          </p>
          <div className="flex gap-2 mt-3">
            <button
              onClick={handleInstall}
              className="flex-1 bg-blue-600 text-white text-xs font-medium px-3 py-1.5 rounded-md hover:bg-blue-700"
            >
              Instalar
            </button>
            <button
              onClick={handleLater}
              className="text-gray-500 text-xs px-3 py-1.5 hover:text-gray-700"
            >
              Depois
            </button>
          </div>
        </div>
        <button
          onClick={handleLater}
          aria-label="Fechar"
          className="text-gray-400 hover:text-gray-600 flex-shrink-0"
        >
          <X size={16} />
        </button>
      </div>
    </div>
  )
}
