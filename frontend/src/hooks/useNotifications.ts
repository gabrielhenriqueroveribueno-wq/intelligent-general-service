import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'
import { useWebSocket } from './useWebSocket'

export type Notification = {
  id: string
  type: string
  message: string
  conversationId?: string
  timestamp: Date
  read: boolean
}

export function useNotifications() {
  const { token } = useAuth()
  const [notifications, setNotifications] = useState<Notification[]>([])

  // WS URL: usa wss em HTTPS, ws em HTTP; token no query param
  const wsUrl = token
    ? `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/api/v1/ws?token=${token}`
    : null

  const { lastMessage, isConnected } = useWebSocket(wsUrl)

  useEffect(() => {
    if (!lastMessage) return

    switch (lastMessage.type) {
      case 'new_message': {
        const notif: Notification = {
          id: crypto.randomUUID(),
          type: 'new_message',
          message: 'Nova mensagem recebida no WhatsApp',
          conversationId: lastMessage.conversation_id,
          timestamp: new Date(),
          read: false,
        }
        setNotifications((prev) => [notif, ...prev].slice(0, 50))
        toast('💬 Nova mensagem WhatsApp', { duration: 3000 })
        break
      }
      case 'conversation_waiting': {
        const notif: Notification = {
          id: crypto.randomUUID(),
          type: 'conversation_waiting',
          message: 'Conversa aguardando atendente humano',
          conversationId: lastMessage.conversation_id,
          timestamp: new Date(),
          read: false,
        }
        setNotifications((prev) => [notif, ...prev].slice(0, 50))
        toast.error('🙋 Conversa aguardando atendente', { duration: 5000 })
        break
      }
      case 'conversation_closed': {
        setNotifications((prev) =>
          prev.filter((n) => n.conversationId !== lastMessage.conversation_id),
        )
        break
      }
    }
  }, [lastMessage])

  const markAllRead = () =>
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))

  const unreadCount = notifications.filter((n) => !n.read).length

  return { notifications, unreadCount, markAllRead, isConnected }
}
