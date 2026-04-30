import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Building2, Plus, CheckCircle2, X, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import clsx from 'clsx'
import { api } from '../api/client'

interface Tenant {
  id: string
  name: string
  slug: string
  plan: string
  is_active: boolean
  whatsapp_phone?: string | null
}

interface CreateTenantForm {
  tenant_name: string
  tenant_slug: string
  plan: string
  admin_email: string
  admin_password: string
  admin_full_name: string
  bot_name: string
  welcome_message: string
}

const EMPTY_FORM: CreateTenantForm = {
  tenant_name: '',
  tenant_slug: '',
  plan: 'basic',
  admin_email: '',
  admin_password: '',
  admin_full_name: '',
  bot_name: 'Billie',
  welcome_message: '',
}

function slugify(input: string): string {
  return input
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 64)
}

export default function Tenants() {
  const qc = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<CreateTenantForm>(EMPTY_FORM)
  const [created, setCreated] = useState<{ slug: string; email: string } | null>(null)

  const { data: tenants, isLoading } = useQuery({
    queryKey: ['tenants'],
    queryFn: () => api.get('/api/v1/tenants').then((r) => r.data as Tenant[]),
  })

  const createMutation = useMutation({
    mutationFn: (payload: CreateTenantForm) =>
      api.post('/api/v1/onboarding/tenants', payload).then((r) => r.data),
    onSuccess: (data: any) => {
      toast.success('Tenant criado com sucesso!')
      setCreated({ slug: data.slug, email: data.admin_email })
      setShowForm(false)
      setForm(EMPTY_FORM)
      qc.invalidateQueries({ queryKey: ['tenants'] })
    },
    onError: (err: any) => {
      const detail = err?.response?.data?.detail || 'Erro ao criar tenant'
      toast.error(typeof detail === 'string' ? detail : 'Erro de validacao')
    },
  })

  const canSubmit =
    form.tenant_name.trim().length >= 2 &&
    form.tenant_slug.trim().length >= 3 &&
    form.admin_email.includes('@') &&
    form.admin_password.length >= 8 &&
    form.admin_full_name.trim().length >= 2

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!canSubmit) {
      toast.error('Preencha todos os campos obrigatorios (senha min 8 chars)')
      return
    }
    createMutation.mutate(form)
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Instituicoes (Tenants)</h1>
          <p className="text-sm text-gray-500">
            Gerencie as instituicoes que usam o IGS
          </p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
        >
          <Plus size={16} />
          Nova Instituicao
        </button>
      </div>

      {created && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-start justify-between">
          <div className="flex gap-3">
            <CheckCircle2 className="text-green-600 flex-shrink-0" size={20} />
            <div className="text-sm">
              <p className="font-medium text-green-900">
                Instituicao criada! Slug: <span className="font-mono">{created.slug}</span>
              </p>
              <p className="text-green-700 mt-1">
                Login do admin: <span className="font-mono">{created.email}</span>
              </p>
              <p className="text-green-700 mt-2">
                Proximos passos: configurar WhatsApp Business API em Configuracoes e
                importar lista de alunos via CSV.
              </p>
            </div>
          </div>
          <button onClick={() => setCreated(null)} className="text-green-700">
            <X size={16} />
          </button>
        </div>
      )}

      <div className="card p-0 overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <Loader2 className="animate-spin text-blue-600" size={20} />
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">
                  Nome
                </th>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">
                  Slug
                </th>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">
                  Plano
                </th>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">
                  WhatsApp
                </th>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {tenants?.map((t) => (
                <tr key={t.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-medium">{t.name}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 font-mono">{t.slug}</td>
                  <td className="px-4 py-3">
                    <span className="badge bg-blue-100 text-blue-700 capitalize">
                      {t.plan}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {t.whatsapp_phone || (
                      <span className="text-gray-400 italic">nao configurado</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={clsx(
                        'badge',
                        t.is_active
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-600',
                      )}
                    >
                      {t.is_active ? 'Ativo' : 'Inativo'}
                    </span>
                  </td>
                </tr>
              ))}
              {!tenants?.length && (
                <tr>
                  <td colSpan={5} className="text-center py-8 text-gray-400">
                    <Building2 className="mx-auto mb-2 opacity-30" size={32} />
                    <p>Nenhuma instituicao cadastrada</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

      {/* Modal de criacao */}
      {showForm && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-5 border-b">
              <h2 className="text-lg font-bold">Nova Instituicao</h2>
              <button
                onClick={() => setShowForm(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-5 space-y-4">
              <section>
                <h3 className="text-sm font-semibold text-gray-700 mb-3">Dados da Instituicao</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-medium text-gray-600">Nome *</label>
                    <input
                      type="text"
                      value={form.tenant_name}
                      onChange={(e) => {
                        const name = e.target.value
                        setForm((f) => ({
                          ...f,
                          tenant_name: name,
                          tenant_slug: f.tenant_slug || slugify(name),
                        }))
                      }}
                      placeholder="Faculdade Anchieta"
                      className="input w-full mt-1"
                      required
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-600">
                      Slug * (identificador)
                    </label>
                    <input
                      type="text"
                      value={form.tenant_slug}
                      onChange={(e) =>
                        setForm((f) => ({ ...f, tenant_slug: slugify(e.target.value) }))
                      }
                      placeholder="anchieta"
                      className="input w-full mt-1 font-mono"
                      pattern="[a-z0-9][a-z0-9-]{1,62}[a-z0-9]"
                      required
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-600">Plano</label>
                    <select
                      value={form.plan}
                      onChange={(e) => setForm((f) => ({ ...f, plan: e.target.value }))}
                      className="input w-full mt-1"
                    >
                      <option value="basic">Basic</option>
                      <option value="pro">Pro</option>
                      <option value="enterprise">Enterprise</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-600">
                      Nome do Bot
                    </label>
                    <input
                      type="text"
                      value={form.bot_name}
                      onChange={(e) =>
                        setForm((f) => ({ ...f, bot_name: e.target.value }))
                      }
                      placeholder="Billie"
                      className="input w-full mt-1"
                    />
                  </div>
                </div>
                <div className="mt-3">
                  <label className="text-xs font-medium text-gray-600">
                    Mensagem de boas-vindas
                  </label>
                  <textarea
                    value={form.welcome_message}
                    onChange={(e) =>
                      setForm((f) => ({ ...f, welcome_message: e.target.value }))
                    }
                    rows={2}
                    placeholder="Oi! Sou a Billie, do atendimento."
                    className="input w-full mt-1"
                  />
                </div>
              </section>

              <section className="border-t pt-4">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">
                  Administrador Principal
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-medium text-gray-600">Nome *</label>
                    <input
                      type="text"
                      value={form.admin_full_name}
                      onChange={(e) =>
                        setForm((f) => ({ ...f, admin_full_name: e.target.value }))
                      }
                      placeholder="Maria Gestora"
                      className="input w-full mt-1"
                      required
                    />
                  </div>
                  <div>
                    <label className="text-xs font-medium text-gray-600">Email *</label>
                    <input
                      type="email"
                      value={form.admin_email}
                      onChange={(e) =>
                        setForm((f) => ({ ...f, admin_email: e.target.value }))
                      }
                      placeholder="gestor@anchieta.edu.br"
                      className="input w-full mt-1"
                      required
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="text-xs font-medium text-gray-600">
                      Senha * (min 8 chars)
                    </label>
                    <input
                      type="password"
                      value={form.admin_password}
                      onChange={(e) =>
                        setForm((f) => ({ ...f, admin_password: e.target.value }))
                      }
                      minLength={8}
                      className="input w-full mt-1"
                      required
                    />
                  </div>
                </div>
              </section>

              <div className="flex justify-end gap-2 border-t pt-4">
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  disabled={!canSubmit || createMutation.isPending}
                  className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {createMutation.isPending && (
                    <Loader2 className="animate-spin" size={16} />
                  )}
                  Criar Instituicao
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
