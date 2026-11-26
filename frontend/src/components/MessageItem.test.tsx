import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import MessageItem, { formatTime } from './MessageItem'
import type { Message } from '../types/chat'

afterEach(cleanup)

const ts = '2024-05-01T12:34:56.000Z'

function make(role: Message['role'], content: string): Message {
  return { id: '1', role, content, timestamp: ts }
}

describe('MessageItem', () => {
  it('renders badge, body and timestamp for a user message', () => {
    const { container } = render(<MessageItem message={make('user', 'hello\nworld')} />)
    expect(screen.getByText('You')).toBeTruthy()
    expect(container.querySelector('p')?.textContent).toBe('hello\nworld')
    expect(screen.getByText(formatTime(ts))).toBeTruthy()
    expect(formatTime(ts)).toMatch(/\d{1,2}:\d{2}/)
    expect(container.querySelector('[data-role="user"]')?.className).toContain('justify-end')
  })

  it('renders badge, body and timestamp for an assistant message', () => {
    const { container } = render(<MessageItem message={make('assistant', 'hi there')} />)
    expect(screen.getByText('Gemini Assistant')).toBeTruthy()
    expect(screen.getByText('hi there')).toBeTruthy()
    expect(screen.getByText(formatTime(ts))).toBeTruthy()
    expect(container.querySelector('[data-role="assistant"]')?.className).toContain('justify-start')
  })

  it('renders content as text, not HTML', () => {
    const { container } = render(<MessageItem message={make('assistant', '<b>x</b>')} />)
    expect(container.querySelector('b')).toBeNull()
    expect(screen.getByText('<b>x</b>')).toBeTruthy()
  })

  it('shows typing indicator for empty streaming assistant message', () => {
    render(<MessageItem message={make('assistant', '')} isStreaming />)
    expect(screen.getByLabelText('Assistant is typing')).toBeTruthy()
    expect(screen.getByText('Gemini Assistant')).toBeTruthy()
  })
})
