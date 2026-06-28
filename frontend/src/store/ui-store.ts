import { create } from "zustand"
import { persist } from "zustand/middleware"

interface UiState {
  sidebarOpen: boolean
  theme: "dark" | "light" | "system"
  activeConversationId: string | null
  selectedWorkspace: string
}

interface UiActions {
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
  setTheme: (theme: "dark" | "light" | "system") => void
  setActiveConversation: (id: string | null) => void
  setSelectedWorkspace: (ws: string) => void
}

export const useUiStore = create<UiState & UiActions>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      theme: "system",
      activeConversationId: null,
      selectedWorkspace: "default",
      toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      setTheme: (theme) => set({ theme }),
      setActiveConversation: (id) => set({ activeConversationId: id }),
      setSelectedWorkspace: (ws) => set({ selectedWorkspace: ws }),
    }),
    { name: "hearme-ui" }
  )
)
