import { useEffect, useState } from 'react'

import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { api, type Passage } from '@/lib/api'
import { ApiError } from '@/lib/http'

type PassageSheetProps = {
  chunkId: string | null
  onOpenChange: (open: boolean) => void
}

function filingLabel(passage: Passage): string {
  const filing = [passage.form, passage.fiscalYear ? `FY${passage.fiscalYear}` : '']
    .filter(Boolean)
    .join(' ')
  return [passage.company, filing || null, passage.section].filter(Boolean).join(' · ')
}

export function PassageSheet({ chunkId, onOpenChange }: PassageSheetProps) {
  const open = chunkId !== null
  const [passage, setPassage] = useState<Passage | null>(null)
  const [neighbors, setNeighbors] = useState<Passage[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!chunkId) {
      setPassage(null)
      setNeighbors([])
      setError(null)
      setLoading(false)
      return
    }

    let cancelled = false

    async function load() {
      setLoading(true)
      setError(null)
      setPassage(null)
      setNeighbors([])
      try {
        const context = await api.getCitationContext(chunkId!)
        if (!cancelled) {
          setPassage(context.passage)
          setNeighbors(context.neighbors)
        }
      } catch (err: unknown) {
        if (!cancelled) {
          if (err instanceof ApiError) {
            if (err.status === 404) {
              setError('This source passage is no longer available.')
            } else if (err.status === 401 || err.status === 403) {
              setError('You do not have access to this source passage.')
            } else {
              setError(err.message)
            }
          } else {
            setError('Could not load source passage.')
          }
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [chunkId])

  const before =
    passage === null
      ? []
      : neighbors.filter((item) => item.chunkIndex < passage.chunkIndex)
  const after =
    passage === null
      ? []
      : neighbors.filter((item) => item.chunkIndex > passage.chunkIndex)

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-lg">
        <SheetHeader>
          <SheetTitle>Source passage</SheetTitle>
          <SheetDescription>
            {passage
              ? filingLabel(passage)
              : 'Inspect the cited filing excerpt and surrounding context.'}
          </SheetDescription>
        </SheetHeader>

        <div className="flex-1 space-y-6 overflow-y-auto px-4 pb-6">
          {loading ? (
            <p className="text-sm text-muted-foreground">Loading passage…</p>
          ) : null}

          {error ? (
            <p className="text-sm text-destructive" role="alert">
              {error}
            </p>
          ) : null}

          {passage ? (
            <>
              <div className="space-y-1 text-xs text-muted-foreground">
                <p>
                  {[passage.ticker, passage.filingDate ? `filed ${passage.filingDate}` : null]
                    .filter(Boolean)
                    .join(' · ')}
                </p>
                {passage.sourceUrl ? (
                  <a
                    href={passage.sourceUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="underline hover:text-foreground"
                  >
                    View original filing
                  </a>
                ) : null}
              </div>

              {before.length > 0 ? (
                <section className="space-y-2">
                  <h3 className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Earlier context
                  </h3>
                  {before.map((item) => (
                    <p
                      key={item.chunkId}
                      className="whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground"
                    >
                      {item.text}
                    </p>
                  ))}
                </section>
              ) : null}

              <section className="space-y-2">
                <h3 className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                  Cited passage
                </h3>
                <p className="whitespace-pre-wrap border-l-2 border-primary pl-3 text-sm leading-relaxed">
                  {passage.text}
                </p>
              </section>

              {after.length > 0 ? (
                <section className="space-y-2">
                  <h3 className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                    Later context
                  </h3>
                  {after.map((item) => (
                    <p
                      key={item.chunkId}
                      className="whitespace-pre-wrap text-sm leading-relaxed text-muted-foreground"
                    >
                      {item.text}
                    </p>
                  ))}
                </section>
              ) : null}
            </>
          ) : null}
        </div>
      </SheetContent>
    </Sheet>
  )
}
