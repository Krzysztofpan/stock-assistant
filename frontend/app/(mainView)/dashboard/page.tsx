import InputWindow from "@/components/main/conversation/InputWindow"
import { serverApi } from "@/services/stockAssistantService/server"
import { Metadata } from "next"

export const metadata: Metadata = {
  title: "Dashboard",
  description:
    "Start a new conversation with Stock Assistant. Ask about stock prices, company fundamentals, market trends, and investment research.",
}

export default async function Page() {
  const { user } = await serverApi.getCurrentUser()

  return (
    <div className="flex justify-center w-full items-center h-[80vh] flex-col gap-8 ">
      <h1 className="text-3xl font-semibold text-center">
        Hello again
        {" "}
        {user.name}
        , how can I help you.
      </h1>
      <div className="w-full">
        <InputWindow />
      </div>
    </div>
  )
}
