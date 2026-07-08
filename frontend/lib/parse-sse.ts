export type ParsedSSEEvent = {
  event: string
  data: string
}

export function parseSSEChunk(buffer: string): { events: ParsedSSEEvent[], rest: string } {
  const events: ParsedSSEEvent[] = []
  const parts = buffer.split("\n\n")
  const rest = parts.pop() ?? ""

  for (const part of parts) {
    if (!part.trim()) {
      continue
    }

    let event = "message"
    const dataLines: string[] = []

    for (const line of part.split("\n")) {
      if (line.startsWith("event:")) {
        event = line.slice(6).trim()
      }
      else if (line.startsWith("data:")) {
        dataLines.push(line.slice(5).trimStart())
      }
    }

    if (dataLines.length) {
      events.push({ event, data: dataLines.join("\n") })
    }
  }

  return { events, rest }
}
