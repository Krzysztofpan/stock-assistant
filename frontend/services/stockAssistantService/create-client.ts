import qs from "qs"

import type { ChatRequest, ChatResponse, ConversationBookmarkResponse, ConversationParams, ConversationResponse, ConversationsParams, ConversationsResponse, CurrentUserResponse, MessagesParams, MessagesResponse } from "./types"

export type RequestFn = <T>(path: string, init?: RequestInit) => Promise<T>

const queryStringOptions: qs.IStringifyOptions = {
  addQueryPrefix: true,
  skipNulls: true,
}

function toQueryString(params?: object) {
  return qs.stringify(params ?? {}, queryStringOptions)
}

function toFieldsQuery(params?: object) {
  if (params) {
    const keys = Object.keys(params)

    return keys.length ? `?fields=${keys.join(",")}` : ""
  }

  return ""
}

export function createStockAssistantClient(request: RequestFn) {
  return {
    getCurrentUser: () => request<CurrentUserResponse>("/me"),

    getConversations: (params?: ConversationsParams) => {
      const query = toQueryString(params)

      return request<ConversationsResponse>(`/conversations${query}`)
    },

    getConversation: (conversationId: string, params?: ConversationParams) => {
      const query = toFieldsQuery(params)

      return request<ConversationResponse>(`/conversations/${conversationId}${query}`)
    },

    updateConversationBookmark: (conversationId: string, is_bookmarked: boolean) => {
      return request<ConversationBookmarkResponse>(`/conversations/${conversationId}/bookmark`, {
        method: "PUT",
        body: JSON.stringify({ is_bookmarked }),
      })
    },

    getMessages: (conversationId: string, params?: MessagesParams) => {
      const query = toQueryString(params)

      return request<MessagesResponse>(`/conversations/${conversationId}/messages${query}`)
    },

    chat: (body: ChatRequest) =>
      request<ChatResponse>("/chat", {
        method: "POST",
        body: JSON.stringify(body),
      }),
  }
}
