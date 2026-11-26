import { useState } from 'react'
import type { KeyboardEvent } from 'react'
import { Loader2, Send, Trash2 } from 'lucide-react'

interface ChatInputProps {
  onSend: (content: string) => void | Promise<void>
  onClear: () => void
  isStreaming: boolean
}

function ChatInput({ onSend, onClear, isStreaming }: ChatInputProps) {
  const [value, setValue] = useState('')

  const submit = () => {
    const text = value.trim()
    if (!text || isStreaming) return
    setValue('')
    void onSend(text)
  }

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault()
      submit()
    }
  }

  return (
    <form
      className="flex items-end gap-2 border-t border-slate-700 bg-slate-800 p-3 sm:p-4"
      onSubmit={(event) => {
        event.preventDefault()
        submit()
      }}
    >
      <textarea
        aria-label="Message"
        className="max-h-40 min-h-[44px] flex-1 resize-none rounded-lg border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
        placeholder="Type a message (Enter to send, Shift+Enter for newline)"
        rows={1}
        value={value}
        onChange={(event) => setValue(event.target.value)}
        onKeyDown={handleKeyDown}
      />
      <button
        type="submit"
        disabled={isStreaming || value.trim() === ''}
        className="flex h-11 items-center gap-2 rounded-lg bg-indigo-600 px-4 text-sm font-medium text-white hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isStreaming ? (
          <Loader2 className="h-4 w-4 animate-spin" data-testid="send-spinner" aria-hidden="true" />
        ) : (
          <Send className="h-4 w-4" aria-hidden="true" />
        )}
        Send
      </button>
      <button
        type="button"
        onClick={onClear}
        className="flex h-11 items-center gap-2 rounded-lg border border-slate-600 px-3 text-sm text-slate-200 hover:bg-slate-700"
      >
        <Trash2 className="h-4 w-4" aria-hidden="true" />
        Clear Chat
      </button>
    </form>
  )
}

export default ChatInput
