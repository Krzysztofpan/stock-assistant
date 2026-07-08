"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query"

import {
  conversationEntitiesQueryKey,
  deleteConversationFromPool,

  type ConversationPool,
} from "@/hooks/queries/conversation-store"
import { deleteConversation } from "@/services/stockAssistantService/actions"

type ConversationDeleteContext = {
  previousPool: ConversationPool | undefined
}

export const useConversationDelete = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ conversationId }: { conversationId: string }) => {
      const conversation_id = await deleteConversation(conversationId)

      return conversation_id
    },
    onMutate: ({ conversationId }) => {
      const previousPool = queryClient.getQueryData<ConversationPool>(
        conversationEntitiesQueryKey(),
      )

      deleteConversationFromPool(queryClient, conversationId)

      return { previousPool }
    },
    onError: (_error, _input, context: ConversationDeleteContext | undefined) => {
      queryClient.setQueryData(conversationEntitiesQueryKey(), context?.previousPool)
    },
    onSuccess: ({ conversation_id }) => {
      deleteConversationFromPool(queryClient, conversation_id)
    },
  })
}
