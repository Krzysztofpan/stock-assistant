"use server"

import type {
  ConversationResponse,
  ConversationUpdateRequest,
  ConversationsParams,
  ConversationsResponse,
  CurrentUserResponse,
  MessagesParams,
  MessagesResponse,
} from "./types"
import { serverApi } from "./server"

export async function getCurrentUser(): Promise<CurrentUserResponse> {
  return serverApi.getCurrentUser()
}

export async function getConversations(
  params?: ConversationsParams,
): Promise<ConversationsResponse> {
  return serverApi.getConversations(params)
}

export async function updateConversation(
  conversationId: string,
  data: ConversationUpdateRequest,
): Promise<ConversationResponse> {
  return serverApi.updateConversation(conversationId, data)
}

export async function deleteConversation(
  conversationId: string,
): Promise<{ conversation_id: string }> {
  return serverApi.deleteConversation(conversationId)
}

export async function getMessages(
  conversationId: string,
  params?: MessagesParams,
): Promise<MessagesResponse> {
  return serverApi.getMessages(conversationId, params)
}
