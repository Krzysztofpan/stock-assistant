const PENDING_CHAT_MESSAGE_KEY = "pending-chat-message"

type PendingChatMessage = {
  conversationId: string
  message: string
}

export function setPendingChatMessage(data: PendingChatMessage) {
  localStorage.setItem(PENDING_CHAT_MESSAGE_KEY, JSON.stringify(data))
}

export function consumePendingChatMessage(conversationId: string): string | null {
  const raw = localStorage.getItem(PENDING_CHAT_MESSAGE_KEY)

  if (!raw) {
    return null
  }

  try {
    const data = JSON.parse(raw) as PendingChatMessage

    if (data.conversationId !== conversationId) {
      return null
    }

    localStorage.removeItem(PENDING_CHAT_MESSAGE_KEY)

    return data.message
  }
  catch {
    localStorage.removeItem(PENDING_CHAT_MESSAGE_KEY)

    return null
  }
}
