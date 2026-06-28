"use client"

import { useCallback, useRef, useState } from "react"
import { api } from "@/services/api-client"
import type { KnowledgeQuery, StreamEvent } from "@/types"

interface UseChatStreamOptions {
  onStage?: (stage: string, label: string) => void
  onToken?: (token: string) => void
  onCitation?: (citations: string[], sources: any[]) => void
  onDone?: (result: StreamEvent["result"]) => void
  onError?: (message: string) => void
}

export function useChatStream() {
  const [isStreaming, setIsStreaming] = useState(false)
  const [currentStage, setCurrentStage] = useState<string | null>(null)
  const [currentLabel, setCurrentLabel] = useState<string>("")
  const abortRef = useRef<AbortController | null>(null)

  const stream = useCallback(async (query: KnowledgeQuery, opts: UseChatStreamOptions = {}) => {
    const controller = new AbortController()
    abortRef.current = controller
    setIsStreaming(true)

    try {
      const response = await api.knowledgeQueryStream(query, controller.signal)

      if (!response.ok) {
        const text = await response.text().catch(() => "Stream request failed")
        opts.onError?.(text)
        setIsStreaming(false)
        return
      }

      const reader = response.body?.getReader()
      if (!reader) {
        opts.onError?.("No response body")
        setIsStreaming(false)
        return
      }

      const decoder = new TextDecoder()
      let buffer = ""

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n")
        buffer = lines.pop() || ""

        for (const line of lines) {
          const trimmed = line.trim()
          if (!trimmed.startsWith("data: ")) continue

          try {
            const event: StreamEvent = JSON.parse(trimmed.slice(6))

            switch (event.type) {
              case "stage":
                setCurrentStage(event.stage || null)
                setCurrentLabel(event.label || "")
                opts.onStage?.(event.stage || "", event.label || "")
                break
              case "token":
                opts.onToken?.(event.token || "")
                break
              case "citation":
                opts.onCitation?.(event.citations || [], event.sources || [])
                break
              case "done":
                opts.onDone?.(event.result)
                setIsStreaming(false)
                setCurrentStage(null)
                setCurrentLabel("")
                return
              case "error":
                opts.onError?.(event.message || "Unknown error")
                setIsStreaming(false)
                setCurrentStage(null)
                setCurrentLabel("")
                return
            }
          } catch {
          }
        }
      }
    } catch (err: any) {
      if (err?.name !== "AbortError") {
        opts.onError?.(err?.message || "Stream error")
      }
    } finally {
      setIsStreaming(false)
      setCurrentStage(null)
      setCurrentLabel("")
      abortRef.current = null
    }
  }, [])

  const cancel = useCallback(() => {
    abortRef.current?.abort()
    setIsStreaming(false)
    setCurrentStage(null)
    setCurrentLabel("")
  }, [])

  return { stream, cancel, isStreaming, currentStage, currentLabel }
}
