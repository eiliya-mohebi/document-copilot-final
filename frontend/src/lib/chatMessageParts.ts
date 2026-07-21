import type { MessageCitation, MessageRefusal, RefusalReason } from '@/lib/api'

export function messageText(parts: Array<{ type: string; text?: string }>): string {
  return parts
    .filter((part) => part.type === 'text' && typeof part.text === 'string')
    .map((part) => part.text ?? '')
    .join('')
}

export function messageCitations(
  parts: Array<{ type: string; data?: unknown }>,
): MessageCitation[] {
  return parts
    .filter((part) => part.type === 'data-citations' && Array.isArray(part.data))
    .flatMap((part) => part.data as MessageCitation[])
}

export function messageRefusal(
  parts: Array<{ type: string; data?: unknown }>,
): MessageRefusal | null {
  const part = parts.find((item) => item.type === 'data-refusal')
  if (!part || part.data === null || typeof part.data !== 'object') {
    return null
  }
  const reasons = (part.data as { reasons?: unknown }).reasons
  if (!Array.isArray(reasons)) {
    return null
  }
  const allowed: RefusalReason[] = ['insufficient_evidence', 'no_advice']
  const filtered = reasons.filter(
    (reason): reason is RefusalReason =>
      typeof reason === 'string' && allowed.includes(reason as RefusalReason),
  )
  return filtered.length > 0 ? { reasons: filtered } : null
}
