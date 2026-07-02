"use client"

import { useDocuments } from "@/hooks/use-documents"
import { useMemories } from "@/hooks/use-memory"
import { useConversations } from "@/hooks/use-conversations"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import Link from "next/link"
import {
  MessageSquare,
  Brain,
  Database,
  FileText,
  Upload,
  Sparkles,
  ArrowRight,
  Clock,
  BookOpen,
  Lightbulb,
  BarChart3,
  Activity,
} from "lucide-react"
import { formatDate } from "@/lib/utils"
import { motion } from "framer-motion"

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.07 } },
}

const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.3 } },
}

function Greeting() {
  const hour = new Date().getHours()
  if (hour < 12) return "Good morning"
  if (hour < 17) return "Good afternoon"
  return "Good evening"
}

const suggestionPrompts = [
  { icon: Lightbulb, text: "Summarize my recent documents", color: "text-amber-400", bg: "bg-amber-500/10" },
  { icon: Brain, text: "What do you know about me?", color: "text-blue-400", bg: "bg-blue-500/10" },
  { icon: Activity, text: "Analyze my knowledge gaps", color: "text-emerald-400", bg: "bg-emerald-500/10" },
  { icon: BookOpen, text: "Help me learn about a topic", color: "text-cyan-400", bg: "bg-cyan-500/10" },
]

const quickActions = [
  { icon: MessageSquare, label: "Start Chat", href: "/chat", desc: "Ask questions and get answers", color: "text-blue-400", bg: "bg-blue-500/10", border: "border-blue-500/20" },
  { icon: Upload, label: "Upload Document", href: "/library", desc: "Process PDFs and more", color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20" },
  { icon: Brain, label: "Explore Knowledge", href: "/knowledge", desc: "Search your knowledge base", color: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/20" },
  { icon: Database, label: "View Memories", href: "/memory", desc: "What I remember about you", color: "text-cyan-400", bg: "bg-cyan-500/10", border: "border-cyan-500/20" },
]

export default function Home() {
  const { data: docs, isLoading: docsLoad } = useDocuments()
  const { data: mems, isLoading: memsLoad } = useMemories()
  const { data: convsData } = useConversations()

  const docCount = docs?.count ?? 0
  const memCount = mems?.count ?? 0
  const convCount = convsData?.conversations?.length ?? 0
  const recentDocs = docs?.documents?.slice(0, 5) ?? []
  const recentMems = mems?.memories?.slice(0, 4) ?? []

  return (
    <div className="p-6 lg:p-8 space-y-8 max-w-6xl mx-auto">
      <motion.div variants={container} initial="hidden" animate="show" className="space-y-8">

        {/* Greeting */}
        <motion.div variants={item} className="space-y-1.5">
          <div className="flex items-center gap-2 text-sm text-zinc-500 mb-2">
            <Clock className="h-3.5 w-3.5" />
            <span>{new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}</span>
          </div>
          <h1 className="text-3xl font-semibold tracking-tight text-zinc-100">
            {Greeting()}, Ayush 👋
          </h1>
          <p className="text-zinc-500">Ready to continue learning?</p>
        </motion.div>

        {/* Stats strip */}
        <motion.div variants={item} className="grid grid-cols-3 gap-3">
          {[
            { label: "Documents", value: docCount, icon: FileText, color: "text-emerald-400" },
            { label: "Conversations", value: convCount, icon: MessageSquare, color: "text-blue-400" },
            { label: "Memories", value: memCount, icon: Database, color: "text-cyan-400" },
          ].map(({ label, value, icon: Icon, color }) => (
            <div key={label} className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 flex items-center gap-3">
              <div className={`rounded-lg bg-zinc-800 p-2 shrink-0`}>
                <Icon className={`h-4 w-4 ${color}`} />
              </div>
              <div>
                <p className="text-xl font-bold text-zinc-100">{value}</p>
                <p className="text-xs text-zinc-500">{label}</p>
              </div>
            </div>
          ))}
        </motion.div>

        {/* Quick Actions */}
        <motion.div variants={item}>
          <p className="text-xs font-semibold text-zinc-600 uppercase tracking-widest mb-3">Quick actions</p>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {quickActions.map((action) => (
              <Link key={action.href} href={action.href}>
                <div className={`group flex flex-col gap-3 rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 cursor-pointer transition-all duration-200 hover:bg-zinc-900 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-black/20 hover:border-zinc-700`}>
                  <div className={`rounded-lg p-2.5 w-fit ${action.bg} border ${action.border}`}>
                    <action.icon className={`h-4.5 w-4.5 ${action.color}`} />
                  </div>
                  <div>
                    <p className="font-medium text-sm text-zinc-200 group-hover:text-zinc-100">{action.label}</p>
                    <p className="text-xs text-zinc-500 mt-0.5">{action.desc}</p>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </motion.div>

        {/* Suggested Prompts + Memory */}
        <motion.div variants={item} className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2 rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="h-4 w-4 text-blue-400" />
              <h2 className="font-semibold text-sm text-zinc-200">Suggested Prompts</h2>
            </div>
            <div className="grid gap-2.5 sm:grid-cols-2">
              {suggestionPrompts.map((p, i) => (
                <Link key={i} href={`/chat?prompt=${encodeURIComponent(p.text)}`}>
                  <div className="flex items-start gap-3 rounded-lg border border-zinc-800 p-3 hover:bg-zinc-800/60 hover:border-zinc-700 transition-all duration-150 group cursor-pointer">
                    <div className={`rounded-md p-1.5 ${p.bg} shrink-0`}>
                      <p.icon className={`h-3.5 w-3.5 ${p.color}`} />
                    </div>
                    <p className="text-xs text-zinc-400 group-hover:text-zinc-200 transition-colors">{p.text}</p>
                  </div>
                </Link>
              ))}
            </div>
          </div>

          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <div className="flex items-center gap-2 mb-4">
              <Brain className="h-4 w-4 text-cyan-400" />
              <h2 className="font-semibold text-sm text-zinc-200">AI Memory</h2>
            </div>
            {memsLoad ? (
              <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-12 w-full bg-zinc-800" />)}
              </div>
            ) : recentMems.length > 0 ? (
              <div className="space-y-1.5">
                {recentMems.slice(0, 3).map((mem) => (
                  <Link key={mem.memory_id} href="/memory">
                    <div className="flex items-start gap-2.5 rounded-lg p-2 hover:bg-zinc-800/60 transition-colors">
                      <div className="rounded-full bg-cyan-500/10 p-1.5 mt-0.5 shrink-0">
                        <Database className="h-2.5 w-2.5 text-cyan-400" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-xs text-zinc-300 line-clamp-1">{mem.content}</p>
                        <p className="text-[10px] text-zinc-600 mt-0.5">{formatDate(mem.created_at)}</p>
                      </div>
                    </div>
                  </Link>
                ))}
                <Link href="/memory">
                  <Button variant="link" size="sm" className="mt-1 h-auto p-0 text-xs text-zinc-500 hover:text-zinc-300">
                    View all memories <ArrowRight className="h-3 w-3 ml-1" />
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="text-center py-6">
                <Brain className="h-8 w-8 mx-auto mb-2 text-zinc-700" />
                <p className="text-xs text-zinc-600">No memories yet</p>
                <p className="text-[10px] text-zinc-700 mt-0.5">Start chatting to build your memory</p>
              </div>
            )}
          </div>
        </motion.div>

        {/* Recent Documents + Knowledge */}
        <motion.div variants={item} className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <div className="flex items-center gap-2 mb-4">
              <FileText className="h-4 w-4 text-emerald-400" />
              <h2 className="font-semibold text-sm text-zinc-200">Recent Documents</h2>
            </div>
            {docsLoad ? (
              <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-14 w-full bg-zinc-800" />)}
              </div>
            ) : recentDocs.length > 0 ? (
              <div className="space-y-1.5">
                {recentDocs.map((doc) => (
                  <Link key={doc.id} href="/library">
                    <div className="flex items-center gap-3 rounded-lg p-2.5 hover:bg-zinc-800/60 transition-colors">
                      <div className="rounded-lg bg-emerald-500/10 p-1.5 shrink-0">
                        <FileText className="h-3.5 w-3.5 text-emerald-400" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-medium text-zinc-300 truncate">{doc.filename}</p>
                        <p className="text-[10px] text-zinc-600">{formatDate(doc.upload_time)}</p>
                      </div>
                      <div className={`h-1.5 w-1.5 rounded-full shrink-0 ${doc.status === "indexed" ? "bg-emerald-500" : "bg-amber-500"}`} />
                    </div>
                  </Link>
                ))}
                <Link href="/library">
                  <Button variant="link" size="sm" className="mt-1 h-auto p-0 text-xs text-zinc-500 hover:text-zinc-300">
                    View all documents <ArrowRight className="h-3 w-3 ml-1" />
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="text-center py-6">
                <Upload className="h-8 w-8 mx-auto mb-2 text-zinc-700" />
                <p className="text-xs text-zinc-600">No documents yet</p>
                <Link href="/library">
                  <Button variant="link" size="sm" className="mt-1 h-auto p-0 text-xs text-zinc-500 hover:text-zinc-300">
                    Upload your first document
                  </Button>
                </Link>
              </div>
            )}
          </div>

          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <div className="flex items-center gap-2 mb-4">
              <BookOpen className="h-4 w-4 text-blue-400" />
              <h2 className="font-semibold text-sm text-zinc-200">Knowledge</h2>
            </div>
            <div className="grid grid-cols-2 gap-3 mb-4">
              <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4 text-center">
                <p className="text-2xl font-bold text-blue-400">{docCount}</p>
                <p className="text-xs text-zinc-500 mt-1">Documents</p>
              </div>
              <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-4 text-center">
                <p className="text-2xl font-bold text-cyan-400">{memCount}</p>
                <p className="text-xs text-zinc-500 mt-1">Memories</p>
              </div>
            </div>
            <div className="space-y-2">
              <Link href="/knowledge">
                <div className="flex items-center justify-between rounded-lg border border-zinc-800 p-3 hover:bg-zinc-800/60 hover:border-zinc-700 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="rounded-lg bg-blue-500/10 p-1.5">
                      <Brain className="h-3.5 w-3.5 text-blue-400" />
                    </div>
                    <div>
                      <p className="text-xs font-medium text-zinc-300">Ask a question</p>
                      <p className="text-[10px] text-zinc-600">Search across all your knowledge</p>
                    </div>
                  </div>
                  <ArrowRight className="h-3.5 w-3.5 text-zinc-600" />
                </div>
              </Link>
              <Link href="/analytics">
                <div className="flex items-center justify-between rounded-lg border border-zinc-800 p-3 hover:bg-zinc-800/60 hover:border-zinc-700 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="rounded-lg bg-emerald-500/10 p-1.5">
                      <BarChart3 className="h-3.5 w-3.5 text-emerald-400" />
                    </div>
                    <div>
                      <p className="text-xs font-medium text-zinc-300">View insights</p>
                      <p className="text-[10px] text-zinc-600">See your usage analytics</p>
                    </div>
                  </div>
                  <ArrowRight className="h-3.5 w-3.5 text-zinc-600" />
                </div>
              </Link>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </div>
  )
}
