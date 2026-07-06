"use client"

import { memo } from "react"
import { motion, useReducedMotion } from "framer-motion"
import { Sparkles, User } from "lucide-react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { StreamingCursor } from "@/components/chat/streaming-cursor"
import { ChatMarkdown } from "@/components/chat/chat-markdown"
import { MessageToolbar } from "@/components/chat/message-toolbar"
import { ContextStrip } from "@/components/chat/context-strip"
import { cn, formatMessageTime } from "@/lib/utils"
import { MOTION, TYPOGRAPHY } from "@/lib/design-tokens"

export interface ChatBubbleMessage {
  id: string
  role: "assistant" | "user"
  content: string
  citations?: string[]
  isStreaming?: boolean
  timestamp?: string
  retrieval_trace?: any
}

interface ChatMessageBubbleProps {
  msg: ChatBubbleMessage
  shouldAnimate?: boolean
}

export const ChatMessageBubble = memo(function ChatMessageBubble({
  msg,
  shouldAnimate = false,
}: ChatMessageBubbleProps) {
  const prefersReducedMotion = useReducedMotion()
  const animateEntry = shouldAnimate && !prefersReducedMotion

  console.log("[4] Bubble", msg.id, msg.retrieval_trace)

  const isUser = msg.role === "user"
  const timeLabel = msg.timestamp ? formatMessageTime(msg.timestamp) : null

  return (
    <motion.div
      initial={animateEntry ? { opacity: 0, y: 8 } : false}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: MOTION.fade / 1000, ease: "easeOut" }}
      className={cn("group/message flex gap-3", isUser ? "justify-end" : "justify-start")}
    >
      {!isUser && (
        <Avatar className="mt-1 h-8 w-8 shrink-0 ring-2 ring-primary/20">
          <AvatarFallback className="bg-gradient-to-br from-primary to-primary/60 text-primary-foreground">
            <Sparkles className="h-4 w-4" aria-hidden="true" />
          </AvatarFallback>
        </Avatar>
      )}

      <div className={cn("flex max-w-[min(80%,42rem)] flex-col gap-1", isUser && "items-end")}>
        {!isUser && timeLabel && (
          <span className={cn(TYPOGRAPHY.caption, "px-1")}>{timeLabel}</span>
        )}

        {isUser ? (
          <div className="rounded-2xl rounded-br-md bg-primary px-4 py-3 text-primary-foreground shadow-sm">
            <p className={cn(TYPOGRAPHY.body, "whitespace-pre-wrap leading-relaxed text-primary-foreground")}>
              {msg.content}
            </p>
          </div>
        ) : (
          <div className="flex flex-col gap-1 w-full">
            <ContextStrip trace={msg.retrieval_trace} />
            <div className="w-full rounded-2xl rounded-bl-md border border-border bg-card px-4 py-3 shadow-sm">
            {msg.isStreaming ? (
              <div className={cn(TYPOGRAPHY.body, "leading-relaxed")}>
                {msg.content ? (
                  <span className="whitespace-pre-wrap">{msg.content}</span>
                ) : null}
                <StreamingCursor />
              </div>
            ) : msg.content ? (
              <ChatMarkdown content={msg.content} />
            ) : null}

            {msg.citations && msg.citations.length > 0 && !msg.isStreaming && (
              <div className="mt-4 border-t border-border pt-3">
                <p className={cn(TYPOGRAPHY.caption, "mb-2 font-medium")}>Sources</p>
                <div className="flex flex-wrap gap-1.5">
                  {msg.citations.map((c, i) => (
                    <Badge key={i} variant="secondary" className="max-w-[200px] gap-1 text-[11px]">
                      <span className="truncate">{c.replace(/[\[\]]/g, "")}</span>
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {!msg.isStreaming && msg.content && <MessageToolbar content={msg.content} />}
          </div>
          </div>
        )}

        {isUser && timeLabel && (
          <span className={cn(TYPOGRAPHY.caption, "px-1")}>{timeLabel}</span>
        )}
      </div>

      {isUser && (
        <Avatar className="mt-1 h-8 w-8 shrink-0 ring-2 ring-muted">
          <AvatarFallback className="bg-muted">
            <User className="h-4 w-4" aria-hidden="true" />
          </AvatarFallback>
        </Avatar>
      )}
    </motion.div>
  )
})
