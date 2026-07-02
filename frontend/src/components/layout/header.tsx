"use client"

import { useTheme } from "next-themes"
import { Moon, Sun, Menu } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useUiStore } from "@/store/ui-store"
import { useEffect, useState } from "react"

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

  const dotColor = {
    ready: "bg-emerald-500",
    thinking: "bg-amber-400",
    processing: "bg-blue-400",
  }[status]

  return (
    <div className="flex items-center gap-1.5 text-xs text-zinc-500">
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
    <header className="sticky top-0 z-30 flex h-14 items-center gap-4 border-b border-zinc-800/60 bg-zinc-950/80 backdrop-blur supports-[backdrop-filter]:bg-zinc-950/60 px-4 lg:px-6">
      <Button
        variant="ghost"
        size="icon"
        onClick={toggleSidebar}
        className="md:hidden text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800"
        aria-label="Toggle sidebar"
      >
        <Menu className="h-5 w-5" />
      </Button>

      <div className="flex-1" />

      <AIStatusBadge status={aiStatus} />

      {mounted && (
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className="text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800"
          aria-label="Toggle theme"
        >
          {theme === "dark" ? <Sun className="h-4.5 w-4.5" /> : <Moon className="h-4.5 w-4.5" />}
        </Button>
      )}
    </header>
  )
}
