"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { NAV_ITEMS } from "@/lib/constants"
import { cn } from "@/lib/utils"
import { useUiStore } from "@/store/ui-store"
import {
  LayoutDashboard,
  MessageSquare,
  Brain,
  Database,
  FileText,
  BarChart3,
  Settings,
  ChevronLeft,
  Sparkles,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { motion, AnimatePresence } from "framer-motion"

const iconMap: Record<string, React.ElementType> = {
  LayoutDashboard,
  MessageSquare,
  Brain,
  Database,
  FileText,
  BarChart3,
  Settings,
}

export function Sidebar() {
  const pathname = usePathname()
  const { sidebarOpen, toggleSidebar } = useUiStore()

  return (
    <AnimatePresence mode="wait">
      <motion.aside
        initial={false}
        animate={{ width: sidebarOpen ? 240 : 64 }}
        className="fixed left-0 top-0 z-40 h-screen border-r bg-background flex flex-col"
        transition={{ duration: 0.2, ease: "easeInOut" }}
      >
        <div className={cn("flex items-center h-14 px-4", sidebarOpen ? "justify-between" : "justify-center")}>
          {sidebarOpen && (
            <Link href="/" className="flex items-center gap-2 font-semibold text-lg">
              <Sparkles className="h-5 w-5 text-primary" />
              <span>HearMe AI</span>
            </Link>
          )}
          <Button variant="ghost" size="icon" onClick={toggleSidebar} className="shrink-0">
            <ChevronLeft className={cn("h-4 w-4 transition-transform", !sidebarOpen && "rotate-180")} />
          </Button>
        </div>

        <Separator />

        <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map((item) => {
            const Icon = iconMap[item.icon]
            const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href))
            return (
              <Link key={item.href} href={item.href}>
                <div
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                    active
                      ? "bg-primary/10 text-primary"
                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground",
                    !sidebarOpen && "justify-center px-2"
                  )}
                >
                  <Icon className="h-5 w-5 shrink-0" />
                  {sidebarOpen && <span>{item.label}</span>}
                </div>
              </Link>
            )
          })}
        </nav>

        <Separator />

        <div className={cn("p-4", !sidebarOpen && "p-2")}>
          <div className={cn("rounded-lg bg-muted p-3", !sidebarOpen && "p-2")}>
            {sidebarOpen ? (
              <>
                <p className="text-xs font-medium text-muted-foreground">AI Brain</p>
                <p className="text-xs text-muted-foreground/60 mt-1">Knowledge + Memory active</p>
              </>
            ) : (
              <div className="flex justify-center">
                <Sparkles className="h-4 w-4 text-primary" />
              </div>
            )}
          </div>
        </div>
      </motion.aside>
    </AnimatePresence>
  )
}
