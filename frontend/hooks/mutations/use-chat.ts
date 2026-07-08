"use client"

import { useMutation, useQueryClient } from "@tanstack/react-query"

import { useOptionalChatStreamContext } from "@/contexts/chat-stream-context"
import {
  appendMessageToCache,
  appendTokenToMessageInCache,
  createOptimisticUserMessage,
  createStreamingAiMessage,
  getStreamingMessageIdFromCache,
  MESSAGES_PAGE_SIZE,
  messagesQueryKey,
  removeMessageFromCache,
  replaceMessageInCache,
} from "@/hooks/queries/messages-query"
import { parseSSEChunk } from "@/lib/parse-sse"
import type { ErrorDetail, MessageItem } from "@/services/stockAssistantService/types"

export type { ChatStreamErrorState } from "@/contexts/chat-stream-context"

export type SendChatMessageInput = {
  message: string
  conversationId: string
  newConversation?: boolean
}

type ChatStreamDoneData = {
  message: MessageItem
  error: ErrorDetail | null
}

type ChatStreamMutationContext = {
  optimisticId: number
  streamingId: number
  activeConversationId: string
}

export class StreamChatError extends Error {
  readonly statusCode: number

  constructor(message: string, statusCode: number) {
    super(message)
    this.name = "StreamChatError"
    this.statusCode = statusCode
  }
}

export function useSendChatMessageStream(pageSize = MESSAGES_PAGE_SIZE) {
  const queryClient = useQueryClient()
  const chatStream = useOptionalChatStreamContext()

  return useMutation({
    mutationFn: async ({
      message,
      conversationId: activeConversationId,
      newConversation,
    }: SendChatMessageInput): Promise<MessageItem> => {
      const response = await fetch("/api/chat/stream", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          message,
          conversation_id: activeConversationId,
          new_conversation: newConversation ?? false,
        }),
      })

      if (!response.ok) {
        throw new Error(await response.text())
      }

      if (!response.body) {
        throw new Error("Streaming response body is empty")
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ""
      let finalMessage: MessageItem | null = null

      while (true) {
        const { done, value } = await reader.read()

        if (done) {
          break
        }

        buffer += decoder.decode(value, { stream: true })

        const { events, rest } = parseSSEChunk(buffer)

        buffer = rest

        for (const { event, data } of events) {
          if (event === "status") {
            const parsed = JSON.parse(data) as { label: string }

            chatStream?.appendProcessStep(parsed.label)
            continue
          }

          if (event === "token") {
            const parsed = JSON.parse(data) as { delta: string }
            const streamingId = getStreamingMessageIdFromCache(
              queryClient,
              activeConversationId,
              pageSize,
            )

            if (!streamingId || !parsed.delta) {
              continue
            }

            chatStream?.setTyping(false)
            chatStream?.clearProcessSteps()
            appendTokenToMessageInCache(
              queryClient,
              activeConversationId,
              streamingId,
              parsed.delta,
              pageSize,
            )
          }

          if (event === "done") {
            const parsed = JSON.parse(data) as ChatStreamDoneData
            const streamingId = getStreamingMessageIdFromCache(
              queryClient,
              activeConversationId,
              pageSize,
            )

            finalMessage = parsed.message
            chatStream?.setTyping(false)
            chatStream?.clearProcessSteps()
            chatStream?.setStreamError(
              parsed.error
                ? { ...parsed.error, variant: "warning" }
                : null,
            )

            if (streamingId) {
              replaceMessageInCache(
                queryClient,
                activeConversationId,
                streamingId,
                parsed.message,
                pageSize,
              )
            }
            else {
              appendMessageToCache(
                queryClient,
                activeConversationId,
                parsed.message,
                pageSize,
              )
            }
          }

          if (event === "error") {
            const parsed = JSON.parse(data) as ErrorDetail

            throw new StreamChatError(parsed.message, parsed.status_code)
          }
        }
      }

      if (!finalMessage) {
        throw new Error("Stream ended without a final message")
      }

      return finalMessage
    },
    onMutate: async ({ message, conversationId: activeConversationId }) => {
      chatStream?.setTyping(true)
      chatStream?.clearProcessSteps()
      chatStream?.setStreamError(null)

      await queryClient.cancelQueries({
        queryKey: messagesQueryKey(activeConversationId, pageSize),
      })

      const optimisticMessage = createOptimisticUserMessage(message)
      const streamingMessage = createStreamingAiMessage(-Date.now() - 1)

      appendMessageToCache(queryClient, activeConversationId, optimisticMessage, pageSize)
      appendMessageToCache(queryClient, activeConversationId, streamingMessage, pageSize)

      return {
        optimisticId: optimisticMessage.id,
        streamingId: streamingMessage.id,
        activeConversationId,
      } satisfies ChatStreamMutationContext
    },
    onError: (error, _input, context) => {
      if (!context) {
        return
      }

      removeMessageFromCache(
        queryClient,
        context.activeConversationId,
        context.streamingId,
        pageSize,
      )

      if (error instanceof StreamChatError && error.statusCode === 400) {
        removeMessageFromCache(
          queryClient,
          context.activeConversationId,
          context.optimisticId,
          pageSize,
        )
      }

      if (error instanceof StreamChatError) {
        chatStream?.setStreamError({
          message: error.message,
          status_code: error.statusCode,
          variant: "fatal",
        })
      }
    },
    onSettled: () => {
      chatStream?.setTyping(false)
      chatStream?.clearProcessSteps()
    },
  })
}
