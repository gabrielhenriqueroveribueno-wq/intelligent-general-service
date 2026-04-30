import { WifiOff } from 'lucide-react'
import { usePWA } from '../../hooks/usePWA'

/**
 * Banner fino no topo da tela quando o usuario esta offline.
 * Auto-some ao reconectar.
 */
export default function OfflineBanner() {
  const { isOnline } = usePWA()
  if (isOnline) return null

  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed top-0 inset-x-0 z-50 bg-amber-500 text-white text-xs py-1.5 px-3 flex items-center justify-center gap-2 shadow-md"
    >
      <WifiOff size={14} />
      <span>Você está offline. Mostrando dados do último carregamento.</span>
    </div>
  )
}
