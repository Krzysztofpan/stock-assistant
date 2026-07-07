import type {
  ConversationsParams,
  ConversationsResponse,
} from "@/services/stockAssistantService/types"

export const SIDEBAR_CONVERSATIONS_PAGE_SIZE = 8

export type ConversationsListFilter = "bookmarked" | "unbookmarked"

export type ConversationsCursor = Pick<
  ConversationsParams,
  "before_updated_at" | "before_id"
>

export function conversationsListFilterToParam(
  filter: ConversationsListFilter,
): boolean {
  return filter === "bookmarked"
}

export function getConversationsNextPageParam(
  lastPage: ConversationsResponse,
): ConversationsCursor | undefined {
  if (!lastPage.has_more) {
    return undefined
  }

  const lastConversation = lastPage.conversations.at(-1)

  if (!lastConversation) {
    return undefined
  }

  return {
    before_updated_at: lastConversation.updated_at,
    before_id: lastConversation.id,
  }
}
