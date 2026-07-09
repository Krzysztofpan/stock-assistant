"use client"

import { SidebarMenuAction, SidebarMenuButton, SidebarMenuItem, useSidebar } from "@/components/ui/sidebar"
import ElementWithOptionalTooltip from "@/components/utlis/ElementWithOptionalTooltip"
import { useConversationUpdate } from "@/hooks/mutations/use-conversation-update"
import { cn } from "@/lib/utils"
import { ConversationItem as ConversationItemType } from "@/services/stockAssistantService/types"
import { Pin, PinOff } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { useState } from "react"
import ConversationItemActions from "./ConversationItemActions"

import ConversationTitleEditMode from "./ConversationTitleEditMode"

export type ConversationItemProps = {
  conversation: ConversationItemType
}

const actionsPositionClassName = cn("absolute top-1.5 right-1 flex items-center gap-0.5 text-sidebar-accent-foreground group-data-[collapsible=icon]:hidden", "peer-data-[size=default]/menu-button:top-2 peer-data-[size=lg]/menu-button:top-2.5 peer-data-[size=sm]/menu-button:top-1")

const actionsVisibilityClassName = cn("opacity-0 pointer-events-none transition-opacity duration-150", "max-md:opacity-100 max-md:pointer-events-auto", "md:group-hover/menu-item:opacity-100 md:group-hover/menu-item:pointer-events-auto", "md:group-focus-within/menu-item:opacity-100 md:group-focus-within/menu-item:pointer-events-auto")

const ConversationItem = ({ conversation }: ConversationItemProps) => {
  const pathname = usePathname()
  const { state } = useSidebar()
  const { mutate } = useConversationUpdate()
  const [optionsOpen, setOptionsOpen] = useState(false)
  const [editMode, setEditMode] = useState(false)
  const handleToggleBookmark = (event: React.MouseEvent) => {
    event.preventDefault()
    event.stopPropagation()

    mutate({
      conversationId: conversation.id,
      patch: { is_bookmarked: !conversation.is_bookmarked },
    })
  }

  const handleChangeTitle = (title: string) => {
    const trimmedTitle = title.trim()

    if (trimmedTitle.length > 0) {
      mutate({ conversationId: conversation.id, patch: { title: trimmedTitle } })
    }
  }

  if (editMode) return (
    <ConversationTitleEditMode
      handleChangeTitle={handleChangeTitle}
      setEditMode={setEditMode}
      conversationTitle={conversation.title}
    />
  )

  return (
    <SidebarMenuItem className="shrink-0">
      <SidebarMenuButton asChild isActive={pathname === `/conversations/${conversation.id}`} tooltip={state === "collapsed" ? conversation.title : undefined} className={cn("pr-3! transition-[padding] max-md:pr-14!", "md:group-hover/menu-item:pr-14! md:group-focus-within/menu-item:pr-14!", optionsOpen && "md:pr-14! md:bg-sidebar-accent md:text-sidebar-accent-foreground")}>
        <Link href={`/conversations/${conversation.id}`} className="min-w-0">
          <ElementWithOptionalTooltip text={conversation.title} />
        </Link>
      </SidebarMenuButton>

      <div className={cn(actionsPositionClassName, actionsVisibilityClassName, optionsOpen && "md:opacity-100! md:pointer-events-auto!")}>
        <SidebarMenuAction className="static top-auto right-auto" onClick={handleToggleBookmark} aria-label={conversation.is_bookmarked ? "Unpin conversation" : "Pin conversation"}>
          {conversation.is_bookmarked ? <PinOff /> : <Pin />}
        </SidebarMenuAction>

        <ConversationItemActions
          conversationId={conversation.id}
          is_bookmarked={conversation.is_bookmarked}
          handleToggleBookmark={handleToggleBookmark}
          optionsOpen={optionsOpen}
          setOptionsOpen={setOptionsOpen}
          setEditMode={setEditMode}
        />
      </div>
    </SidebarMenuItem>
  )
}

export default ConversationItem
