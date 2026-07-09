"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query"

import {
  conversationEntitiesQueryKey,
  updateConversationInPool,
  type ConversationPool,
} from "@/hooks/queries/conversation-store"
import { updateConversation } from "@/services/stockAssistantService/actions"
import type { ConversationUpdateRequest } from "@/services/stockAssistantService/types"

type ConversationUpdateInput = {
  conversationId: string
  patch: ConversationUpdateRequest
}

type ConversationUpdateContext = {
  previousPool: ConversationPool | undefined
}

export const useConversationUpdate = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ conversationId, patch }: ConversationUpdateInput) => {
      const response = await updateConversation(conversationId, patch)

      return response.conversation
    },
    onMutate: ({ conversationId, patch }) => {
      const previousPool = queryClient.getQueryData<ConversationPool>(
        conversationEntitiesQueryKey(),
      )

      updateConversationInPool(queryClient, conversationId, patch)

      return { previousPool }
    },
    onError: (_error, _input, context: ConversationUpdateContext | undefined) => {
      queryClient.setQueryData(conversationEntitiesQueryKey(), context?.previousPool)
    },
    onSuccess: (conversation, { conversationId, patch }) => {
      const reconciledPatch: ConversationUpdateRequest = {}

      if (patch.is_bookmarked !== undefined) {
        reconciledPatch.is_bookmarked = conversation.is_bookmarked ?? patch.is_bookmarked
      }

      if (patch.title !== undefined) {
        reconciledPatch.title = conversation.title ?? patch.title
      }

      updateConversationInPool(queryClient, conversationId, reconciledPatch)
    },
  })
}
