import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header from './Header'
import { useNotifications } from '../../hooks/useNotifications'

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { unreadCount, markAllRead, isConnected } = useNotifications()

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Overlay mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="flex-1 flex flex-col overflow-hidden">
        <Header
          onMenuToggle={() => setSidebarOpen((v) => !v)}
          unreadCount={unreadCount}
          onBellClick={markAllRead}
          wsConnected={isConnected}
        />
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
