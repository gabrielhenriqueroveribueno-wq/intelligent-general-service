import { X } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTrial } from '../../hooks/useTrial'

export default function TrialBanner() {
  const { isTrial, daysLeft } = useTrial()
  const [dismissed, setDismissed] = useState(false)
  const navigate = useNavigate()

  if (!isTrial || dismissed || daysLeft === null) return null

  const urgency = daysLeft <= 1 ? 'bg-red-600' : daysLeft <= 3 ? 'bg-orange-500' : 'bg-blue-600'
  const label =
    daysLeft === 0
      ? 'Seu trial expira hoje!'
      : daysLeft === 1
      ? 'Seu trial expira amanhã!'
      : `Seu trial expira em ${daysLeft} dias.`

  return (
    <div className={`${urgency} text-white text-sm flex items-center justify-between px-4 py-2`}>
      <span>
        {label}{' '}
        <button
          onClick={() => navigate('/app/billing')}
          className="underline font-semibold hover:no-underline"
        >
          Escolha um plano agora
        </button>
      </span>
      <button onClick={() => setDismissed(true)} className="ml-4 opacity-80 hover:opacity-100">
        <X size={16} />
      </button>
    </div>
  )
}
