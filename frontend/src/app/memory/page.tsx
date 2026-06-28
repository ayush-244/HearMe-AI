"use client"

import { useState, useMemo, useCallback } from "react"
import { useMemories, useSearchMemories, useDeleteMemory } from "@/hooks/use-memory"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Brain,
  Search,
  Trash2,
  Pin,
  Sparkles,
  Clock,
  Heart,
  Lightbulb,
  X,
  User,
  BookOpen,
  Award,
} from "lucide-react"
import { formatDate } from "@/lib/utils"
import { motion, AnimatePresence } from "framer-motion"
import { toast } from "@/components/ui/toast"
import { useDeveloperStore } from "@/stores/developer-store"

interface MemoryDisplay {
  memory_id: string
  type: string
  content: string
  summary: string
  created_at: string
  pinned: boolean
  importance?: number
  confidence?: number
}

const typeConfig: Record<string, { label: string; icon: React.ElementType; color: string; bg: string }> = {
  semantic: { label: "Fact", icon: BookOpen, color: "text-blue-500", bg: "bg-blue-500/10" },
  episodic: { label: "Experience", icon: Clock, color: "text-green-500", bg: "bg-green-500/10" },
  preference: { label: "Preference", icon: Heart, color: "text-purple-500", bg: "bg-purple-500/10" },
  working: { label: "Working", icon: Lightbulb, color: "text-amber-500", bg: "bg-amber-500/10" },
}

function MemoryCard({
  mem,
  onDelete,
  developerMode,
}: {
  mem: MemoryDisplay
  onDelete: (id: string) => void
  developerMode: boolean
}) {
  const [deleting, setDeleting] = useState(false)
  const config = typeConfig[mem.type] || typeConfig.semantic
  const Icon = config.icon

  const handleDelete = useCallback(async () => {
    setDeleting(true)
    try {
      await onDelete(mem.memory_id)
      toast({ title: "Memory deleted" })
    } catch {
      toast({ title: "Delete failed", variant: "destructive" })
    }
    setDeleting(false)
  }, [mem.memory_id, onDelete])

  const displayText = mem.summary || mem.content

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.2 }}
    >
      <Card className="group relative border-0 shadow-sm hover:shadow-md transition-all duration-200">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <div className={`rounded-xl p-2.5 ${config.bg} shrink-0`}>
              <Icon className={`h-4 w-4 ${config.color}`} />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 mb-1">
                <Badge variant="secondary" className={`${config.color} ${config.bg} border-0 text-[11px]`}>
                  {config.label}
                </Badge>
                {mem.pinned && <Pin className="h-3 w-3 text-amber-500" />}
              </div>
              <p className="text-sm leading-relaxed">{displayText}</p>
              <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {formatDate(mem.created_at)}
                </span>
                {developerMode && mem.importance !== undefined && (
                  <span className="text-[10px] text-muted-foreground/60">
                    Importance: {(mem.importance * 100).toFixed(0)}%
                  </span>
                )}
                {developerMode && mem.confidence !== undefined && (
                  <span className="text-[10px] text-muted-foreground/60">
                    Confidence: {(mem.confidence * 100).toFixed(0)}%
                  </span>
                )}
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
              onClick={handleDelete}
              disabled={deleting}
            >
              <Trash2 className="h-4 w-4 text-destructive/70 hover:text-destructive" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}

export default function MemoryPage() {
  const [query, setQuery] = useState("")
  const [searchResults, setSearchResults] = useState<{
    memories: MemoryDisplay[]
    count: number
  } | null>(null)
  const [isSearching, setIsSearching] = useState(false)

  const developerMode = useDeveloperStore((s) => s.developerMode)

  const { data, isLoading } = useMemories({ include_working: !developerMode })
  const searchMem = useSearchMemories()
  const deleteMem = useDeleteMemory()

  const memories = useMemo(
    () => searchResults?.memories ?? data?.memories ?? [],
    [searchResults, data]
  )

  const grouped = useMemo(() => {
    const groups: Record<string, MemoryDisplay[]> = {
      facts: [],
      preferences: [],
      experiences: [],
    }
    for (const m of memories) {
      if (m.type === "semantic") groups.facts.push(m)
      else if (m.type === "preference") groups.preferences.push(m)
      else if (m.type === "episodic") groups.experiences.push(m)
    }
    return groups
  }, [memories])

  async function handleSearch() {
    if (!query.trim()) {
      setSearchResults(null)
      return
    }
    setIsSearching(true)
    try {
      const result = await searchMem.mutateAsync({ query, top_k: 20 })
      setSearchResults(result as typeof searchResults)
    } catch {
      toast({ title: "Search failed", variant: "destructive" })
    }
    setIsSearching(false)
  }

  async function handleDelete(id: string) {
    await deleteMem.mutateAsync(id)
  }

  return (
    <div className="p-6 lg:p-8 space-y-6">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
          <User className="h-8 w-8 text-purple-500" />
          Things I Know About You
        </h1>
        <p className="text-muted-foreground">Facts, preferences, and experiences I&apos;ve learned from our conversations.</p>
      </motion.div>

      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search memories..."
            className="pl-9 h-10"
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          />
        </div>
        <Button variant="outline" onClick={handleSearch} disabled={isSearching} className="h-10">
          {isSearching ? <Sparkles className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
          Search
        </Button>
        {searchResults && (
          <Button variant="ghost" size="icon" className="h-10 w-10" onClick={() => { setSearchResults(null); setQuery("") }}>
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>

      {!searchResults && (
        <div className="grid gap-4 grid-cols-2 sm:grid-cols-4">
          {[
            { label: "All Memories", count: memories.length, icon: Brain, color: "text-purple-500", bg: "bg-purple-500/10" },
            { label: "Facts", count: grouped.facts.length, icon: BookOpen, color: "text-blue-500", bg: "bg-blue-500/10" },
            { label: "Preferences", count: grouped.preferences.length, icon: Heart, color: "text-pink-500", bg: "bg-pink-500/10" },
            { label: "Experiences", count: grouped.experiences.length, icon: Award, color: "text-amber-500", bg: "bg-amber-500/10" },
          ].map((stat) => (
            <Card key={stat.label} className="border-0 shadow-sm">
              <CardContent className="p-4 flex items-center gap-3">
                <div className={`rounded-xl p-2.5 ${stat.bg}`}>
                  <stat.icon className={`h-4 w-4 ${stat.color}`} />
                </div>
                <div>
                  <p className="text-xl font-bold">{stat.count}</p>
                  <p className="text-xs text-muted-foreground">{stat.label}</p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-28" />)}
        </div>
      ) : memories.length === 0 ? (
        <Card className="border-0 shadow-sm">
          <CardContent className="p-12 text-center text-muted-foreground">
            <User className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p className="font-medium text-lg">Nothing yet</p>
            <p className="text-sm mt-2 max-w-md mx-auto">
              Start chatting and I&apos;ll automatically remember facts, preferences, and experiences about you.
            </p>
            {query && (
              <p className="text-sm mt-2 text-muted-foreground">Try a different search term.</p>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-8">
          {grouped.facts.length > 0 && (
            <div className="space-y-3">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <BookOpen className="h-5 w-5 text-blue-500" />
                Facts
              </h2>
              <AnimatePresence mode="popLayout">
                <div className="grid gap-4 md:grid-cols-2">
                  {grouped.facts.map((mem) => (
                    <MemoryCard key={mem.memory_id} mem={mem} onDelete={handleDelete} developerMode={developerMode} />
                  ))}
                </div>
              </AnimatePresence>
            </div>
          )}

          {grouped.preferences.length > 0 && (
            <div className="space-y-3">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Heart className="h-5 w-5 text-purple-500" />
                Preferences
              </h2>
              <AnimatePresence mode="popLayout">
                <div className="grid gap-4 md:grid-cols-2">
                  {grouped.preferences.map((mem) => (
                    <MemoryCard key={mem.memory_id} mem={mem} onDelete={handleDelete} developerMode={developerMode} />
                  ))}
                </div>
              </AnimatePresence>
            </div>
          )}

          {grouped.experiences.length > 0 && (
            <div className="space-y-3">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Award className="h-5 w-5 text-amber-500" />
                Experiences
              </h2>
              <AnimatePresence mode="popLayout">
                <div className="grid gap-4 md:grid-cols-2">
                  {grouped.experiences.map((mem) => (
                    <MemoryCard key={mem.memory_id} mem={mem} onDelete={handleDelete} developerMode={developerMode} />
                  ))}
                </div>
              </AnimatePresence>
            </div>
          )}

          {searchResults && memories.filter((m) => m.type === "working").length > 0 && developerMode && (
            <div className="space-y-3">
              <h2 className="text-lg font-semibold flex items-center gap-2">
                <Lightbulb className="h-5 w-5 text-amber-500" />
                Working Memory
              </h2>
              <AnimatePresence mode="popLayout">
                <div className="grid gap-4 md:grid-cols-2">
                  {memories.filter((m) => m.type === "working").map((mem) => (
                    <MemoryCard key={mem.memory_id} mem={mem} onDelete={handleDelete} developerMode={developerMode} />
                  ))}
                </div>
              </AnimatePresence>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
