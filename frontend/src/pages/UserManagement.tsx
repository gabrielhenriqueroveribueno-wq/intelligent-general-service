import { useQuery } from '@tanstack/react-query'
import { UserCog } from 'lucide-react'
import { api } from '../api/client'
import clsx from 'clsx'

const roleColors: Record<string, string> = {
  super_admin: 'bg-purple-100 text-purple-700',
  admin: 'bg-red-100 text-red-700',
  manager: 'bg-orange-100 text-orange-700',
  agent: 'bg-blue-100 text-blue-700',
}

export default function UserManagement() {
  const { data: users, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: () => api.get('/api/v1/users').then((r) => r.data),
  })

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Usuários</h1>
        <p className="text-sm text-gray-500">Gerencie os usuários do painel</p>
      </div>

      <div className="card p-0 overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600" />
          </div>
        ) : (
          <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Nome</th>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Email</th>
                <th className="text-left text-xs font-medium text-gray-500 px-4 py-3">Papel</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {users?.map((user: any) => (
                <tr key={user.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-medium">{user.full_name}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{user.email}</td>
                  <td className="px-4 py-3">
                    <span className={clsx('badge', roleColors[user.role] || 'bg-gray-100')}>
                      {user.role}
                    </span>
                  </td>
                </tr>
              ))}
              {!users?.length && (
                <tr>
                  <td colSpan={3} className="text-center py-8 text-gray-400">
                    <UserCog className="mx-auto mb-2 opacity-30" size={32} />
                    <p>Nenhum usuário encontrado</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
          </div>
        )}
      </div>
    </div>
  )
}
