"use client"

import { useQuery } from "@tanstack/react-query"

import { getConversations } from "@/services/stockAssistantService/actions"
import type { ConversationsParams } from "@/services/stockAssistantService/types"

export function useConversationsSearch(searchQuery: string) {
  return useQuery({
    queryKey: ["conversations", searchQuery],
    queryFn: () => getConversations({ query: searchQuery }),
    enabled: searchQuery.length > 2,
  })
}
