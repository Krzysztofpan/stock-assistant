"use server"

import { chatRequestSchemaType } from "@/services/stockAssistantService/schemas"
import { serverApi } from "@/services/stockAssistantService/server"
import { ChatResponse } from "@/services/stockAssistantService/types"

export const requestChat = async (data: chatRequestSchemaType): Promise<ChatResponse> => {
  console.log(data)

  const res = await serverApi.chat({ message: data.message, conversation_id: data.conversationId, new_conversation: data.newConversation ?? undefined })

  if (res.error) {
    console.log(res.error)
  }

  return { message: res.message, error: res.error }
}
