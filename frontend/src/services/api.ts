import type {
  ChatRequest,
  ConnectionStatus,
  Message,
  StreamChunk,
} from '../types/chat'

const CHAT_URL = '/api/chat/stream'
const HEALTH_URL = '/api/health'

export async function checkHealth(
  signal?: AbortSignal,
): Promise<Exclude<ConnectionStatus, 'checking'>> {
  try {
    const response = await fetch(HEALTH_URL, { signal })
    return response.ok ? 'connected' : 'disconnected'
  } catch {
    return 'disconnected'
  }
}

type SseEvent =
  | { kind: 'text'; text: string }
  | { kind: 'error'; message: string }
  | { kind: 'done' }
  | { kind: 'ignore' }

function parseSseLine(line: string): SseEvent {
  if (!line.startsWith('data:')) return { kind: 'ignore' }
  const data = line.slice(5).trimStart()
  if (data === '[DONE]') return { kind: 'done' }
  let chunk: StreamChunk
  try {
    chunk = JSON.parse(data) as StreamChunk
  } catch {
    return { kind: 'ignore' }
  }
  if (typeof chunk.error === 'string') {
    return { kind: 'error', message: chunk.error }
  }
  if (typeof chunk.text === 'string') return { kind: 'text', text: chunk.text }
  return { kind: 'ignore' }
}

function isAbortError(err: unknown): boolean {
  return err instanceof Error && err.name === 'AbortError'
}

/**
 * Streams a chat completion. Exactly one of onDone / onError is called,
 * unless the request is aborted, in which case neither is called.
 */
export async function streamChat(
  messages: Message[],
  onChunk: (text: string) => void,
  onDone: () => void,
  onError: (message: string) => void,
  signal?: AbortSignal,
): Promise<void> {
  const body: ChatRequest = {
    messages: messages.map(({ role, content, timestamp }) => ({
      role,
      content,
      timestamp,
    })),
  }

  try {
    const response = await fetch(CHAT_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal,
    })
    if (!response.ok || !response.body) {
      onError(`Request failed (${response.status})`)
      return
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    // Returns true when the stream is finished (done or error).
    const handleLine = (rawLine: string): boolean => {
      const event = parseSseLine(rawLine.replace(/\r$/, ''))
      if (event.kind === 'text') {
        onChunk(event.text)
      } else if (event.kind === 'error') {
        onError(event.message)
        return true
      } else if (event.kind === 'done') {
        onDone()
        return true
      }
      return false
    }

    for (;;) {
      const { done, value } = await reader.read()
      buffer += decoder.decode(value, { stream: !done })
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''
      for (const line of lines) {
        if (handleLine(line)) {
          await reader.cancel().catch(() => undefined)
          return
        }
      }
      if (done) break
    }

    if (buffer && handleLine(buffer)) return
    onError('Stream ended unexpectedly')
  } catch (err) {
    if (isAbortError(err) || signal?.aborted) return
    onError(err instanceof Error ? err.message : 'Network error')
  }
}
