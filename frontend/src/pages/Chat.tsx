import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { ChatPanel } from '@/components/chat/ChatPanel'
import { buttonVariants } from '@/components/ui/button'
import { api, type UIChatMessage } from '@/lib/api'
import { ApiError } from '@/lib/http'
import { cn } from '@/lib/utils'

export function Chat() {
  const { threadId } = useParams<{ threadId: string }>()
  const [messages, setMessages] = useState<UIChatMessage[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!threadId) {
      return
    }

    let cancelled = false

    async function loadHistory() {
      setMessages(null)
      setError(null)
      try {
        const history = await api.getThread(threadId!)
        if (!cancelled) {
          setMessages(history.messages)
        }
      } catch (err: unknown) {
        if (!cancelled) {
          if (err instanceof ApiError) {
            setError(err.message)
          } else {
            setError('Could not load chat history.')
          }
        }
      }
    }

    void loadHistory()
    return () => {
      cancelled = true
    }
  }, [threadId])

  if (!threadId) {
    return (
      <div className="mx-auto flex min-h-svh max-w-lg flex-col justify-center gap-4 p-6">
        <p className="text-sm text-destructive" role="alert">
          Missing chat thread.
        </p>
        <Link to="/" className={cn(buttonVariants({ variant: 'outline' }))}>
          Back home
        </Link>
      </div>
    )
  }

  if (error) {
    return (
      <div className="mx-auto flex min-h-svh max-w-lg flex-col justify-center gap-4 p-6">
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
        <Link to="/" className={cn(buttonVariants({ variant: 'outline' }))}>
          Back home
        </Link>
      </div>
    )
  }

  if (messages === null) {
    return (
      <div className="mx-auto flex min-h-svh max-w-lg flex-col justify-center gap-4 p-6">
        <p className="text-sm text-muted-foreground">Loading chat…</p>
      </div>
    )
  }

  return (
    <div className="relative">
      <div className="absolute left-4 top-4 z-10">
        <Link to="/" className={cn(buttonVariants({ variant: 'ghost', size: 'sm' }))}>
          ← Chats
        </Link>
      </div>
      <ChatPanel threadId={threadId} initialMessages={messages} />
    </div>
  )
}
