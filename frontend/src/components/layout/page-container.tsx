"use client"

import { useUiStore } from "@/store/ui-store"
import { useDeveloperStore } from "@/stores/developer-store"

export function PageContainer({ children }: { children: React.ReactNode }) {
  const { sidebarOpen } = useUiStore()
  const { developerMode } = useDeveloperStore()

  const devOffset = developerMode ? 240 : 0
  const userOffset = sidebarOpen ? 240 : 64

  return (
    <div
      className="min-h-screen transition-all duration-200"
      style={{ marginLeft: userOffset + devOffset }}
    >
      {children}
    </div>
  )
}
