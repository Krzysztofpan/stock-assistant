import * as React from "react"

import { NavUser } from "@/components/main/sidebar/nav-user"

import { Sidebar, SidebarContent, SidebarFooter, SidebarHeader, SidebarRail, SidebarTrigger } from "@/components/ui/sidebar"
import NewChatBtn from "./SidebarBtns/NewChatBtn"
import ConversationsSearch from "./ConversationsSearch"
import SidebarConversations from "./SidebarConversations"

export async function MainSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  return (
    <Sidebar className="flex-1" collapsible="icon" {...props}>
      <SidebarHeader className="flex flex-row justify-between items-center m-2 group-data-[collapsible=icon]:m-0">
        <h3 className="font-bold text-lg group-data-[collapsible=icon]:hidden whitespace-nowrap">Stock Assistant</h3>
        <SidebarTrigger className="scale-x-125 scale-y-110" />
      </SidebarHeader>
      <SidebarContent className="px-2 flex flex-col gap-8 group-data-[collapsible=icon]:px-0 bg-inherit">
        <div className="sticky top-0 flex flex-col gap-2 z-10 bg-inherit py-2">
          <NewChatBtn />
          <ConversationsSearch />
        </div>
        <SidebarConversations />
      </SidebarContent>
      <SidebarFooter>
        <NavUser />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  )
}
