import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { useAuth } from '../context/AuthContext'

export interface TrialStatus {
  plan: string
  trial_days_left: number | null
  trial_expired: boolean
  trial_ends_at: string | null
  is_active: boolean
}

export function useTrial() {
  const { user } = useAuth()
  const [status, setStatus] = useState<TrialStatus | null>(null)

  useEffect(() => {
    if (!user?.tenant_id) return
    api.get('/api/v1/billing/status')
      .then(r => setStatus(r.data))
      .catch(() => {/* billing status is optional */})
  }, [user?.tenant_id])

  const isTrial = status?.plan === 'trial'
  const isExpired = status?.plan === 'trial_expired' || status?.trial_expired === true
  const daysLeft = status?.trial_days_left ?? null

  return { status, isTrial, isExpired, daysLeft }
}
