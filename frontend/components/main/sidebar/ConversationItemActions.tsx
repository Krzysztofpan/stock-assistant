"use client"
import { Button } from "@/components/ui/button"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { SidebarMenuAction } from "@/components/ui/sidebar"
import { useConversationDelete } from "@/hooks/mutations/use-delete-conversation"
import { Ellipsis, Pencil, Pin, PinOff, Trash2 } from "lucide-react"
import { Dispatch, SetStateAction } from "react"

type ConversationItemActionsProps = {
  conversationId: string
  is_bookmarked: boolean
  optionsOpen: boolean
  handleToggleBookmark: () => void
  setOptionsOpen: Dispatch<SetStateAction<boolean>>
  setEditMode: Dispatch<SetStateAction<boolean>>
}

const ConversationItemActions = ({ conversationId, is_bookmarked, handleToggleBookmark, optionsOpen, setOptionsOpen, setEditMode }: ConversationItemActionsProps) => {
  const { mutate } = useConversationDelete()

  const handleDelete = () => {
    mutate({ conversationId })
  }

  const handleChangeTitle = () => {
    setEditMode(true)
  }

  return (
    <DropdownMenu open={optionsOpen} onOpenChange={setOptionsOpen} modal={false}>
      <DropdownMenuTrigger asChild>
        <SidebarMenuAction className="static top-auto right-auto" aria-label="Conversation options" onClick={event => event.stopPropagation()}>
          <Ellipsis />
        </SidebarMenuAction>
      </DropdownMenuTrigger>
      <DropdownMenuContent className="p-1 flex flex-col gap-1" align="start" side="bottom" onClick={event => event.stopPropagation()}>
        <DropdownMenuItem className="m-0 p-0">
          <Button variant="ghost" onClick={handleChangeTitle} className="w-full justify-start cursor-pointer">
            <Pencil />
            Edit Title
          </Button>
        </DropdownMenuItem>
        <DropdownMenuItem className="m-0 p-0">
          <Button onClick={handleToggleBookmark} variant="ghost" className="w-full justify-start cursor-pointer">
            {is_bookmarked ? <PinOff /> : <Pin />}
            {is_bookmarked ? "unpin" : "pin"}
          </Button>
        </DropdownMenuItem>
        <DropdownMenuItem className="m-0 p-0">
          <Button onClick={handleDelete} variant="destructive" className="w-full justify-start cursor-pointer">
            <Trash2 />
            Delete
          </Button>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

export default ConversationItemActions
