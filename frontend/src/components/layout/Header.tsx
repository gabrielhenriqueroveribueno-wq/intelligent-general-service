import { LogOut, User } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

export default function Header() {
  const { user, logout } = useAuth()

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
      <div />
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <div className="bg-blue-100 p-1.5 rounded-full">
            <User size={16} className="text-blue-600" />
          </div>
          <span className="font-medium">{user?.full_name}</span>
          <span className="text-gray-400 capitalize">({user?.role})</span>
        </div>
        <button
          onClick={logout}
          className="flex items-center gap-2 text-sm text-gray-500 hover:text-red-600 transition-colors"
        >
          <LogOut size={16} />
          Sair
        </button>
      </div>
    </header>
  )
}
