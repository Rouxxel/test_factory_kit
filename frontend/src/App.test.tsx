import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App.tsx'

vi.mock('./services/api', () => ({
  checkHealth: vi.fn().mockResolvedValue('connected'),
  streamChat: vi.fn(),
}))

afterEach(cleanup)

describe('App', () => {
  it('renders the chat layout', async () => {
    render(<App />)
    expect(
      screen.getByRole('heading', { name: 'Gemini 2.5 Flash Chatbot' }),
    ).toBeTruthy()
    expect(screen.getByLabelText('Message')).toBeTruthy()
    expect(await screen.findByText('Connected')).toBeTruthy()
  })
})
