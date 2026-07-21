const EXAMPLE_PROMPTS = [
  'Across Apple’s 2021–2025 10-Ks, how did the revenue mix between iPhone, Services, Mac, iPad, and Wearables change?',
  'For Amazon, compare AWS operating income and margin against North America and International from 2021–2025.',
  'Do the filings prove that generative AI improved margins for any of these companies?',
] as const

type ChatEmptyStateProps = {
  onPrompt: (prompt: string) => void
  disabled?: boolean
}

export function ChatEmptyState({ onPrompt, disabled = false }: ChatEmptyStateProps) {
  return (
    <div className="animate-message-in flex flex-col gap-6 py-8">
      <div className="space-y-2">
        <p className="font-heading text-2xl font-semibold tracking-tight text-foreground">
          Ask the filings
        </p>
        <p className="max-w-md text-sm leading-relaxed text-muted-foreground">
          Get grounded answers from the curated SEC corpus. Every claim cites a
          passage you can open and verify.
        </p>
      </div>

      <div className="space-y-2">
        <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
          Try a question
        </p>
        <ul className="space-y-2">
          {EXAMPLE_PROMPTS.map((prompt) => (
            <li key={prompt}>
              <button
                type="button"
                disabled={disabled}
                onClick={() => onPrompt(prompt)}
                className="w-full rounded-lg border border-border/80 bg-card/70 px-3 py-2.5 text-left text-sm leading-relaxed text-foreground/90 shadow-none transition-colors hover:border-primary/30 hover:bg-accent/60 disabled:opacity-50"
              >
                {prompt}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
