"use client"

import MessageView from "@/components/main/conversation/MessageView"
import TypingIndicator from "@/components/main/conversation/TypingIndicator"
import { Skeleton } from "@/components/ui/skeleton"
import { useIsAiTyping } from "@/hooks/mutations/use-chat"
import { useInfiniteScrollSentinel } from "@/hooks/use-infinite-scroll-sentinel"
import { flattenMessagePages, MESSAGES_PAGE_SIZE } from "@/hooks/queries/messages-query"
import { useInfiniteMessages } from "@/hooks/queries/use-infinite-messages"
import { usePendingChatMessage } from "@/hooks/use-pending-chat-message"
import { useMessageListScroll } from "@/hooks/use-message-list-scroll"

type MessageListClientProps = {
  conversationId: string
  pageSize?: number
}

const MessageListClient = ({ conversationId, pageSize = MESSAGES_PAGE_SIZE }: MessageListClientProps) => {
  usePendingChatMessage(conversationId)

  const { data, fetchNextPage, hasNextPage, isFetchingNextPage } = useInfiniteMessages(conversationId, pageSize)
  const messages = flattenMessagePages(data?.pages)
  const isAiTyping = useIsAiTyping(conversationId)

  const { containerRef, bottomRef, isAnchored, userScrolledUp } = useMessageListScroll({
    messages,
    isFetchingNextPage,
    isAiTyping,
  })

  const topSentinelRef = useInfiniteScrollSentinel({
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    enabled: isAnchored && userScrolledUp,
    rootMargin: "200px 0px 0px 0px",
  })

  return (
    <div ref={containerRef} className="my-10 flex  flex-col flex-1 justify-end">
      {/*       <div className="flex-1 shrink-0" aria-hidden /> */}
      <div className="flex flex-col gap-8">
        {hasNextPage && <div ref={topSentinelRef} aria-hidden className="h-px shrink-0" />}
        {isFetchingNextPage && (
          <div className="space-y-8">
            <Skeleton className="h-12 w-3/4 rounded-full" />
            <Skeleton className="ml-auto h-12 w-1/2 rounded-full" />
          </div>
        )}
        {messages.map(message => (
          <div key={message.id} data-message-id={message.id} className="scroll-mt-4">
            <MessageView messageObj={message} />
          </div>
        ))}
        {isAiTyping && <TypingIndicator />}
        <div
          ref={bottomRef}
          aria-hidden
          className="h-px shrink-0 scroll-mb-32"
        />
      </div>
    </div>
  )
}

export default MessageListClient
