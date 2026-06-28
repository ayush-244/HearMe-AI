"use client"

import { useState, useCallback } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { useConversations, useCreateConversation, useDeleteConversation, useUpdateConversation } from "@/hooks/use-conversations"
import { useUiStore } from "@/store/ui-store"
import { cn } from "@/lib/utils"
import { NAV_ITEMS } from "@/lib/constants"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { motion } from "framer-motion"
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

const iconMap: Record<string, React.ElementType> = {
  LayoutDashboard,
  MessageSquare,
  FileText,
  Brain,
  Database,
  Settings,
  MessagesSquare,
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
      <div className="flex items-center gap-1 px-3 py-1.5">
        <input
          value={editTitle}
          onChange={(e) => setEditTitle(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") handleRename(); if (e.key === "Escape") setEditing(false) }}
          className="flex-1 text-sm bg-muted rounded px-2 py-1 outline-none focus:ring-1 focus:ring-primary"
          autoFocus
          onBlur={handleRename}
        />
        <Button variant="ghost" size="icon" className="h-6 w-6" onClick={handleRename}>
          <Check className="h-3 w-3" />
        </Button>
        <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => setEditing(false)}>
          <X className="h-3 w-3" />
        </Button>
      </div>
    )
  }

  return (
    <div
      className={cn(
        "group relative flex items-center gap-2 rounded-lg px-3 py-2 text-sm cursor-pointer transition-colors",
        isActive ? "bg-primary/10 text-primary font-medium" : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
      )}
      onClick={onSelect}
    >
      {conv.pinned && <Pin className="h-3 w-3 shrink-0 text-amber-500" />}
      <span className="flex-1 truncate">{conv.title}</span>
      <span className="text-[10px] text-muted-foreground/50 shrink-0 hidden group-hover:block">
        <div className="relative">
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            onClick={(e) => { e.stopPropagation(); setShowMenu(!showMenu) }}
          >
            <MoreHorizontal className="h-3.5 w-3.5" />
          </Button>
          {showMenu && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setShowMenu(false)} />
              <div className="absolute right-0 top-full z-50 mt-1 w-40 rounded-lg border bg-popover p-1 shadow-md">
                <button
                  className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-xs hover:bg-accent"
                  onClick={(e) => { e.stopPropagation(); setEditing(true); setShowMenu(false) }}
                >
                  <Pencil className="h-3.5 w-3.5" /> Rename
                </button>
                <button
                  className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-xs hover:bg-accent"
                  onClick={(e) => { e.stopPropagation(); onTogglePin(); setShowMenu(false) }}
                >
                  <Pin className="h-3.5 w-3.5" /> {conv.pinned ? "Unpin" : "Pin"}
                </button>
                <Separator className="my-1" />
                <button
                  className="flex w-full items-center gap-2 rounded px-2 py-1.5 text-xs text-destructive hover:bg-destructive/10"
                  onClick={(e) => { e.stopPropagation(); onDelete(); setShowMenu(false) }}
                >
                  <Trash2 className="h-3.5 w-3.5" /> Delete
                </button>
              </div>
            </>
          )}
        </div>
      </span>
      <span className="text-[10px] text-muted-foreground/50 shrink-0 group-hover:hidden">
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
      animate={{ width: sidebarOpen ? 300 : 64 }}
      className="fixed left-0 top-0 z-40 h-screen border-r bg-background flex flex-col"
      transition={{ duration: 0.2, ease: "easeInOut" }}
    >
      <div className={cn("flex items-center h-14 px-3", sidebarOpen ? "justify-between" : "justify-center")}>
        {sidebarOpen && (
          <Link href="/" className="flex items-center gap-2 font-semibold text-base">
            <Sparkles className="h-5 w-5 text-primary" />
            <span>HearMe AI</span>
          </Link>
        )}
        <Button variant="ghost" size="icon" onClick={toggleSidebar} className="shrink-0">
          {sidebarOpen ? <PanelLeftClose className="h-4 w-4" /> : <PanelLeft className="h-4 w-4" />}
        </Button>
      </div>

      {sidebarOpen && (
        <>
          <div className="px-3 pb-2">
            <Button onClick={handleNewChat} className="w-full justify-start gap-2 rounded-lg" variant="outline" size="sm">
              <Plus className="h-4 w-4" />
              New Chat
            </Button>
          </div>

          <div className="px-3 pb-2">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
              <input
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search conversations..."
                className="w-full rounded-lg border bg-muted/50 pl-8 pr-3 py-1.5 text-xs placeholder:text-muted-foreground/60 outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
          </div>
        </>
      )}

      <nav className="flex-1 overflow-y-auto px-2 pb-4 space-y-0.5">
        {sidebarOpen ? (
          <>
            {pinnedConvs.length > 0 && (
              <>
                <p className="px-2 py-1 text-[10px] font-medium text-muted-foreground/60 uppercase tracking-wider">Pinned</p>
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
                  <p className="px-2 py-1 text-[10px] font-medium text-muted-foreground/60 uppercase tracking-wider pt-2">Recent</p>
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
              <div className="px-3 py-8 text-center">
                <MessagesSquare className="h-8 w-8 mx-auto mb-2 text-muted-foreground/30" />
                <p className="text-xs text-muted-foreground/50">No conversations yet</p>
              </div>
            )}
            {conversations.length === 0 && searchQuery && (
              <div className="px-3 py-8 text-center">
                <p className="text-xs text-muted-foreground/50">No matching conversations</p>
              </div>
            )}
          </>
        ) : (
          <div className="flex flex-col items-center gap-1 py-2">
            {NAV_ITEMS.map((item) => {
              const Icon = iconMap[item.icon] || MessageSquare
              const active = pathname === item.href || (item.href !== "/" && pathname.startsWith(item.href))
              return (
                <Link key={item.href} href={item.href}>
                  <div
                    className={cn(
                      "flex items-center justify-center rounded-lg p-2 transition-colors",
                      active ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                    )}
                    title={item.label}
                  >
                    <Icon className="h-5 w-5" />
                  </div>
                </Link>
              )
            })}
          </div>
        )}
      </nav>

      {sidebarOpen && (
        <>
          <Separator />
          <div className="p-3">
            <div className="flex items-center gap-2 rounded-lg bg-muted/50 p-2.5">
              <Sparkles className="h-4 w-4 text-primary shrink-0" />
              <div className="min-w-0 flex-1">
                <p className="text-xs font-medium">HearMe AI</p>
                <p className="text-[10px] text-muted-foreground/60 truncate">Knowledge + Memory active</p>
              </div>
            </div>
          </div>
        </>
      )}
    </motion.aside>
  )
}
