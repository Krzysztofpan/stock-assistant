"use client"

import { Command, CommandDialog, CommandEmpty, CommandGroup, CommandItem, CommandList } from "@/components/ui/command"
import ConversationsSearchBtn from "./SidebarBtns/ConversationsSearchBtn"
import { useEffect, useMemo, useState } from "react"

import { debounce } from "lodash"
import { useConversationsSearch } from "@/hooks/queries/use-conversations-search"
import { Input } from "@/components/ui/input"
import { Search } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import { useRouter } from "next/navigation"

const ConversationsSearch = () => {
  const [open, setOpen] = useState(false)
  const [searchInput, setSearchInput] = useState("")
  const [debouncedQuery, setDebouncedQuery] = useState("")
  const router = useRouter()

  const debouncedSetQuery = useMemo(
    () =>
      debounce((value: string) => {
        setDebouncedQuery(value)
      }, 500),
    [],
  )

  const { data, isLoading, error } = useConversationsSearch(debouncedQuery)

  useEffect(() => {
    debouncedSetQuery(searchInput)

    return () => {
      debouncedSetQuery.cancel()
    }
  }, [searchInput, debouncedSetQuery])

  const onSelectConversation = (conversationId: string) => {
    setOpen(false)
    setSearchInput("")
    router.replace(`/conversations/${conversationId}`)
  }

  return (
    <>
      <ConversationsSearchBtn onClick={() => setOpen(true)} />
      <CommandDialog className="px-4 py-6 gap-2" open={open} onOpenChange={setOpen}>
        <div className="relative">
          <Input value={searchInput} onChange={e => setSearchInput(e.target.value)} className="pl-9" />
          <Search className="absolute left-5 top-1/2 -translate-1/2 scale-75" />
        </div>
        {isLoading && (
          <>
            <Skeleton className="w-full h-12.5" />
            <Skeleton className="w-full h-12.5" />
          </>
        )}
        {searchInput.length <= 2 && <p className="text-center py-4 font-semibold">Type some titile of conversation (at least 3 characters)</p>}
        {error && <p className="text-center py-4 font-semibold text-destructive">Something went wrong, please try again later</p>}
        {searchInput.length > 2 && data
          ? (
              <Command>
                <CommandList>
                  {data.conversations.length > 0
                    ? (
                        <CommandGroup heading="Matched conversations title">
                          {data?.conversations.map((conversation) => {
                            return (
                              <CommandItem className="cursor-pointer font-semibold" key={conversation.id} onSelect={() => onSelectConversation(conversation.id)}>
                                {conversation.title}
                              </CommandItem>
                            )
                          })}
                        </CommandGroup>
                      )
                    : (
                        <CommandEmpty>No conversation found.</CommandEmpty>
                      )}
                </CommandList>
              </Command>
            )
          : null}
      </CommandDialog>
    </>
  )
}

export default ConversationsSearch
