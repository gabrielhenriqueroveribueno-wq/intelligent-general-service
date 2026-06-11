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
  Building2,
  FileSpreadsheet,
  Smartphone,
  Mail,
  Plug,
  Activity,
  Shield,
  HelpCircle,
  X,
  Crown,
  CreditCard,
  Presentation as PresentationIcon,
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

interface NavSection {
  title: string
  items: NavItem[]
}

const navSections: NavSection[] = [
  {
    title: 'Atendimento',
    items: [
      { to: '/app/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
      { to: '/app/conversations', icon: MessageSquare, label: 'Conversas' },
      { to: '/app/tickets', icon: Ticket, label: 'Tickets' },
      { to: '/app/presentation', icon: PresentationIcon, label: 'Apresentação', adminOnly: true },
    ],
  },
  {
    title: 'Acadêmico',
    items: [
      { to: '/app/students', icon: GraduationCap, label: 'Alunos' },
      { to: '/app/employees', icon: Users, label: 'Funcionários' },
      { to: '/app/knowledge-base', icon: BookOpen, label: 'Base de Conhecimento' },
    ],
  },
  {
    title: 'Análise',
    items: [
      { to: '/app/reports', icon: BarChart2, label: 'Relatórios' },
      { to: '/app/metrics', icon: TrendingUp, label: 'Métricas IA vs Humano' },
      { to: '/app/learning', icon: Brain, label: 'Aprendizado IA' },
    ],
  },
  {
    title: 'Configuração',
    items: [
      { to: '/app/integrations', icon: Plug, label: 'Integrações', adminOnly: true },
      { to: '/app/import-data', icon: FileSpreadsheet, label: 'Importar Dados', adminOnly: true },
      { to: '/app/whatsapp-setup', icon: Smartphone, label: 'Configurar WhatsApp', adminOnly: true },
      { to: '/app/templates', icon: MessageSquare, label: 'Templates WhatsApp', adminOnly: true },
      { to: '/app/report-subscriptions', icon: Mail, label: 'Relatórios por Email', adminOnly: true },
    ],
  },
  {
    title: 'Administração',
    items: [
      { to: '/app/users', icon: UserCog, label: 'Usuários' },
      { to: '/app/billing', icon: CreditCard, label: 'Plano e Cobrança', adminOnly: true },
      { to: '/app/audit', icon: Shield, label: 'Auditoria', adminOnly: true },
      { to: '/app/status', icon: Activity, label: 'Status do Sistema', adminOnly: true },
      { to: '/app/tenants', icon: Building2, label: 'Instituições', superAdminOnly: true },
      { to: '/app/super-admin', icon: Crown, label: 'Super Admin', superAdminOnly: true },
    ],
  },
]

const footerItems: NavItem[] = [
  { to: '/app/help', icon: HelpCircle, label: 'Ajuda' },
  { to: '/app/settings', icon: Settings, label: 'Configurações' },
]

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

function canSee(item: NavItem, role: string): boolean {
  if (item.superAdminOnly) return role === 'super_admin'
  if (item.adminOnly) return role === 'super_admin' || role === 'admin'
  return true
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

  const visibleSections = navSections
    .map((section) => ({ ...section, items: section.items.filter((i) => canSee(i, role)) }))
    .filter((section) => section.items.length > 0)

  return (
    <aside
      className={clsx(
        'w-64 bg-navy-900 text-white flex flex-col flex-shrink-0 transition-transform duration-300 ease-in-out',
        'fixed inset-y-0 left-0 z-50',
        isOpen ? 'translate-x-0' : '-translate-x-full',
        'lg:relative lg:translate-x-0 lg:z-auto',
      )}
    >
      <div className="px-5 py-4 border-b border-navy-line flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="bg-accent p-2 rounded-lg">
            <Bot size={20} className="text-accent-ink" />
          </div>
          <div>
            <p className="font-bold text-sm text-white">IGS</p>
            <p className="text-xs text-accent">Intelligent General Service</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="lg:hidden p-1 rounded text-slate-400 hover:text-white"
          aria-label="Fechar menu"
        >
          <X size={18} />
        </button>
      </div>

      <nav className="flex-1 px-3 py-3 overflow-y-auto">
        {visibleSections.map((section) => (
          <div key={section.title} className="mb-3">
            <p className="px-3 mb-1 text-[10px] font-semibold uppercase tracking-wider text-slate-500">
              {section.title}
            </p>
            <div className="space-y-0.5">
              {section.items.map(({ to, icon: Icon, label }) => (
                <NavLink
                  key={to}
                  to={to}
                  onClick={onClose}
                  className={({ isActive }) =>
                    clsx(
                      'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors border-l-2',
                      isActive
                        ? 'bg-navy-700 border-accent text-white'
                        : 'border-transparent text-slate-400 hover:bg-navy-750 hover:text-white',
                    )
                  }
                >
                  {({ isActive }) => (
                    <>
                      <Icon size={17} className={isActive ? 'text-primary-500' : undefined} />
                      <span className="flex-1">{label}</span>
                      {to === '/app/conversations' && waitingCount > 0 && (
                        <span className="bg-accent text-accent-ink text-xs font-bold px-1.5 py-0.5 rounded-full">
                          {waitingCount}
                        </span>
                      )}
                    </>
                  )}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>

      <div className="px-3 py-3 border-t border-navy-line">
        <div className="space-y-0.5">
          {footerItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              onClick={onClose}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors border-l-2',
                  isActive
                    ? 'bg-navy-700 border-accent text-white'
                    : 'border-transparent text-slate-400 hover:bg-navy-750 hover:text-white',
                )
              }
            >
              <Icon size={17} />
              <span className="flex-1">{label}</span>
            </NavLink>
          ))}
        </div>
        <p className="text-xs text-slate-600 text-center mt-3">v1.0.0</p>
      </div>
    </aside>
  )
}
