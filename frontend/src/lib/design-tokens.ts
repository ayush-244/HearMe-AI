/**
 * HearMe AI Design System — TypeScript tokens
 * CSS variables are defined in globals.css; use these for layout logic & component config.
 */

/* ── Layout ─────────────────────────────────────────────── */

export const LAYOUT = {
  sidebarExpanded: 280,
  sidebarCollapsed: 60,
  devSidebarWidth: 240,
  headerHeight: 56,
} as const

/* ── Spacing scale (px) ─────────────────────────────────── */

export const SPACING = {
  1: 8,
  2: 12,
  3: 16,
  4: 24,
  5: 32,
  6: 48,
} as const

/* ── Motion ─────────────────────────────────────────────── */

export const MOTION = {
  hover: 200,
  fade: 200,
  sidebar: 250,
  stagger: 70,
} as const

/* ── Icon sizes ─────────────────────────────────────────── */

export const ICON_SIZE = {
  xs: "h-3 w-3",
  sm: "h-3.5 w-3.5",
  md: "h-4 w-4",
  lg: "h-5 w-5",
  xl: "h-7 w-7",
  page: "h-7 w-7",
} as const

/* ── Typography class names ─────────────────────────────── */

export const TYPOGRAPHY = {
  pageTitle: "text-3xl font-semibold tracking-tight text-foreground",
  sectionTitle: "text-lg font-semibold tracking-tight text-foreground",
  cardTitle: "text-sm font-medium text-foreground",
  body: "text-sm text-foreground",
  bodyMuted: "text-sm text-muted-foreground",
  caption: "text-xs text-muted-foreground",
  overline: "text-xs font-medium uppercase tracking-widest text-muted-foreground",
} as const

/* ── Surface & interaction ────────────────────────────────── */

export const SURFACE = {
  card: "rounded-xl border border-border bg-card shadow-sm",
  cardPadding: "p-4",
  cardPaddingLg: "p-6",
  cardInteractive:
    "rounded-xl border border-border bg-card shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md cursor-pointer",
  iconContainer: "flex items-center justify-center rounded-lg bg-muted p-2 shrink-0",
} as const

export const FOCUS_RING =
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"

/* ── Feature accent colors (icons & status only) ──────────── */

export const FEATURE_ACCENTS = {
  chat: "text-blue-400",
  library: "text-emerald-400",
  knowledge: "text-amber-400",
  memory: "text-cyan-400",
  developer: "text-amber-500",
  settings: "text-muted-foreground",
  analytics: "text-emerald-400",
} as const

export const STATUS_COLORS = {
  ready: "bg-emerald-500",
  thinking: "bg-amber-400",
  processing: "bg-blue-400",
  error: "bg-red-500",
  warning: "bg-amber-500",
} as const

/* ── Memory type config (single source) ───────────────────── */

export const MEMORY_TYPE_CONFIG: Record<
  string,
  { label: string; iconName: string; color: string; bg: string }
> = {
  semantic: { label: "Fact", iconName: "BookOpen", color: "text-blue-400", bg: "bg-muted" },
  episodic: { label: "Experience", iconName: "Clock", color: "text-emerald-400", bg: "bg-muted" },
  preference: { label: "Preference", iconName: "Heart", color: "text-purple-400", bg: "bg-muted" },
  working: { label: "Working", iconName: "Lightbulb", color: "text-amber-400", bg: "bg-muted" },
}
