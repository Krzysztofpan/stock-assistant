import { useEffect } from "react"
import { useQueryClient } from "@tanstack/react-query"

import { updateConversationInPool } from "@/hooks/queries/conversation-store"

type ConversationTitleUpdatedEvent = {
  conversation_id: string
  title: string
}

export function useConversationEvents() {
  const queryClient = useQueryClient()

  useEffect(() => {
    const source = new EventSource("/api/conversations/events")

    source.addEventListener("conversation.updated", () => {
      queryClient.invalidateQueries({ queryKey: ["conversations", "list-meta"] })
    })
    source.addEventListener("conversation.title_updated", (e) => {
      const event: ConversationTitleUpdatedEvent = JSON.parse(e.data)

      updateConversationInPool(queryClient, event.conversation_id, {
        title: event.title,
      })
    })

    source.onerror = () => {
      // maybe i will handle it later :)
    }

    return () => {
      source.close()
    }
  }, [queryClient])
}
