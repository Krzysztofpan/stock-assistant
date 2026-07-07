"use client"

import SidebarBtn from "@/components/utlis/SidebarBtn"
import { SquarePen } from "lucide-react"
import { useRouter } from "next/navigation"

const NewChatBtn = () => {
  const router = useRouter()
  const path = "/dashboard"

  return (
    <SidebarBtn icon={<SquarePen />} label="New Chat" onClick={() => router.replace(path)} path={path} />
  )
}

export default NewChatBtn
