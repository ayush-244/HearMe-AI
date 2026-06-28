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

const DEV_NAV_ITEMS = [
  { label: "System", href: "/developer/system", icon: Cpu },
  { label: "Pipeline", href: "/developer/pipeline", icon: GitBranch },
  { label: "Retrieval", href: "/developer/retrieval", icon: Search },
  { label: "Memory", href: "/developer/memory", icon: Database },
  { label: "Vector Store", href: "/developer/vectorstore", icon: HardDrive },
  { label: "Prompt Inspector", href: "/developer/prompts", icon: FileCode },
  { label: "Logs", href: "/developer/logs", icon: ScrollText },
  { label: "API Explorer", href: "/developer/api", icon: Globe },
]

export function DeveloperSidebar() {
  const pathname = usePathname()
  const { developerMode, toggleDeveloperMode } = useDeveloperStore()

  return (
    <AnimatePresence>
      {developerMode && (
        <motion.aside
          initial={{ width: 0, opacity: 0 }}
          animate={{ width: 240, opacity: 1 }}
          exit={{ width: 0, opacity: 0 }}
          transition={{ duration: 0.2, ease: "easeInOut" }}
          className="fixed left-[240px] top-0 z-30 h-screen border-r bg-background/95 backdrop-blur flex flex-col overflow-hidden"
        >
          <div className="flex items-center justify-between h-14 px-4">
            <div className="flex items-center gap-2 font-semibold text-sm">
              <Code2 className="h-4 w-4 text-amber-500" />
              <span>Developer</span>
            </div>
            <Button variant="ghost" size="icon" onClick={toggleDeveloperMode} className="shrink-0 h-7 w-7">
              <ChevronLeft className="h-3.5 w-3.5" />
            </Button>
          </div>

          <Separator />

          <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
            {DEV_NAV_ITEMS.map((item) => {
              const Icon = item.icon
              const active = pathname === item.href || pathname.startsWith(item.href)
              return (
                <Link key={item.href} href={item.href}>
                  <div
                    className={cn(
                      "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                      active
                        ? "bg-amber-500/10 text-amber-500"
                        : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                    )}
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    <span>{item.label}</span>
                  </div>
                </Link>
              )
            })}
          </nav>

          <Separator />

          <div className="p-4">
            <div className="rounded-lg bg-amber-500/5 border border-amber-500/10 p-3">
              <p className="text-xs font-medium text-amber-500">Developer Mode</p>
              <p className="text-xs text-muted-foreground/60 mt-1">Active</p>
            </div>
          </div>
        </motion.aside>
      )}
    </AnimatePresence>
  )
}
