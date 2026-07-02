"use client"

import { useState, useCallback } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { useConversations, useCreateConversation, useDeleteConversation, useUpdateConversation } from "@/hooks/use-conversations"
import { useUiStore } from "@/store/ui-store"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { motion, AnimatePresence } from "framer-motion"
import {
  MessageSquare,
  FileText,
  Brain,
  Database,
  Settings,
  LayoutDashboard,
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

const NAV_ITEMS_FULL = [
  { label: "Chat", href: "/chat", Icon: MessageSquare, color: "text-blue-400" },
  { label: "Library", href: "/library", Icon: FileText, color: "text-emerald-400" },
  { label: "Knowledge", href: "/knowledge", Icon: Brain, color: "text-amber-400" },
  { label: "Memory", href: "/memory", Icon: Database, color: "text-cyan-400" },
  { label: "Settings", href: "/settings", Icon: Settings, color: "text-zinc-400" },
]

function Tooltip({ children, label }: { children: React.ReactNode; label: string }) {
  return (
    <div className="relative group/tooltip">
      {children}
      <div className="pointer-events-none absolute left-full ml-2.5 top-1/2 -translate-y-1/2 z-50 whitespace-nowrap rounded-md bg-zinc-900 border border-zinc-800 px-2.5 py-1.5 text-xs font-medium text-zinc-100 opacity-0 group-hover/tooltip:opacity-100 transition-opacity duration-150 shadow-xl">
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
        <input
          value={editTitle}
          onChange={(e) => setEditTitle(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") handleRename(); if (e.key === "Escape") setEditing(false) }}
          className="flex-1 text-sm bg-zinc-800 rounded px-2 py-1 outline-none focus:ring-1 focus:ring-blue-500 text-zinc-100"
          autoFocus
          onBlur={handleRename}
        />
        <Button variant="ghost" size="icon" className="h-6 w-6 text-zinc-400 hover:text-zinc-100" onClick={handleRename}>
          <Check className="h-3 w-3" />
        </Button>
        <Button variant="ghost" size="icon" className="h-6 w-6 text-zinc-400 hover:text-zinc-100" onClick={() => setEditing(false)}>
          <X className="h-3 w-3" />
        </Button>
      </div>
    )
  }

  return (
    <div
      className={cn(
        "group relative flex items-center gap-2 rounded-lg px-2.5 py-2 text-sm cursor-pointer transition-all duration-150",
        isActive
          ? "bg-zinc-800 text-zinc-100 border-l-2 border-blue-500 pl-2"
          : "text-zinc-400 hover:bg-zinc-800/60 hover:text-zinc-200 border-l-2 border-transparent"
      )}
      onClick={onSelect}
    >
      <MessageSquare className={cn("h-3.5 w-3.5 shrink-0", isActive ? "text-blue-400" : "text-zinc-500")} />
      {conv.pinned && <Pin className="h-2.5 w-2.5 shrink-0 text-amber-400" />}
      <span className="flex-1 truncate text-xs">{conv.title}</span>

      {/* Hover actions */}
      <span className="hidden group-hover:flex items-center gap-0.5 shrink-0">
        <div className="relative">
          <Button
            variant="ghost"
            size="icon"
            className="h-5 w-5 text-zinc-500 hover:text-zinc-300"
            onClick={(e) => { e.stopPropagation(); setShowMenu(!showMenu) }}
          >
            <MoreHorizontal className="h-3 w-3" />
          </Button>
          {showMenu && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setShowMenu(false)} />
              <div className="absolute right-0 top-full z-50 mt-1 w-40 rounded-lg border border-zinc-800 bg-zinc-900 p-1 shadow-xl">
                <button
                  className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-xs text-zinc-300 hover:bg-zinc-800 transition-colors"
                  onClick={(e) => { e.stopPropagation(); setEditing(true); setShowMenu(false) }}
                >
                  <Pencil className="h-3 w-3" /> Rename
                </button>
                <button
                  className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-xs text-zinc-300 hover:bg-zinc-800 transition-colors"
                  onClick={(e) => { e.stopPropagation(); onTogglePin(); setShowMenu(false) }}
                >
                  <Pin className="h-3 w-3" /> {conv.pinned ? "Unpin" : "Pin"}
                </button>
                <Separator className="my-1 bg-zinc-800" />
                <button
                  className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-xs text-red-400 hover:bg-red-500/10 transition-colors"
                  onClick={(e) => { e.stopPropagation(); onDelete(); setShowMenu(false) }}
                >
                  <Trash2 className="h-3 w-3" /> Delete
                </button>
              </div>
            </>
          )}
        </div>
      </span>
      <span className={cn("text-[10px] text-zinc-600 shrink-0", "group-hover:hidden")}>
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
      animate={{ width: sidebarOpen ? 280 : 60 }}
      className="fixed left-0 top-0 z-40 h-screen border-r border-zinc-800/80 bg-zinc-950 flex flex-col"
      transition={{ duration: 0.25, ease: "easeInOut" }}
    >
      {/* Header */}
      <div className={cn("flex items-center h-14 px-3 shrink-0", sidebarOpen ? "justify-between" : "justify-center")}>
        <AnimatePresence mode="wait">
          {sidebarOpen && (
            <motion.div
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.15 }}
            >
              <Link href="/" className="flex items-center gap-2 font-semibold text-sm text-zinc-100">
                <Sparkles className="h-4 w-4 text-blue-400" />
                <span>HearMe AI</span>
              </Link>
            </motion.div>
          )}
        </AnimatePresence>
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleSidebar}
          className="shrink-0 h-8 w-8 text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800"
          aria-label={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
        >
          {sidebarOpen ? <PanelLeftClose className="h-4 w-4" /> : <PanelLeft className="h-4 w-4" />}
        </Button>
      </div>

      <div className="border-t border-zinc-800/80 shrink-0" />

      {/* Expanded: New chat + search */}
      <AnimatePresence>
        {sidebarOpen && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={{ duration: 0.15 }}
            className="px-3 pt-3 pb-2 space-y-2 shrink-0"
          >
            <Button
              onClick={handleNewChat}
              className="w-full justify-start gap-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-100 border-0 text-sm font-medium h-9"
              variant="outline"
              size="sm"
            >
              <Plus className="h-4 w-4 text-zinc-400" />
              New Chat
            </Button>
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-zinc-500" />
              <input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search conversations..."
                className="w-full rounded-lg border border-zinc-800 bg-zinc-900 pl-8 pr-3 py-1.5 text-xs placeholder:text-zinc-600 text-zinc-300 outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500/50 transition-colors"
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Collapsed: New chat button */}
      {!sidebarOpen && (
        <div className="flex flex-col items-center pt-3 pb-2 shrink-0">
          <Tooltip label="New Chat">
            <Button
              onClick={handleNewChat}
              variant="ghost"
              size="icon"
              className="h-9 w-9 rounded-lg text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800"
              aria-label="New Chat"
            >
              <Plus className="h-4 w-4" />
            </Button>
          </Tooltip>
        </div>
      )}

      {/* Navigation / Conversation list */}
      <nav className="flex-1 overflow-y-auto pb-4 scrollbar-thin" aria-label="Navigation">
        {sidebarOpen ? (
          <div className="px-2 space-y-0.5">
            {pinnedConvs.length > 0 && (
              <>
                <p className="px-2 pt-2 pb-1 text-[10px] font-semibold text-zinc-600 uppercase tracking-widest">Pinned</p>
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
                  <p className="px-2 pt-3 pb-1 text-[10px] font-semibold text-zinc-600 uppercase tracking-widest">Recent</p>
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
                <MessagesSquare className="h-8 w-8 mx-auto mb-2 text-zinc-700" />
                <p className="text-xs text-zinc-600">No conversations yet</p>
                <p className="text-[10px] text-zinc-700 mt-0.5">Start a new chat to begin</p>
              </div>
            )}
            {conversations.length === 0 && searchQuery && (
              <div className="px-3 py-8 text-center">
                <p className="text-xs text-zinc-600">No matching conversations</p>
              </div>
            )}
          </div>
        ) : (
          /* Collapsed: icon nav */
          <div className="flex flex-col items-center gap-1 pt-2 px-1.5">
            {NAV_ITEMS_FULL.map((navItem) => {
              const active = pathname === navItem.href || (navItem.href !== "/" && pathname.startsWith(navItem.href))
              return (
                <Tooltip key={navItem.href} label={navItem.label}>
                  <Link href={navItem.href} aria-label={navItem.label}>
                    <motion.div
                      whileHover={{ scale: 1.08 }}
                      whileTap={{ scale: 0.96 }}
                      className={cn(
                        "flex items-center justify-center rounded-lg p-2.5 w-10 h-10 transition-all duration-150",
                        active
                          ? `bg-zinc-800 border border-zinc-700 ${navItem.color}`
                          : "text-zinc-600 hover:bg-zinc-800/60 hover:text-zinc-300"
                      )}
                    >
                      <navItem.Icon className="h-4.5 w-4.5" />
                    </motion.div>
                  </Link>
                </Tooltip>
              )
            })}
          </div>
        )}
      </nav>

      {/* Footer */}
      <div className="border-t border-zinc-800/80 shrink-0">
        {sidebarOpen ? (
          <div className="p-3">
            <div className="flex items-center gap-2.5 rounded-lg bg-zinc-900 border border-zinc-800 px-3 py-2.5">
              <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse shrink-0" />
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium text-zinc-300">HearMe AI</p>
                <p className="text-[10px] text-zinc-600 truncate">Knowledge + Memory active</p>
              </div>
              <Sparkles className="h-3.5 w-3.5 text-zinc-600 shrink-0" />
            </div>
          </div>
        ) : (
          <div className="flex justify-center p-3">
            <Tooltip label="AI Active">
              <div className="flex items-center justify-center h-9 w-9 rounded-lg bg-zinc-900 border border-zinc-800">
                <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
              </div>
            </Tooltip>
          </div>
        )}
      </div>
    </motion.aside>
  )
}
