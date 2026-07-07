import { QueryClient } from "@tanstack/react-query"

import {
  buildConversationPool,
  conversationEntitiesQueryKey,
  conversationListMetaQueryKey,
  conversationsListMetaFromPage,
} from "@/hooks/queries/conversation-store"
import { SIDEBAR_CONVERSATIONS_PAGE_SIZE } from "@/hooks/queries/conversations-query"
import { serverApi } from "@/services/stockAssistantService/server"

export async function prefetchSidebarConversations() {
  const queryClient = new QueryClient()
  const [bookmarkedPage, unbookmarkedPage] = await Promise.all([
    serverApi.getConversations({ limit: SIDEBAR_CONVERSATIONS_PAGE_SIZE, is_bookmarked: true }),
    serverApi.getConversations({ limit: SIDEBAR_CONVERSATIONS_PAGE_SIZE, is_bookmarked: false }),
  ])

  queryClient.setQueryData(
    conversationEntitiesQueryKey(),
    buildConversationPool([
      ...bookmarkedPage.conversations,
      ...unbookmarkedPage.conversations,
    ]),
  )
  queryClient.setQueryData(
    conversationListMetaQueryKey("bookmarked"),
    conversationsListMetaFromPage(bookmarkedPage),
  )
  queryClient.setQueryData(
    conversationListMetaQueryKey("unbookmarked"),
    conversationsListMetaFromPage(unbookmarkedPage),
  )

  return queryClient
}
