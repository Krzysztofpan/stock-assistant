"use client"

import { Button } from "@/components/ui/button"

import { usePathname } from "next/navigation"
import { ReactNode } from "react"

type SidebarBtnProps = {
  label: string
  icon: ReactNode
  path?: string
  onClick?: (...args: []) => void
}

const SidebarBtn = ({ label, icon, path, onClick }: SidebarBtnProps) => {
  const pathname = usePathname()

  const isPathActive = pathname === path

  return (
    <Button
      onClick={onClick}
      variant="ghost"
      className={`cursor-pointer justify-start group-data-[collapsible=icon]:justify-center items-center ${isPathActive ? "bg-muted" : null}`}
    >
      {icon}
      <span className="group-data-[collapsible=icon]:hidden">{label}</span>
    </Button>
  )
}

export default SidebarBtn
