"use client"

import { useState } from "react"
import { motion, AnimatePresence, useReducedMotion } from "framer-motion"
import { Brain, FileText, ChevronDown, ChevronUp } from "lucide-react"
import { RetrievalTrace } from "@/types"
import { cn } from "@/lib/utils"

interface ContextStripProps {
  trace?: RetrievalTrace | null
}

export function ContextStrip({ trace }: ContextStripProps) {
  const [expanded, setExpanded] = useState(false)
  const prefersReducedMotion = useReducedMotion()

  if (!trace) return null

  // Ensure there's something to render to avoid empty component
  const hasMemories = trace.memories && trace.memories.length > 0
  const hasDocuments = trace.documents && trace.documents.length > 0

  if (!hasMemories && !hasDocuments) return null

  const animationVariants = {
    hidden: { opacity: 0, y: prefersReducedMotion ? 0 : 4 },
    visible: { opacity: 1, y: 0 },
  }

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      transition={{ duration: 0.2, ease: "easeOut" }}
      variants={animationVariants}
      className="mb-2 w-full max-w-[min(100%,42rem)]"
    >
      <div className="rounded-xl border border-border bg-secondary/50 overflow-hidden text-sm text-muted-foreground shadow-sm">
        <div
          className="flex items-center justify-between px-4 py-2"
        >
          <div className="flex items-center gap-4 flex-wrap">
            <span className="font-medium text-foreground/80">Using Context</span>
            <div className="flex items-center gap-3">
              {hasMemories && (
                <div className="flex items-center gap-1.5">
                  <Brain className="h-3.5 w-3.5" aria-hidden="true" />
                  <span>
                    {trace.memory_count === 1 ? "Personal Memory" : `${trace.memory_count || trace.memories?.length} Memories`}
                  </span>
                </div>
              )}
              {hasDocuments && (
                <div className="flex items-center gap-1.5">
                  <FileText className="h-3.5 w-3.5" aria-hidden="true" />
                  <span>
                    {trace.document_count === 1 
                      ? trace.documents?.[0]?.source || "Document" 
                      : `${trace.document_count || trace.documents?.length} Documents`}
                  </span>
                </div>
              )}
            </div>
          </div>
          
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 text-xs hover:text-foreground transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary rounded px-1"
            aria-expanded={expanded}
            aria-label={expanded ? "Hide context details" : "View context details"}
          >
            <span>{expanded ? "Hide details" : "View details"}</span>
            {expanded ? (
              <ChevronUp className="h-3 w-3" aria-hidden="true" />
            ) : (
              <ChevronDown className="h-3 w-3" aria-hidden="true" />
            )}
          </button>
        </div>

        <AnimatePresence initial={false}>
          {expanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: prefersReducedMotion ? 0 : 0.2, ease: "easeInOut" }}
              className="border-t border-border/50"
            >
              <div className="px-4 py-3 space-y-4 text-xs">
                {hasMemories && (
                  <div>
                    <h4 className="font-medium text-foreground/80 mb-2">Memory</h4>
                    <ul className="space-y-1">
                      {trace.memories?.map((mem) => (
                        <li key={mem.id} className="flex gap-2">
                          <span className="text-muted-foreground/60 mt-0.5">•</span>
                          <span>{mem.title || mem.type}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {hasDocuments && (
                  <div>
                    <h4 className="font-medium text-foreground/80 mb-2">Documents</h4>
                    <ul className="space-y-3">
                      {trace.documents?.map((doc) => {
                        const chunksForDoc = trace.chunks?.filter(
                          (c) => c.source === doc.source || c.source === doc.title
                        )
                        const uniquePages = Array.from(
                          new Set(chunksForDoc?.map((c) => c.page).filter((p) => p && p > 0))
                        ).sort((a, b) => a - b)

                        return (
                          <li key={doc.id} className="flex flex-col">
                            <span className="font-medium">{doc.source || doc.title}</span>
                            {uniquePages.length > 0 && (
                              <span className="text-muted-foreground/70">
                                {uniquePages.length === 1 
                                  ? `Page ${uniquePages[0]}` 
                                  : `Pages ${uniquePages.join(", ")}`}
                              </span>
                            )}
                          </li>
                        )
                      })}
                    </ul>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  )
}
