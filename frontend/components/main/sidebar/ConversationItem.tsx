"use client"

import {
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar"
import ElementWithOptionalTooltip from "@/components/utlis/ElementWithOptionalTooltip"
import { useBookmarkUpdate } from "@/hooks/mutations/use-bookmark-update"
import { ConversationItem as ConversationItemType } from "@/services/stockAssistantService/types"
import { Pin, PinOff } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"

export type ConversationItemProps = {
  conversation: ConversationItemType
}

const ConversationItem = ({ conversation }: ConversationItemProps) => {
  const pathname = usePathname()
  const { state } = useSidebar()
  const { mutate } = useBookmarkUpdate()

  const handleToggleBookmark = (event: React.MouseEvent) => {
    event.preventDefault()
    event.stopPropagation()

    mutate({
      conversationId: conversation.id,
      isBookmarked: !conversation.is_bookmarked,
    })
  }

  return (
    <SidebarMenuItem className="shrink-0">
      <SidebarMenuButton
        asChild
        isActive={pathname === `/conversations/${conversation.id}`}
        tooltip={state === "collapsed" ? conversation.title : undefined}
      >
        <Link href={`/conversations/${conversation.id}`} className="min-w-0">
          <ElementWithOptionalTooltip text={conversation.title} />
        </Link>
      </SidebarMenuButton>
      <SidebarMenuAction
        showOnHover
        onClick={handleToggleBookmark}
        aria-label={conversation.is_bookmarked ? "Unpin conversation" : "Pin conversation"}
      >
        {conversation.is_bookmarked ? <PinOff /> : <Pin />}
      </SidebarMenuAction>
    </SidebarMenuItem>
  )
}

export default ConversationItem
