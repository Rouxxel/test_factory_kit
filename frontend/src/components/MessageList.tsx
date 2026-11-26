import { useEffect, useRef } from 'react'
import type { Message } from '../types/chat'
import MessageItem from './MessageItem'

interface MessageListProps {
  messages: Message[]
  isStreaming: boolean
}

function MessageList({ messages, isStreaming }: MessageListProps) {
  const endRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    // scrollIntoView is missing in some environments (e.g. jsdom).
    endRef.current?.scrollIntoView?.({ behavior: 'smooth', block: 'end' })
  }, [messages])

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center p-6 text-center text-slate-400">
        <p>Send a message to start chatting with Gemini.</p>
      </div>
    )
  }

  return (
    <div
      className="flex flex-1 flex-col gap-4 overflow-y-auto p-4 sm:p-6"
      role="log"
      aria-live="polite"
    >
      {messages.map((message) => (
        <MessageItem key={message.id} message={message} isStreaming={isStreaming} />
      ))}
      <div ref={endRef} />
    </div>
  )
}

export default MessageList
