import { Link, useParams } from 'react-router-dom'

import { ChatPanel } from '@/components/chat/ChatPanel'
import { buttonVariants } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export function Chat() {
  const { threadId } = useParams<{ threadId: string }>()

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

  return (
    <div className="relative">
      <div className="absolute left-4 top-4 z-10">
        <Link to="/" className={cn(buttonVariants({ variant: 'ghost', size: 'sm' }))}>
          ← New chat
        </Link>
      </div>
      <ChatPanel threadId={threadId} />
    </div>
  )
}
