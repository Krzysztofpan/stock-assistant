"use client"

import { useConversationEvents } from "@/hooks/use-conversation-events"

const ConversationEventsBridge = () => {
  useConversationEvents()

  return null
}

export default ConversationEventsBridge
