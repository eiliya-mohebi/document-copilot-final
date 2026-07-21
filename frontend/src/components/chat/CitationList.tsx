import type { MessageCitation } from '@/lib/api'

type CitationListProps = {
  citations: MessageCitation[]
}

export function CitationList({ citations }: CitationListProps) {
  if (citations.length === 0) {
    return null
  }

  return (
    <div className="mt-2 space-y-1">
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
        Sources
      </p>
      {citations.map((citation) => (
        <details
          key={`${citation.marker}-${citation.chunkId}`}
          className="rounded-md border border-border bg-muted/40 px-3 py-2 text-sm"
        >
          <summary className="cursor-pointer select-none text-sm">
            <span className="font-mono text-xs text-muted-foreground">
              [{citation.marker}]
            </span>{' '}
            <span className="font-medium">{citation.company}</span>{' '}
            <span className="text-muted-foreground">
              {citation.form} FY{citation.fiscalYear}
              {citation.section ? ` · ${citation.section}` : ''}
            </span>
          </summary>
          <div className="mt-2 space-y-2 text-sm text-muted-foreground">
            {citation.quote ? (
              <p className="italic">“{citation.quote}”</p>
            ) : null}
            <p className="whitespace-pre-wrap border-l-2 border-border pl-3">
              {citation.excerpt}
            </p>
            <p className="text-xs">
              {citation.ticker} · filed {citation.filingDate}
              {citation.sourceUrl ? (
                <>
                  {' · '}
                  <a
                    href={citation.sourceUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="underline hover:text-foreground"
                  >
                    view filing
                  </a>
                </>
              ) : null}
            </p>
          </div>
        </details>
      ))}
    </div>
  )
}
