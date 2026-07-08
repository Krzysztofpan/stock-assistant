"use client"

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react"

import type { ErrorDetail } from "@/services/stockAssistantService/types"

export type ChatStreamErrorState = ErrorDetail & {
  variant: "fatal" | "warning"
}

type ChatStreamContextValue = {
  isAiTyping: boolean
  processSteps: string[]
  streamError: ChatStreamErrorState | null
  setTyping: (isTyping: boolean) => void
  appendProcessStep: (label: string) => void
  clearProcessSteps: () => void
  setStreamError: (error: ChatStreamErrorState | null) => void
}

const ChatStreamContext = createContext<ChatStreamContextValue | null>(null)

type ChatStreamProviderProps = {
  children: ReactNode
}

export function ChatStreamProvider({ children }: ChatStreamProviderProps) {
  const [isAiTyping, setIsAiTyping] = useState(false)
  const [processSteps, setProcessSteps] = useState<string[]>([])
  const [streamError, setStreamErrorState] = useState<ChatStreamErrorState | null>(null)

  const setTyping = useCallback((isTyping: boolean) => {
    setIsAiTyping(isTyping)
  }, [])

  const appendProcessStep = useCallback((label: string) => {
    setProcessSteps((current) => {
      if (current.at(-1) === label) {
        return current
      }

      return [...current, label]
    })
  }, [])

  const clearProcessSteps = useCallback(() => {
    setProcessSteps([])
  }, [])

  const setStreamError = useCallback((error: ChatStreamErrorState | null) => {
    setStreamErrorState(error)
  }, [])

  const value = useMemo(
    () => ({
      isAiTyping,
      processSteps,
      streamError,
      setTyping,
      appendProcessStep,
      clearProcessSteps,
      setStreamError,
    }),
    [
      isAiTyping,
      processSteps,
      streamError,
      setTyping,
      appendProcessStep,
      clearProcessSteps,
      setStreamError,
    ],
  )

  return (
    <ChatStreamContext.Provider value={value}>
      {children}
    </ChatStreamContext.Provider>
  )
}

export function useChatStreamContext() {
  const context = useContext(ChatStreamContext)

  if (!context) {
    throw new Error("useChatStreamContext must be used within ChatStreamProvider")
  }

  return context
}

export function useOptionalChatStreamContext() {
  return useContext(ChatStreamContext)
}
