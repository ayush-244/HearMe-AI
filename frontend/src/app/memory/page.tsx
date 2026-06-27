"use client"

import { useState } from "react"
import { useMemories, useSearchMemories, useDeleteMemory, useConsolidateMemories } from "@/hooks/use-memory"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Database, Search, Trash2, Merge, Pin, Sparkles, Brain, Clock, ArrowUp } from "lucide-react"
import { MEMORY_TYPE_COLORS, MEMORY_TYPE_LABELS } from "@/lib/constants"
import { formatDate } from "@/lib/utils"
import { motion } from "framer-motion"
import { toast } from "@/components/ui/toast"

export default function MemoryPage() {
  const [query, setQuery] = useState("")
  const [filterType, setFilterType] = useState<string | undefined>(undefined)
  const { data, isLoading } = useMemories({ memory_type: filterType, include_working: true })
  const searchMem = useSearchMemories()
  const deleteMem = useDeleteMemory()
  const consolidate = useConsolidateMemories()
  const [searchResults, setSearchResults] = useState<{ memories: { memory_id: string; user_id: string; workspace_id: string; type: string; content: string; summary: string; importance: number; confidence: number; created_at: string; updated_at: string; last_accessed: string; access_count: number; source: string; pinned: boolean }[]; count: number } | null>(null)
  const [isSearching, setIsSearching] = useState(false)

  const memories = searchResults?.memories ?? data?.memories ?? []
  const count = searchResults?.count ?? data?.count ?? 0

  async function handleSearch() {
    if (!query.trim()) {
      setSearchResults(null)
      return
    }
    setIsSearching(true)
    const result = await searchMem.mutateAsync({ query, top_k: 20 })
    setSearchResults(result)
    setIsSearching(false)
  }

  async function handleDelete(id: string) {
    await deleteMem.mutateAsync(id)
    toast({ title: "Memory deleted", variant: "default" })
  }

  async function handleConsolidate() {
    const result = await consolidate.mutateAsync({})
    toast({ title: `Consolidated ${result.consolidated_count} memories`, variant: "success" })
  }

  const typeFilters = [
    { label: "All", value: undefined },
    { label: "Semantic", value: "semantic" },
    { label: "Episodic", value: "episodic" },
    { label: "Preferences", value: "preference" },
    { label: "Working", value: "working" },
  ]

  return (
    <div className="p-6 lg:p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <Database className="h-8 w-8 text-purple-500" />
            Personal Memory
          </h1>
          <p className="text-muted-foreground">Facts, events, and preferences remembered about you across conversations.</p>
        </div>
        <Button variant="outline" onClick={handleConsolidate} disabled={consolidate.isPending}>
          <Merge className="h-4 w-4 mr-2" />
          Consolidate
        </Button>
      </div>

      <div className="flex gap-3 max-w-2xl">
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search memories..."
          className="flex-1 h-11"
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
        />
        <Button onClick={handleSearch} disabled={isSearching} className="h-11">
          <Search className="h-4 w-4 mr-2" />
          Search
        </Button>
      </div>

      <div className="flex gap-2 flex-wrap">
        {typeFilters.map(({ label, value }) => (
          <Button
            key={label}
                  variant={filterType === value ? "default" : "outline"}
                  size="sm"
                  onClick={() => { setFilterType(value); setSearchResults(null) }}
          >
            {label}
          </Button>
        ))}
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-32" />)}
        </div>
      ) : memories.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center text-muted-foreground">
            <Brain className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p className="font-medium">No memories yet</p>
            <p className="text-sm mt-1">Memories are created automatically from conversations. Start chatting to build your memory profile.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {memories.map((mem, i) => (
            <motion.div key={mem.memory_id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.03 }}>
              <Card className="relative">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Badge className={`${MEMORY_TYPE_COLORS[mem.type] || ""}`} variant="secondary">
                        {MEMORY_TYPE_LABELS[mem.type] || mem.type}
                      </Badge>
                      {mem.pinned && <Pin className="h-3.5 w-3.5 text-amber-500" />}
                    </div>
                    <div className="flex items-center gap-1">
                      {mem.importance > 0.7 && <ArrowUp className="h-3.5 w-3.5 text-emerald-500" />}
                      <span className="text-xs text-muted-foreground">
                        {(mem.importance * 100).toFixed(0)}%
                      </span>
                      <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => handleDelete(mem.memory_id)}>
                        <Trash2 className="h-3.5 w-3.5 text-muted-foreground hover:text-destructive" />
                      </Button>
                    </div>
                  </div>
                  <p className="text-sm">{mem.content}</p>
                  <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {formatDate(mem.created_at)}
                    </span>
                    <span>Accessed {mem.access_count} times</span>
                    <span>C:{(mem.confidence * 100).toFixed(0)}%</span>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      )}

      {count > 0 && (
        <p className="text-sm text-muted-foreground text-center">
          {count} memory{count !== 1 ? "ies" : "y"} stored
        </p>
      )}
    </div>
  )
}
