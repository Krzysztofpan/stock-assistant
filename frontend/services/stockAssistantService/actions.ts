"use server"

import type {
  ChatRequest,
  ChatResponse,
  ConversationBookmarkResponse,
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

export async function updateConversationBookmark(
  conversationId: string,
  is_bookmarked: boolean,
): Promise<ConversationBookmarkResponse> {
  return serverApi.updateConversationBookmark(conversationId, is_bookmarked)
}

export async function getMessages(
  conversationId: string,
  params?: MessagesParams,
): Promise<MessagesResponse> {
  return serverApi.getMessages(conversationId, params)
}

export async function chat(body: ChatRequest): Promise<ChatResponse> {
  return serverApi.chat(body)
}
