import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { api, type MeResponse } from '@/lib/api'
import { ApiError } from '@/lib/http'
import { supabase } from '@/lib/supabase'

export function Home() {
  const navigate = useNavigate()
  const [me, setMe] = useState<MeResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let mounted = true

    api
      .me()
      .then((response) => {
        if (mounted) {
          setMe(response)
          setError(null)
        }
      })
      .catch((err: unknown) => {
        if (!mounted) {
          return
        }
        if (err instanceof ApiError) {
          setError(err.message)
          return
        }
        setError('Failed to load identity from the API.')
      })
      .finally(() => {
        if (mounted) {
          setIsLoading(false)
        }
      })

    return () => {
      mounted = false
    }
  }, [])

  async function handleSignOut() {
    await supabase.auth.signOut()
    navigate('/login', { replace: true })
  }

  return (
    <div className="mx-auto flex min-h-svh max-w-lg flex-col justify-center gap-6 p-6">
      <div>
        <p className="text-sm text-muted-foreground">Document Copilot</p>
        <h1 className="text-2xl font-semibold tracking-tight">You are signed in</h1>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Protected API identity</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Calling protected API…</p>
          ) : null}

          {error ? (
            <p className="text-sm text-destructive" role="alert">
              {error}
            </p>
          ) : null}

          {me ? (
            <dl className="space-y-3 text-sm">
              <div>
                <dt className="text-muted-foreground">Email</dt>
                <dd className="font-medium">{me.email}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">User id</dt>
                <dd className="font-mono text-xs">{me.id}</dd>
              </div>
            </dl>
          ) : null}
        </CardContent>
      </Card>

      <Button type="button" variant="outline" onClick={handleSignOut}>
        Sign out
      </Button>
    </div>
  )
}
