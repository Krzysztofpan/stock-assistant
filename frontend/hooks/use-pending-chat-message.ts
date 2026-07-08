"use client"

import { useEffect } from "react"

import { useSendChatMessageStream } from "@/hooks/mutations/use-chat"
import { consumePendingChatMessage } from "@/lib/pending-chat-message"

export function usePendingChatMessage(conversationId: string) {
  const { mutate: sendMessage } = useSendChatMessageStream()

  useEffect(() => {
    const message = consumePendingChatMessage(conversationId)

    if (message) {
      sendMessage({ message, conversationId, newConversation: true })
    }
  }, [conversationId, sendMessage])
}
