"use client"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { requestChat } from "@/actions/conversation.action"
import {
  appendMessageToCache,
  chatTypingQueryKey,
  createOptimisticUserMessage,
  MESSAGES_PAGE_SIZE,
  messagesQueryKey,
  removeMessageFromCache,
  setChatTyping,
} from "@/hooks/queries/messages-query"

export type SendChatMessageInput = {
  message: string
  conversationId: string
  newConversation?: boolean
}

export function useIsAiTyping(conversationId: string) {
  const { data } = useQuery({
    queryKey: chatTypingQueryKey(conversationId),
    queryFn: () => false,
    initialData: false,
    staleTime: Infinity,
    gcTime: Infinity,
  })

  return data
}

export function useSendChatMessage(pageSize = MESSAGES_PAGE_SIZE) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ message, conversationId: activeConversationId, newConversation }: SendChatMessageInput) => {
      const response = await requestChat({ message, conversationId: activeConversationId, newConversation })

      return response.message
    },
    onMutate: async ({ message, conversationId: activeConversationId }) => {
      setChatTyping(queryClient, activeConversationId, true)

      await queryClient.cancelQueries({
        queryKey: messagesQueryKey(activeConversationId, pageSize),
      })

      const optimisticMessage = createOptimisticUserMessage(message)

      appendMessageToCache(
        queryClient,
        activeConversationId,
        optimisticMessage,
        pageSize,
      )

      return { optimisticId: optimisticMessage.id, activeConversationId }
    },
    onSuccess: (aiMessage, _input, context) => {
      if (!context) {
        return
      }

      appendMessageToCache(
        queryClient,
        context.activeConversationId,
        aiMessage,
        pageSize,
      )
      /* queryClient.invalidateQueries({ queryKey: ["conversations", "list-meta"] }) */
    },
    onError: (_error, _input, context) => {
      if (!context) {
        return
      }

      removeMessageFromCache(
        queryClient,
        context.activeConversationId,
        context.optimisticId,
        pageSize,
      )
    },
    onSettled: (_data, _error, { conversationId }) => {
      setChatTyping(queryClient, conversationId, false)
    },
  })
}
