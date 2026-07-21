import { useChat } from '@ai-sdk/react'
import { DefaultChatTransport } from 'ai'
import { useState, type FormEvent } from 'react'

import { ChatEmptyState } from '@/components/chat/ChatEmptyState'
import { CitationList } from '@/components/chat/CitationList'
import { RefusalNotice } from '@/components/chat/RefusalNotice'
import { ErrorAlert } from '@/components/ErrorAlert'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { getAccessToken, type UIChatMessage } from '@/lib/api'
import {
  messageCitations,
  messageRefusal,
  messageText,
} from '@/lib/chatMessageParts'
import { env } from '@/lib/env'
import { friendlyErrorMessage } from '@/lib/errors'

type ChatPanelProps = {
  threadId: string
  initialMessages?: UIChatMessage[]
}

export function ChatPanel({ threadId, initialMessages = [] }: ChatPanelProps) {
  const [input, setInput] = useState('')
  const { messages, sendMessage, status, error } = useChat({
    id: threadId,
    messages: initialMessages,
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

  async function send(text: string) {
    const trimmed = text.trim()
    if (!trimmed || isStreaming) {
      return
    }
    setInput('')
    await sendMessage({ text: trimmed })
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    await send(input)
  }

  return (
    <div className="mx-auto flex h-svh w-full max-w-2xl flex-col px-4 pb-6 pt-14">
      <header className="mb-5 animate-message-in border-b border-border/70 pb-4">
        <p className="font-heading text-xl font-semibold tracking-tight text-foreground">
          Document Copilot
        </p>
        <p className="mt-1 text-sm text-muted-foreground">
          Grounded answers from the SEC filing corpus
        </p>
      </header>

      <div className="flex-1 space-y-5 overflow-y-auto pb-4">
        {messages.length === 0 ? (
          <ChatEmptyState
            disabled={isStreaming}
            onPrompt={(prompt) => void send(prompt)}
          />
        ) : null}

        {messages.map((message) => {
          const refusal =
            message.role === 'assistant' ? messageRefusal(message.parts) : null
          const citations =
            message.role === 'assistant' ? messageCitations(message.parts) : []
          const isUser = message.role === 'user'

          return (
            <div
              key={message.id}
              className={`animate-message-in space-y-2 ${isUser ? 'ml-6' : 'mr-2'}`}
            >
              <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-muted-foreground">
                {isUser ? 'You' : 'Assistant'}
              </p>
              <div
                className={
                  isUser
                    ? 'rounded-2xl rounded-tr-md bg-primary px-3.5 py-2.5 text-sm leading-relaxed text-primary-foreground'
                    : 'space-y-3 rounded-2xl rounded-tl-md border border-border/70 bg-card/80 px-3.5 py-3 text-sm leading-relaxed shadow-[0_1px_0_oklch(0.85_0.02_220/0.5)]'
                }
              >
                <p className="whitespace-pre-wrap">{messageText(message.parts)}</p>
                {!isUser && refusal ? <RefusalNotice reasons={refusal.reasons} /> : null}
                {!isUser ? <CitationList citations={citations} /> : null}
              </div>
            </div>
          )
        })}

        {isStreaming ? (
          <p
            className="flex items-center gap-2 text-xs text-muted-foreground"
            aria-live="polite"
          >
            <span className="inline-flex gap-1" aria-hidden>
              <span className="size-1.5 rounded-full bg-primary animate-pulse-dot" />
              <span
                className="size-1.5 rounded-full bg-primary animate-pulse-dot"
                style={{ animationDelay: '160ms' }}
              />
              <span
                className="size-1.5 rounded-full bg-primary animate-pulse-dot"
                style={{ animationDelay: '320ms' }}
              />
            </span>
            Searching filings and drafting a cited answer…
          </p>
        ) : null}

        {error ? <ErrorAlert message={friendlyErrorMessage(error)} /> : null}
      </div>

      <form
        onSubmit={handleSubmit}
        className="flex gap-2 border-t border-border/70 bg-card/40 pt-4 backdrop-blur-sm"
      >
        <Input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Ask about a filing…"
          disabled={isStreaming}
          aria-label="Message"
          className="bg-card/90"
        />
        <Button type="submit" disabled={isStreaming || input.trim() === ''}>
          Send
        </Button>
      </form>
    </div>
  )
}
