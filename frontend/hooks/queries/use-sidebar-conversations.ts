"use client"

import { useCallback, useMemo, useRef, useState } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"

import {
  conversationEntitiesQueryKey,
  conversationListMetaQueryKey,
  conversationsListMetaFromPage,
  mergeConversationsIntoPool,
  selectConversations,
  type ConversationPool,
  type ConversationsListMeta,
} from "@/hooks/queries/conversation-store"
import {
  conversationsListFilterToParam,
  SIDEBAR_CONVERSATIONS_PAGE_SIZE,
  type ConversationsListFilter,
} from "@/hooks/queries/conversations-query"
import { getConversations } from "@/services/stockAssistantService/actions"

export function useSidebarConversations(
  filter: ConversationsListFilter,
  limit = SIDEBAR_CONVERSATIONS_PAGE_SIZE,
) {
  const queryClient = useQueryClient()
  const is_bookmarked = conversationsListFilterToParam(filter)

  const { data: pool } = useQuery<ConversationPool>({
    queryKey: conversationEntitiesQueryKey(),
    // The pool is a client-side store: a refetch must never wipe merged entities.
    queryFn: () => queryClient.getQueryData<ConversationPool>(conversationEntitiesQueryKey()) ?? {},
    staleTime: Infinity,
    gcTime: Infinity,
  })

  const { data: meta } = useQuery<ConversationsListMeta>({
    queryKey: conversationListMetaQueryKey(filter),
    queryFn: async () => {
      const page = await getConversations({ limit, is_bookmarked })

      mergeConversationsIntoPool(queryClient, page.conversations)

      return conversationsListMetaFromPage(page)
    },
    staleTime: Infinity,
  })

  const conversations = useMemo(
    () => selectConversations(pool, filter),
    [pool, filter],
  )

  const [isFetchingNextPage, setIsFetchingNextPage] = useState(false)
  const isFetchingNextPageRef = useRef(false)

  const fetchNextPage = useCallback(async () => {
    const currentMeta = queryClient.getQueryData<ConversationsListMeta>(
      conversationListMetaQueryKey(filter),
    )

    if (!currentMeta?.hasMore || !currentMeta.nextCursor || isFetchingNextPageRef.current) {
      return
    }

    isFetchingNextPageRef.current = true
    setIsFetchingNextPage(true)

    try {
      const page = await getConversations({
        limit,
        is_bookmarked,
        ...currentMeta.nextCursor,
      })

      mergeConversationsIntoPool(queryClient, page.conversations)
      queryClient.setQueryData(
        conversationListMetaQueryKey(filter),
        conversationsListMetaFromPage(page),
      )
    }
    finally {
      isFetchingNextPageRef.current = false
      setIsFetchingNextPage(false)
    }
  }, [queryClient, filter, limit, is_bookmarked])

  return {
    conversations,
    fetchNextPage,
    hasNextPage: meta?.hasMore ?? false,
    isFetchingNextPage,
  }
}
