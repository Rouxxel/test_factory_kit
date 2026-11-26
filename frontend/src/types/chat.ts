export type Role = 'user' | 'assistant'

export interface Message {
  id: string
  role: Role
  content: string
  timestamp: string
}

/** Message as sent to the backend (the client-only `id` is omitted). */
export type ChatRequestMessage = Omit<Message, 'id'>

export interface ChatRequest {
  messages: ChatRequestMessage[]
}

/** Parsed payload of one SSE `data:` event (excluding the `[DONE]` sentinel). */
export interface StreamChunk {
  text?: string
  error?: string
}

export type ConnectionStatus = 'connected' | 'disconnected' | 'checking'
