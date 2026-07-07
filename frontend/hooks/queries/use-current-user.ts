"use client"

import { useQuery } from "@tanstack/react-query"

import { getCurrentUser } from "@/services/stockAssistantService/actions"

export function useCurrentUser() {
  return useQuery({
    queryKey: ["currentUser"],
    queryFn: getCurrentUser,
  })
}
