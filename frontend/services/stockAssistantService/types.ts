export type MessageRole = "user" | "system" | "ai"

export type ErrorDetail = {
  message: string
  status_code: number
}

export type UserPublic = {
  id: string
  name: string
  email: string
}

export type CurrentUserResponse = {
  user: UserPublic
}

export type MessageItem = {
  id: number
  role: MessageRole
  text: string
  created_at: string
}

export type MessagesResponse = {
  messages: MessageItem[]
  has_more: boolean
}

export type ConversationItem = {
  id: string
  title: string
  created_at: string
  updated_at: string
  is_bookmarked: boolean
}

export type ConversationParams = Partial<{ [K in keyof ConversationItem]: boolean }>

export type ConversationsResponse = {
  conversations: ConversationItem[]
  has_more: boolean
}

export type ConversationResponse = {
  conversation: Partial<ConversationItem>
}

export type ConversationUpdateRequest = Partial<Pick<ConversationItem, "title" | "is_bookmarked">>

export type ConversationsParams = {
  before_updated_at?: string
  before_id?: string
  limit?: number
  query?: string
  is_bookmarked?: boolean
}

export type MessagesParams = {
  before_id?: number
  limit?: number
}

export type AuthActionState = {
  error?: string
}
