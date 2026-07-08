import type { QueryClient } from "@tanstack/react-query"

import { conversationsListFilterToParam, getConversationsNextPageParam, type ConversationsCursor, type ConversationsListFilter } from "@/hooks/queries/conversations-query"
import type { ConversationItem, ConversationsResponse } from "@/services/stockAssistantService/types"

export type ConversationPool = Record<string, ConversationItem>

export type ConversationsListMeta = {
  nextCursor: ConversationsCursor | undefined
  hasMore: boolean
}

export function conversationEntitiesQueryKey() {
  return ["conversations", "entities"] as const
}

export function conversationListMetaQueryKey(filter: ConversationsListFilter) {
  return ["conversations", "list-meta", filter] as const
}

export function conversationsListMetaFromPage(page: ConversationsResponse): ConversationsListMeta {
  return {
    nextCursor: getConversationsNextPageParam(page),
    hasMore: page.has_more,
  }
}

export function buildConversationPool(conversations: ConversationItem[]): ConversationPool {
  const pool: ConversationPool = {}

  for (const conversation of conversations) {
    pool[conversation.id] = conversation
  }

  return pool
}

export function addConversationToPool(queryClient: QueryClient, conversation: ConversationItem) {
  queryClient.setQueryData<ConversationPool>(conversationEntitiesQueryKey(), (pool = {}) => {
    const updatedPool = { [conversation.id]: conversation, ...pool }

    return updatedPool
  })
}

export function mergeConversationsIntoPool(queryClient: QueryClient, conversations: ConversationItem[]) {
  queryClient.setQueryData<ConversationPool>(conversationEntitiesQueryKey(), (pool = {}) => {
    const updatedPool = { ...pool }

    for (const conversation of conversations) {
      updatedPool[conversation.id] = conversation
    }

    return updatedPool
  })
}

export function updateConversationInPool(queryClient: QueryClient, conversationId: string, patch: Partial<ConversationItem>) {
  queryClient.setQueryData<ConversationPool>(conversationEntitiesQueryKey(), (pool) => {
    const conversation = pool?.[conversationId]

    if (!conversation) {
      return pool
    }

    return {
      ...pool,
      [conversationId]: { ...conversation, ...patch },
    }
  })
}

export function deleteConversationFromPool(queryClient: QueryClient, conversationId: string) {
  queryClient.setQueryData<ConversationPool>(conversationEntitiesQueryKey(), (pool) => {
    if (!pool?.[conversationId]) {
      return pool
    }

    const { [conversationId]: _removed, ...updatedPool } = pool

    return updatedPool
  })
}

function compareConversationsByRecency(first: ConversationItem, second: ConversationItem) {
  const updatedAtDifference = new Date(second.updated_at).getTime() - new Date(first.updated_at).getTime()

  if (updatedAtDifference !== 0) {
    return updatedAtDifference
  }

  return second.id.localeCompare(first.id)
}

export function selectConversations(pool: ConversationPool | undefined, filter: ConversationsListFilter): ConversationItem[] {
  if (!pool) {
    return []
  }

  const isBookmarked = conversationsListFilterToParam(filter)

  return Object.values(pool)
    .filter(conversation => conversation.is_bookmarked === isBookmarked)
    .sort(compareConversationsByRecency)
}
