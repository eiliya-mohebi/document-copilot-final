import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'
import { ApiError } from '@/lib/http'
import { supabase } from '@/lib/supabase'

export function Home() {
  const navigate = useNavigate()
  const [error, setError] = useState<string | null>(null)
  const [isCreating, setIsCreating] = useState(false)

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

  async function handleSignOut() {
    await supabase.auth.signOut()
    navigate('/login', { replace: true })
  }

  return (
    <div className="mx-auto flex min-h-svh max-w-lg flex-col justify-center gap-6 p-6">
      <div>
        <p className="text-sm text-muted-foreground">Document Copilot</p>
        <h1 className="text-2xl font-semibold tracking-tight">Start a chat</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Open a new thread and ask a question. Replies are stubbed until retrieval
          is wired up.
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
    </div>
  )
}
