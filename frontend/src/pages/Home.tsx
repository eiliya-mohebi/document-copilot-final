import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { Button, buttonVariants } from '@/components/ui/button'
import { api, type ThreadListItem } from '@/lib/api'
import { ApiError } from '@/lib/http'
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
          if (err instanceof ApiError) {
            setError(err.message)
          } else {
            setError('Could not load chat threads.')
          }
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
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError('Could not create a chat thread.')
      }
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
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError('Could not delete that chat thread.')
      }
    } finally {
      setDeletingId(null)
    }
  }

  async function handleSignOut() {
    await supabase.auth.signOut()
    navigate('/login', { replace: true })
  }

  return (
    <div className="mx-auto flex min-h-svh max-w-lg flex-col justify-center gap-6 p-6">
      <div>
        <p className="text-sm text-muted-foreground">Document Copilot</p>
        <h1 className="text-2xl font-semibold tracking-tight">Your chats</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Open a past thread or start a new one. History persists across refreshes.
        </p>
      </div>

      {error ? (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      ) : null}

      <div className="flex flex-col gap-3">
        <Button type="button" onClick={handleNewChat} disabled={isCreating}>
          {isCreating ? 'Creating…' : 'New chat'}
        </Button>
        <Button type="button" variant="outline" onClick={handleSignOut}>
          Sign out
        </Button>
      </div>

      <section aria-label="Past chats" className="space-y-3">
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Loading threads…</p>
        ) : threads.length === 0 ? (
          <p className="text-sm text-muted-foreground">No chats yet.</p>
        ) : (
          <ul className="space-y-2">
            {threads.map((thread) => (
              <li
                key={thread.id}
                className="flex items-center justify-between gap-3 border-b border-border py-2"
              >
                <Link
                  to={`/chats/${thread.id}`}
                  className={cn(
                    buttonVariants({ variant: 'ghost' }),
                    'h-auto flex-1 justify-start px-0 text-left whitespace-normal',
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
