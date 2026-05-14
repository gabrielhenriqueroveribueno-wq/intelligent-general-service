import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/common/ProtectedRoute'
import ErrorBoundary from './components/common/ErrorBoundary'
import Layout from './components/layout/Layout'
import PublicLayout from './components/layout/PublicLayout'
import InstallBanner from './components/common/InstallBanner'
import OfflineBanner from './components/common/OfflineBanner'
import PageLoader from './components/common/PageLoader'
import CookieBanner from './components/common/CookieBanner'

// Eager: páginas críticas / first paint
import Login from './pages/Login'
import ForgotPassword from './pages/ForgotPassword'
import ResetPassword from './pages/ResetPassword'
import ChangePassword from './pages/ChangePassword'
import Onboarding from './pages/Onboarding'
import Landing from './pages/Landing'
import Dashboard from './pages/Dashboard'
import Conversations from './pages/Conversations'
import Tickets from './pages/Tickets'
import Students from './pages/Students'
import Employees from './pages/Employees'
import KnowledgeBase from './pages/KnowledgeBase'
import Settings from './pages/Settings'
import NotFound from './pages/NotFound'
import Signup from './pages/Signup'

// Lazy: páginas pesadas ou de acesso menos frequente
const CaseStudy = lazy(() => import('./pages/CaseStudy'))
const Legal = lazy(() => import('./pages/Legal'))
const Help = lazy(() => import('./pages/Help'))
const Demo = lazy(() => import('./pages/Demo'))
const Pricing = lazy(() => import('./pages/Pricing'))
const Tour = lazy(() => import('./pages/Tour'))
const PublicStatus = lazy(() => import('./pages/PublicStatus'))
const ConversationDetail = lazy(() => import('./pages/ConversationDetail'))
const StudentDetail = lazy(() => import('./pages/StudentDetail'))
const EmployeeDetail = lazy(() => import('./pages/EmployeeDetail'))
const Reports = lazy(() => import('./pages/Reports'))
const MetricsDashboard = lazy(() => import('./pages/MetricsDashboard'))
const LearningInsights = lazy(() => import('./pages/LearningInsights'))
const Templates = lazy(() => import('./pages/Templates'))
const Billing = lazy(() => import('./pages/Billing'))
const Tenants = lazy(() => import('./pages/Tenants'))
const ImportData = lazy(() => import('./pages/ImportData'))
const WhatsAppSetup = lazy(() => import('./pages/WhatsAppSetup'))
const ReportSubscriptions = lazy(() => import('./pages/ReportSubscriptions'))
const Integrations = lazy(() => import('./pages/Integrations'))
const UserManagement = lazy(() => import('./pages/UserManagement'))
const Status = lazy(() => import('./pages/Status'))
const AuditLog = lazy(() => import('./pages/AuditLog'))
const SuperAdmin = lazy(() => import('./pages/SuperAdmin'))
const Presentation = lazy(() => import('./pages/Presentation'))
const PitchDeck = lazy(() => import('./pages/PitchDeck'))

function Lazy({ children }: { children: React.ReactNode }) {
  return (
    <Suspense fallback={<PageLoader />}>
      {children}
    </Suspense>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <OfflineBanner />
      <InstallBanner />
      <CookieBanner />
      <ErrorBoundary>
        <Routes>
          {/* Rotas publicas */}
          <Route element={<PublicLayout />}>
            <Route path="/" element={<Landing />} />
            <Route path="/case-study" element={<Lazy><CaseStudy /></Lazy>} />
            <Route path="/legal" element={<Lazy><Legal /></Lazy>} />
            <Route path="/demo" element={<Lazy><Demo /></Lazy>} />
            <Route path="/pricing" element={<Lazy><Pricing /></Lazy>} />
          </Route>

          {/* Páginas públicas sem layout de navegação */}
          <Route path="/status" element={<Lazy><PublicStatus /></Lazy>} />
          <Route path="/tour" element={<Lazy><Tour /></Lazy>} />

          {/* Login / Signup / Onboarding / Change Password (sem layout) */}
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/onboarding" element={<Onboarding />} />
          <Route path="/change-password" element={<ChangePassword />} />

          {/* Painel admin (protegido) */}
          <Route
            path="/app"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/app/dashboard" replace />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="conversations" element={<Conversations />} />
            <Route path="conversations/:id" element={<Lazy><ConversationDetail /></Lazy>} />
            <Route path="tickets" element={<Tickets />} />
            <Route path="students" element={<Students />} />
            <Route path="students/:id" element={<Lazy><StudentDetail /></Lazy>} />
            <Route path="employees" element={<Employees />} />
            <Route path="employees/:id" element={<Lazy><EmployeeDetail /></Lazy>} />
            <Route path="knowledge-base" element={<KnowledgeBase />} />
            <Route path="reports" element={<Lazy><Reports /></Lazy>} />
            <Route path="metrics" element={<Lazy><MetricsDashboard /></Lazy>} />
            <Route path="learning" element={<Lazy><LearningInsights /></Lazy>} />
            <Route path="users" element={<Lazy><UserManagement /></Lazy>} />
            <Route path="tenants" element={<Lazy><Tenants /></Lazy>} />
            <Route path="import-data" element={<Lazy><ImportData /></Lazy>} />
            <Route path="whatsapp-setup" element={<Lazy><WhatsAppSetup /></Lazy>} />
            <Route path="templates" element={<Lazy><Templates /></Lazy>} />
            <Route path="billing" element={<Lazy><Billing /></Lazy>} />
            <Route path="report-subscriptions" element={<Lazy><ReportSubscriptions /></Lazy>} />
            <Route path="integrations" element={<Lazy><Integrations /></Lazy>} />
            <Route path="settings" element={<Settings />} />
            <Route path="status" element={<Lazy><Status /></Lazy>} />
            <Route path="audit" element={<Lazy><AuditLog /></Lazy>} />
            <Route path="super-admin" element={<Lazy><SuperAdmin /></Lazy>} />
            <Route path="help" element={<Lazy><Help /></Lazy>} />
          </Route>

          {/* Apresentação fullscreen — fora do Layout pra ocupar tela toda */}
          <Route
            path="/app/presentation"
            element={
              <ProtectedRoute>
                <Lazy>
                  <Presentation />
                </Lazy>
              </ProtectedRoute>
            }
          />

          {/* Pitch deck comercial — público (acessível sem login para envio a investidores) */}
          <Route
            path="/pitch"
            element={
              <Lazy>
                <PitchDeck />
              </Lazy>
            }
          />

          {/* Aliases compat */}
          <Route path="/dashboard" element={<Navigate to="/app/dashboard" replace />} />
          <Route path="/conversations" element={<Navigate to="/app/conversations" replace />} />
          <Route path="/tickets" element={<Navigate to="/app/tickets" replace />} />
          <Route path="/students" element={<Navigate to="/app/students" replace />} />
          <Route path="/employees" element={<Navigate to="/app/employees" replace />} />
          <Route path="/knowledge-base" element={<Navigate to="/app/knowledge-base" replace />} />
          <Route path="/reports" element={<Navigate to="/app/reports" replace />} />
          <Route path="/metrics" element={<Navigate to="/app/metrics" replace />} />
          <Route path="/learning" element={<Navigate to="/app/learning" replace />} />
          <Route path="/users" element={<Navigate to="/app/users" replace />} />
          <Route path="/tenants" element={<Navigate to="/app/tenants" replace />} />
          <Route path="/import-data" element={<Navigate to="/app/import-data" replace />} />
          <Route path="/whatsapp-setup" element={<Navigate to="/app/whatsapp-setup" replace />} />
          <Route path="/report-subscriptions" element={<Navigate to="/app/report-subscriptions" replace />} />
          <Route path="/settings" element={<Navigate to="/app/settings" replace />} />

          {/* 404 */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </ErrorBoundary>
    </AuthProvider>
  )
}
