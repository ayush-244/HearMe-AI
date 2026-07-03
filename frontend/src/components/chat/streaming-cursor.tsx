"use client"

import { memo } from "react"
import { cn } from "@/lib/utils"

export const StreamingCursor = memo(function StreamingCursor() {
  return (
    <span
      className={cn(
        "streaming-cursor inline-block w-[0.55em] shrink-0 align-text-bottom",
        "bg-primary"
      )}
      aria-hidden="true"
    />
  )
})
