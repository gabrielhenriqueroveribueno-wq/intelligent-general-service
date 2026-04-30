import { useEffect, useState } from 'react'
import { X, Cookie } from 'lucide-react'

const STORAGE_KEY = 'igs_cookie_consent'
const GA_ID = import.meta.env.VITE_GA_MEASUREMENT_ID

function loadGA(id: string) {
  if (document.getElementById('ga-script') || !id) return
  const script = document.createElement('script')
  script.id = 'ga-script'
  script.src = `https://www.googletagmanager.com/gtag/js?id=${id}`
  script.async = true
  document.head.appendChild(script)

  window.dataLayer = window.dataLayer || []
  function gtag(...args: unknown[]) { window.dataLayer.push(args) }
  gtag('js', new Date())
  gtag('config', id, { anonymize_ip: true })
  ;(window as any).gtag = gtag
}

export default function CookieBanner() {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const consent = localStorage.getItem(STORAGE_KEY)
    if (!consent) {
      setVisible(true)
    } else if (consent === 'accepted' && GA_ID) {
      loadGA(GA_ID)
    }
  }, [])

  function accept() {
    localStorage.setItem(STORAGE_KEY, 'accepted')
    if (GA_ID) loadGA(GA_ID)
    setVisible(false)
  }

  function reject() {
    localStorage.setItem(STORAGE_KEY, 'rejected')
    setVisible(false)
  }

  if (!visible) return null

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 p-4 bg-white border-t border-gray-200 shadow-xl">
      <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-start sm:items-center gap-4">
        <Cookie size={22} className="text-blue-600 shrink-0 mt-0.5 sm:mt-0" />
        <p className="text-sm text-gray-700 flex-1">
          Usamos cookies para melhorar sua experiência e analisar o uso da plataforma.{' '}
          Ao aceitar, você concorda com nossa{' '}
          <a href="/legal" className="text-blue-600 hover:underline">Política de Privacidade</a>.
        </p>
        <div className="flex items-center gap-2 shrink-0 w-full sm:w-auto">
          <button
            onClick={reject}
            className="flex-1 sm:flex-none px-4 py-2 text-sm border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
          >
            Recusar
          </button>
          <button
            onClick={accept}
            className="flex-1 sm:flex-none px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
          >
            Aceitar cookies
          </button>
          <button onClick={reject} className="p-1.5 text-gray-400 hover:text-gray-600">
            <X size={16} />
          </button>
        </div>
      </div>
    </div>
  )
}

declare global {
  interface Window {
    dataLayer: unknown[]
    gtag: (...args: unknown[]) => void
  }
}
