"use client"

import { useCallback, useRef, useState, memo, isValidElement, type ReactNode } from "react"
import { Check, Copy } from "lucide-react"
import { cn } from "@/lib/utils"
import { FOCUS_RING, ICON_SIZE, TYPOGRAPHY } from "@/lib/design-tokens"

interface CodeBlockProps {
  language: string
  children: ReactNode
}

export const CodeBlock = memo(function CodeBlock({ language, children }: CodeBlockProps) {
  const preRef = useRef<HTMLPreElement>(null)
  const [copied, setCopied] = useState(false)

  const handleCopy = useCallback(async () => {
    const text = preRef.current?.textContent ?? ""
    if (!text) return
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      window.setTimeout(() => setCopied(false), 2000)
    } catch {
      /* clipboard unavailable */
    }
  }, [])

  const displayLanguage = language && language !== "text" ? language : "plain text"

  return (
    <div className="chat-code-block group/code my-3 overflow-hidden rounded-lg border border-border">
      <div className="flex items-center justify-between border-b border-border bg-muted/40 px-3 py-1.5">
        <span className={cn(TYPOGRAPHY.caption, "font-mono uppercase tracking-wide")}>
          {displayLanguage}
        </span>
        <button
          type="button"
          onClick={handleCopy}
          aria-label={copied ? "Code copied to clipboard" : "Copy code to clipboard"}
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
      <pre
        ref={preRef}
        className="chat-code-pre overflow-x-auto bg-muted/60 p-4 text-sm leading-relaxed scrollbar-thin"
      >
        {children}
      </pre>
    </div>
  )
})

export function extractCodeBlock(children: ReactNode): { language: string; content: ReactNode } | null {
  const child = Array.isArray(children) ? children[0] : children
  if (!isValidElement<{ className?: string; children?: ReactNode }>(child)) return null
  if (child.type !== "code") return null

  const className = child.props.className ?? ""
  const language = className.replace(/language-/, "").trim() || "text"
  return { language, content: child.props.children }
}
