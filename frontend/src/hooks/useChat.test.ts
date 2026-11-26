import { act, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { useChat } from './useChat'
import * as api from '../services/api'

afterEach(() => vi.restoreAllMocks())

const ISO = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$/

describe('useChat', () => {
  it('streams a reply and timestamps both messages', async () => {
    const spy = vi
      .spyOn(api, 'streamChat')
      .mockImplementation(async (_m, onChunk, onDone) => {
        onChunk('Hel')
        onChunk('lo')
        onDone()
      })
    const { result } = renderHook(() => useChat())
    await act(() => result.current.sendMessage('  hi  '))

    const [user, assistant] = result.current.messages
    expect(user).toMatchObject({ role: 'user', content: 'hi' })
    expect(assistant).toMatchObject({ role: 'assistant', content: 'Hello' })
    expect(user.timestamp).toMatch(ISO)
    expect(assistant.timestamp).toMatch(ISO)
    expect(result.current.isStreaming).toBe(false)
    expect(result.current.error).toBeNull()
    // History sent excludes the assistant placeholder.
    expect(spy.mock.calls[0][0].map((m) => m.role)).toEqual(['user'])
  })

  it('ignores blank input', async () => {
    const spy = vi.spyOn(api, 'streamChat')
    const { result } = renderHook(() => useChat())
    await act(() => result.current.sendMessage('   '))
    expect(spy).not.toHaveBeenCalled()
    expect(result.current.messages).toEqual([])
  })

  it('blocks sending while streaming', async () => {
    let finish: () => void = () => undefined
    const spy = vi
      .spyOn(api, 'streamChat')
      .mockImplementation((_m, _c, onDone) => new Promise<void>((r) => {
        finish = () => {
          onDone()
          r()
        }
      }))
    const { result } = renderHook(() => useChat())
    let first: Promise<void> = Promise.resolve()
    act(() => {
      first = result.current.sendMessage('one')
    })
    expect(result.current.isStreaming).toBe(true)
    await act(() => result.current.sendMessage('two'))
    expect(spy).toHaveBeenCalledTimes(1)
    await act(async () => {
      finish()
      await first
    })
    expect(result.current.isStreaming).toBe(false)
  })

  it('sets error and drops the empty placeholder', async () => {
    vi.spyOn(api, 'streamChat').mockImplementation(async (_m, _c, _d, onError) => {
      onError('boom')
    })
    const { result } = renderHook(() => useChat())
    await act(() => result.current.sendMessage('hi'))
    expect(result.current.error).toBe('boom')
    expect(result.current.messages).toHaveLength(1)
    expect(result.current.isStreaming).toBe(false)
  })

  it('aborts and clears on clearChat', async () => {
    let signal: AbortSignal | undefined
    vi.spyOn(api, 'streamChat').mockImplementation(
      (_m, _c, _d, _e, s) => {
        signal = s
        return new Promise<void>(() => undefined)
      },
    )
    const { result } = renderHook(() => useChat())
    act(() => {
      void result.current.sendMessage('hi')
    })
    act(() => result.current.clearChat())
    expect(signal?.aborted).toBe(true)
    expect(result.current.messages).toEqual([])
    expect(result.current.isStreaming).toBe(false)
  })

  it('aborts on unmount', () => {
    let signal: AbortSignal | undefined
    vi.spyOn(api, 'streamChat').mockImplementation((_m, _c, _d, _e, s) => {
      signal = s
      return new Promise<void>(() => undefined)
    })
    const { result, unmount } = renderHook(() => useChat())
    act(() => {
      void result.current.sendMessage('hi')
    })
    unmount()
    expect(signal?.aborted).toBe(true)
  })
})
