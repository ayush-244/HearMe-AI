"use client"

import { useTheme } from "next-themes"
import { Moon, Sun, Menu } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useUiStore } from "@/store/ui-store"
import { useEffect, useState } from "react"
import { STATUS_COLORS } from "@/lib/design-tokens"
import { ICON_SIZE } from "@/lib/design-tokens"

function useMounted() {
  const [mounted, setMounted] = useState(false)
  useEffect(() => {
    setMounted(true)
  }, [])
  return mounted
}

type Status = "ready" | "thinking" | "processing"

function AIStatusBadge({ status }: { status: Status }) {
  const label = {
    ready: "AI Ready",
    thinking: "Thinking...",
    processing: "Processing...",
  }[status]

  const dotColor = STATUS_COLORS[status]

  return (
    <div className="flex items-center gap-2 text-caption" role="status" aria-live="polite">
      <span className={`h-1.5 w-1.5 rounded-full shrink-0 animate-pulse ${dotColor}`} />
      <span>{label}</span>
    </div>
  )
}

export function Header({ aiStatus = "ready" }: { aiStatus?: Status }) {
  const { theme, setTheme } = useTheme()
  const { toggleSidebar } = useUiStore()
  const mounted = useMounted()

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-4 border-b border-border bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-4 lg:px-6">
      <Button
        variant="ghost"
        size="icon"
        onClick={toggleSidebar}
        className="md:hidden text-muted-foreground hover:text-foreground"
        aria-label="Toggle sidebar"
      >
        <Menu className={ICON_SIZE.lg} />
      </Button>

      <div className="flex-1" />

      <AIStatusBadge status={aiStatus} />

      {mounted && (
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className="text-muted-foreground hover:text-foreground"
          aria-label="Toggle theme"
        >
          {theme === "dark" ? <Sun className={ICON_SIZE.md} /> : <Moon className={ICON_SIZE.md} />}
        </Button>
      )}
    </header>
  )
}
