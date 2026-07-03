"use client"

import { useCallback, useState, memo } from "react"
import { Check, Copy } from "lucide-react"
import { cn } from "@/lib/utils"
import { FOCUS_RING, ICON_SIZE, TYPOGRAPHY } from "@/lib/design-tokens"

interface MessageToolbarProps {
  content: string
  className?: string
}

export const MessageToolbar = memo(function MessageToolbar({ content, className }: MessageToolbarProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = useCallback(async () => {
    if (!content) return
    try {
      await navigator.clipboard.writeText(content)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 2000)
    } catch {
      /* clipboard unavailable */
    }
  }, [content])

  return (
    <div
      className={cn(
        "flex items-center gap-0.5 pt-2 opacity-0 transition-opacity duration-200",
        "group-hover/message:opacity-100 group-focus-within/message:opacity-100",
        className
      )}
    >
      <button
        type="button"
        onClick={handleCopy}
        aria-label={copied ? "Message copied to clipboard" : "Copy message to clipboard"}
        className={cn(
          FOCUS_RING,
          "inline-flex items-center gap-1.5 rounded-md px-2 py-1",
          TYPOGRAPHY.caption,
          "text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        )}
      >
        {copied ? (
          <>
            <Check className={cn(ICON_SIZE.sm, "text-emerald-500")} aria-hidden="true" />
            <span>Copied ✓</span>
          </>
        ) : (
          <>
            <Copy className={ICON_SIZE.sm} aria-hidden="true" />
            <span>Copy</span>
          </>
        )}
      </button>
    </div>
  )
})
