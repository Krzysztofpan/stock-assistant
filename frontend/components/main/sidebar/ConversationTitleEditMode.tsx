"use client"
import { Input } from "@/components/ui/input"

import { Dispatch, SetStateAction, useEffect, useRef, useState } from "react"

type ConversationTitleEditModeProps = {
  conversationTitle: string
  setEditMode: Dispatch<SetStateAction<boolean>>
  handleChangeTitle: (title: string) => void
}

const ConversationTitleEditMode = ({ setEditMode, conversationTitle, handleChangeTitle }: ConversationTitleEditModeProps) => {
  const [title, setTitle] = useState(conversationTitle)
  const inputRef = useRef<HTMLInputElement | null>(null)

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.focus()
    }
  }, [])

  return (
    <Input
      className="border-0 bg-transparent shadow-none ring-0 outline-none focus-visible:border-0! focus-visible:ring-0! focus-visible:ring-offset-0!"
      value={title}
      ref={inputRef}
      onBlur={() => setEditMode(false)}
      onChange={e => setTitle(e.target.value)}
      onKeyDown={(e) => {
        if (e.key === "Enter") {
          e.preventDefault()
          handleChangeTitle(title)
          setEditMode(false)
        }
        if (e.key === "Escape") {
          setEditMode(false)
        }
      }}
    />
  )
}

export default ConversationTitleEditMode
