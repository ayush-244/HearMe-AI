"use client"

import { useState, useRef, useEffect, useCallback, memo } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/services/api-client"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import rehypeHighlight from "rehype-highlight"
import {
  Send,
  Sparkles,
  Copy,
  Check,
  RefreshCw,
  User,
  StopCircle,
  Lightbulb,
} from "lucide-react"
import type { ChatMessage } from "@/types"
import { motion, AnimatePresence } from "framer-motion"

const ThinkingDots = memo(function ThinkingDots() {
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
})

const suggestedFollowUps = [
  "Tell me more about that",
  "Can you summarize this?",
  "What are the key insights?",
  "How does this relate to my other documents?",
]

interface MessageBubbleProps {
  msg: ChatMessage
  onCopy: (content: string) => void
  onRegenerate: () => void
  onFollowUp: (text: string) => void
}

const MessageBubble = memo(function MessageBubble({ msg, onCopy, onRegenerate, onFollowUp }: MessageBubbleProps) {
  const [copied, setCopied] = useState(false)

  const handleCopy = useCallback(() => {
    onCopy(msg.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }, [msg.content, onCopy])

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
    >
      {msg.role === "assistant" && (
        <Avatar className="h-8 w-8 mt-0.5 ring-2 ring-primary/20">
          <AvatarFallback className="bg-gradient-to-br from-primary to-primary/60 text-primary-foreground">
            <Sparkles className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
      )}

      <div className={`max-w-[80%] ${msg.role === "user" ? "order-first" : ""} space-y-1`}>
        {msg.role === "user" ? (
          <div className="rounded-2xl bg-primary text-primary-foreground px-4 py-3 shadow-sm">
            <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
          </div>
        ) : (
          <div className="rounded-2xl bg-muted/50 border px-4 py-3 shadow-sm">
            <div className="prose prose-sm dark:prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-muted prose-code:text-primary">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeHighlight]}
              >
                {msg.content}
              </ReactMarkdown>
            </div>

            {msg.citations && msg.citations.length > 0 && (
              <div className="mt-3 pt-3 border-t">
                <p className="text-xs font-medium text-muted-foreground mb-2">Sources</p>
                <div className="flex flex-wrap gap-1.5">
                  {msg.citations.map((c, i) => (
                    <Badge key={i} variant="secondary" className="text-[11px] gap-1 max-w-[200px]">
                      <span className="truncate">{c.replace(/[\[\]]/g, "")}</span>
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            <div className="flex items-center gap-1 mt-3 pt-2 border-t border-border/50">
              <Button variant="ghost" size="icon" className="h-7 w-7 hover:bg-muted" onClick={handleCopy} title="Copy response">
                {copied ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
              </Button>
              <Button variant="ghost" size="icon" className="h-7 w-7 hover:bg-muted" onClick={onRegenerate} title="Regenerate">
                <RefreshCw className="h-3.5 w-3.5" />
              </Button>
            </div>

            {msg.role === "assistant" && msg.id !== "welcome" && (
              <div className="mt-3 pt-2 border-t border-border/50">
                <p className="text-xs font-medium text-muted-foreground mb-2 flex items-center gap-1">
                  <Lightbulb className="h-3 w-3" /> Follow up
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {suggestedFollowUps.map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() => onFollowUp(suggestion)}
                      className="text-xs px-2.5 py-1 rounded-full bg-muted hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {msg.role === "user" && (
        <Avatar className="h-8 w-8 mt-0.5 ring-2 ring-muted">
          <AvatarFallback className="bg-muted">
            <User className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
      )}
    </motion.div>
  )
})

export default function ChatPage() {
  const queryClient = useQueryClient()
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
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      const el = scrollRef.current
      requestAnimationFrame(() => {
        el.scrollTo({ top: el.scrollHeight, behavior: "smooth" })
      })
    }
  }, [messages, isStreaming])

  const chatMutation = useMutation({
    mutationFn: async (text: string) => {
      setIsStreaming(true)
      return api.sendMessage(text, "auto", messages)
    },
    onSuccess: (result, variables) => {
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
      api.extractMemory({ user_text: variables }).then(() => queryClient.invalidateQueries({ queryKey: ["memories"] })).catch(() => {})
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
          content: result.answer,
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

  const copyMessage = useCallback((content: string) => {
    navigator.clipboard.writeText(content)
  }, [])

  function regenerate() {
    const lastUser = [...messages].reverse().find((m) => m.role === "user")
    if (lastUser) {
      setMessages((prev) => prev.slice(0, -1))
      setIsStreaming(true)
      chatMutation.mutate(lastUser.content)
    }
  }

  function handleFollowUp(text: string) {
    setInput(text)
    inputRef.current?.focus()
  }

  const suggestedPrompts = [
    "What can I ask you?",
    "Upload a document for me",
    "Tell me about my memories",
    "How does the knowledge system work?",
  ]

  const hasMessages = messages.length > 1

  return (
    <div className="flex h-[calc(100vh-3.5rem)] flex-col">
      <ScrollArea ref={scrollRef} className="flex-1 px-4 lg:px-8">
        <div className="mx-auto max-w-3xl py-6 space-y-6">
          {messages.length === 1 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center py-12 space-y-6"
            >
              <div className="inline-flex rounded-2xl bg-gradient-to-br from-primary/10 to-primary/5 p-4">
                <Sparkles className="h-14 w-14 text-primary" />
              </div>
              <div className="space-y-2">
                <h2 className="text-3xl font-bold">How can I help you?</h2>
                <p className="text-muted-foreground max-w-md mx-auto">
                  Ask me anything — I can search your documents, remember facts about you, and reason across knowledge.
                </p>
              </div>
              <div className="flex flex-wrap justify-center gap-2">
                {suggestedPrompts.map((p) => (
                  <Button
                    key={p}
                    variant="outline"
                    size="sm"
                    onClick={() => { setInput(p); inputRef.current?.focus() }}
                    className="rounded-full text-xs"
                  >
                    {p}
                  </Button>
                ))}
              </div>
            </motion.div>
          )}

          <AnimatePresence mode="popLayout">
            {messages.map((msg) => (
              <MessageBubble
                key={msg.id}
                msg={msg}
                onCopy={copyMessage}
                onRegenerate={regenerate}
                onFollowUp={handleFollowUp}
              />
            ))}
          </AnimatePresence>

          {isStreaming && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex gap-3"
            >
              <Avatar className="h-8 w-8 ring-2 ring-primary/20">
                <AvatarFallback className="bg-gradient-to-br from-primary to-primary/60 text-primary-foreground">
                  <Sparkles className="h-4 w-4" />
                </AvatarFallback>
              </Avatar>
              <div className="rounded-2xl bg-muted/50 border px-4 py-3 shadow-sm">
                <ThinkingDots />
              </div>
            </motion.div>
          )}
        </div>
      </ScrollArea>

      <div className="border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 p-4 lg:px-8">
        <div className="mx-auto max-w-3xl">
          {hasMessages && (
            <div className="flex items-center gap-2 mb-3 overflow-x-auto pb-1">
              {suggestedPrompts.slice(0, 2).map((p) => (
                <button
                  key={p}
                  onClick={() => { setInput(p); inputRef.current?.focus() }}
                  className="text-xs whitespace-nowrap px-3 py-1.5 rounded-full bg-muted hover:bg-accent text-muted-foreground hover:text-foreground transition-colors shrink-0"
                >
                  {p}
                </button>
              ))}
            </div>
          )}
          <div className="flex gap-3 items-end">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask anything..."
                rows={1}
                className="flex w-full rounded-xl border bg-muted/50 px-4 py-3 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-none min-h-[48px] max-h-[200px]"
                disabled={isStreaming}
                style={{ height: "auto" }}
                onInput={(e) => {
                  const el = e.currentTarget
                  el.style.height = "auto"
                  el.style.height = `${Math.min(el.scrollHeight, 200)}px`
                }}
              />
            </div>
            <Button
              onClick={isStreaming ? () => setIsStreaming(false) : handleSend}
              disabled={!input.trim() && !isStreaming}
              size="icon"
              className="h-12 w-12 shrink-0 rounded-xl"
            >
              {isStreaming ? <StopCircle className="h-5 w-5" /> : <Send className="h-5 w-5" />}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground text-center mt-3">
            Responses are grounded in your documents and personal memory
          </p>
        </div>
      </div>
    </div>
  )
}
