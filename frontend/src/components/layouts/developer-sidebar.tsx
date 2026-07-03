"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { useDeveloperStore } from "@/stores/developer-store"
import { motion, AnimatePresence } from "framer-motion"
import {
  Cpu,
  GitBranch,
  Search,
  Database,
  HardDrive,
  FileCode,
  ScrollText,
  Globe,
  ChevronLeft,
  Code2,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { DEV_NAV_ITEMS } from "@/lib/constants"
import { LAYOUT, MOTION, FEATURE_ACCENTS, ICON_SIZE } from "@/lib/design-tokens"

const DEV_ICON_MAP: Record<string, React.ElementType> = {
  Cpu,
  GitBranch,
  Search,
  Database,
  HardDrive,
  FileCode,
  ScrollText,
  Globe,
}

export function DeveloperSidebar() {
  const pathname = usePathname()
  const { developerMode, toggleDeveloperMode } = useDeveloperStore()

  return (
    <AnimatePresence>
      {developerMode && (
        <motion.aside
          initial={{ width: 0, opacity: 0 }}
          animate={{ width: LAYOUT.devSidebarWidth, opacity: 1 }}
          exit={{ width: 0, opacity: 0 }}
          transition={{ duration: MOTION.sidebar / 1000, ease: "easeInOut" }}
          style={{ left: LAYOUT.sidebarExpanded }}
          className="fixed top-0 z-30 h-screen border-r border-border bg-sidebar/95 backdrop-blur flex flex-col overflow-hidden"
        >
          <div className="flex items-center justify-between h-14 px-4">
            <div className="flex items-center gap-2 text-card-title">
              <Code2 className={cn(ICON_SIZE.md, FEATURE_ACCENTS.developer)} />
              <span>Developer</span>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleDeveloperMode}
              className="shrink-0 h-8 w-8"
              aria-label="Close developer sidebar"
            >
              <ChevronLeft className={ICON_SIZE.sm} />
            </Button>
          </div>

          <Separator />

          <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto scrollbar-thin" aria-label="Developer navigation">
            {DEV_NAV_ITEMS.map((item) => {
              const Icon = DEV_ICON_MAP[item.icon] ?? Code2
              const active = pathname === item.href || pathname.startsWith(item.href)
              return (
                <Link key={item.href} href={item.href} aria-current={active ? "page" : undefined}>
                  <div
                    className={cn(
                      "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all duration-200",
                      active
                        ? "bg-muted text-foreground"
                        : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                    )}
                  >
                    <Icon className={cn(ICON_SIZE.md, "shrink-0", active && FEATURE_ACCENTS.developer)} />
                    <span>{item.label}</span>
                  </div>
                </Link>
              )
            })}
          </nav>

          <Separator />

          <div className="p-4">
            <div className="rounded-lg border border-border bg-muted/50 p-3">
              <p className={cn("text-caption font-medium", FEATURE_ACCENTS.developer)}>Developer Mode</p>
              <p className="text-caption mt-1">Active</p>
            </div>
          </div>
        </motion.aside>
      )}
    </AnimatePresence>
  )
}
