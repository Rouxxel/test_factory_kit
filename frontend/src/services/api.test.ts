import { afterEach, describe, expect, it, vi } from 'vitest'
import { checkHealth, streamChat } from './api'
import type { Message } from '../types/chat'

const msgs: Message[] = [
  { id: 'a', role: 'user', content: 'hi', timestamp: '2026-01-01T00:00:00.000Z' },
]

function sseResponse(parts: string[], status = 200): Response {
  const enc = new TextEncoder()
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      for (const p of parts) controller.enqueue(enc.encode(p))
      controller.close()
    },
  })
  return new Response(stream, { status })
}

function run(parts: string[]) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(sseResponse(parts)))
  const onChunk = vi.fn()
  const onDone = vi.fn()
  const onError = vi.fn()
  return { onChunk, onDone, onError, p: streamChat(msgs, onChunk, onDone, onError) }
}

afterEach(() => vi.unstubAllGlobals())

describe('streamChat', () => {
  it('parses chunks split across reads and finishes on [DONE]', async () => {
    const { p, onChunk, onDone, onError } = run([
      'data: {"te',
      'xt": "Hel"}\n\ndata: {"text": "lo"}\n',
      '\ndata: [DONE]\n\n',
    ])
    await p
    expect(onChunk.mock.calls).toEqual([['Hel'], ['lo']])
    expect(onDone).toHaveBeenCalledTimes(1)
    expect(onError).not.toHaveBeenCalled()
  })

  it('handles CRLF line endings', async () => {
    const { p, onChunk, onDone } = run(['data: {"text":"x"}\r\n\r\ndata: [DONE]\r\n\r\n'])
    await p
    expect(onChunk).toHaveBeenCalledWith('x')
    expect(onDone).toHaveBeenCalledTimes(1)
  })

  it('reports an error event without calling onDone', async () => {
    const { p, onDone, onError } = run(['data: {"error": "boom"}\n\n'])
    await p
    expect(onError).toHaveBeenCalledWith('boom')
    expect(onDone).not.toHaveBeenCalled()
  })

  it('reports an error when the stream ends without [DONE]', async () => {
    const { p, onDone, onError } = run(['data: {"text":"x"}\n\n'])
    await p
    expect(onError).toHaveBeenCalledTimes(1)
    expect(onDone).not.toHaveBeenCalled()
  })

  it('reports HTTP errors', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(sseResponse([], 500)))
    const onError = vi.fn()
    await streamChat(msgs, vi.fn(), vi.fn(), onError)
    expect(onError).toHaveBeenCalledWith('Request failed (500)')
  })

  it('posts messages without id', async () => {
    const fetchMock = vi.fn().mockResolvedValue(sseResponse(['data: [DONE]\n\n']))
    vi.stubGlobal('fetch', fetchMock)
    await streamChat(msgs, vi.fn(), vi.fn(), vi.fn())
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    expect(url).toBe('/api/chat/stream')
    expect(JSON.parse(init.body as string)).toEqual({
      messages: [{ role: 'user', content: 'hi', timestamp: msgs[0].timestamp }],
    })
  })

  it('stays silent when aborted', async () => {
    const controller = new AbortController()
    vi.stubGlobal(
      'fetch',
      vi.fn().mockImplementation(() => {
        controller.abort()
        return Promise.reject(new DOMException('aborted', 'AbortError'))
      }),
    )
    const onDone = vi.fn()
    const onError = vi.fn()
    await streamChat(msgs, vi.fn(), onDone, onError, controller.signal)
    expect(onDone).not.toHaveBeenCalled()
    expect(onError).not.toHaveBeenCalled()
  })
})

describe('checkHealth', () => {
  it('returns connected on 200 and disconnected otherwise', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}', { status: 200 })))
    expect(await checkHealth()).toBe('connected')
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('{}', { status: 503 })))
    expect(await checkHealth()).toBe('disconnected')
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('down')))
    expect(await checkHealth()).toBe('disconnected')
  })
})
