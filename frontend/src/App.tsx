import Header from './components/Header'
import MessageList from './components/MessageList'
import ChatInput from './components/ChatInput'
import { useChat } from './hooks/useChat'

function App() {
  const { messages, isStreaming, error, sendMessage, clearChat } = useChat()

  return (
    <div className="mx-auto flex h-screen w-full max-w-4xl flex-col bg-slate-900 text-slate-100">
      <Header />
      <main className="flex min-h-0 flex-1 flex-col">
        <MessageList messages={messages} isStreaming={isStreaming} />
        {error && (
          <div
            role="alert"
            className="mx-4 mb-2 rounded-lg border border-red-700 bg-red-950 px-3 py-2 text-sm text-red-200"
          >
            {error}
          </div>
        )}
      </main>
      <ChatInput onSend={sendMessage} onClear={clearChat} isStreaming={isStreaming} />
    </div>
  )
}

export default App
