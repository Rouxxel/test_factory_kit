import { MessageSquare } from 'lucide-react'

function App() {
  return (
    <div className="flex min-h-screen flex-col bg-slate-900 text-slate-100">
      <header className="flex items-center gap-2 border-b border-slate-700 px-6 py-4">
        <MessageSquare className="h-5 w-5" aria-hidden="true" />
        <h1 className="text-lg font-semibold">Chat</h1>
      </header>
      <main className="flex flex-1 items-center justify-center p-6">
        <p className="text-slate-400">Chat interface coming soon.</p>
      </main>
    </div>
  )
}

export default App