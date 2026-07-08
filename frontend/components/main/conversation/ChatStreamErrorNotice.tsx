import type { ErrorDetail } from "@/services/stockAssistantService/types"

type ChatStreamErrorNoticeProps = {
  error: ErrorDetail
  variant?: "fatal" | "warning"
}

const ChatStreamErrorNotice = ({ error, variant = "fatal" }: ChatStreamErrorNoticeProps) => {
  const isWarning = variant === "warning"

  return (
    <div
      className={
        isWarning
          ? "mx-3 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-900 dark:text-amber-100"
          : "mx-3 rounded-xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive"
      }
      role="alert"
    >
      {isWarning
        ? "The response was generated, but an error occurred during processing."
        : "Something went wrong while processing your message."}
      <p className="mt-1 text-xs opacity-80">{error.message}</p>
    </div>
  )
}

export default ChatStreamErrorNotice
