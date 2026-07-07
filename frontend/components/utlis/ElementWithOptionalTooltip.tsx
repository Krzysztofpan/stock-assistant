"use client"

import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { useIsTruncated } from "@/hooks/use-is-truncated"
import { useRef, useState } from "react"

type ElementWithOptionalTooltipProps = {
  text: string
}

const ElementWithOptionalTooltip = ({ text }: ElementWithOptionalTooltipProps) => {
  const ref = useRef<HTMLSpanElement>(null)
  const isTruncated = useIsTruncated(ref, text)
  const [open, setOpen] = useState(false)

  const handleOpenChange = (next: boolean) => {
    if (isTruncated) {
      setOpen(next)
    }
  }

  return (
    <Tooltip delayDuration={700} open={isTruncated && open} onOpenChange={handleOpenChange}>
      <TooltipTrigger asChild>
        <span ref={ref} className="block truncate">
          {text}
        </span>
      </TooltipTrigger>
      <TooltipContent side="bottom">{text}</TooltipContent>
    </Tooltip>
  )
}

export default ElementWithOptionalTooltip
