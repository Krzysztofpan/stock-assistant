import { Check, Loader2 } from "lucide-react"

import { cn } from "@/lib/utils"

type TypingIndicatorProps = {
  steps?: string[]
}

const TYPING_DOT_DELAYS = [0, 160, 320] as const

function TypingDots() {
  return (
    <div className="flex h-9 items-center gap-1.5 px-5">
      {TYPING_DOT_DELAYS.map(delay => (
        <span
          key={delay}
          className="inline-block size-2.5 shrink-0 rounded-full bg-muted-foreground/50 animate-bounce"
          style={{
            animationDelay: `${delay}ms`,
            animationDuration: "0.9s",
          }}
        />
      ))}
    </div>
  )
}

function ProcessSteps({ steps }: { steps: string[] }) {
  return (
    <ol className="flex flex-col px-4 py-3">
      {steps.map((step, index) => {
        const isActive = index === steps.length - 1
        const isLast = index === steps.length - 1

        return (
          <li
            key={`${step}-${index}`}
            className="relative flex gap-3 pb-2.5 last:pb-0"
          >
            {!isLast && (
              <span
                className="absolute top-5 left-[7px] h-[calc(100%-6px)] w-px bg-mist-400/80"
                aria-hidden
              />
            )}
            <span className="relative z-10 mt-0.5 flex size-4 shrink-0 items-center justify-center rounded-full bg-mist-300">
              {isActive
                ? <Loader2 className="size-3.5 animate-spin text-foreground" aria-hidden />
                : <Check className="size-3.5 text-muted-foreground" aria-hidden />}
            </span>
            <span
              className={cn(
                "pt-0.5 text-sm leading-5",
                isActive ? "font-medium text-foreground" : "text-muted-foreground",
              )}
            >
              {step}
            </span>
          </li>
        )
      })}
    </ol>
  )
}

const TypingIndicator = ({ steps = [] }: TypingIndicatorProps) => {
  const hasSteps = steps.length > 0

  return (
    <div
      className="flex w-full px-3 pb-2 pt-0"
      aria-label={hasSteps ? steps.join(", ") : "AI is typing"}
      role="status"
    >
      <div className="max-w-sm rounded-3xl bg-mist-300/90 ring-1 ring-mist-400/50">
        {hasSteps ? <ProcessSteps steps={steps} /> : <TypingDots />}
      </div>
    </div>
  )
}

export default TypingIndicator
