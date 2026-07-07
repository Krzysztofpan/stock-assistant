import { dehydrate, HydrationBoundary } from "@tanstack/react-query"
import { Pin } from "lucide-react"

import ConversationEventsBridge from "@/components/main/sidebar/ConversationEventsBridge"
import ConversationListClient from "@/components/main/sidebar/ConversationListClient"
import { prefetchSidebarConversations } from "@/hooks/queries/sidebar-conversations-prefetch"

const SidebarConversations = async () => {
  const queryClient = await prefetchSidebarConversations()

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <ConversationEventsBridge />
      <div className="flex flex-col gap-0">
        <section className="mx-3.5 flex min-w-0 translate-x-px flex-col gap-1 border-l border-sidebar-border px-2.5 py-0.5 group-data-[collapsible=icon]:hidden mr-0 pr-0">
          <header className="flex justify-between">
            <h3 className="font-bold">Pined</h3>
            <Pin className="scale-75 rotate-45 text-muted-foreground" />
          </header>
          <ConversationListClient filter="bookmarked" />
        </section>
        <section className="mx-3.5 flex min-w-0 translate-x-px flex-col gap-1 border-l border-sidebar-border px-2.5 py-0.5 group-data-[collapsible=icon]:hidden mr-0 pr-0">
          <h3 className="font-bold">Recents</h3>
          <ConversationListClient filter="unbookmarked" />
        </section>
      </div>
    </HydrationBoundary>
  )
}

export default SidebarConversations
