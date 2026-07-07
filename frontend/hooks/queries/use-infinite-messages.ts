"use client"

import { infiniteQueryOptions, useInfiniteQuery } from "@tanstack/react-query"

import {
  MESSAGES_PAGE_SIZE,
  getMessagesNextPageParam,
  messagesQueryKey,
  type MessagesCursor,
} from "@/hooks/queries/messages-query"
import { getMessages } from "@/services/stockAssistantService/actions"

export { MESSAGES_PAGE_SIZE } from "@/hooks/queries/messages-query"

function messagesInfiniteQueryOptions(
  conversationId: string,
  limit = MESSAGES_PAGE_SIZE,
) {
  return infiniteQueryOptions({
    queryKey: messagesQueryKey(conversationId, limit),
    queryFn: ({ pageParam }) =>
      getMessages(conversationId, {
        limit,
        ...(pageParam ?? {}),
      }),
    initialPageParam: undefined as MessagesCursor | undefined,
    getNextPageParam: getMessagesNextPageParam,
    enabled: Boolean(conversationId),
  })
}

export function useInfiniteMessages(
  conversationId: string,
  limit = MESSAGES_PAGE_SIZE,
) {
  return useInfiniteQuery(messagesInfiniteQueryOptions(conversationId, limit))
}
