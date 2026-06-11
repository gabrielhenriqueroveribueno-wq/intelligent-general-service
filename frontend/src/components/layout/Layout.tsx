import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header from './Header'
import TrialBanner from '../common/TrialBanner'
import PaywallModal from '../common/PaywallModal'
import { useNotifications } from '../../hooks/useNotifications'

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { unreadCount, markAllRead, isConnected } = useNotifications()

  return (
    <div className="theme-dark flex h-screen bg-navy-950">
      <PaywallModal />

      {/* Overlay mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="flex-1 flex flex-col overflow-hidden">
        <TrialBanner />
        <Header
          onMenuToggle={() => setSidebarOpen((v) => !v)}
          unreadCount={unreadCount}
          onBellClick={markAllRead}
          wsConnected={isConnected}
        />
        <main className="flex-1 overflow-y-auto p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
