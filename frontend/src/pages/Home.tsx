import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { ErrorAlert } from '@/components/ErrorAlert'
import { Button, buttonVariants } from '@/components/ui/button'
import { api, type ThreadListItem } from '@/lib/api'
import { friendlyErrorMessage } from '@/lib/errors'
import { cn } from '@/lib/utils'
import { supabase } from '@/lib/supabase'

function formatUpdatedAt(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

export function Home() {
  const navigate = useNavigate()
  const [threads, setThreads] = useState<ThreadListItem[]>([])
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isCreating, setIsCreating] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function loadThreads() {
      setIsLoading(true)
      setError(null)
      try {
        const response = await api.listThreads()
        if (!cancelled) {
          setThreads(response.threads)
        }
      } catch (err: unknown) {
        if (!cancelled) {
          setError(friendlyErrorMessage(err))
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    void loadThreads()
    return () => {
      cancelled = true
    }
  }, [])

  async function handleNewChat() {
    setIsCreating(true)
    setError(null)
    try {
      const thread = await api.createThread()
      navigate(`/chats/${thread.id}`)
    } catch (err: unknown) {
      setError(friendlyErrorMessage(err))
    } finally {
      setIsCreating(false)
    }
  }

  async function handleDelete(threadId: string) {
    setDeletingId(threadId)
    setError(null)
    try {
      await api.deleteThread(threadId)
      setThreads((current) => current.filter((thread) => thread.id !== threadId))
    } catch (err: unknown) {
      setError(friendlyErrorMessage(err))
    } finally {
      setDeletingId(null)
    }
  }

  async function handleSignOut() {
    await supabase.auth.signOut()
    navigate('/login', { replace: true })
  }

  return (
    <div className="mx-auto flex min-h-svh w-full max-w-xl flex-col gap-8 px-6 py-12">
      <header className="animate-message-in space-y-3">
        <p className="font-heading text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
          Document Copilot
        </p>
        <p className="max-w-md text-sm leading-relaxed text-muted-foreground">
          Your grounded filing research workspace. Open a thread or start a new
          question against the curated corpus.
        </p>
      </header>

      {error ? <ErrorAlert message={error} /> : null}

      <div className="animate-message-in flex flex-wrap gap-3">
        <Button type="button" onClick={handleNewChat} disabled={isCreating}>
          {isCreating ? 'Creating…' : 'New chat'}
        </Button>
        <Button type="button" variant="outline" onClick={handleSignOut}>
          Sign out
        </Button>
      </div>

      <section aria-label="Past chats" className="animate-message-in space-y-3">
        <h2 className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">
          Your chats
        </h2>

        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading threads…</p>
        ) : threads.length === 0 ? (
          <div className="rounded-xl border border-dashed border-border/80 bg-card/50 px-4 py-6">
            <p className="text-sm font-medium text-foreground">No chats yet</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Start a new chat and ask something like how Apple’s revenue mix
              shifted across recent 10-Ks.
            </p>
          </div>
        ) : (
          <ul className="space-y-2">
            {threads.map((thread) => (
              <li
                key={thread.id}
                className="flex items-center justify-between gap-3 rounded-xl border border-border/70 bg-card/70 px-3 py-2.5 transition-colors hover:border-primary/25 hover:bg-accent/40"
              >
                <Link
                  to={`/chats/${thread.id}`}
                  className={cn(
                    buttonVariants({ variant: 'ghost' }),
                    'h-auto flex-1 justify-start px-0 text-left whitespace-normal hover:bg-transparent',
                  )}
                >
                  <span className="flex flex-col gap-0.5">
                    <span className="text-sm font-medium">{thread.title}</span>
                    <span className="text-xs text-muted-foreground">
                      {formatUpdatedAt(thread.updatedAt)}
                    </span>
                  </span>
                </Link>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={deletingId === thread.id}
                  onClick={() => void handleDelete(thread.id)}
                >
                  {deletingId === thread.id ? 'Deleting…' : 'Delete'}
                </Button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
