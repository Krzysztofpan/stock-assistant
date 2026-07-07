"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query"

import {
  conversationEntitiesQueryKey,
  updateConversationInPool,
  type ConversationPool,
} from "@/hooks/queries/conversation-store"
import { updateConversationBookmark } from "@/services/stockAssistantService/actions"

type BookmarkUpdateInput = {
  conversationId: string
  isBookmarked: boolean
}

type BookmarkUpdateContext = {
  previousPool: ConversationPool | undefined
}

export const useBookmarkUpdate = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ conversationId, isBookmarked }: BookmarkUpdateInput) => {
      const response = await updateConversationBookmark(conversationId, isBookmarked)

      return response.is_bookmarked
    },
    onMutate: ({ conversationId, isBookmarked }) => {
      const previousPool = queryClient.getQueryData<ConversationPool>(
        conversationEntitiesQueryKey(),
      )

      updateConversationInPool(queryClient, conversationId, {
        is_bookmarked: isBookmarked,
      })

      return { previousPool }
    },
    onError: (_error, _input, context: BookmarkUpdateContext | undefined) => {
      queryClient.setQueryData(conversationEntitiesQueryKey(), context?.previousPool)
    },
    onSuccess: (isBookmarked, { conversationId }) => {
      updateConversationInPool(queryClient, conversationId, {
        is_bookmarked: isBookmarked,
      })
    },
  })
}
