"use client"

import { useQuery } from "@tanstack/react-query"

import { getConversations } from "@/services/stockAssistantService/actions"
import type { ConversationsParams } from "@/services/stockAssistantService/types"

export function useConversations(params?: ConversationsParams) {
  return useQuery({
    queryKey: ["conversations", params],
    queryFn: () => getConversations(params),
  })
}
