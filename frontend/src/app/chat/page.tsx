"use client"

import { Suspense, useState, useRef, useEffect, useCallback, useMemo } from "react"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useSearchParams, useRouter } from "next/navigation"
import { api } from "@/services/api-client"
import { useConversation, useCreateConversation, useAddMessage, useAddAttachment } from "@/hooks/use-conversations"
import { useUiStore } from "@/store/ui-store"
import { useChatStream } from "@/hooks/use-chat-stream"
import { useAutoScroll } from "@/hooks/use-auto-scroll"
import { Button } from "@/components/ui/button"
import { ReasoningStages } from "@/components/chat/ReasoningStages"
import { EmptyConversation } from "@/components/chat/EmptyConversation"
import { ChatMessageBubble } from "@/components/chat/chat-message-bubble"
import {
  Send,
  RefreshCw,
  ChevronDown,
  StopCircle,
  Paperclip,
  X,
  Loader2,
  FileText,
  CheckCircle2,
  AlertCircle,
} from "lucide-react"
import type { ChatMessage, RetrievalTrace } from "@/types"
import { motion } from "framer-motion"
import { toast } from "@/components/ui/toast"
import { FOCUS_RING } from "@/lib/design-tokens"
import { cn } from "@/lib/utils"

interface StreamMessage {
  id: string
  role: "assistant" | "user"
  content: string
  citations?: string[]
  isStreaming?: boolean
  timestamp?: string
  retrieval_trace?: RetrievalTrace | null
}

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

  // Rotating placeholder
  const PLACEHOLDERS = ["Ask anything...", "Explain Kubernetes", "Summarize my notes", "What do you remember?", "Compare React vs Vue"]
  const [placeholderIdx, setPlaceholderIdx] = useState(0)
  const [placeholderVisible, setPlaceholderVisible] = useState(true)
  useEffect(() => {
    if (input) return
    const id = setInterval(() => {
      setPlaceholderVisible(false)
      setTimeout(() => { setPlaceholderIdx((i) => (i + 1) % PLACEHOLDERS.length); setPlaceholderVisible(true) }, 280)
    }, 3200)
    return () => clearInterval(id)
  }, [input])

  const dbMessages = useMemo(() => conversation?.messages ?? [], [conversation?.messages])
  const attachedFiles = useMemo(() => conversation?.attached_documents ?? [], [conversation?.attached_documents])
  const historicalMessageIds = useMemo(
    () => new Set(dbMessages.map((m: ChatMessage) => m.id)),
    [dbMessages]
  )

  const { stream: streamQuery, cancel, isStreaming, currentStage, currentLabel } = useChatStream()

  const { containerRef, showJumpButton, scrollToBottom } = useAutoScroll([
    streamMessages,
    isPending,
    isStreaming,
  ])

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
      setStreamMessages((prev) => {
        const synced = dbMessages.map((m: ChatMessage) => {
          const existing =
            prev.find(sm => sm.id === m.id) ??
            prev.find(
              sm =>
                sm.role === m.role &&
                sm.content.trim() === m.content.trim()
            )
          
          return {
            id: m.id,
            role: m.role,
            content: m.content,
            citations: m.citations,
            isStreaming: false,
            timestamp: m.timestamp,
            retrieval_trace: m.retrieval_trace ?? existing?.retrieval_trace,
          }
        })

        const pendingMessages = prev.filter(sm => {
          const exists = synced.some(s =>
            s.id === sm.id ||
            (
              s.role === sm.role &&
              s.content.trim() === sm.content.trim()
            )
          )
          return !exists
        })

        return [...synced, ...pendingMessages]
      })
    }
  }, [dbMessages, convId])

  async function ensureConversation(): Promise<string> {
    if (convId) return convId
    const conv = await createConv.mutateAsync("")
    setActiveConversation(conv.id)
    currentConvIdRef.current = conv.id
    router.push(`/chat?id=${conv.id}`, { scroll: false })
    return conv.id
  }

  useEffect(() => {
    console.log("[3] STREAM STATE", streamMessages)
  }, [streamMessages])

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
    const now = new Date().toISOString()
    setStreamMessages((prev) => [
      ...prev,
      { id: `user-${Date.now()}`, role: "user", content: text, timestamp: now },
      { id: msgId, role: "assistant", content: "", isStreaming: true, timestamp: now },
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
          console.log("[2] ON DONE", result?.retrieval_trace)
          setStreamMessages((prev) =>
            prev.map((m) => (m.id === msgId ? { ...m, isStreaming: false, content: result?.answer || m.content, citations: result?.citations || m.citations, retrieval_trace: result?.retrieval_trace } : m))
          )
          try {
            const saved = await addMsg.mutateAsync({
              convId: cid,
              role: "assistant",
              content: result?.answer || "",
              citations: result?.citations,
            })
            // Promote stream message to server identity so the
            // dbMessages sync effect matches by id deterministically
            setStreamMessages((prev) =>
              prev.map((m) =>
                m.id === msgId
                  ? {
                      ...m,
                      id: saved.id,
                      timestamp: saved.timestamp,
                      citations: saved.citations ?? m.citations,
                      retrieval_trace: m.retrieval_trace ?? result?.retrieval_trace,
                      isStreaming: false,
                    }
                  : m
              )
            )
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

  const showEmpty = !convLoading && streamMessages.length === 0

  return (
    <div className="relative flex h-[calc(100vh-3.5rem)] flex-col">
      <div
        ref={containerRef}
        className="scrollbar-thin flex-1 overflow-y-auto px-4 lg:px-8"
      >
        <div className="mx-auto max-w-3xl space-y-8 py-6">
          {showEmpty && (
            <EmptyConversation 
              onSelect={(text) => {
                setInput(text)
                inputRef.current?.focus()
              }} 
            />
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

          {streamMessages.map((msg) => (
            <ChatMessageBubble
              key={msg.id}
              msg={msg}
              shouldAnimate={!historicalMessageIds.has(msg.id)}
            />
          ))}

          <ReasoningStages currentStage={currentStage} currentLabel={currentLabel} />
        </div>
      </div>

      {showJumpButton && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="pointer-events-none absolute bottom-24 left-1/2 z-10 -translate-x-1/2"
        >
          <Button
            variant="secondary"
            size="sm"
            className={cn(FOCUS_RING, "pointer-events-auto h-8 gap-1.5 rounded-full shadow-lg")}
            onClick={() => scrollToBottom()}
            aria-label="Jump to latest messages"
          >
            <ChevronDown className="h-4 w-4" aria-hidden="true" />
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
                placeholder={input ? "" : PLACEHOLDERS[placeholderIdx]}
                rows={1}
                className="flex w-full rounded-xl border bg-muted/50 px-4 py-3 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-none min-h-[48px] max-h-[200px] transition-placeholder"
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
