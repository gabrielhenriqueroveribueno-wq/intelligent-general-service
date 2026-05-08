import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { Bot, Eye, EyeOff, Lock } from 'lucide-react'
import { api } from '../api/client'
import toast from 'react-hot-toast'

interface ChangePasswordForm {
  current_password: string
  new_password: string
  confirm_password: string
}

export default function ChangePassword() {
  const navigate = useNavigate()
  const [showCurrent, setShowCurrent] = useState(false)
  const [showNew, setShowNew] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const { register, handleSubmit, watch, formState: { errors } } = useForm<ChangePasswordForm>()
  const newPassword = watch('new_password')

  const onSubmit = async (data: ChangePasswordForm) => {
    setIsLoading(true)
    try {
      await api.post('/api/v1/auth/change-password', {
        current_password: data.current_password,
        new_password: data.new_password,
      })
      toast.success('Senha alterada com sucesso!')
      navigate('/app/dashboard')
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Erro ao alterar senha'
      toast.error(msg)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 to-gray-900 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center bg-orange-500 p-3 rounded-2xl mb-4">
            <Lock size={32} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Troque sua senha</h1>
          <p className="text-gray-500 text-sm mt-1">
            Por segurança, você deve definir uma nova senha antes de continuar.
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Senha atual
            </label>
            <div className="relative">
              <input
                type={showCurrent ? 'text' : 'password'}
                className="input pr-10"
                placeholder="••••••••"
                {...register('current_password', { required: 'Senha atual obrigatória' })}
              />
              <button
                type="button"
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                onClick={() => setShowCurrent(!showCurrent)}
              >
                {showCurrent ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            {errors.current_password && (
              <p className="text-red-500 text-xs mt-1">{errors.current_password.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Nova senha
            </label>
            <div className="relative">
              <input
                type={showNew ? 'text' : 'password'}
                className="input pr-10"
                placeholder="Mínimo 8 caracteres"
                {...register('new_password', {
                  required: 'Nova senha obrigatória',
                  minLength: { value: 8, message: 'Mínimo 8 caracteres' },
                })}
              />
              <button
                type="button"
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                onClick={() => setShowNew(!showNew)}
              >
                {showNew ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            {errors.new_password && (
              <p className="text-red-500 text-xs mt-1">{errors.new_password.message}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Confirmar nova senha
            </label>
            <input
              type="password"
              className="input"
              placeholder="Repita a nova senha"
              {...register('confirm_password', {
                required: 'Confirmação obrigatória',
                validate: (v) => v === newPassword || 'Senhas não coincidem',
              })}
            />
            {errors.confirm_password && (
              <p className="text-red-500 text-xs mt-1">{errors.confirm_password.message}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary w-full py-3"
          >
            {isLoading ? (
              <span className="flex items-center justify-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                Salvando...
              </span>
            ) : (
              'Definir nova senha'
            )}
          </button>
        </form>

        <div className="mt-4 flex justify-center">
          <div className="inline-flex items-center gap-1.5 text-xs text-gray-400">
            <Bot size={12} />
            IGS — Intelligent General Service
          </div>
        </div>
      </div>
    </div>
  )
}
