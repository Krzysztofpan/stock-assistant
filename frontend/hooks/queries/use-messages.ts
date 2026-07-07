"use client"

import { useQuery, useQueryClient } from "@tanstack/react-query"

import { getMessages } from "@/services/stockAssistantService/actions"
import type { MessageItem, MessagesParams } from "@/services/stockAssistantService/types"

export function useMessages(
  conversationId: string,
  params?: MessagesParams,
) {
  console.log(conversationId, params)

  return useQuery({
    queryKey: ["messages", conversationId, params],
    queryFn: () => getMessages(conversationId, params),
    enabled: Boolean(conversationId),
  })
}

export function useMessagesClient(
  conversationId: string,
  params?: MessagesParams,
) {
  const client = useQueryClient()

  const addMessageToWindow = (message: MessageItem) => {
    client.setQueryData(["messages", conversationId, params], (currMessages: { pages: { messages: MessageItem[], has_more: boolean }[], pageParams?: MessagesParams }) => {
      return { ...currMessages, pages: [{ messages: [message], has_more: true }, ...currMessages.pages] }
    })
  }

  return {
    addMessageToWindow,
  }
}
