"use client"

import { SidebarMenu, SidebarMenuSkeleton } from "@/components/ui/sidebar"
import { cn } from "@/lib/utils"
import type { ConversationsListFilter } from "@/hooks/queries/conversations-query"
import { useSidebarConversations } from "@/hooks/queries/use-sidebar-conversations"
import { useInfiniteScrollSentinel } from "@/hooks/use-infinite-scroll-sentinel"
import ConversationItem from "./ConversationItem"

type ConversationListClientProps = {
  filter: ConversationsListFilter
}

const ConversationListClient = ({ filter }: ConversationListClientProps) => {
  const { conversations, fetchNextPage, hasNextPage, isFetchingNextPage } = useSidebarConversations(filter)

  const sentinelRef = useInfiniteScrollSentinel({
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    scrollRootSelector: "[data-sidebar=\"content\"]",
  })

  return (
    <SidebarMenu className={cn(filter === "bookmarked" && "max-h-50 min-h-0 overflow-y-auto")}>
      {conversations.length
        ? conversations.map(conversation => <ConversationItem conversation={conversation} key={conversation.id} />)
        : (
            <p className="text-muted-foreground text-sm mt-2">
              {filter == "unbookmarked" ? "Create a new" : "Pin existing"}
              {" "}
              conversation to see
            </p>
          )}
      {isFetchingNextPage && (
        <>
          <SidebarMenuSkeleton />
          <SidebarMenuSkeleton />
        </>
      )}
      {hasNextPage && <div ref={sentinelRef} aria-hidden className="h-px shrink-0" />}
    </SidebarMenu>
  )
}

export default ConversationListClient
