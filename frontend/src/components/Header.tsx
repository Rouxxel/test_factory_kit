import { useEffect, useState } from 'react'
import { Bot } from 'lucide-react'
import { checkHealth } from '../services/api'
import type { ConnectionStatus } from '../types/chat'

const POLL_INTERVAL_MS = 30000

const STATUS_STYLES: Record<ConnectionStatus, { dot: string; label: string }> = {
  connected: { dot: 'bg-emerald-500', label: 'Connected' },
  disconnected: { dot: 'bg-red-500', label: 'Disconnected' },
  checking: { dot: 'bg-amber-400 animate-pulse', label: 'Checking...' },
}

function Header() {
  const [status, setStatus] = useState<ConnectionStatus>('checking')

  useEffect(() => {
    const controller = new AbortController()
    const run = async () => {
      const result = await checkHealth(controller.signal)
      if (!controller.signal.aborted) setStatus(result)
    }
    void run()
    const timer = setInterval(() => void run(), POLL_INTERVAL_MS)
    return () => {
      controller.abort()
      clearInterval(timer)
    }
  }, [])

  const { dot, label } = STATUS_STYLES[status]

  return (
    <header className="flex items-center justify-between gap-3 border-b border-slate-700 bg-slate-800 px-4 py-3 sm:px-6">
      <div className="flex items-center gap-2">
        <Bot className="h-5 w-5 text-indigo-400" aria-hidden="true" />
        <h1 className="text-base font-semibold sm:text-lg">
          Gemini 2.5 Flash Chatbot
        </h1>
      </div>
      <div
        className="flex items-center gap-2 text-xs text-slate-300"
        role="status"
        aria-label={`Backend status: ${label}`}
        data-status={status}
      >
        <span className={`h-2.5 w-2.5 rounded-full ${dot}`} aria-hidden="true" />
        <span>{label}</span>
      </div>
    </header>
  )
}

export default Header
