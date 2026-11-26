import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import ChatInput from './ChatInput'

afterEach(cleanup)

function setup(isStreaming = false) {
  const onSend = vi.fn()
  const onClear = vi.fn()
  render(<ChatInput onSend={onSend} onClear={onClear} isStreaming={isStreaming} />)
  return { onSend, onClear, box: screen.getByLabelText('Message') as HTMLTextAreaElement }
}

describe('ChatInput', () => {
  it('submits on Enter and clears the box', () => {
    const { onSend, box } = setup()
    fireEvent.change(box, { target: { value: 'hi' } })
    fireEvent.keyDown(box, { key: 'Enter' })
    expect(onSend).toHaveBeenCalledWith('hi')
    expect(box.value).toBe('')
  })

  it('does not submit on Shift+Enter', () => {
    const { onSend, box } = setup()
    fireEvent.change(box, { target: { value: 'hi' } })
    fireEvent.keyDown(box, { key: 'Enter', shiftKey: true })
    expect(onSend).not.toHaveBeenCalled()
    expect(box.value).toBe('hi')
  })

  it('submits via Send button', () => {
    const { onSend, box } = setup()
    fireEvent.change(box, { target: { value: 'yo' } })
    fireEvent.click(screen.getByRole('button', { name: /send/i }))
    expect(onSend).toHaveBeenCalledWith('yo')
  })

  it('does not send empty input', () => {
    const { onSend, box } = setup()
    fireEvent.keyDown(box, { key: 'Enter' })
    expect(onSend).not.toHaveBeenCalled()
  })

  it('calls onClear from Clear Chat', () => {
    const { onClear } = setup()
    fireEvent.click(screen.getByRole('button', { name: /clear chat/i }))
    expect(onClear).toHaveBeenCalledTimes(1)
  })

  it('disables Send and shows spinner while streaming', () => {
    const { onSend, box } = setup(true)
    fireEvent.change(box, { target: { value: 'hi' } })
    fireEvent.keyDown(box, { key: 'Enter' })
    expect(onSend).not.toHaveBeenCalled()
    expect((screen.getByRole('button', { name: /send/i }) as HTMLButtonElement).disabled).toBe(true)
    expect(screen.getByTestId('send-spinner')).toBeTruthy()
  })
})
