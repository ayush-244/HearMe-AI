"use client"

import { create } from "zustand"
import { persist } from "zustand/middleware"

interface DeveloperState {
  developerMode: boolean
  enableDeveloperMode: () => void
  disableDeveloperMode: () => void
  toggleDeveloperMode: () => void
}

export const useDeveloperStore = create<DeveloperState>()(
  persist(
    (set) => ({
      developerMode: false,
      enableDeveloperMode: () => set({ developerMode: true }),
      disableDeveloperMode: () => set({ developerMode: false }),
      toggleDeveloperMode: () => set((s) => ({ developerMode: !s.developerMode })),
    }),
    { name: "hearme-developer" }
  )
)
