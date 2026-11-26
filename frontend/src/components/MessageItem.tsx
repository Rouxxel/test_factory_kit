import type { Message } from '../types/chat'

interface MessageItemProps {
  message: Message
  isStreaming?: boolean
}

export function formatTime(iso: string): string {
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function MessageItem({ message, isStreaming = false }: MessageItemProps) {
  const isUser = message.role === 'user'
  const showTyping = !isUser && isStreaming && message.content === ''

  return (
    <div
      className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'}`}
      data-role={message.role}
    >
      <div
        className={`flex max-w-[85%] flex-col gap-1 rounded-2xl px-4 py-2 shadow-sm sm:max-w-[75%] ${
          isUser
            ? 'items-end rounded-br-sm bg-indigo-600 text-white'
            : 'items-start rounded-bl-sm border border-slate-700 bg-slate-800 text-slate-100'
        }`}
      >
        <span
          className={`rounded-full px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide ${
            isUser ? 'bg-indigo-800 text-indigo-100' : 'bg-slate-700 text-slate-200'
          }`}
        >
          {isUser ? 'You' : 'Gemini Assistant'}
        </span>
        {showTyping ? (
          <span role="status" aria-label="Assistant is typing" className="flex gap-1 py-1">
            <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400" />
            <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:150ms]" />
            <span className="h-2 w-2 animate-bounce rounded-full bg-slate-400 [animation-delay:300ms]" />
          </span>
        ) : (
          <p className="whitespace-pre-wrap break-words text-sm">
            {message.content}
          </p>
        )}
        <time
          dateTime={message.timestamp}
          className={`text-xs ${isUser ? 'text-indigo-200' : 'text-slate-400'}`}
        >
          {formatTime(message.timestamp)}
        </time>
      </div>
    </div>
  )
}

export default MessageItem
