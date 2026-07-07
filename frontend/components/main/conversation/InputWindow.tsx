"use client"

import { FieldErrors, useForm, useWatch } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { chatRequestFormSchema, chatRequestSchemaType } from "@/services/stockAssistantService/schemas"
import { useParams, useRouter } from "next/navigation"
import { useSendChatMessage } from "@/hooks/mutations/use-chat"
import { setPendingChatMessage } from "@/lib/pending-chat-message"
import { Button } from "@/components/ui/button"
import { SendHorizonal } from "lucide-react"
import { Textarea } from "@/components/ui/textarea"
import CircularProgressBar from "@/components/utlis/CircularProgressBar"

import { cva } from "class-variance-authority"
import { useRef } from "react"
import { addConversationToPool } from "@/hooks/queries/conversation-store"
import { useQueryClient } from "@tanstack/react-query"

export const promptInputVariants = cva(
  `
  rounded-xl border border-input
  bg-background
  ring-offset-background
  focus-within:ring-1
  focus-within:ring-ring
  focus-within:ring-offset-1
  relative 
  border-mist-400 min-h-10 max-h-45 bg-mist-300 
  px-2 
  py-1
  `,
)

const MAX_MESSAGE_LENGTH = 1000

const InputWindow = () => {
  const router = useRouter()
  const { conversation_id } = useParams<{ conversation_id?: string }>()
  const { mutate: sendMessage, isPending } = useSendChatMessage()
  const inputRef = useRef<null | HTMLTextAreaElement>(null)
  const { register, handleSubmit, reset, control } = useForm({
    resolver: zodResolver(chatRequestFormSchema),
    defaultValues: {
      conversationId: conversation_id || crypto.randomUUID(),
      message: "",
    },
  })
  const queryClient = useQueryClient()

  const message = useWatch({ control, name: "message" }) ?? ""
  const messageLength = message.length
  const usagePercentage = (messageLength / MAX_MESSAGE_LENGTH) * 100
  const remainingCharacters = MAX_MESSAGE_LENGTH - messageLength

  const { ref: registerRef, ...messageField } = register("message")

  const onSubmit = (formData: chatRequestSchemaType) => {
    if (!conversation_id) {
      setPendingChatMessage({
        conversationId: formData.conversationId,
        message: formData.message,
      })
      addConversationToPool(
        queryClient,
        {
          id: formData.conversationId,
          is_bookmarked: false,
          created_at: Date().toLocaleString(),
          title: "New Conversation",
          updated_at: Date().toLocaleString(),
        })
      reset({ message: "", conversationId: formData.conversationId })
      router.replace(`/conversations/${formData.conversationId}`)

      return
    }

    reset({ message: "", conversationId: formData.conversationId })
    sendMessage({ message: formData.message, conversationId: formData.conversationId })
  }

  const onError = (error: FieldErrors<FormData>) => {
    console.log(error)
  }

  const handleFocusInput = () => {
    if (inputRef.current) {
      inputRef.current.focus()
    }
  }

  const handleEnterSubmit = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      void handleSubmit(onSubmit)()
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit, onError)}>
      <div
        onClick={handleFocusInput}
        className={`
          ${promptInputVariants()} 
          flex items-center justify-center flex-wrap 
          rounded-4xl! cursor-text gap-2 
        `}
      >
        <Textarea
          ref={(element) => {
            registerRef(element)
            inputRef.current = element
          }}
          {...messageField}
          onKeyDown={handleEnterSubmit}
          className="
          ring-0 w-fit overflow-y-auto scrollbar-thin focus-within:border-0! focus-within:ring-0!
          max-h-30 bg-transparent border-0 min-h-10 text-muted-foreground
          py-2 text-base!
          "
          id="message"
          placeholder="ask any question..."
          maxLength={MAX_MESSAGE_LENGTH}
        />
        <div className="ml-auto flex gap-2 items-center">
          {messageLength
            ? (
                <>
                  <CircularProgressBar percentage={usagePercentage} size={32} trackColor="rgb(180, 180, 180)" progressColor="rgb(100, 100, 100)" label={() => remainingCharacters} labelColor="rgb(80, 80, 80)" scaleOnWarning={false} className="shrink-0" />
                  <Button type="submit" variant="outline" disabled={isPending || !messageLength} className="cursor-pointer  aspect-square">
                    <SendHorizonal />
                  </Button>
                </>
              )
            : null}
        </div>
      </div>
    </form>
  )
}

export default InputWindow
