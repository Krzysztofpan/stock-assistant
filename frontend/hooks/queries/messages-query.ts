import type { InfiniteData, QueryClient } from "@tanstack/react-query"

import { flattenInfinitePages } from "@/lib/infinite-query"
import type { MessageItem, MessagesParams, MessagesResponse } from "@/services/stockAssistantService/types"

export const MESSAGES_PAGE_SIZE = 5

export type MessagesCursor = Pick<MessagesParams, "before_id">

export function messagesQueryKey(conversationId: string, limit = MESSAGES_PAGE_SIZE) {
  return ["messages", conversationId, { limit }] as const
}

export function getMessagesNextPageParam(lastPage: MessagesResponse): MessagesCursor | undefined {
  if (!lastPage.has_more) {
    return undefined
  }

  const oldestInPage = lastPage.messages[0]

  if (!oldestInPage) {
    return undefined
  }

  return {
    before_id: oldestInPage.id,
  }
}

export function flattenMessagePages(pages: MessagesResponse[] | undefined) {
  return flattenInfinitePages(pages, page => page.messages, { prependPages: true })
}

export function createOptimisticUserMessage(text: string): MessageItem {
  return {
    id: -Date.now(),
    role: "user",
    text,
    created_at: new Date().toISOString(),
  }
}

function updateMessagesCache(queryClient: QueryClient, conversationId: string, limit: number, updater: (messages: MessageItem[]) => MessageItem[]) {
  const queryKey = messagesQueryKey(conversationId, limit)

  queryClient.setQueryData<InfiniteData<MessagesResponse>>(queryKey, (old) => {
    if (!old?.pages.length) {
      const messages = updater([])

      return {
        pages: [{ messages, has_more: false }],
        pageParams: [undefined],
      }
    }

    const pages = [...old.pages]
    const firstPage = pages[0]

    pages[0] = {
      ...firstPage,
      messages: updater(firstPage.messages),
    }

    return { ...old, pages }
  })
}

export function appendMessageToCache(queryClient: QueryClient, conversationId: string, message: MessageItem, limit = MESSAGES_PAGE_SIZE) {
  updateMessagesCache(queryClient, conversationId, limit, messages => [...messages, message])
}

export function removeMessageFromCache(queryClient: QueryClient, conversationId: string, messageId: number, limit = MESSAGES_PAGE_SIZE) {
  updateMessagesCache(queryClient, conversationId, limit, messages => messages.filter(message => message.id !== messageId))
}

export function createStreamingAiMessage(id: number): MessageItem {
  return {
    id,
    role: "ai",
    text: "",
    created_at: new Date().toISOString(),
  }
}

export function getStreamingMessageIdFromCache(queryClient: QueryClient, conversationId: string, limit = MESSAGES_PAGE_SIZE): number | undefined {
  const cached = queryClient.getQueryData<InfiniteData<MessagesResponse>>(messagesQueryKey(conversationId, limit))
  const messages = cached?.pages[0]?.messages ?? []

  for (let index = messages.length - 1; index >= 0; index -= 1) {
    const message = messages[index]

    if (message.role === "ai" && message.id < 0) {
      return message.id
    }
  }

  return undefined
}

export function appendTokenToMessageInCache(queryClient: QueryClient, conversationId: string, messageId: number, delta: string, limit = MESSAGES_PAGE_SIZE) {
  updateMessagesCache(queryClient, conversationId, limit, messages => messages.map(message => (message.id === messageId ? { ...message, text: message.text + delta } : message)))
}

export function replaceMessageInCache(queryClient: QueryClient, conversationId: string, messageId: number, newMessage: MessageItem, limit = MESSAGES_PAGE_SIZE) {
  updateMessagesCache(queryClient, conversationId, limit, messages => messages.map(message => (message.id === messageId ? newMessage : message)))
}
