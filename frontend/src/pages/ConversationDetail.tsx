import { useState, useRef, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Send, User, Bot, UserCheck, X, Phone, HandshakeIcon, BotOff, AlertCircle } from 'lucide-react'
import { api } from '../api/client'
import { format } from 'date-fns'
import { ptBR } from 'date-fns/locale'
import clsx from 'clsx'
import toast from 'react-hot-toast'
import { useWebSocket } from '../hooks/useWebSocket'
import { useAuth } from '../context/AuthContext'

const statusLabels: Record<string, string> = {
  active: 'Ativa',
  waiting_agent: 'Aguardando agente',
  awaiting_feedback: 'Aguardando avaliação',
  closed: 'Encerrada',
}

const statusColors: Record<string, string> = {
  active: 'bg-green-100 text-green-700',
  waiting_agent: 'bg-orange-100 text-orange-700',
  awaiting_feedback: 'bg-blue-100 text-blue-700',
  closed: 'bg-gray-100 text-gray-600',
}

const senderLabels: Record<string, string> = {
  user: 'Usuário',
  bot: 'Bot',
  agent: 'Agente',
}

const sentimentDot: Record<string, string> = {
  negative: '🔴',
  positive: '🟢',
  neutral: '⚪',
}

export default function ConversationDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { token, user } = useAuth()
  const [messageText, setMessageText] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const { data: conv, isLoading } = useQuery({
    queryKey: ['conversation', id],
    queryFn: () => api.get(`/api/v1/conversations/${id}`).then((r) => r.data),
    enabled: !!id,
    refetchInterval: 5000,
  })

  const wsUrl = token
    ? `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/api/v1/ws?token=${token}`
    : null
  const { lastMessage } = useWebSocket(wsUrl)

  useEffect(() => {
    if (
      lastMessage &&
      ['new_message', 'agent_message', 'agent_took_over'].includes(lastMessage.type) &&
      lastMessage.conversation_id === id
    ) {
      queryClient.invalidateQueries({ queryKey: ['conversation', id] })
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    }
  }, [lastMessage, id, queryClient])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [conv?.messages])

  const sendMutation = useMutation({
    mutationFn: (content: string) =>
      api.post(`/api/v1/conversations/${id}/messages`, { content }),
    onSuccess: () => {
      setMessageText('')
      queryClient.invalidateQueries({ queryKey: ['conversation', id] })
    },
    onError: () => toast.error('Falha ao enviar mensagem'),
  })

  const takeOverMutation = useMutation({
    mutationFn: () => api.post(`/api/v1/conversations/${id}/take-over`),
    onSuccess: () => {
      toast.success('Você assumiu o atendimento')
      queryClient.invalidateQueries({ queryKey: ['conversation', id] })
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
    onError: () => toast.error('Falha ao assumir conversa'),
  })

  const releaseMutation = useMutation({
    mutationFn: () => api.post(`/api/v1/conversations/${id}/release`),
    onSuccess: () => {
      toast.success('Conversa devolvida ao bot')
      queryClient.invalidateQueries({ queryKey: ['conversation', id] })
    },
    onError: () => toast.error('Falha ao devolver ao bot'),
  })

  const closeMutation = useMutation({
    mutationFn: () => api.post(`/api/v1/conversations/${id}/close`),
    onSuccess: () => {
      toast.success('Conversa encerrada')
      queryClient.invalidateQueries({ queryKey: ['conversation', id] })
      queryClient.invalidateQueries({ queryKey: ['conversations'] })
    },
    onError: () => toast.error('Falha ao encerrar conversa'),
  })

  const handleSend = () => {
    const content = messageText.trim()
    if (!content || sendMutation.isPending) return
    sendMutation.mutate(content)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    )
  }

  if (!conv) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p>Conversa não encontrada</p>
        <Link to="/app/conversations" className="text-blue-600 hover:underline mt-2 block">
          Voltar para conversas
        </Link>
      </div>
    )
  }

  const isClosed = conv.status === 'closed'
  const isWaiting = conv.status === 'waiting_agent'
  const hasAgent = !!conv.assigned_agent_id
  const isMyConv = conv.assigned_agent_id === user?.id
  const canSend = !isClosed && (hasAgent || isWaiting)

  return (
    <div className="flex flex-col h-full -m-4 lg:-m-6">
      {/* Header */}
      <div className="bg-white border-b px-4 lg:px-6 py-3 lg:py-4 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/app/conversations')}
            className="p-1.5 rounded-lg text-gray-500 hover:bg-gray-100"
          >
            <ArrowLeft size={18} />
          </button>
          <div className="bg-blue-100 p-2 rounded-full">
            <User size={18} className="text-blue-600" />
          </div>
          <div className="min-w-0">
            <p className="font-semibold text-gray-900 truncate">
              {conv.contact_name || conv.contact_phone || 'Contato desconhecido'}
            </p>
            {conv.contact_phone && conv.contact_name && (
              <div className="flex items-center gap-1 text-xs text-gray-500">
                <Phone size={11} />
                {conv.contact_phone}
              </div>
            )}
          </div>
          <span className={clsx('badge text-xs px-2 py-0.5 rounded-full font-medium flex-shrink-0', statusColors[conv.status])}>
            {statusLabels[conv.status] || conv.status}
          </span>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          {/* Assumir atendimento */}
          {isWaiting && !hasAgent && (
            <button
              onClick={() => takeOverMutation.mutate()}
              disabled={takeOverMutation.isPending}
              className="flex items-center gap-1.5 text-sm bg-orange-600 hover:bg-orange-700 text-white px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50"
            >
              <HandshakeIcon size={14} />
              <span className="hidden sm:inline">Assumir</span>
            </button>
          )}

          {/* Devolver ao bot */}
          {hasAgent && !isClosed && (
            <button
              onClick={() => releaseMutation.mutate()}
              disabled={releaseMutation.isPending}
              className="flex items-center gap-1.5 text-sm text-purple-600 hover:bg-purple-50 px-3 py-1.5 rounded-lg border border-purple-200 transition-colors disabled:opacity-50"
            >
              <BotOff size={14} />
              <span className="hidden sm:inline">Devolver ao bot</span>
            </button>
          )}

          {!isClosed && (
            <button
              onClick={() => closeMutation.mutate()}
              disabled={closeMutation.isPending}
              className="flex items-center gap-1.5 text-sm text-red-600 hover:bg-red-50 px-3 py-1.5 rounded-lg border border-red-200 transition-colors"
            >
              <X size={14} />
              <span className="hidden sm:inline">Encerrar</span>
            </button>
          )}
        </div>
      </div>

      {/* Banner de handoff */}
      {isWaiting && !hasAgent && (
        <div className="bg-orange-50 border-b border-orange-200 px-4 py-2.5 flex items-center gap-3">
          <AlertCircle size={16} className="text-orange-600 flex-shrink-0" />
          <p className="text-sm text-orange-700">
            O bot solicitou atendimento humano. Clique em <strong>Assumir</strong> para responder diretamente ao usuário.
          </p>
        </div>
      )}

      {/* Banner de agente atribuído */}
      {hasAgent && !isClosed && (
        <div className="bg-green-50 border-b border-green-200 px-4 py-2 flex items-center gap-2">
          <UserCheck size={14} className="text-green-600 flex-shrink-0" />
          <p className="text-xs text-green-700">
            {isMyConv ? 'Você está atendendo esta conversa. O bot está inativo.' : 'Esta conversa está sendo atendida por um agente. O bot está inativo.'}
          </p>
        </div>
      )}

      <div className="flex flex-1 overflow-hidden">
        {/* Thread de mensagens */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto p-4 lg:p-6 space-y-3">
            {conv.messages?.length === 0 && (
              <p className="text-center text-gray-400 text-sm py-8">Nenhuma mensagem ainda</p>
            )}
            {conv.messages?.map((msg: any) => (
              <div
                key={msg.id}
                className={clsx(
                  'flex',
                  msg.sender_type === 'user' ? 'justify-start' : 'justify-end',
                )}
              >
                <div
                  className={clsx(
                    'max-w-[80%] lg:max-w-[70%] rounded-2xl px-4 py-2.5 shadow-sm text-white',
                    msg.sender_type === 'user'
                      ? 'bg-blue-600 rounded-tl-sm'
                      : msg.sender_type === 'bot'
                        ? 'bg-blue-600 rounded-tr-sm'
                        : 'bg-green-600 rounded-tr-sm',
                  )}
                >
                  <div className="flex items-center gap-1.5 mb-1">
                    {msg.sender_type === 'bot' ? (
                      <Bot size={12} className="opacity-70" />
                    ) : msg.sender_type === 'agent' ? (
                      <UserCheck size={12} className="opacity-70" />
                    ) : (
                      <User size={12} className="opacity-70" />
                    )}
                    <span className="text-[10px] font-medium opacity-70">
                      {senderLabels[msg.sender_type] || msg.sender_type}
                    </span>
                    {msg.intent && (
                      <span className="text-[10px] opacity-50">· {msg.intent}</span>
                    )}
                    {msg.sender_type === 'user' && msg.sentiment && msg.sentiment !== 'neutral' && (
                      <span className="text-[10px]" title={`Sentimento: ${msg.sentiment}`}>
                        {sentimentDot[msg.sentiment]}
                      </span>
                    )}
                  </div>
                  <p className="text-sm whitespace-pre-wrap break-words">{msg.content}</p>
                  <p className="text-[10px] mt-1 text-right opacity-60">
                    {format(new Date(msg.created_at), 'HH:mm', { locale: ptBR })}
                  </p>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input — disponível quando agente assumiu ou conversa está esperando */}
          {!isClosed ? (
            hasAgent ? (
              <div className="bg-white border-t px-4 py-3 flex items-end gap-3 flex-shrink-0">
                <div className="flex items-center gap-2 mr-1">
                  <UserCheck size={16} className="text-green-600" />
                </div>
                <textarea
                  value={messageText}
                  onChange={(e) => setMessageText(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Mensagem como agente (Enter para enviar, Shift+Enter nova linha)"
                  rows={1}
                  className="flex-1 resize-none rounded-xl border border-gray-200 px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent max-h-32 overflow-y-auto"
                  style={{ minHeight: '40px' }}
                />
                <button
                  onClick={handleSend}
                  disabled={!messageText.trim() || sendMutation.isPending}
                  className="bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl p-2.5 transition-colors flex-shrink-0"
                >
                  <Send size={18} />
                </button>
              </div>
            ) : isWaiting ? (
              <div className="bg-orange-50 border-t border-orange-200 px-4 py-3 text-center text-sm text-orange-600 flex-shrink-0">
                Assuma o atendimento para responder ao usuário
              </div>
            ) : (
              <div className="bg-gray-50 border-t px-4 py-3 text-center text-xs text-gray-400 flex-shrink-0">
                Bot está atendendo · O usuário não verá mensagens enviadas aqui
              </div>
            )
          ) : (
            <div className="bg-gray-50 border-t px-4 py-3 text-center text-sm text-gray-400 flex-shrink-0">
              Conversa encerrada
            </div>
          )}
        </div>

        {/* Painel lateral de metadados */}
        <div className="w-56 lg:w-64 border-l bg-white flex-shrink-0 overflow-y-auto hidden xl:block">
          <div className="p-4 space-y-4">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Informações</h3>
            <div className="space-y-3 text-sm">
              <div>
                <p className="text-xs text-gray-400">Canal</p>
                <p className="font-medium capitalize text-gray-800">{conv.channel}</p>
              </div>
              <div>
                <p className="text-xs text-gray-400">Tipo</p>
                <p className="font-medium text-gray-800">{conv.context_type || 'Geral'}</p>
              </div>
              <div>
                <p className="text-xs text-gray-400">Status</p>
                <p className="font-medium text-gray-800">{statusLabels[conv.status] || conv.status}</p>
              </div>
              {conv.assigned_agent_id && (
                <div>
                  <p className="text-xs text-gray-400">Agente</p>
                  <p className="font-medium text-green-700 flex items-center gap-1">
                    <UserCheck size={13} /> {isMyConv ? 'Você' : 'Atribuído'}
                  </p>
                </div>
              )}
              <div>
                <p className="text-xs text-gray-400">Início</p>
                <p className="font-medium text-gray-800">
                  {format(new Date(conv.started_at), "dd/MM/yyyy HH:mm", { locale: ptBR })}
                </p>
              </div>
              {conv.last_message_at && (
                <div>
                  <p className="text-xs text-gray-400">Última mensagem</p>
                  <p className="font-medium text-gray-800">
                    {format(new Date(conv.last_message_at), "dd/MM HH:mm", { locale: ptBR })}
                  </p>
                </div>
              )}
              <div>
                <p className="text-xs text-gray-400">Mensagens</p>
                <p className="font-medium text-gray-800">{conv.messages?.length || 0}</p>
              </div>
              {conv.satisfaction_score && (
                <div>
                  <p className="text-xs text-gray-400">Avaliação</p>
                  <p className="font-medium text-gray-800">{'⭐'.repeat(conv.satisfaction_score)} ({conv.satisfaction_score}/5)</p>
                </div>
              )}
            </div>

            {/* Ações rápidas */}
            {isWaiting && !hasAgent && (
              <div className="pt-3 border-t">
                <button
                  onClick={() => takeOverMutation.mutate()}
                  disabled={takeOverMutation.isPending}
                  className="w-full btn-primary text-sm py-2 flex items-center justify-center gap-2"
                >
                  <HandshakeIcon size={14} />
                  Assumir atendimento
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
