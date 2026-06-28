"use client"

import { useState } from "react"
import { useMutation } from "@tanstack/react-query"
import { api } from "@/services/api-client"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Brain, Sparkles, FileText, BookOpen, Lightbulb, Send, ArrowRight } from "lucide-react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import rehypeHighlight from "rehype-highlight"
import { motion } from "framer-motion"
import type { Source } from "@/types"

const suggestionQuestions = [
  "What are my documents about?",
  "Summarize the key topics",
  "What insights can you find?",
  "Tell me something interesting",
]

export default function KnowledgePage() {
  const [question, setQuestion] = useState("")

  const mutation = useMutation({
    mutationFn: (q: string) => api.knowledgeQuery({ question: q, top_k: 5 }),
  })

  function handleAsk() {
    const q = question.trim()
    if (!q) return
    mutation.mutate(q)
  }

  const result = mutation.data
  const hasResult = result && !mutation.isPending
  const sources: Source[] = result?.sources ?? []

  return (
    <div className="p-6 lg:p-8 space-y-6">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
          <Brain className="h-8 w-8 text-primary" />
          Knowledge
        </h1>
        <p className="text-muted-foreground">Ask questions and get answers grounded in your documents.</p>
      </motion.div>

      <div className="relative">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask a question..."
              className="h-12 pr-4 text-base rounded-xl"
              onKeyDown={(e) => e.key === "Enter" && handleAsk()}
            />
          </div>
          <Button
            onClick={handleAsk}
            disabled={!question.trim() || mutation.isPending}
            className="h-12 px-6 rounded-xl gap-2"
          >
            {mutation.isPending ? (
              <Sparkles className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
            Ask
          </Button>
        </div>

        {!hasResult && !mutation.isPending && !mutation.isError && (
          <div className="flex flex-wrap gap-2 mt-4">
            {suggestionQuestions.map((q) => (
              <button
                key={q}
                onClick={() => setQuestion(q)}
                className="text-xs px-3 py-1.5 rounded-full bg-muted hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        )}
      </div>

      {mutation.isPending && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <Card className="border-0 shadow-sm bg-gradient-to-br from-primary/5 to-transparent">
            <CardContent className="p-8 text-center">
              <div className="inline-flex rounded-xl bg-primary/10 p-3 mb-4">
                <Sparkles className="h-6 w-6 text-primary animate-pulse" />
              </div>
              <p className="font-medium">Searching your knowledge...</p>
              <p className="text-sm text-muted-foreground mt-1">Analyzing documents and generating answer</p>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {mutation.isError && (
        <Card className="border-0 shadow-sm border-destructive/20 bg-destructive/5">
          <CardContent className="p-6 text-center">
            <p className="text-destructive font-medium">Failed to get answer</p>
            <p className="text-sm text-muted-foreground mt-1">Please try again or rephrase your question.</p>
          </CardContent>
        </Card>
      )}

      {hasResult && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          <Card className="border-0 shadow-md bg-gradient-to-br from-primary/5 to-transparent">
            <CardContent className="p-6">
              <div className="flex items-center gap-2 mb-4">
                <div className="rounded-lg bg-primary/10 p-2">
                  <Brain className="h-5 w-5 text-primary" />
                </div>
                <div>
                  <p className="font-semibold">Answer</p>
                  <p className="text-xs text-muted-foreground">Generated from your documents</p>
                </div>
              </div>
              <div className="prose prose-sm dark:prose-invert max-w-none prose-p:leading-relaxed">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  rehypePlugins={[rehypeHighlight]}
                >
                  {result.answer}
                </ReactMarkdown>
              </div>

              {result.citations && result.citations.length > 0 && (
                <div className="mt-6 pt-4 border-t">
                  <p className="text-sm font-medium mb-3 flex items-center gap-2">
                    <BookOpen className="h-4 w-4 text-muted-foreground" />
                    Sources
                  </p>
                  <div className="space-y-2">
                    {result.citations.map((c, i) => (
                      <div key={i} className="flex items-start gap-2 rounded-lg bg-muted/50 p-2.5">
                        <FileText className="h-4 w-4 text-muted-foreground shrink-0 mt-0.5" />
                        <span className="text-sm text-muted-foreground">{c.replace(/[\[\]]/g, "")}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {sources.length > 0 && (
            <Card className="border-0 shadow-sm">
              <CardContent className="p-6">
                <p className="text-sm font-medium mb-3 flex items-center gap-2">
                  <FileText className="h-4 w-4 text-muted-foreground" />
                  Related Documents
                </p>
                <div className="grid gap-2 sm:grid-cols-2">
                  {sources.map((source, i) => (
                    <div key={i} className="flex items-start gap-3 rounded-lg border p-3 hover:bg-accent/50 transition-colors">
                      <div className="rounded-lg bg-blue-500/10 p-2">
                        <FileText className="h-4 w-4 text-blue-500" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate">{source.title || "Untitled"}</p>
                        {source.sections && source.sections.length > 0 && (
                          <p className="text-xs text-muted-foreground mt-0.5">{source.sections.join(", ")}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          <div className="flex justify-center">
            <Button
              variant="outline"
              onClick={() => { setQuestion(""); mutation.reset() }}
              className="rounded-full gap-2"
            >
              <ArrowRight className="h-4 w-4" />
              Ask another question
            </Button>
          </div>
        </motion.div>
      )}

      {!hasResult && !mutation.isPending && !mutation.isError && (
        <Card className="border-0 shadow-sm bg-gradient-to-br from-muted/50 to-transparent">
          <CardContent className="p-12 text-center">
            <div className="inline-flex rounded-xl bg-primary/5 p-4 mb-4">
              <Lightbulb className="h-10 w-10 text-primary opacity-60" />
            </div>
            <p className="font-medium text-lg">Ask anything about your documents</p>
            <p className="text-sm text-muted-foreground mt-2 max-w-md mx-auto">
              I&apos;ll search your knowledge base and provide answers with sources.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
