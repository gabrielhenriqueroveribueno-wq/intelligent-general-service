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
  Brain,
  TrendingUp,
  Presentation,
  Building2,
  FileSpreadsheet,
  Smartphone,
  Mail,
  Plug,
  Activity,
  Shield,
  HelpCircle,
  X,
} from 'lucide-react'
import clsx from 'clsx'
import { useAuth } from '../../context/AuthContext'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../api/client'

interface NavItem {
  to: string
  icon: typeof LayoutDashboard
  label: string
  superAdminOnly?: boolean
  adminOnly?: boolean
}

const navItems: NavItem[] = [
  { to: '/app/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/app/conversations', icon: MessageSquare, label: 'Conversas' },
  { to: '/app/tickets', icon: Ticket, label: 'Tickets' },
  { to: '/app/students', icon: GraduationCap, label: 'Alunos' },
  { to: '/app/employees', icon: Users, label: 'Funcionários' },
  { to: '/app/knowledge-base', icon: BookOpen, label: 'Base de Conhecimento' },
  { to: '/app/slides', icon: Presentation, label: 'Slides IA' },
  { to: '/app/reports', icon: BarChart2, label: 'Relatórios' },
  { to: '/app/report-subscriptions', icon: Mail, label: 'Email Reports', adminOnly: true },
  { to: '/app/integrations', icon: Plug, label: 'Integrações', adminOnly: true },
  { to: '/app/metrics', icon: TrendingUp, label: 'Métricas IA vs Humano' },
  { to: '/app/learning', icon: Brain, label: 'Aprendizado IA' },
  { to: '/app/import-data', icon: FileSpreadsheet, label: 'Importar Dados', adminOnly: true },
  { to: '/app/whatsapp-setup', icon: Smartphone, label: 'Configurar WhatsApp', adminOnly: true },
  { to: '/app/users', icon: UserCog, label: 'Usuários' },
  { to: '/app/tenants', icon: Building2, label: 'Instituições', superAdminOnly: true },
  { to: '/app/audit', icon: Shield, label: 'Auditoria', adminOnly: true },
  { to: '/app/status', icon: Activity, label: 'Status do Sistema', adminOnly: true },
  { to: '/app/help', icon: HelpCircle, label: 'Ajuda' },
  { to: '/app/settings', icon: Settings, label: 'Configurações' },
]

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

export default function Sidebar({ isOpen, onClose }: SidebarProps) {
  const { user } = useAuth()
  const role = user?.role || 'agent'

  const { data: waitingData } = useQuery({
    queryKey: ['sidebar-waiting'],
    queryFn: () =>
      api.get('/api/v1/conversations', { params: { status: 'waiting_agent', page: 1, size: 1 } }).then((r) => r.data),
    refetchInterval: 20_000,
    retry: false,
  })
  const waitingCount: number = waitingData?.total ?? 0

  const visibleItems = navItems.filter((item) => {
    if (item.superAdminOnly) return role === 'super_admin'
    if (item.adminOnly) return role === 'super_admin' || role === 'admin'
    return true
  })

  return (
    <aside
      className={clsx(
        'w-64 bg-gray-900 text-white flex flex-col flex-shrink-0 transition-transform duration-300 ease-in-out',
        'fixed inset-y-0 left-0 z-50',
        isOpen ? 'translate-x-0' : '-translate-x-full',
        'lg:relative lg:translate-x-0 lg:z-auto',
      )}
    >
      <div className="p-6 border-b border-gray-700 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600 p-2 rounded-lg">
            <Bot size={20} />
          </div>
          <div>
            <p className="font-bold text-sm">IGS</p>
            <p className="text-xs text-gray-400">Intelligent General Service</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="lg:hidden p-1 rounded text-gray-400 hover:text-white"
          aria-label="Fechar menu"
        >
          <X size={18} />
        </button>
      </div>

      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {visibleItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            onClick={onClose}
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
            <span className="flex-1">{label}</span>
            {to === '/app/conversations' && waitingCount > 0 && (
              <span className="bg-orange-500 text-white text-xs font-bold px-1.5 py-0.5 rounded-full">
                {waitingCount}
              </span>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-gray-700">
        <p className="text-xs text-gray-500 text-center">v1.0.0</p>
      </div>
    </aside>
  )
}
