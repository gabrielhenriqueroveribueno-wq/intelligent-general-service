import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  MessageSquare,
  Ticket,
  GraduationCap,
  Users,
  BookOpen,
  BarChart2,
  Settings,
  UserCog,
  Bot,
} from 'lucide-react'
import clsx from 'clsx'

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/conversations', icon: MessageSquare, label: 'Conversas' },
  { to: '/tickets', icon: Ticket, label: 'Tickets' },
  { to: '/students', icon: GraduationCap, label: 'Alunos' },
  { to: '/employees', icon: Users, label: 'Funcionários' },
  { to: '/knowledge-base', icon: BookOpen, label: 'Base de Conhecimento' },
  { to: '/reports', icon: BarChart2, label: 'Relatórios' },
  { to: '/users', icon: UserCog, label: 'Usuários' },
  { to: '/settings', icon: Settings, label: 'Configurações' },
]

export default function Sidebar() {
  return (
    <aside className="w-64 bg-gray-900 text-white flex flex-col">
      {/* Logo */}
      <div className="p-6 border-b border-gray-700">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600 p-2 rounded-lg">
            <Bot size={20} />
          </div>
          <div>
            <p className="font-bold text-sm">IGS</p>
            <p className="text-xs text-gray-400">Intelligent General Service</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-4 space-y-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-white',
              )
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Version */}
      <div className="p-4 border-t border-gray-700">
        <p className="text-xs text-gray-500 text-center">v1.0.0</p>
      </div>
    </aside>
  )
}
