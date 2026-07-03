"use client"

import { useUiStore } from "@/store/ui-store"
import { useDeveloperStore } from "@/stores/developer-store"
import { LAYOUT } from "@/lib/design-tokens"

export function PageContainer({ children }: { children: React.ReactNode }) {
  const { sidebarOpen } = useUiStore()
  const { developerMode } = useDeveloperStore()

  const devOffset = developerMode ? LAYOUT.devSidebarWidth : 0
  const userOffset = sidebarOpen ? LAYOUT.sidebarExpanded : LAYOUT.sidebarCollapsed

  return (
    <div
      className="min-h-screen transition-sidebar"
      style={{ marginLeft: userOffset + devOffset }}
    >
      {children}
    </div>
  )
}
