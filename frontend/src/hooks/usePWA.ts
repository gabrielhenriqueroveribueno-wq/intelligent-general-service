import { useEffect, useState } from 'react'

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed'; platform: string }>
}

interface PWAState {
  isInstallable: boolean
  isInstalled: boolean
  isOnline: boolean
  promptInstall: () => Promise<'accepted' | 'dismissed' | 'unsupported'>
  isStandalone: boolean
}

const DISMISS_KEY = 'igs_pwa_install_dismissed_at'
const DISMISS_COOLDOWN_MS = 7 * 24 * 60 * 60 * 1000 // 7 dias

export function usePWA(): PWAState {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null)
  const [isOnline, setIsOnline] = useState<boolean>(typeof navigator !== 'undefined' ? navigator.onLine : true)
  const [isInstalled, setIsInstalled] = useState(false)

  useEffect(() => {
    // Detecta modo standalone (rodando como app instalado)
    const mq = window.matchMedia('(display-mode: standalone)')
    const updateInstalled = () => {
      const standaloneIos = (window.navigator as any).standalone === true
      setIsInstalled(mq.matches || standaloneIos)
    }
    updateInstalled()
    mq.addEventListener?.('change', updateInstalled)

    // Captura o prompt antes do navegador exibir
    const handleBeforeInstall = (e: Event) => {
      e.preventDefault()
      setDeferredPrompt(e as BeforeInstallPromptEvent)
    }
    window.addEventListener('beforeinstallprompt', handleBeforeInstall)

    // Quando usuario instala via banner do navegador
    const handleInstalled = () => {
      setIsInstalled(true)
      setDeferredPrompt(null)
      try {
        localStorage.removeItem(DISMISS_KEY)
      } catch {}
    }
    window.addEventListener('appinstalled', handleInstalled)

    // Online/offline
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      mq.removeEventListener?.('change', updateInstalled)
      window.removeEventListener('beforeinstallprompt', handleBeforeInstall)
      window.removeEventListener('appinstalled', handleInstalled)
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])

  const isInstallable = !!deferredPrompt && !isInstalled

  const promptInstall = async (): Promise<'accepted' | 'dismissed' | 'unsupported'> => {
    if (!deferredPrompt) return 'unsupported'
    try {
      await deferredPrompt.prompt()
      const choice = await deferredPrompt.userChoice
      setDeferredPrompt(null)
      if (choice.outcome === 'dismissed') {
        try {
          localStorage.setItem(DISMISS_KEY, String(Date.now()))
        } catch {}
      }
      return choice.outcome
    } catch {
      return 'dismissed'
    }
  }

  const isStandalone = isInstalled

  return { isInstallable, isInstalled, isOnline, promptInstall, isStandalone }
}

/** Dispensa do banner: o usuario clicou em "depois". */
export function dismissInstallPrompt(): void {
  try {
    localStorage.setItem(DISMISS_KEY, String(Date.now()))
  } catch {}
}

/** Banner deve aparecer? Verifica cooldown de 7 dias apos dismiss. */
export function shouldShowInstallBanner(isInstallable: boolean): boolean {
  if (!isInstallable) return false
  try {
    const dismissedAt = localStorage.getItem(DISMISS_KEY)
    if (!dismissedAt) return true
    const elapsed = Date.now() - Number(dismissedAt)
    return elapsed > DISMISS_COOLDOWN_MS
  } catch {
    return true
  }
}
