import { useEffect, useRef, useCallback, useState } from 'react'

export type WsEvent = {
  type: string
  tenant_id?: string
  conversation_id?: string
  intent?: string
  resolution_type?: string
  [key: string]: unknown
}

export function useWebSocket(url: string | null) {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>()
  const reconnectDelay = useRef(1000)
  const [lastMessage, setLastMessage] = useState<WsEvent | null>(null)
  const [isConnected, setIsConnected] = useState(false)

  const connect = useCallback(() => {
    if (!url) return

    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      setIsConnected(true)
      reconnectDelay.current = 1000
    }

    ws.onmessage = (event) => {
      try {
        const data: WsEvent = JSON.parse(event.data)
        setLastMessage(data)
      } catch (_e) {
        // ignore malformed messages
      }
    }

    ws.onclose = () => {
      setIsConnected(false)
      reconnectTimer.current = setTimeout(() => {
        reconnectDelay.current = Math.min(reconnectDelay.current * 2, 30_000)
        connect()
      }, reconnectDelay.current)
    }

    ws.onerror = () => {
      ws.close()
    }
  }, [url])

  useEffect(() => {
    connect()
    return () => {
      clearTimeout(reconnectTimer.current)
      wsRef.current?.close()
    }
  }, [connect])

  return { lastMessage, isConnected }
}
