const TYPING_DOT_DELAYS = [0, 160, 320] as const

const TypingIndicator = () => {
  return (
    <div className="flex w-full px-3 py-3" aria-label="AI is typing" role="status">
      <div className="flex h-9 items-center gap-1.5 rounded-3xl bg-white px-5">
        {TYPING_DOT_DELAYS.map(delay => (
          <span
            key={delay}
            className="inline-block size-2.5 shrink-0 rounded-full bg-gray-400 animate-bounce"
            style={{
              animationDelay: `${delay}ms`,
              animationDuration: "0.9s",
            }}
          />
        ))}
      </div>
    </div>
  )
}

export default TypingIndicator
