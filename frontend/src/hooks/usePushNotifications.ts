import { useCallback, useEffect, useState } from 'react'
import { api } from '../api/client'

type PushState = 'unsupported' | 'denied' | 'subscribed' | 'unsubscribed'

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
  const rawData = atob(base64)
  return Uint8Array.from([...rawData].map((c) => c.charCodeAt(0)))
}

async function getVapidPublicKey(): Promise<string | null> {
  try {
    const res = await api.get<{ public_key: string; enabled: boolean }>(
      '/push-subscriptions/vapid-public-key'
    )
    return res.data.enabled ? res.data.public_key : null
  } catch {
    return null
  }
}

async function registerSubscription(sub: PushSubscription): Promise<void> {
  const json = sub.toJSON() as { endpoint: string; keys: { p256dh: string; auth: string } }
  await api.post('/push-subscriptions', {
    endpoint: json.endpoint,
    p256dh: json.keys.p256dh,
    auth: json.keys.auth,
    user_agent: navigator.userAgent.slice(0, 200),
  })
}

export function usePushNotifications() {
  const [state, setState] = useState<PushState>('unsubscribed')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
      setState('unsupported')
      return
    }
    if (Notification.permission === 'denied') {
      setState('denied')
      return
    }
    // Check existing subscription
    navigator.serviceWorker.ready.then((reg) =>
      reg.pushManager.getSubscription().then((sub) => {
        if (sub) setState('subscribed')
      })
    )
  }, [])

  const subscribe = useCallback(async () => {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) return
    setLoading(true)
    try {
      const publicKey = await getVapidPublicKey()
      if (!publicKey) return

      const reg = await navigator.serviceWorker.ready
      const sub = await reg.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(publicKey).buffer as ArrayBuffer,
      })
      await registerSubscription(sub)
      setState('subscribed')
    } catch (err) {
      if ((err as Error).name === 'NotAllowedError') setState('denied')
      console.error('Push subscribe error:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  const unsubscribe = useCallback(async () => {
    setLoading(true)
    try {
      const reg = await navigator.serviceWorker.ready
      const sub = await reg.pushManager.getSubscription()
      if (sub) {
        const hash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(sub.endpoint))
        const hex = Array.from(new Uint8Array(hash))
          .map((b) => b.toString(16).padStart(2, '0'))
          .join('')
          .slice(0, 16)
        await sub.unsubscribe()
        await api.delete(`/push-subscriptions/${hex}`).catch(() => {})
      }
      setState('unsubscribed')
    } catch (err) {
      console.error('Push unsubscribe error:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  return { state, loading, subscribe, unsubscribe }
}
