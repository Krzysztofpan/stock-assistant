import { dehydrate, HydrationBoundary, QueryClient } from "@tanstack/react-query"

import MessageListClient from "@/components/main/conversation/MessageListClient"
import { MESSAGES_PAGE_SIZE, messagesQueryKey } from "@/hooks/queries/messages-query"
import { setInitialInfiniteQueryData } from "@/lib/infinite-query"
import { serverApi } from "@/services/stockAssistantService/server"

type MessageListProps = {
  conversationId: string
}

const MessageList = async ({ conversationId }: MessageListProps) => {
  const queryClient = new QueryClient()
  const initialPage = await serverApi.getMessages(conversationId, {
    limit: 10,
  })

  setInitialInfiniteQueryData(queryClient, messagesQueryKey(conversationId, MESSAGES_PAGE_SIZE), initialPage)

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <MessageListClient key={conversationId} conversationId={conversationId} pageSize={MESSAGES_PAGE_SIZE} />
    </HydrationBoundary>
  )
}

export default MessageList
