"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { MessageSquare, FileText, Activity, BookOpen, ArrowRight, Sparkles } from "lucide-react"
import { SurfaceCard } from "@/components/ui/surface-card"
import { FEATURE_ACCENTS, ICON_SIZE, TYPOGRAPHY } from "@/lib/design-tokens"
import { cn } from "@/lib/utils"

interface EmptyConversationProps {
  onSelect: (text: string) => void
}

const ROTATING_PLACEHOLDERS = [
  "Ask anything...",
  "Explain Docker containers",
  "Summarize my PDF",
  "What do you remember about me?",
  "Compare React vs Vue",
  "Teach me Machine Learning",
]

const ACTION_CARDS = [
  {
    title: "Start Chat",
    desc: "Ask questions & get AI answers",
    icon: MessageSquare,
    accent: FEATURE_ACCENTS.chat,
    prompt: "Hello! What can you help me with today?",
  },
  {
    title: "Upload Document",
    desc: "Process PDFs and text files",
    icon: FileText,
    accent: FEATURE_ACCENTS.library,
    prompt: "I'd like to upload and analyze a document.",
    href: "/library",
  },
  {
    title: "Search Knowledge",
    desc: "Query your knowledge base",
    icon: Activity,
    accent: FEATURE_ACCENTS.knowledge,
    prompt: "Analyze my knowledge gaps and what I should learn next.",
  },
  {
    title: "View Memories",
    desc: "What do I remember about you?",
    icon: BookOpen,
    accent: FEATURE_ACCENTS.memory,
    prompt: "What do you know and remember about me?",
  },
]

const SUGGESTED_PROMPTS = [
  "Explain Docker",
  "Summarize my PDF",
  "What do you remember about me?",
  "Teach me Machine Learning",
]

function Greeting() {
  const hour = new Date().getHours()
  if (hour < 12) return "Good morning"
  if (hour < 17) return "Good afternoon"
  return "Good evening"
}

export function EmptyConversation({ onSelect }: EmptyConversationProps) {
  const [placeholderIdx, setPlaceholderIdx] = useState(0)
  const [visible, setVisible] = useState(true)

  useEffect(() => {
    const interval = setInterval(() => {
      setVisible(false)
      setTimeout(() => {
        setPlaceholderIdx((i) => (i + 1) % ROTATING_PLACEHOLDERS.length)
        setVisible(true)
      }, 300)
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  const cardContent = (card: typeof ACTION_CARDS[0]) => (
    <SurfaceCard interactive padding="md" className="group h-full">
      <div className="flex items-start gap-3 text-left">
        <div className="icon-container">
          <card.icon className={cn(ICON_SIZE.md, card.accent)} />
        </div>
        <div className="min-w-0 flex-1">
          <p className={TYPOGRAPHY.cardTitle}>{card.title}</p>
          <p className="text-caption mt-1">{card.desc}</p>
        </div>
        <ArrowRight className={cn(ICON_SIZE.sm, "text-muted-foreground shrink-0 mt-0.5 group-hover:text-foreground group-hover:translate-x-0.5 transition-all duration-200")} />
      </div>
    </SurfaceCard>
  )

  return (
    <div className="flex flex-col items-center justify-center min-h-full w-full max-w-2xl mx-auto px-4 py-12 text-center">
      <div className="mb-8 space-y-2">
        <div className="inline-flex items-center gap-2 text-caption mb-3">
          <Sparkles className={cn(ICON_SIZE.md, FEATURE_ACCENTS.chat)} />
          <span>HearMe AI</span>
        </div>
        <h1 className={TYPOGRAPHY.pageTitle}>
          {Greeting()} 👋
        </h1>
        <p className={TYPOGRAPHY.bodyMuted}>
          What would you like to do today?
        </p>
      </div>

      <div className="grid w-full grid-cols-1 sm:grid-cols-2 gap-3 mb-8">
        {ACTION_CARDS.map((card, i) =>
          card.href ? (
            <Link key={i} href={card.href} className="group">
              {cardContent(card)}
            </Link>
          ) : (
            <button key={i} onClick={() => onSelect(card.prompt)} className="text-left">
              {cardContent(card)}
            </button>
          )
        )}
      </div>

      <div className="w-full">
        <p className="text-overline mb-3">Suggested prompts</p>
        <div className="flex flex-wrap justify-center gap-2">
          {SUGGESTED_PROMPTS.map((prompt, i) => (
            <button
              key={i}
              onClick={() => onSelect(prompt)}
              className="rounded-full border border-border bg-card px-3 py-1.5 text-caption hover:text-foreground hover:bg-accent transition-all duration-200 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-8 h-5">
        <p
          className="text-caption opacity-60 transition-opacity duration-200"
          style={{ opacity: visible ? 1 : 0 }}
        >
          {ROTATING_PLACEHOLDERS[placeholderIdx]}
        </p>
      </div>
    </div>
  )
}
