import { useChat } from '@ai-sdk/react'
import { DefaultChatTransport } from 'ai'
import { useState, type FormEvent } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { getAccessToken } from '@/lib/api'
import { env } from '@/lib/env'

type ChatPanelProps = {
  threadId: string
}

function messageText(parts: Array<{ type: string; text?: string }>): string {
  return parts
    .filter((part) => part.type === 'text' && typeof part.text === 'string')
    .map((part) => part.text ?? '')
    .join('')
}

export function ChatPanel({ threadId }: ChatPanelProps) {
  const [input, setInput] = useState('')
  const { messages, sendMessage, status, error } = useChat({
    id: threadId,
    transport: new DefaultChatTransport({
      api: `${env.apiBaseUrl}/chat/stream`,
      headers: async () => {
        const token = await getAccessToken()
        if (!token) {
          throw new Error('Not authenticated')
        }
        return { Authorization: `Bearer ${token}` }
      },
      body: { threadId },
    }),
  })

  const isStreaming = status === 'submitted' || status === 'streaming'

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const text = input.trim()
    if (!text || isStreaming) {
      return
    }
    setInput('')
    await sendMessage({ text })
  }

  return (
    <div className="mx-auto flex h-svh w-full max-w-2xl flex-col px-4 py-6">
      <header className="mb-4 border-b border-border pb-4">
        <p className="text-sm text-muted-foreground">Document Copilot</p>
        <h1 className="text-lg font-semibold tracking-tight">Chat</h1>
      </header>

      <div className="flex-1 space-y-4 overflow-y-auto pb-4">
        {messages.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Ask a question to see a stubbed streamed reply.
          </p>
        ) : null}

        {messages.map((message) => (
          <div key={message.id} className="space-y-1">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              {message.role === 'user' ? 'You' : 'Assistant'}
            </p>
            <p className="whitespace-pre-wrap text-sm leading-relaxed">
              {messageText(message.parts)}
            </p>
          </div>
        ))}

        {isStreaming ? (
          <p className="text-xs text-muted-foreground" aria-live="polite">
            Assistant is responding…
          </p>
        ) : null}

        {error ? (
          <p className="text-sm text-destructive" role="alert">
            {error.message}
          </p>
        ) : null}
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2 border-t border-border pt-4">
        <Input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask about a filing…"
          disabled={isStreaming}
          aria-label="Message"
        />
        <Button type="submit" disabled={isStreaming || input.trim() === ''}>
          Send
        </Button>
      </form>
    </div>
  )
}
