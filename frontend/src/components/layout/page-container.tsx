"use client"

import { useUiStore } from "@/store/ui-store"
import { cn } from "@/lib/utils"

export function PageContainer({ children }: { children: React.ReactNode }) {
  const { sidebarOpen } = useUiStore()

  return (
    <div
      className={cn(
        "min-h-screen transition-all duration-200",
        sidebarOpen ? "ml-60" : "ml-16"
      )}
    >
      {children}
    </div>
  )
}
