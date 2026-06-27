export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"

export const NAV_ITEMS = [
  { label: "Home", href: "/", icon: "LayoutDashboard" },
  { label: "Chat", href: "/chat", icon: "MessageSquare" },
  { label: "Knowledge", href: "/knowledge", icon: "Brain" },
  { label: "Memory", href: "/memory", icon: "Database" },
  { label: "Documents", href: "/documents", icon: "FileText" },
  { label: "Analytics", href: "/analytics", icon: "BarChart3" },
  { label: "Settings", href: "/settings", icon: "Settings" },
] as const

export const MEMORY_TYPE_COLORS: Record<string, string> = {
  semantic: "text-blue-500",
  episodic: "text-green-500",
  preference: "text-purple-500",
  working: "text-amber-500",
}

export const MEMORY_TYPE_LABELS: Record<string, string> = {
  semantic: "Semantic",
  episodic: "Episodic",
  preference: "Preference",
  working: "Working",
}
