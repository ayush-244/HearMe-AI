"use client"

import { useEffect, useState, useRef } from "react"
import Link from "next/link"
import { MessageSquare, FileText, User, Activity, BookOpen, ArrowRight, Sparkles } from "lucide-react"

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
    color: "text-blue-400",
    bg: "bg-blue-500/10",
    border: "border-blue-500/20",
    prompt: "Hello! What can you help me with today?",
  },
  {
    title: "Upload Document",
    desc: "Process PDFs and text files",
    icon: FileText,
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/20",
    prompt: "I'd like to upload and analyze a document.",
    href: "/library",
  },
  {
    title: "Search Knowledge",
    desc: "Query your knowledge base",
    icon: Activity,
    color: "text-amber-400",
    bg: "bg-amber-500/10",
    border: "border-amber-500/20",
    prompt: "Analyze my knowledge gaps and what I should learn next.",
  },
  {
    title: "View Memories",
    desc: "What do I remember about you?",
    icon: BookOpen,
    color: "text-cyan-400",
    bg: "bg-cyan-500/10",
    border: "border-cyan-500/20",
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

  return (
    <div className="flex flex-col items-center justify-center min-h-full w-full max-w-2xl mx-auto px-4 py-12 text-center">
      {/* Greeting */}
      <div className="mb-8 space-y-2">
        <div className="inline-flex items-center gap-2 text-zinc-500 text-sm mb-3">
          <Sparkles className="h-4 w-4 text-blue-400" />
          <span>HearMe AI</span>
        </div>
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-100">
          {Greeting()} 👋
        </h1>
        <p className="text-zinc-500 text-base">
          What would you like to do today?
        </p>
      </div>

      {/* Action Cards */}
      <div className="grid w-full grid-cols-1 sm:grid-cols-2 gap-3 mb-8">
        {ACTION_CARDS.map((card, i) =>
          card.href ? (
            <Link key={i} href={card.href} className="group">
              <div
                className={`flex items-start gap-3.5 rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 text-left transition-all duration-200 hover:bg-zinc-900 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-black/20 hover:border-zinc-700`}
              >
                <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${card.bg} border ${card.border}`}>
                  <card.icon className={`h-4.5 w-4.5 ${card.color}`} />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-zinc-200 group-hover:text-zinc-100">{card.title}</p>
                  <p className="text-xs text-zinc-500 mt-0.5">{card.desc}</p>
                </div>
                <ArrowRight className="h-3.5 w-3.5 text-zinc-600 shrink-0 mt-0.5 group-hover:text-zinc-400 group-hover:translate-x-0.5 transition-all" />
              </div>
            </Link>
          ) : (
            <button
              key={i}
              onClick={() => onSelect(card.prompt)}
              className={`group flex items-start gap-3.5 rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 text-left transition-all duration-200 hover:bg-zinc-900 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-black/20 hover:border-zinc-700`}
            >
              <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${card.bg} border ${card.border}`}>
                <card.icon className={`h-4.5 w-4.5 ${card.color}`} />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-zinc-200 group-hover:text-zinc-100">{card.title}</p>
                <p className="text-xs text-zinc-500 mt-0.5">{card.desc}</p>
              </div>
              <ArrowRight className="h-3.5 w-3.5 text-zinc-600 shrink-0 mt-0.5 group-hover:text-zinc-400 group-hover:translate-x-0.5 transition-all" />
            </button>
          )
        )}
      </div>

      {/* Suggested prompts */}
      <div className="w-full">
        <p className="text-xs font-medium text-zinc-600 uppercase tracking-widest mb-3">Suggested prompts</p>
        <div className="flex flex-wrap justify-center gap-2">
          {SUGGESTED_PROMPTS.map((prompt, i) => (
            <button
              key={i}
              onClick={() => onSelect(prompt)}
              className="rounded-full border border-zinc-800 bg-zinc-900 px-3.5 py-1.5 text-xs text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 hover:border-zinc-700 transition-all duration-150"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      {/* Rotating placeholder hint */}
      <div className="mt-8 h-5">
        <p
          className="text-xs text-zinc-700 transition-opacity duration-300"
          style={{ opacity: visible ? 1 : 0 }}
        >
          {ROTATING_PLACEHOLDERS[placeholderIdx]}
        </p>
      </div>
    </div>
  )
}
