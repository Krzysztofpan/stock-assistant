import InputWindow from "@/components/main/conversation/InputWindow"
import { ReactNode } from "react"

const ConversationLayout = ({ children }: { children: ReactNode }) => {
  return (
    <div className="min-h-screen flex flex-col">
      {children}
      <div className="sticky bottom-10 w-full max-w-3xl">
        <InputWindow />
      </div>
    </div>
  )
}

export default ConversationLayout
