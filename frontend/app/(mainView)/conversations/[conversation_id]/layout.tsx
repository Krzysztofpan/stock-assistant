import ConversationLayoutClient from "@/components/main/conversation/ConversationLayoutClient"
import { ReactNode } from "react"

type ConversationLayoutProps = {
  children: ReactNode
  params: Promise<{ conversation_id: string }>
}

const ConversationLayout = async ({ children, params }: ConversationLayoutProps) => {
  const { conversation_id } = await params

  return (
    <ConversationLayoutClient conversationId={conversation_id}>
      {children}
    </ConversationLayoutClient>
  )
}

export default ConversationLayout
