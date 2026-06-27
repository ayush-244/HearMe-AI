"use client"

import { useState } from "react"
import { useMutation } from "@tanstack/react-query"
import { api } from "@/services/api-client"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Brain, Search, FileText, Quote, Layers, Sparkles, BookOpen } from "lucide-react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import type { SearchResult } from "@/types"
import { motion } from "framer-motion"

export default function KnowledgePage() {
  const [searchQuery, setSearchQuery] = useState("")
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [hasSearched, setHasSearched] = useState(false)

  const searchMutation = useMutation({
    mutationFn: (q: string) => api.search({ text: q, top_k: 10 }),
    onSuccess: (data) => {
      setSearchResults(data.results)
      setHasSearched(true)
    },
  })

  const knowledgeMutation = useMutation({
    mutationFn: (q: string) => api.knowledgeQuery({ question: q, top_k: 5 }),
  })

  function handleSearch() {
    const q = searchQuery.trim()
    if (!q) return
    searchMutation.mutate(q)
  }

  return (
    <div className="p-6 lg:p-8 space-y-6">
      <div className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
          <Brain className="h-8 w-8 text-primary" />
          Knowledge Explorer
        </h1>
        <p className="text-muted-foreground">Search across indexed documents and explore knowledge chunks.</p>
      </div>

      <div className="flex gap-3 max-w-2xl">
        <Input
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search your knowledge base..."
          className="flex-1 h-11"
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
        />
        <Button onClick={handleSearch} disabled={!searchQuery.trim() || searchMutation.isPending} className="h-11">
          <Search className="h-4 w-4 mr-2" />
          Search
        </Button>
      </div>

      <Tabs defaultValue="results">
        <TabsList>
          <TabsTrigger value="results"><Search className="h-4 w-4 mr-2" />Search Results</TabsTrigger>
          <TabsTrigger value="reason"><Brain className="h-4 w-4 mr-2" />Reason</TabsTrigger>
        </TabsList>

        <TabsContent value="results" className="space-y-4 mt-4">
          {searchMutation.isPending && (
            <div className="text-center py-12 text-muted-foreground">
              <Sparkles className="h-8 w-8 mx-auto mb-2 animate-pulse" />
              <p>Searching knowledge base...</p>
            </div>
          )}

          {searchMutation.isError && (
            <Card className="border-destructive/50">
              <CardContent className="p-6 text-center text-destructive">
                Search failed. Please try again.
              </CardContent>
            </Card>
          )}

          {searchResults.length > 0 && !searchMutation.isPending && (
            <div className="space-y-3">
              <p className="text-sm text-muted-foreground">
                Found {searchResults.length} results
              </p>
              {searchResults.map((result, i) => (
                <motion.div
                  key={result.chunk_id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                >
                  <Card>
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2 min-w-0">
                          <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
                          <span className="font-medium text-sm truncate">{result.title || "Untitled"}</span>
                          {result.section && (
                            <Badge variant="secondary" className="text-xs shrink-0">{result.section}</Badge>
                          )}
                        </div>
                        <Badge variant={result.score > 0.7 ? "success" : result.score > 0.4 ? "warning" : "secondary"} className="shrink-0 ml-2">
                          {(result.score * 100).toFixed(0)}%
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground line-clamp-3">{result.text}</p>
                      <div className="flex items-center gap-2 mt-2 flex-wrap">
                        {result.page > 0 && <span className="text-xs text-muted-foreground">Page {result.page}</span>}
                        {result.keywords?.slice(0, 4).map((kw) => (
                          <Badge key={kw} variant="outline" className="text-xs">{kw}</Badge>
                        ))}
                        <span className="text-xs text-muted-foreground ml-auto">
                          S:{(result.semantic_score * 100).toFixed(0)}% K:{(result.keyword_score * 100).toFixed(0)}%
                        </span>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          )}

          {hasSearched && searchResults.length === 0 && !searchMutation.isPending && (
            <Card>
              <CardContent className="p-12 text-center text-muted-foreground">
                <BookOpen className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p className="font-medium">No results found</p>
                <p className="text-sm mt-1">Try a different search query or upload more documents.</p>
              </CardContent>
            </Card>
          )}

          {!hasSearched && (
            <Card>
              <CardContent className="p-12 text-center text-muted-foreground">
                <Layers className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p className="font-medium">Search your knowledge base</p>
                <p className="text-sm mt-1">Enter a query above to search across all indexed documents.</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="reason" className="space-y-4 mt-4">
          <KnowledgeReasonTab />
        </TabsContent>
      </Tabs>
    </div>
  )
}

function KnowledgeReasonTab() {
  const [question, setQuestion] = useState("")
  const [answer, setAnswer] = useState<string | null>(null)
  const [citations, setCitations] = useState<string[]>([])

  const mutation = useMutation({
    mutationFn: (q: string) => api.knowledgeQuery({ question: q, top_k: 5 }),
    onSuccess: (data) => {
      setAnswer(data.answer)
      setCitations(data.citations || [])
    },
  })

  return (
    <div className="space-y-4">
      <div className="flex gap-3 max-w-2xl">
        <Input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question to reason across your knowledge..."
          className="flex-1 h-11"
          onKeyDown={(e) => e.key === "Enter" && !mutation.isPending && mutation.mutate(question)}
        />
        <Button onClick={() => mutation.mutate(question)} disabled={!question.trim() || mutation.isPending} className="h-11">
          <Brain className="h-4 w-4 mr-2" />
          Reason
        </Button>
      </div>

      {mutation.isPending && (
        <Card>
          <CardContent className="p-6 text-center text-muted-foreground">
            <Sparkles className="h-8 w-8 mx-auto mb-2 animate-pulse" />
            <p>Reasoning across knowledge...</p>
          </CardContent>
        </Card>
      )}

      {answer && !mutation.isPending && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Brain className="h-5 w-5 text-primary" />
                Answer
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{answer}</ReactMarkdown>
              </div>

              {citations.length > 0 && (
                <div className="border-t pt-3">
                  <p className="text-sm font-medium mb-2 flex items-center gap-2">
                    <Quote className="h-4 w-4 text-muted-foreground" />
                    Citations
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {citations.map((c, i) => (
                      <Badge key={i} variant="secondary" className="text-xs">
                        {c.replace(/[\[\]]/g, "").length > 50
                          ? c.replace(/[\[\]]/g, "").slice(0, 50) + "…"
                          : c.replace(/[\[\]]/g, "")}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      )}
    </div>
  )
}
