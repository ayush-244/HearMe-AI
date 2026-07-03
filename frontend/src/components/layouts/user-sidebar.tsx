"use client"

import { useState, useCallback } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { useConversations, useCreateConversation, useDeleteConversation, useUpdateConversation } from "@/hooks/use-conversations"
import { useUiStore } from "@/store/ui-store"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Input } from "@/components/ui/input"
import { motion, AnimatePresence } from "framer-motion"
import {
  MessageSquare,
  FileText,
  Brain,
  Database,
  Settings,
  Search,
  Plus,
  Trash2,
  Pin,
  MoreHorizontal,
  Pencil,
  Check,
  X,
  Sparkles,
  PanelLeftClose,
  PanelLeft,
  MessagesSquare,
} from "lucide-react"
import { formatDate } from "@/lib/utils"
import { toast } from "@/components/ui/toast"
import { LAYOUT, MOTION, FEATURE_ACCENTS, ICON_SIZE } from "@/lib/design-tokens"

const NAV_ITEMS_FULL = [
  { label: "Chat", href: "/chat", Icon: MessageSquare, accent: FEATURE_ACCENTS.chat },
  { label: "Library", href: "/library", Icon: FileText, accent: FEATURE_ACCENTS.library },
  { label: "Knowledge", href: "/knowledge", Icon: Brain, accent: FEATURE_ACCENTS.knowledge },
  { label: "Memory", href: "/memory", Icon: Database, accent: FEATURE_ACCENTS.memory },
  { label: "Settings", href: "/settings", Icon: Settings, accent: FEATURE_ACCENTS.settings },
]

function Tooltip({ children, label }: { children: React.ReactNode; label: string }) {
  return (
    <div className="relative group/tooltip">
      {children}
      <div className="pointer-events-none absolute left-full ml-2 top-1/2 -translate-y-1/2 z-50 whitespace-nowrap rounded-lg border border-border bg-popover px-2 py-1.5 text-caption opacity-0 group-hover/tooltip:opacity-100 transition-fade shadow-md">
        {label}
      </div>
    </div>
  )
}

function ConversationItem({
  conv,
  isActive,
  onSelect,
  onRename,
  onDelete,
  onTogglePin,
}: {
  conv: { id: string; title: string; updated_at: string; pinned: boolean }
  isActive: boolean
  onSelect: () => void
  onRename: (title: string) => void
  onDelete: () => void
  onTogglePin: () => void
}) {
  const [editing, setEditing] = useState(false)
  const [editTitle, setEditTitle] = useState(conv.title)
  const [showMenu, setShowMenu] = useState(false)

  const handleRename = useCallback(() => {
    if (editTitle.trim() && editTitle !== conv.title) {
      onRename(editTitle.trim())
    }
    setEditing(false)
  }, [editTitle, conv.title, onRename])

  if (editing) {
    return (
      <div className="flex items-center gap-1 px-2 py-1.5">
        <Input
          value={editTitle}
          onChange={(e) => setEditTitle(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") handleRename(); if (e.key === "Escape") setEditing(false) }}
          className="flex-1 h-7 text-xs"
          autoFocus
          onBlur={handleRename}
        />
        <Button variant="ghost" size="icon" className="h-6 w-6" onClick={handleRename} aria-label="Confirm rename">
          <Check className={ICON_SIZE.xs} />
        </Button>
        <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => setEditing(false)} aria-label="Cancel rename">
          <X className={ICON_SIZE.xs} />
        </Button>
      </div>
    )
  }

  return (
    <div
      className={cn(
        "group relative flex items-center gap-2 rounded-lg px-2 py-2 text-sm cursor-pointer transition-all duration-200",
        isActive
          ? "bg-sidebar-accent text-sidebar-foreground border-l-2 border-ring pl-2"
          : "text-muted-foreground hover:bg-sidebar-accent/60 hover:text-foreground border-l-2 border-transparent"
      )}
      onClick={onSelect}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onSelect() } }}
    >
      <MessageSquare className={cn(ICON_SIZE.sm, "shrink-0", isActive ? FEATURE_ACCENTS.chat : "text-muted-foreground")} />
      {conv.pinned && <Pin className={cn(ICON_SIZE.xs, "shrink-0 text-amber-400")} />}
      <span className="flex-1 truncate text-caption">{conv.title}</span>

      <span className="hidden group-hover:flex items-center gap-0.5 shrink-0">
        <div className="relative">
          <Button
            variant="ghost"
            size="icon"
            className="h-5 w-5 text-muted-foreground hover:text-foreground"
            onClick={(e) => { e.stopPropagation(); setShowMenu(!showMenu) }}
            aria-label="Conversation options"
            aria-expanded={showMenu}
          >
            <MoreHorizontal className={ICON_SIZE.xs} />
          </Button>
          {showMenu && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setShowMenu(false)} aria-hidden="true" />
              <div className="absolute right-0 top-full z-50 mt-1 w-40 rounded-lg border border-border bg-popover p-1 shadow-md">
                <button
                  className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-caption hover:bg-accent transition-all duration-200 cursor-pointer"
                  onClick={(e) => { e.stopPropagation(); setEditing(true); setShowMenu(false) }}
                >
                  <Pencil className={ICON_SIZE.xs} /> Rename
                </button>
                <button
                  className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-caption hover:bg-accent transition-all duration-200 cursor-pointer"
                  onClick={(e) => { e.stopPropagation(); onTogglePin(); setShowMenu(false) }}
                >
                  <Pin className={ICON_SIZE.xs} /> {conv.pinned ? "Unpin" : "Pin"}
                </button>
                <Separator className="my-1" />
                <button
                  className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-caption text-destructive hover:bg-destructive/10 transition-all duration-200 cursor-pointer"
                  onClick={(e) => { e.stopPropagation(); onDelete(); setShowMenu(false) }}
                >
                  <Trash2 className={ICON_SIZE.xs} /> Delete
                </button>
              </div>
            </>
          )}
        </div>
      </span>
      <span className={cn("text-caption opacity-60 shrink-0", "group-hover:hidden")}>
        {formatDate(conv.updated_at)}
      </span>
    </div>
  )
}

export function UserSidebar() {
  const pathname = usePathname()
  const router = useRouter()
  const { sidebarOpen, toggleSidebar, setActiveConversation, activeConversationId } = useUiStore()
  const [searchQuery, setSearchQuery] = useState("")
  const { data: convsData } = useConversations(searchQuery || undefined)
  const createConv = useCreateConversation()
  const deleteConv = useDeleteConversation()
  const updateConv = useUpdateConversation()

  const conversations = convsData?.conversations ?? []

  const handleNewChat = useCallback(async () => {
    try {
      const conv = await createConv.mutateAsync("")
      setActiveConversation(conv.id)
      router.push(`/chat?id=${conv.id}`)
    } catch {
      toast({ title: "Failed to create chat", variant: "destructive" })
    }
  }, [createConv, setActiveConversation, router])

  const handleSelectConv = useCallback((id: string) => {
    setActiveConversation(id)
    router.push(`/chat?id=${id}`)
  }, [setActiveConversation, router])

  const handleRename = useCallback(async (id: string, title: string) => {
    try {
      await updateConv.mutateAsync({ id, title })
    } catch {
      toast({ title: "Failed to rename", variant: "destructive" })
    }
  }, [updateConv])

  const handleDelete = useCallback(async (id: string) => {
    try {
      await deleteConv.mutateAsync(id)
      if (activeConversationId === id) {
        setActiveConversation(null)
        router.push("/chat")
      }
    } catch {
      toast({ title: "Failed to delete", variant: "destructive" })
    }
  }, [deleteConv, activeConversationId, setActiveConversation, router])

  const handleTogglePin = useCallback(async (id: string, pinned: boolean) => {
    try {
      await updateConv.mutateAsync({ id, pinned: !pinned })
    } catch {
      toast({ title: "Failed to update", variant: "destructive" })
    }
  }, [updateConv])

  const pinnedConvs = conversations.filter((c) => c.pinned)
  const recentConvs = conversations.filter((c) => !c.pinned)

  return (
    <motion.aside
      initial={false}
      animate={{ width: sidebarOpen ? LAYOUT.sidebarExpanded : LAYOUT.sidebarCollapsed }}
      className="fixed left-0 top-0 z-40 h-screen border-r border-sidebar-border bg-sidebar flex flex-col"
      transition={{ duration: MOTION.sidebar / 1000, ease: "easeInOut" }}
      aria-label="Main sidebar"
    >
      <div className={cn("flex items-center h-14 px-3 shrink-0", sidebarOpen ? "justify-between" : "justify-center")}>
        <AnimatePresence mode="wait">
          {sidebarOpen && (
            <motion.div
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: MOTION.fade / 1000 }}
            >
              <Link href="/" className="flex items-center gap-2 text-card-title">
                <Sparkles className={cn(ICON_SIZE.md, FEATURE_ACCENTS.chat)} />
                <span>HearMe AI</span>
              </Link>
            </motion.div>
          )}
        </AnimatePresence>
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleSidebar}
          className="shrink-0 h-8 w-8 text-muted-foreground hover:text-foreground"
          aria-label={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
        >
          {sidebarOpen ? <PanelLeftClose className={ICON_SIZE.md} /> : <PanelLeft className={ICON_SIZE.md} />}
        </Button>
      </div>

      <Separator />

      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: MOTION.fade / 1000 }}
            className="px-3 pt-3 pb-2 space-y-2 shrink-0"
          >
            <Button
              onClick={handleNewChat}
              className="w-full justify-start gap-2 text-sm font-medium h-9"
              variant="secondary"
              size="sm"
            >
              <Plus className={cn(ICON_SIZE.md, "text-muted-foreground")} />
              New Chat
            </Button>
            <div className="relative">
              <Search className={cn("absolute left-2.5 top-1/2 -translate-y-1/2", ICON_SIZE.sm, "text-muted-foreground")} />
              <Input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search conversations..."
                className="pl-8 h-8 text-xs"
                aria-label="Search conversations"
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {!sidebarOpen && (
        <div className="flex flex-col items-center pt-3 pb-2 shrink-0">
          <Tooltip label="New Chat">
            <Button
              onClick={handleNewChat}
              variant="ghost"
              size="icon"
              className="h-9 w-9"
              aria-label="New Chat"
            >
              <Plus className={ICON_SIZE.md} />
            </Button>
          </Tooltip>
        </div>
      )}

      <nav className="flex-1 overflow-y-auto pb-4 scrollbar-thin" aria-label="Navigation">
        {sidebarOpen ? (
          <div className="px-2 space-y-0.5">
            {pinnedConvs.length > 0 && (
              <>
                <p className="px-2 pt-2 pb-1 text-overline">Pinned</p>
                {pinnedConvs.map((conv) => (
                  <ConversationItem
                    key={conv.id}
                    conv={conv}
                    isActive={activeConversationId === conv.id}
                    onSelect={() => handleSelectConv(conv.id)}
                    onRename={(title) => handleRename(conv.id, title)}
                    onDelete={() => handleDelete(conv.id)}
                    onTogglePin={() => handleTogglePin(conv.id, conv.pinned)}
                  />
                ))}
              </>
            )}
            {recentConvs.length > 0 && (
              <>
                {pinnedConvs.length > 0 && (
                  <p className="px-2 pt-3 pb-1 text-overline">Recent</p>
                )}
                {recentConvs.map((conv) => (
                  <ConversationItem
                    key={conv.id}
                    conv={conv}
                    isActive={activeConversationId === conv.id}
                    onSelect={() => handleSelectConv(conv.id)}
                    onRename={(title) => handleRename(conv.id, title)}
                    onDelete={() => handleDelete(conv.id)}
                    onTogglePin={() => handleTogglePin(conv.id, conv.pinned)}
                  />
                ))}
              </>
            )}
            {conversations.length === 0 && !searchQuery && (
              <div className="px-3 py-10 text-center">
                <MessagesSquare className={cn(ICON_SIZE.xl, "mx-auto mb-2 text-muted-foreground/40")} />
                <p className="text-caption">No conversations yet</p>
                <p className="text-caption opacity-60 mt-1">Start a new chat to begin</p>
              </div>
            )}
            {conversations.length === 0 && searchQuery && (
              <div className="px-3 py-8 text-center">
                <p className="text-caption">No matching conversations</p>
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center gap-1 pt-2 px-1.5">
            {NAV_ITEMS_FULL.map((navItem) => {
              const active = pathname === navItem.href || (navItem.href !== "/" && pathname.startsWith(navItem.href))
              return (
                <Tooltip key={navItem.href} label={navItem.label}>
                  <Link href={navItem.href} aria-label={navItem.label} aria-current={active ? "page" : undefined}>
                    <div
                      className={cn(
                        "flex items-center justify-center rounded-lg p-2 w-10 h-10 transition-all duration-200",
                        active
                          ? "bg-sidebar-accent border border-border"
                          : "text-muted-foreground hover:bg-sidebar-accent/60 hover:text-foreground"
                      )}
                    >
                      <navItem.Icon className={cn(ICON_SIZE.md, active ? navItem.accent : "text-muted-foreground")} />
                    </div>
                  </Link>
                </Tooltip>
              )
            })}
          </div>
        )}
      </nav>

      <Separator />

      <div className="shrink-0">
        {sidebarOpen ? (
          <div className="p-3">
            <div className="flex items-center gap-3 rounded-lg border border-border bg-muted/50 px-3 py-2">
              <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse shrink-0" />
              <div className="min-w-0 flex-1">
                <p className="text-caption font-medium">HearMe AI</p>
                <p className="text-caption opacity-60 truncate">Knowledge + Memory active</p>
              </div>
              <Sparkles className={cn(ICON_SIZE.sm, "text-muted-foreground shrink-0")} />
            </div>
          </div>
        ) : (
          <div className="flex justify-center p-3">
            <Tooltip label="AI Active">
              <div className="flex items-center justify-center h-9 w-9 rounded-lg border border-border bg-muted/50">
                <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" aria-label="AI active" />
              </div>
            </Tooltip>
          </div>
        )}
      </div>
    </motion.aside>
  )
}
