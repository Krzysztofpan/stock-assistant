"use client"
import { useSidebar } from "@/components/ui/sidebar"
import {
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu"

import {
  Avatar,
  AvatarFallback,

} from "@/components/ui/avatar"
import { LogOutIcon, UserIcon } from "lucide-react"
import { UserPublic } from "@/services/stockAssistantService/types"
import { signOut } from "@/services/stockAssistantService/auth-actions"

type UserActionsProps = {
  user: UserPublic
}

const UserActions = ({ user }: UserActionsProps) => {
  const { isMobile } = useSidebar()

  return (
    <DropdownMenuContent
      className="w-fit"
      side={isMobile ? "bottom" : "right"}
      align="end"
      sideOffset={4}
    >
      <DropdownMenuLabel className="p-0 font-normal">
        <div className="flex items-center gap-2 px-1 py-1.5 text-left text-sm">
          <Avatar className="h-8 w-8 rounded-lg">
            <AvatarFallback className="rounded-lg">
              <UserIcon />
            </AvatarFallback>
          </Avatar>
          <div className="grid flex-1 text-left text-sm leading-tight">
            <span className="truncate font-medium">{user.name}</span>
            <span className="truncate text-xs">{user.email}</span>
          </div>
        </div>
      </DropdownMenuLabel>
      <DropdownMenuSeparator />
      <DropdownMenuItem onClick={signOut}>
        <LogOutIcon />
        Log out
      </DropdownMenuItem>
    </DropdownMenuContent>
  )
}

export default UserActions
