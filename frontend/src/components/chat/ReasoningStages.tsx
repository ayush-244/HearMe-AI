"use client"

import { useEffect, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Loader2, FileSearch, Brain, Sparkles, MessageSquare } from "lucide-react"

interface Stage {
  stage: string
  label: string
}

const STAGE_ICONS: Record<string, React.ReactNode> = {
  thinking: <Brain className="h-4 w-4" />,
  searching_documents: <FileSearch className="h-4 w-4" />,
  searching_memories: <Brain className="h-4 w-4" />,
  reasoning: <Sparkles className="h-4 w-4" />,
  writing: <MessageSquare className="h-4 w-4" />,
}

export function ReasoningStages({ currentStage, currentLabel }: { currentStage: string | null; currentLabel: string }) {
  if (!currentStage) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 5 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-center gap-2 px-4 py-2 text-sm text-muted-foreground"
    >
      <motion.div
        animate={{ opacity: [0.4, 1, 0.4] }}
        transition={{ duration: 1.5, repeat: Infinity }}
      >
        <Loader2 className="h-4 w-4 animate-spin" />
      </motion.div>

      <AnimatePresence mode="wait">
        <motion.span
          key={currentStage}
          initial={{ opacity: 0, x: -5 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 5 }}
          className="flex items-center gap-1.5"
        >
          {STAGE_ICONS[currentStage]}
          <span>{currentLabel}</span>
        </motion.span>
      </AnimatePresence>
    </motion.div>
  )
}
