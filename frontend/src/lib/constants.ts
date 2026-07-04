export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"

export const NAV_ITEMS = [
  { label: "Home", href: "/", icon: "LayoutDashboard" },
  { label: "Chat", href: "/chat", icon: "MessageSquare" },
  { label: "Library", href: "/library", icon: "FileText" },
  { label: "Knowledge", href: "/knowledge", icon: "Brain" },
  { label: "Memory", href: "/memory", icon: "Database" },
  { label: "Settings", href: "/settings", icon: "Settings" },
  { label: "Personalization", href: "/settings/personalization", icon: "Sparkles" },
] as const

export const DEV_NAV_ITEMS = [
  { label: "System", href: "/developer/system", icon: "Cpu" },
  { label: "Pipeline", href: "/developer/pipeline", icon: "GitBranch" },
  { label: "Retrieval", href: "/developer/retrieval", icon: "Search" },
  { label: "Memory", href: "/developer/memory", icon: "Database" },
  { label: "Vector Store", href: "/developer/vectorstore", icon: "HardDrive" },
  { label: "Prompt Inspector", href: "/developer/prompts", icon: "FileCode" },
  { label: "Logs", href: "/developer/logs", icon: "ScrollText" },
  { label: "API Explorer", href: "/developer/api", icon: "Globe" },
] as const

export const MEMORY_TYPE_COLORS: Record<string, string> = {
  semantic: "text-blue-400",
  episodic: "text-emerald-400",
  preference: "text-purple-400",
  working: "text-amber-400",
}

export const MEMORY_TYPE_LABELS: Record<string, string> = {
  semantic: "Semantic",
  episodic: "Episodic",
  preference: "Preference",
  working: "Working",
}
