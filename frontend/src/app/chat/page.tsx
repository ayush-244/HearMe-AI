"use client"

import { useState, useRef, useEffect } from "react"
import { useMutation } from "@tanstack/react-query"
import { api } from "@/services/api-client"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import {
  MessageSquare,
  Send,
  Sparkles,
  Copy,
  Check,
  RefreshCw,
  Brain,
  Quote,
  User,
  StopCircle,
} from "lucide-react"
import type { ChatMessage } from "@/types"
import { motion, AnimatePresence } from "framer-motion"

function ThinkingDots() {
  return (
    <div className="flex items-center gap-1.5 py-2">
      {[0, 1, 2].map((i) => (
        <motion.div
          key={i}
          className="h-2 w-2 rounded-full bg-primary/60"
          animate={{ opacity: [0.3, 1, 0.3] }}
          transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.2 }}
        />
      ))}
    </div>
  )
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "welcome",
      role: "assistant",
      content: "Hello! I'm **HearMe AI**. I can answer questions using your uploaded documents and remember information about you across conversations. How can I help today?",
      timestamp: new Date().toISOString(),
    },
  ])
  const [input, setInput] = useState("")
  const [isStreaming, setIsStreaming] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" })
    }
  }, [messages])

  const chatMutation = useMutation({
    mutationFn: async (text: string) => {
      setIsStreaming(true)
      const result = await api.sendMessage(text, "auto", messages)
      return result
    },
    onSuccess: (result) => {
      setMessages((prev) => [
        ...prev,
        {
          id: Math.random().toString(36).slice(2),
          role: "assistant",
          content: result.reply,
          timestamp: new Date().toISOString(),
        },
      ])
      setIsStreaming(false)
    },
    onError: () => {
      setMessages((prev) => [
        ...prev,
        {
          id: Math.random().toString(36).slice(2),
          role: "assistant",
          content: "I encountered an error processing your message. Please try again.",
          timestamp: new Date().toISOString(),
        },
      ])
      setIsStreaming(false)
    },
  })

  const knowledgeMutation = useMutation({
    mutationFn: async (text: string) => {
      return api.knowledgeQuery({ question: text, top_k: 5 })
    },
    onSuccess: (result) => {
      setMessages((prev) => [
        ...prev,
        {
          id: Math.random().toString(36).slice(2),
          role: "assistant",
          content: result.knowledge_gap
            ? result.answer
            : `${result.answer}\n\n${result.citations?.length ? "**Sources:**\n" + result.citations.map((c) => `- ${c.replace(/\[([^\]]+)\]/g, "*$1*")}`).join("\n") : ""}`,
          citations: result.citations,
          sources: result.sources,
          timestamp: new Date().toISOString(),
        },
      ])
      setIsStreaming(false)
    },
    onError: () => {
      setIsStreaming(false)
    },
  })

  function handleSend() {
    const text = input.trim()
    if (!text || isStreaming) return
    setInput("")
    setMessages((prev) => [
      ...prev,
      { id: Math.random().toString(36).slice(2), role: "user", content: text, timestamp: new Date().toISOString() },
    ])
    chatMutation.mutate(text)
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  function copyMessage(content: string) {
    navigator.clipboard.writeText(content)
  }

  function regenerate() {
    const lastUser = [...messages].reverse().find((m) => m.role === "user")
    if (lastUser) {
      setMessages((prev) => prev.slice(0, -1))
      setIsStreaming(true)
      chatMutation.mutate(lastUser.content)
    }
  }

  const suggestedPrompts = ["What can I ask you?", "Upload a document for me", "Tell me about my memories", "How does the knowledge system work?"]

  return (
    <div className="flex h-[calc(100vh-3.5rem)] flex-col">
      <ScrollArea ref={scrollRef} className="flex-1 px-4 lg:px-8">
        <div className="mx-auto max-w-3xl py-6 space-y-6">
          {messages.length === 1 && (
            <div className="text-center py-8 space-y-4">
              <Sparkles className="h-12 w-12 mx-auto text-primary" />
              <h2 className="text-2xl font-bold">How can I help you?</h2>
              <p className="text-muted-foreground">Ask me anything — I can search your documents, remember facts about you, and reason across knowledge.</p>
              <div className="flex flex-wrap justify-center gap-2 mt-4">
                {suggestedPrompts.map((p) => (
                  <Button key={p} variant="outline" size="sm" onClick={() => { setInput(p) }} className="text-xs">
                    {p}
                  </Button>
                ))}
              </div>
            </div>
          )}

          <AnimatePresence>
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                {msg.role === "assistant" && (
                  <Avatar className="h-8 w-8 mt-0.5">
                    <AvatarFallback className="bg-primary/10 text-primary"><Sparkles className="h-4 w-4" /></AvatarFallback>
                  </Avatar>
                )}

                <div className={`max-w-[80%] ${msg.role === "user" ? "order-first" : ""}`}>
                  {msg.role === "user" ? (
                    <div className="rounded-2xl bg-primary text-primary-foreground px-4 py-2.5">
                      <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                    </div>
                  ) : (
                    <Card className="border-0 shadow-none bg-muted/30">
                      <CardContent className="p-4">
                        <div className="prose prose-sm dark:prose-invert max-w-none">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                        </div>

                        {msg.citations && msg.citations.length > 0 && (
                          <div className="mt-3 flex flex-wrap gap-1.5">
                            {msg.citations.map((c, i) => (
                              <Badge key={i} variant="secondary" className="text-xs gap-1">
                                <Quote className="h-3 w-3" />
                                {c.replace(/[\[\]]/g, "").length > 40 ? c.replace(/[\[\]]/g, "").slice(0, 40) + "…" : c.replace(/[\[\]]/g, "")}
                              </Badge>
                            ))}
                          </div>
                        )}

                        <div className="flex items-center gap-2 mt-3 pt-2 border-t">
                          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => copyMessage(msg.content)}>
                            <Copy className="h-3.5 w-3.5" />
                          </Button>
                          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={regenerate}>
                            <RefreshCw className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </div>

                {msg.role === "user" && (
                  <Avatar className="h-8 w-8 mt-0.5">
                    <AvatarFallback className="bg-muted"><User className="h-4 w-4" /></AvatarFallback>
                  </Avatar>
                )}
              </motion.div>
            ))}
          </AnimatePresence>

          {isStreaming && (
            <div className="flex gap-3">
              <Avatar className="h-8 w-8">
                <AvatarFallback className="bg-primary/10 text-primary"><Sparkles className="h-4 w-4" /></AvatarFallback>
              </Avatar>
              <div className="rounded-2xl bg-muted/30 px-4 py-2.5">
                <ThinkingDots />
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      <div className="border-t bg-background p-4 lg:px-8">
        <div className="mx-auto max-w-3xl flex gap-3">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything..."
            className="flex-1 h-12 text-base"
            disabled={isStreaming}
          />
          <Button onClick={handleSend} disabled={!input.trim() || isStreaming} size="icon" className="h-12 w-12 shrink-0">
            {isStreaming ? <StopCircle className="h-5 w-5" /> : <Send className="h-5 w-5" />}
          </Button>
        </div>
        <p className="text-xs text-muted-foreground text-center mt-2">
          Responses are grounded in your documents and personal memory
        </p>
      </div>
    </div>
  )
}
