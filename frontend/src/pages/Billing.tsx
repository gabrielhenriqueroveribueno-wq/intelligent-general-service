import { useQuery, useMutation } from '@tanstack/react-query'
import {
  CreditCard,
  CheckCircle2,
  Zap,
  Building2,
  Loader2,
  ExternalLink,
  AlertCircle,
} from 'lucide-react'
import toast from 'react-hot-toast'
import clsx from 'clsx'
import { api } from '../api/client'

interface BillingStatus {
  found: boolean
  tenant_id: string
  plan: string
  is_active: boolean
  trial_ends_at?: string | null
  subscription_status?: string
  next_billing_date?: string | null
  monthly_messages?: number
  message_limit?: number
}

const PLANS = [
  {
    id: 'trial',
    name: 'Trial',
    price: 'Grátis',
    period: '14 dias',
    color: 'gray',
    features: ['Até 500 mensagens/mês', '1 número WhatsApp', 'Suporte por email'],
  },
  {
    id: 'starter',
    name: 'Starter',
    price: 'R$ 297',
    period: '/mês',
    color: 'blue',
    features: [
      'Até 5.000 mensagens/mês',
      '1 número WhatsApp',
      'Base de conhecimento ilimitada',
      'Relatórios semanais',
      'Suporte prioritário',
    ],
    checkoutPlan: 'starter',
  },
  {
    id: 'pro',
    name: 'Pro',
    price: 'R$ 497',
    period: '/mês',
    color: 'purple',
    features: [
      'Mensagens ilimitadas',
      'Até 3 números WhatsApp',
      'API personalizada',
      'SLA garantido',
      'Gerente de conta dedicado',
    ],
    checkoutPlan: 'pro',
  },
]

export default function Billing() {
  const { data: status, isLoading } = useQuery({
    queryKey: ['billing-status'],
    queryFn: () => api.get('/api/v1/billing/status').then((r) => r.data as BillingStatus),
    retry: false,
  })

  const subscribeMutation = useMutation({
    mutationFn: (plan: string) =>
      api.post(`/api/v1/billing/subscribe?plan=${plan}`).then((r) => r.data),
    onSuccess: (data) => {
      const url = data.subscription_url || data.checkout_url || data.sandbox_url
      if (url) {
        window.open(url, '_blank')
        toast.success('Redirecionando para o pagamento...')
      } else {
        toast.error('Link de pagamento não disponível')
      }
    },
    onError: (err: any) => {
      toast.error(err?.response?.data?.detail || 'Erro ao gerar assinatura')
    },
  })

  const currentPlan = status?.plan || 'trial'
  const isTrialExpired =
    status?.trial_ends_at && new Date(status.trial_ends_at) < new Date()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Plano e Cobrança</h1>
        <p className="text-sm text-gray-500">Gerencie seu plano e assinatura</p>
      </div>

      {/* Status atual */}
      {isLoading ? (
        <div className="card flex justify-center py-8">
          <Loader2 className="animate-spin text-blue-600" size={24} />
        </div>
      ) : (
        <div className="card">
          <div className="flex items-center gap-3 mb-4">
            <CreditCard size={20} className="text-blue-600" />
            <h2 className="font-semibold text-gray-900">Status atual</h2>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div>
              <p className="text-xs text-gray-500">Plano</p>
              <p className="font-bold text-gray-900 capitalize">{currentPlan}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Status</p>
              <p className={clsx('font-bold', status?.is_active ? 'text-green-600' : 'text-red-500')}>
                {status?.is_active ? 'Ativo' : 'Inativo'}
              </p>
            </div>
            {status?.monthly_messages !== undefined && (
              <div>
                <p className="text-xs text-gray-500">Mensagens no mês</p>
                <p className="font-bold text-gray-900">
                  {status.monthly_messages.toLocaleString('pt-BR')}
                  {status.message_limit ? ` / ${status.message_limit.toLocaleString('pt-BR')}` : ''}
                </p>
              </div>
            )}
            {status?.trial_ends_at && (
              <div>
                <p className="text-xs text-gray-500">Trial termina em</p>
                <p className={clsx('font-bold', isTrialExpired ? 'text-red-500' : 'text-gray-900')}>
                  {new Date(status.trial_ends_at).toLocaleDateString('pt-BR')}
                </p>
              </div>
            )}
          </div>

          {isTrialExpired && (
            <div className="mt-4 flex items-center gap-2 bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
              <AlertCircle size={16} />
              Seu período de trial expirou. Faça upgrade para continuar usando.
            </div>
          )}
        </div>
      )}

      {/* Planos */}
      <div className="grid sm:grid-cols-3 gap-4">
        {PLANS.map((plan) => {
          const isCurrent = currentPlan === plan.id
          return (
            <div
              key={plan.id}
              className={clsx(
                'card relative',
                isCurrent && 'border-2 border-blue-500',
              )}
            >
              {isCurrent && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="bg-blue-500 text-white text-xs font-bold px-3 py-1 rounded-full">
                    Plano atual
                  </span>
                </div>
              )}

              {plan.id === 'pro' && (
                <div className="absolute -top-3 right-4">
                  <span className="bg-purple-500 text-white text-xs font-bold px-3 py-1 rounded-full flex items-center gap-1">
                    <Zap size={10} /> Popular
                  </span>
                </div>
              )}

              <div className="mb-4">
                <h3 className="text-lg font-bold text-gray-900">{plan.name}</h3>
                <div className="flex items-baseline gap-1">
                  <span className="text-2xl font-bold text-gray-900">{plan.price}</span>
                  {plan.period && (
                    <span className="text-sm text-gray-500">{plan.period}</span>
                  )}
                </div>
              </div>

              <ul className="space-y-2 mb-6">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-gray-600">
                    <CheckCircle2 size={14} className="text-green-500 shrink-0 mt-0.5" />
                    {f}
                  </li>
                ))}
              </ul>

              {plan.checkoutPlan && !isCurrent && (
                <button
                  onClick={() => subscribeMutation.mutate(plan.checkoutPlan!)}
                  disabled={subscribeMutation.isPending}
                  className={clsx(
                    'w-full py-2 rounded-lg text-sm font-medium flex items-center justify-center gap-2',
                    plan.id === 'pro'
                      ? 'bg-purple-600 text-white hover:bg-purple-700'
                      : 'bg-blue-600 text-white hover:bg-blue-700',
                    'disabled:opacity-50',
                  )}
                >
                  {subscribeMutation.isPending ? (
                    <Loader2 className="animate-spin" size={14} />
                  ) : (
                    <ExternalLink size={14} />
                  )}
                  Assinar {plan.name}
                </button>
              )}

              {isCurrent && (
                <div className="text-center text-sm text-gray-400 mt-auto pt-4">
                  <Building2 size={16} className="mx-auto mb-1 text-gray-300" />
                  Plano ativo
                </div>
              )}
            </div>
          )
        })}
      </div>

      <p className="text-xs text-gray-400 text-center">
        Pagamentos processados de forma segura via Mercado Pago. Cancele a qualquer momento.
      </p>
    </div>
  )
}
