import MarkdownContent from "@/components/main/conversation/MarkdownContent"
import { cn } from "@/lib/utils"
import { MessageItem } from "@/services/stockAssistantService/types"

type MessageViewProps = {
  messageObj: MessageItem
}

const MessageView = ({ messageObj }: MessageViewProps) => {
  const isUser = messageObj.role === "user"

  return (
    <div className={cn("flex w-full px-3 py-3", isUser ? "justify-end font-semibold" : "font-normal")}>
      {isUser
        ? <p className="max-w-2/3 break-all rounded-3xl bg-mist-300 px-5 py-3">{messageObj.text}</p>
        : <MarkdownContent content={messageObj.text} className="max-w-full" />}
    </div>
  )
}

export default MessageView
