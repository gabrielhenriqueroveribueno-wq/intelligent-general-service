import { Bell, LogOut, Menu, User, Wifi, WifiOff } from 'lucide-react'
import { useAuth } from '../../context/AuthContext'

interface HeaderProps {
  onMenuToggle: () => void
  unreadCount: number
  onBellClick: () => void
  wsConnected: boolean
}

export default function Header({ onMenuToggle, unreadCount, onBellClick, wsConnected }: HeaderProps) {
  const { user, logout } = useAuth()

  return (
    <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
      {/* Hambúrguer — visível só em mobile */}
      <button
        onClick={onMenuToggle}
        className="lg:hidden p-2 rounded-lg text-gray-500 hover:bg-gray-100 transition-colors"
        aria-label="Abrir menu"
      >
        <Menu size={20} />
      </button>

      {/* Espaço vazio no desktop */}
      <div className="hidden lg:block" />

      <div className="flex items-center gap-3">
        {/* Indicador de conexão WS */}
        <span
          title={wsConnected ? 'Tempo real ativo' : 'Reconectando...'}
          className="hidden sm:flex items-center gap-1 text-xs text-gray-400"
        >
          {wsConnected ? (
            <Wifi size={14} className="text-green-500" />
          ) : (
            <WifiOff size={14} className="text-gray-400 animate-pulse" />
          )}
        </span>

        {/* Sino de notificações */}
        <button
          onClick={onBellClick}
          className="relative p-2 rounded-lg text-gray-500 hover:bg-gray-100 transition-colors"
          aria-label="Notificações"
        >
          <Bell size={18} />
          {unreadCount > 0 && (
            <span className="absolute -top-0.5 -right-0.5 bg-red-500 text-white text-[10px] font-bold rounded-full min-w-[16px] h-4 flex items-center justify-center px-0.5">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </button>

        {/* Info do usuário */}
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <div className="bg-blue-100 p-1.5 rounded-full">
            <User size={16} className="text-blue-600" />
          </div>
          <span className="hidden sm:block font-medium">{user?.full_name}</span>
          <span className="hidden sm:block text-gray-400 capitalize">({user?.role})</span>
        </div>

        {/* Sair */}
        <button
          onClick={logout}
          className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-red-600 transition-colors"
          aria-label="Sair"
        >
          <LogOut size={16} />
          <span className="hidden sm:block">Sair</span>
        </button>
      </div>
    </header>
  )
}
