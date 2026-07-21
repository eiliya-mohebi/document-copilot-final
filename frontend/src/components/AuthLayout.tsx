import type { ReactNode } from 'react'

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'

type AuthLayoutProps = {
  title: string
  description?: string
  children: ReactNode
}

export function AuthLayout({ title, description, children }: AuthLayoutProps) {
  return (
    <div className="relative flex min-h-svh flex-col items-center justify-center gap-8 p-6">
      <div className="animate-message-in flex max-w-md flex-col items-center gap-3 text-center">
        <p className="font-heading text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
          Document Copilot
        </p>
        <p className="text-sm leading-relaxed text-muted-foreground">
          Grounded SEC research for Driftwood analysts — cited passages, no invented facts.
        </p>
      </div>

      <Card className="animate-message-in w-full max-w-sm border-border/70 bg-card/90 shadow-[0_12px_40px_-24px_oklch(0.35_0.05_230/0.45)]">
        <CardHeader>
          <CardTitle className="text-xl">{title}</CardTitle>
          {description ? <CardDescription>{description}</CardDescription> : null}
        </CardHeader>
        <CardContent>{children}</CardContent>
      </Card>
    </div>
  )
}
