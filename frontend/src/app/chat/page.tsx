"use client"

import { Suspense, useState, useRef, useEffect, useCallback, useMemo, memo } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useSearchParams, useRouter } from "next/navigation"
import { api } from "@/services/api-client"
import { useConversation, useCreateConversation, useAddMessage, useAddAttachment } from "@/hooks/use-conversations"
import { useUiStore } from "@/store/ui-store"
import { useChatStream } from "@/hooks/use-chat-stream"
import { useAutoScroll } from "@/hooks/use-auto-scroll"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { ReasoningStages } from "@/components/chat/ReasoningStages"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import rehypeHighlight from "rehype-highlight"
import {
  Send,
  Sparkles,
  Copy,
  Check,
  RefreshCw,
  ChevronDown,
  User,
  StopCircle,
  Paperclip,
  X,
  Loader2,
  FileText,
  CheckCircle2,
  AlertCircle,
} from "lucide-react"
import type { ChatMessage } from "@/types"
import { motion, AnimatePresence } from "framer-motion"
import { toast } from "@/components/ui/toast"

interface StreamMessage {
  id: string
  role: "assistant" | "user"
  content: string
  citations?: string[]
  isStreaming?: boolean
}

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

const MessageBubble = memo(function MessageBubble({
  msg,
  onCopy,
  onRegenerate,
}: {
  msg: StreamMessage
  onCopy: (content: string) => void
  onRegenerate: () => void
}) {
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
        <Avatar className="h-8 w-8 mt-0.5 ring-2 ring-primary/20 shrink-0">
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
            {msg.isStreaming ? (
              <div>
                <span className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</span>
                <motion.span
                  animate={{ opacity: [1, 0] }}
                  transition={{ duration: 0.6, repeat: Infinity, repeatType: "reverse" }}
                  className="inline-block w-[2px] h-4 bg-primary ml-0.5 align-text-bottom"
                />
              </div>
            ) : (
              <div className="prose prose-sm dark:prose-invert max-w-none prose-p:leading-relaxed prose-pre:bg-muted prose-code:text-primary">
                <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeHighlight]}>
                  {msg.content}
                </ReactMarkdown>
              </div>
            )}

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

            {!msg.isStreaming && msg.content && (
              <div className="flex items-center gap-1 mt-3 pt-2 border-t border-border/50">
                <Button variant="ghost" size="icon" className="h-7 w-7 hover:bg-muted" onClick={handleCopy} title="Copy response">
                  {copied ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
                </Button>
                <Button variant="ghost" size="icon" className="h-7 w-7 hover:bg-muted" onClick={onRegenerate} title="Regenerate">
                  <RefreshCw className="h-3.5 w-3.5" />
                </Button>
              </div>
            )}
          </div>
        )}
      </div>

      {msg.role === "user" && (
        <Avatar className="h-8 w-8 mt-0.5 ring-2 ring-muted shrink-0">
          <AvatarFallback className="bg-muted">
            <User className="h-4 w-4" />
          </AvatarFallback>
        </Avatar>
      )}
    </motion.div>
  )
})

interface UploadProgress {
  status: "uploading" | "processing" | "ready" | "failed"
  progress?: number
  error?: string
}

function ChatPageInner() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const queryClient = useQueryClient()
  const { activeConversationId, setActiveConversation } = useUiStore()

  const convId = searchParams.get("id")
  const { data: conversation, isLoading: convLoading } = useConversation(convId)
  const createConv = useCreateConversation()
  const addMsg = useAddMessage()
  const addAttach = useAddAttachment()

  const [input, setInput] = useState("")
  const [isPending, setIsPending] = useState(false)
  const [streamMessages, setStreamMessages] = useState<StreamMessage[]>([])
  const [uploadProgress, setUploadProgress] = useState<UploadProgress | null>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const currentConvIdRef = useRef<string | null>(null)

  const dbMessages = useMemo(() => conversation?.messages ?? [], [conversation?.messages])
  const attachedFiles = useMemo(() => conversation?.attached_documents ?? [], [conversation?.attached_documents])

  const { containerRef, showJumpButton, scrollToBottom } = useAutoScroll([streamMessages, isPending])

  useEffect(() => {
    setStreamMessages([])
  }, [convId])

  useEffect(() => {
    if (convId) {
      setActiveConversation(convId)
      currentConvIdRef.current = convId
    }
  }, [convId, setActiveConversation])

  useEffect(() => {
    setInput("")
    setStreamMessages([])
    setUploadProgress(null)
  }, [convId])

  useEffect(() => {
    if (!convId && activeConversationId) {
      router.push(`/chat?id=${activeConversationId}`)
    }
  }, [convId, activeConversationId, router])

  useEffect(() => {
    if (convId && dbMessages.length > 0) {
      setStreamMessages(
        dbMessages.map((m: ChatMessage) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          citations: m.citations,
          isStreaming: false,
        }))
      )
    } {
      setStreamMessages(
        dbMessages.map((m: ChatMessage) => ({
          id: m.id,
          role: m.role,
          content: m.content,
          citations: m.citations,
          isStreaming: false,
        }))
      )
    }
  }, [dbMessages, streamMessages.length])

  const { stream: streamQuery, cancel, isStreaming, currentStage, currentLabel } = useChatStream()

  async function ensureConversation(): Promise<string> {
    if (convId) return convId
    const conv = await createConv.mutateAsync("")
    setActiveConversation(conv.id)
    currentConvIdRef.current = conv.id
    router.push(`/chat?id=${conv.id}`, { scroll: false })
    return conv.id
  }

  const knowledgeMutation = useMutation({
    mutationFn: async ({ text, cid }: { text: string; cid: string }) => {
      const docIds = attachedFiles.map((f) => f.document_id)
      return api.knowledgeQuery({
        question: text,
        conversation_id: cid,
        top_k: 5,
        document_ids: docIds.length > 0 ? docIds : undefined,
      })
    },
    onSuccess: async (result, { text, cid }) => {
      setIsPending(true)
      try {
        await addMsg.mutateAsync({ convId: cid, role: "user", content: text })
        await addMsg.mutateAsync({
          convId: cid,
          role: "assistant",
          content: result.answer,
          citations: result.citations,
        })
        api.extractMemory({ user_text: text, assistant_text: result.answer })
          .then(() => queryClient.invalidateQueries({ queryKey: ["memories"] }))
          .catch(() => { })
      } catch {
        toast({ title: "Failed to save message", variant: "destructive" })
      }
      setIsPending(false)
    },
    onError: () => {
      setIsPending(false)
      toast({ title: "Failed to get answer", variant: "destructive" })
    },
  })

  const handleSend = useCallback(async () => {
    const text = input.trim()
    if (!text || isStreaming || isPending) return
    setInput("")

    const cid = await ensureConversation()

    const msgId = `stream-${Date.now()}`
    setStreamMessages((prev) => [
      ...prev,
      { id: `user-${Date.now()}`, role: "user", content: text },
      { id: msgId, role: "assistant", content: "", isStreaming: true },
    ])

    try {
      await addMsg.mutateAsync({ convId: cid, role: "user", content: text })
    } catch { }

    streamQuery(
      { question: text, conversation_id: cid, top_k: 5, document_ids: attachedFiles.length > 0 ? attachedFiles.map((f) => f.document_id) : undefined },
      {
        onToken: (token) => {
          setStreamMessages((prev) =>
            prev.map((m) => (m.id === msgId ? { ...m, content: m.content + token } : m))
          )
        },
        onCitation: (citations) => {
          setStreamMessages((prev) =>
            prev.map((m) => (m.id === msgId ? { ...m, citations } : m))
          )
        },
        onDone: async (result) => {
          setStreamMessages((prev) =>
            prev.map((m) => (m.id === msgId ? { ...m, isStreaming: false, content: result?.answer || m.content, citations: result?.citations || m.citations } : m))
          )
          try {
            await addMsg.mutateAsync({
              convId: cid,
              role: "assistant",
              content: result?.answer || "",
              citations: result?.citations,
            })
            api.extractMemory({ user_text: text, assistant_text: result?.answer || "" })
              .then(() => queryClient.invalidateQueries({ queryKey: ["memories"] }))
              .catch(() => { })
          } catch { }
        },
        onError: (message) => {
          setStreamMessages((prev) =>
            prev.map((m) => (m.id === msgId ? { ...m, isStreaming: false, content: m.content || "I encountered an error generating a response. Please try again." } : m))
          )
          toast({ title: message || "Stream error", variant: "destructive" })
        },
      }
    )
  }, [input, isStreaming, isPending, streamQuery, ensureConversation, addMsg, queryClient, attachedFiles])

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
    const lastUser = [...streamMessages].reverse().find((m) => m.role === "user")
    if (lastUser) {
      setInput(lastUser.content)
    }
  }

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setUploadProgress({ status: "uploading", progress: 0 })
    try {
      const result = await api.uploadDocument(file) as { document_id: string }
      const docId = result.document_id
      setUploadProgress({ status: "processing" })

      await runPipeline(docId)

      let targetConvId = convId
      if (!targetConvId) {
        const conv = await createConv.mutateAsync("")
        targetConvId = conv.id
        setActiveConversation(conv.id)
        router.push(`/chat?id=${conv.id}`, { scroll: false })
      }

      await addAttach.mutateAsync({
        convId: targetConvId!,
        documentId: docId,
        filename: file.name,
        fileType: file.name.split(".").pop() || "unknown",
      })

      setUploadProgress({ status: "ready" })
      toast({ title: "Document ready", variant: "success" })
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Upload failed"
      setUploadProgress({ status: "failed", error: msg })
      toast({ title: "Upload failed", variant: "destructive" })
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
  }

  async function runPipeline(docId: string) {
    const stages = ["extract", "analyze", "chunk", "embed", "index"]
    for (const stage of stages) {
      try {
        switch (stage) {
          case "extract": await api.extractDocument(docId); break
          case "analyze": await api.analyzeDocument(docId); break
          case "chunk": await api.chunkDocument(docId); break
          case "embed": await api.embedDocument(docId); break
          case "index": await api.indexDocument(docId); break
        }
      } catch (err) {
        throw new Error(`Pipeline failed at ${stage}: ${err instanceof Error ? err.message : "Unknown error"}`)
      }
    }
  }

  async function removeAttachedFile(documentId: string) {
    if (!convId) return
    try {
      await api.removeAttachment(convId, documentId)
      queryClient.invalidateQueries({ queryKey: ["conversation", convId] })
    } catch { }
  }

  function retryUpload() {
    if (fileInputRef.current) {
      fileInputRef.current.click()
    }
  }

  const showWelcome = !convId && !convLoading && streamMessages.length === 0

  return (
    <div className="flex h-[calc(100vh-3.5rem)] flex-col">
      <div ref={containerRef} className="flex-1 overflow-y-auto px-4 lg:px-8">
        <div className="mx-auto max-w-3xl py-6 space-y-6">
          {showWelcome && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center py-16 space-y-6"
            >
              <div className="inline-flex rounded-2xl bg-gradient-to-br from-primary/10 to-primary/5 p-4">
                <Sparkles className="h-16 w-16 text-primary" />
              </div>
              <div className="space-y-2">
                <h1 className="text-4xl font-bold">How can I help you?</h1>
                <p className="text-muted-foreground max-w-lg mx-auto text-lg">
                  Ask me anything about your documents — I&apos;ll search, analyze, and answer with sources.
                </p>
              </div>
              <div className="flex flex-wrap justify-center gap-2">
                {[
                  "Summarize my documents",
                  "What are the key topics?",
                  "Find insights across files",
                  "Analyze this for me",
                ].map((p) => (
                  <Button
                    key={p}
                    variant="outline"
                    size="sm"
                    onClick={() => { setInput(p); inputRef.current?.focus() }}
                    className="rounded-full text-sm"
                  >
                    {p}
                  </Button>
                ))}
              </div>
            </motion.div>
          )}

          {convLoading && (
            <div className="flex justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          )}

          {attachedFiles.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex flex-wrap gap-2"
            >
              {attachedFiles.map((doc) => (
                <div
                  key={doc.document_id}
                  className="flex items-center gap-2 rounded-lg border bg-muted/30 px-3 py-1.5 text-sm"
                >
                  <FileText className="h-4 w-4 text-primary" />
                  <span className="text-xs font-medium truncate max-w-[120px]">{doc.filename}</span>
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-5 w-5 -mr-1"
                    onClick={() => removeAttachedFile(doc.document_id)}
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </div>
              ))}
            </motion.div>
          )}

          <AnimatePresence mode="popLayout">
            {streamMessages.map((msg) => (
              <MessageBubble
                key={msg.id}
                msg={msg}
                onCopy={copyMessage}
                onRegenerate={regenerate}
              />
            ))}
          </AnimatePresence>

          <ReasoningStages currentStage={currentStage} currentLabel={currentLabel} />
        </div>
      </div>

      {showJumpButton && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute bottom-24 left-1/2 -translate-x-1/2 z-10"
        >
          <Button
            variant="secondary"
            size="sm"
            className="rounded-full shadow-lg h-8 gap-1.5"
            onClick={() => scrollToBottom()}
          >
            <ChevronDown className="h-4 w-4" />
            Jump to latest
          </Button>
        </motion.div>
      )}

      <div className="border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 p-4 lg:px-8 relative">
        <div className="mx-auto max-w-3xl space-y-3">
          {uploadProgress && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center justify-between rounded-lg border bg-muted/30 px-4 py-2.5"
            >
              <div className="flex items-center gap-3">
                {uploadProgress.status === "uploading" || uploadProgress.status === "processing" ? (
                  <Loader2 className="h-4 w-4 animate-spin text-primary" />
                ) : uploadProgress.status === "ready" ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                ) : (
                  <AlertCircle className="h-4 w-4 text-destructive" />
                )}
                <div>
                  <p className="text-sm font-medium">
                    {uploadProgress.status === "uploading" && "Uploading..."}
                    {uploadProgress.status === "processing" && "Processing..."}
                    {uploadProgress.status === "ready" && "Ready"}
                    {uploadProgress.status === "failed" && "Upload failed"}
                  </p>
                  {uploadProgress.error && (
                    <p className="text-xs text-destructive mt-0.5">{uploadProgress.error}</p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                {uploadProgress.status === "processing" && (
                  <div className="flex gap-1">
                    {[0, 1, 2].map((i) => (
                      <motion.div
                        key={i}
                        className="h-2 w-2 rounded-full bg-primary/60"
                        animate={{ opacity: [0.3, 1, 0.3] }}
                        transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.2 }}
                      />
                    ))}
                  </div>
                )}
                {uploadProgress.status === "failed" && (
                  <Button variant="outline" size="sm" className="h-8 text-xs" onClick={retryUpload}>
                    <RefreshCw className="h-3 w-3 mr-1" /> Retry
                  </Button>
                )}
                {uploadProgress.status === "ready" && (
                  <Button variant="ghost" size="icon" className="h-6 w-6" onClick={() => setUploadProgress(null)}>
                    <X className="h-3 w-3" />
                  </Button>
                )}
              </div>
            </motion.div>
          )}

          <div className="flex gap-3 items-end">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask anything about your documents..."
                rows={1}
                className="flex w-full rounded-xl border bg-muted/50 px-4 py-3 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-none min-h-[48px] max-h-[200px]"
                disabled={isStreaming || isPending}
                style={{ height: "auto" }}
                onInput={(e) => {
                  const el = e.currentTarget
                  el.style.height = "auto"
                  el.style.height = `${Math.min(el.scrollHeight, 200)}px`
                }}
              />
            </div>
            <div className="flex gap-2">
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.txt,.md"
                className="hidden"
                onChange={handleFileUpload}
              />
              <Button
                variant="outline"
                size="icon"
                className="h-12 w-12 shrink-0 rounded-xl"
                onClick={() => fileInputRef.current?.click()}
                disabled={isStreaming || isPending || uploadProgress?.status === "uploading" || uploadProgress?.status === "processing"}
                title="Attach document"
              >
                <Paperclip className="h-5 w-5" />
              </Button>
              <Button
                onClick={isStreaming ? cancel : handleSend}
                disabled={!input.trim() && !isStreaming}
                size="icon"
                className="h-12 w-12 shrink-0 rounded-xl"
              >
                {isStreaming ? <StopCircle className="h-5 w-5" /> : <Send className="h-5 w-5" />}
              </Button>
            </div>
          </div>
          <p className="text-xs text-muted-foreground text-center">
            Responses are grounded in your documents and personal memory
          </p>
        </div>
      </div>
    </div>
  )
}

export default function ChatPage() {
  return (
    <Suspense fallback={
      <div className="flex h-[calc(100vh-3.5rem)] items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    }>
      <ChatPageInner />
    </Suspense>
  )
}
