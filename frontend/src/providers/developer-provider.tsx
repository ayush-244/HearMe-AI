"use client"

import { useDeveloperStore } from "@/stores/developer-store"
import { useKeyboardShortcut } from "@/hooks/use-keyboard-shortcut"

export function DeveloperProvider({ children }: { children: React.ReactNode }) {
  const toggleDeveloperMode = useDeveloperStore((s) => s.toggleDeveloperMode)

  useKeyboardShortcut({ key: "d", ctrl: true, shift: true }, toggleDeveloperMode)

  return <>{children}</>
}
