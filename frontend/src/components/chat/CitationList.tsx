import { useState } from 'react'

import { PassageSheet } from '@/components/chat/PassageSheet'
import type { MessageCitation } from '@/lib/api'

type CitationListProps = {
  citations: MessageCitation[]
}

export function CitationList({ citations }: CitationListProps) {
  const [selectedChunkId, setSelectedChunkId] = useState<string | null>(null)

  if (citations.length === 0) {
    return null
  }

  return (
    <div className="mt-2 space-y-1">
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
        Sources
      </p>
      {citations.map((citation) => (
        <button
          key={`${citation.marker}-${citation.chunkId}`}
          type="button"
          onClick={() => setSelectedChunkId(citation.chunkId)}
          className="flex w-full items-start gap-2 rounded-md border border-border/70 bg-background/60 px-3 py-2 text-left text-sm transition-colors hover:border-primary/30 hover:bg-accent/50"
        >
          <span className="font-mono text-xs text-muted-foreground">
            [{citation.marker}]
          </span>
          <span>
            <span className="font-medium">{citation.company}</span>{' '}
            <span className="text-muted-foreground">
              {citation.form} FY{citation.fiscalYear}
              {citation.section ? ` · ${citation.section}` : ''}
            </span>
          </span>
        </button>
      ))}

      <PassageSheet
        chunkId={selectedChunkId}
        onOpenChange={(open) => {
          if (!open) {
            setSelectedChunkId(null)
          }
        }}
      />
    </div>
  )
}
