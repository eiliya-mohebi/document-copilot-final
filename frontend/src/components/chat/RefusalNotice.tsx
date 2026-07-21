import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import type { RefusalReason } from '@/lib/api'

type RefusalNoticeProps = {
  reasons: RefusalReason[]
}

function copyFor(reasons: RefusalReason[]): { title: string; body: string } {
  const insufficient = reasons.includes('insufficient_evidence')
  const noAdvice = reasons.includes('no_advice')

  if (insufficient && noAdvice) {
    return {
      title: 'Limited answer',
      body: 'Not enough evidence in the corpus for part of this question, and investment advice is out of scope.',
    }
  }
  if (insufficient) {
    return {
      title: 'Not enough evidence in the corpus',
      body: 'The filings retrieved for this turn do not support a grounded answer, so nothing was invented.',
    }
  }
  return {
    title: 'No investment advice',
    body: 'Stock picks and trading recommendations are out of scope. Filing facts are cited below when available.',
  }
}

export function RefusalNotice({ reasons }: RefusalNoticeProps) {
  if (reasons.length === 0) {
    return null
  }

  const { title, body } = copyFor(reasons)

  return (
    <Alert className="border-trust/30 bg-trust-muted text-trust-foreground">
      <AlertTitle>{title}</AlertTitle>
      <AlertDescription>{body}</AlertDescription>
    </Alert>
  )
}
