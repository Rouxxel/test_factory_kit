import { useCallback, useEffect, useRef, useState } from 'react'
import { streamChat } from '../services/api'
import type { Message } from '../types/chat'

function newId(): string {
  return crypto.randomUUID()
}

export interface UseChat {
  messages: Message[]
  isStreaming: boolean
  error: string | null
  sendMessage: (content: string) => Promise<void>
  clearChat: () => void
}

export function useChat(): UseChat {
  const [messages, setMessages] = useState<Message[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const messagesRef = useRef<Message[]>([])
  const streamingRef = useRef(false)
  const controllerRef = useRef<AbortController | null>(null)

  const update = useCallback((next: Message[]) => {
    messagesRef.current = next
    setMessages(next)
  }, [])

  const abort = useCallback(() => {
    controllerRef.current?.abort()
    controllerRef.current = null
    streamingRef.current = false
  }, [])

  useEffect(() => abort, [abort])

  const sendMessage = useCallback(
    async (content: string) => {
      const text = content.trim()
      if (!text || streamingRef.current) return

      const userMessage: Message = {
        id: newId(),
        role: 'user',
        content: text,
        timestamp: new Date().toISOString(),
      }
      const assistantMessage: Message = {
        id: newId(),
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
      }
      // History excludes the empty assistant placeholder.
      const history = [...messagesRef.current, userMessage]
      update([...history, assistantMessage])

      const controller = new AbortController()
      controllerRef.current = controller
      streamingRef.current = true
      setIsStreaming(true)
      setError(null)

      const finish = () => {
        if (controllerRef.current !== controller) return
        controllerRef.current = null
        streamingRef.current = false
        setIsStreaming(false)
      }

      await streamChat(
        history,
        (delta) => {
          if (controller.signal.aborted) return
          update(
            messagesRef.current.map((m) =>
              m.id === assistantMessage.id
                ? { ...m, content: m.content + delta }
                : m,
            ),
          )
        },
        finish,
        (message) => {
          if (controller.signal.aborted) return
          setError(message)
          // Drop the placeholder if nothing streamed so the UI has no empty bubble.
          update(
            messagesRef.current.filter(
              (m) => m.id !== assistantMessage.id || m.content !== '',
            ),
          )
          finish()
        },
        controller.signal,
      )
    },
    [update],
  )

  const clearChat = useCallback(() => {
    abort()
    update([])
    setError(null)
    setIsStreaming(false)
  }, [abort, update])

  return { messages, isStreaming, error, sendMessage, clearChat }
}
