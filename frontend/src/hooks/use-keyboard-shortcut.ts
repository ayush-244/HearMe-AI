"use client"

import { useEffect } from "react"

interface ShortcutOptions {
  key: string
  ctrl?: boolean
  shift?: boolean
  alt?: boolean
}

export function useKeyboardShortcut(
  { key, ctrl = false, shift = false, alt = false }: ShortcutOptions,
  handler: () => void
) {
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (
        e.key.toLowerCase() === key.toLowerCase() &&
        e.ctrlKey === ctrl &&
        e.shiftKey === shift &&
        e.altKey === alt
      ) {
        e.preventDefault()
        handler()
      }
    }

    window.addEventListener("keydown", onKeyDown)
    return () => window.removeEventListener("keydown", onKeyDown)
  }, [key, ctrl, shift, alt, handler])
}
