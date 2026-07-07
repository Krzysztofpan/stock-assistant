import MessageList from "@/components/main/conversation/MessageList"
import { ApiError } from "@/services/stockAssistantService/errors"
import { serverApi } from "@/services/stockAssistantService/server"
import { Metadata } from "next"

type ConversationPageProps = {
  params: Promise<{ conversation_id: string }>
}

const defaultMetadata: Metadata = {
  title: "Conversation",
  description: "Continue a conversation with Stock Assistant about stocks, markets, and publicly traded companies.",
}

export async function generateMetadata({ params }: ConversationPageProps): Promise<Metadata> {
  const { conversation_id } = await params

  try {
    const { conversation } = await serverApi.getConversation(conversation_id, { title: true })
    const title = conversation.title ?? defaultMetadata.title

    return {
      title,
      description: `Continue "${title}" - chat with Stock Assistant about stocks, markets, and publicly traded companies.`,
    }
  }
  catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return defaultMetadata
    }

    throw error
  }
}

const ConversationPage = async ({ params }: ConversationPageProps) => {
  const { conversation_id } = await params

  return <MessageList conversationId={conversation_id} />
}

export default ConversationPage
