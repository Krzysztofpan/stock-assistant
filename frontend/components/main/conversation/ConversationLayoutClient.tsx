"use client"

import InputWindow from "@/components/main/conversation/InputWindow"
import { ChatStreamProvider } from "@/contexts/chat-stream-context"
import type { ReactNode } from "react"

type ConversationLayoutClientProps = {
  conversationId: string
  children: ReactNode
}

const ConversationLayoutClient = ({ conversationId, children }: ConversationLayoutClientProps) => {
  return (
    <ChatStreamProvider key={conversationId}>
      <div className="min-h-screen flex flex-col">
        {children}
        <div className="sticky bottom-10 z-30 w-full max-w-3xl bg-background pt-3">
          <InputWindow />
        </div>
      </div>
    </ChatStreamProvider>
  )
}

export default ConversationLayoutClient
