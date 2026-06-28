"use client"

import { useDocuments } from "@/hooks/use-documents"
import { useMemories } from "@/hooks/use-memory"
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
} from "lucide-react"
import { formatDate } from "@/lib/utils"
import { motion } from "framer-motion"

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.08 } },
}

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
}

function Greeting() {
  const hour = new Date().getHours()
  if (hour < 12) return "Good morning"
  if (hour < 17) return "Good afternoon"
  return "Good evening"
}

const suggestionPrompts = [
  { icon: Lightbulb, text: "Summarize my recent documents", color: "text-amber-500", bg: "bg-amber-500/10" },
  { icon: Brain, text: "What do you know about me?", color: "text-purple-500", bg: "bg-purple-500/10" },
  { icon: BarChart3, text: "Analyze my knowledge gaps", color: "text-blue-500", bg: "bg-blue-500/10" },
  { icon: BookOpen, text: "Help me learn about a topic", color: "text-emerald-500", bg: "bg-emerald-500/10" },
]

const quickActions = [
  { icon: MessageSquare, label: "Start Chat", href: "/chat", desc: "Ask questions and get answers", color: "from-blue-500 to-violet-500" },
  { icon: Upload, label: "Upload Document", href: "/documents", desc: "Process PDFs and more", color: "from-emerald-500 to-teal-500" },
  { icon: Brain, label: "Explore Knowledge", href: "/knowledge", desc: "Search your knowledge base", color: "from-purple-500 to-pink-500" },
  { icon: Database, label: "View Memories", href: "/memory", desc: "What I remember about you", color: "from-amber-500 to-orange-500" },
]

export default function Home() {
  const { data: docs, isLoading: docsLoad } = useDocuments()
  const { data: mems, isLoading: memsLoad } = useMemories()

  const docCount = docs?.count ?? 0
  const memCount = mems?.count ?? 0
  const recentDocs = docs?.documents?.slice(0, 5) ?? []
  const recentMems = mems?.memories?.slice(0, 4) ?? []

  return (
    <div className="p-6 lg:p-8 space-y-8">
      <motion.div variants={container} initial="hidden" animate="show" className="space-y-8">
        <motion.div variants={item} className="space-y-2">
          <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
            <Clock className="h-4 w-4" />
            <span>{new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}</span>
          </div>
          <h1 className="text-4xl font-bold tracking-tight">
            {Greeting()}
            <span className="text-primary">.</span>
          </h1>
          <p className="text-lg text-muted-foreground">What would you like to do today?</p>
        </motion.div>

        <motion.div variants={item} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {quickActions.map((action) => (
            <Link key={action.href} href={action.href}>
              <Card className="group relative overflow-hidden border-0 shadow-md hover:shadow-xl transition-all duration-300 cursor-pointer">
                <div className={`absolute inset-0 bg-gradient-to-br ${action.color} opacity-10 group-hover:opacity-20 transition-opacity`} />
                <CardContent className="p-5 relative">
                  <div className={`rounded-xl p-2.5 w-fit mb-3 ${action.color.replace("from-", "bg-").replace(" to-", "/10")} bg-opacity-10`}>
                    <action.icon className={`h-5 w-5 ${action.color.split(" ")[0].replace("from-", "text-")}`} />
                  </div>
                  <p className="font-semibold">{action.label}</p>
                  <p className="text-sm text-muted-foreground mt-1">{action.desc}</p>
                </CardContent>
              </Card>
            </Link>
          ))}
        </motion.div>

        <motion.div variants={item} className="grid gap-6 lg:grid-cols-3">
          <Card className="lg:col-span-2 border-0 shadow-md">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <Sparkles className="h-5 w-5 text-primary" />
                Suggested Prompts
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-3 sm:grid-cols-2">
                {suggestionPrompts.map((p, i) => (
                  <Link key={i} href={`/chat?prompt=${encodeURIComponent(p.text)}`}>
                    <div className="rounded-xl border p-4 hover:bg-accent transition-all duration-200 space-y-2 group cursor-pointer">
                      <div className={`rounded-lg p-2 w-fit ${p.bg} group-hover:scale-110 transition-transform`}>
                        <p.icon className={`h-4 w-4 ${p.color}`} />
                      </div>
                      <p className="text-sm font-medium">{p.text}</p>
                    </div>
                  </Link>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-md">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <Brain className="h-5 w-5 text-purple-500" />
                AI Memory Summary
              </CardTitle>
            </CardHeader>
            <CardContent>
              {memsLoad ? (
                <div className="space-y-3">
                  {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
                </div>
              ) : recentMems.length > 0 ? (
                <div className="space-y-2">
                  {recentMems.slice(0, 3).map((mem) => (
                    <Link key={mem.memory_id} href="/memory">
                      <div className="flex items-start gap-3 rounded-lg p-2 hover:bg-accent transition-colors">
                        <div className="rounded-full bg-purple-500/10 p-1.5 mt-0.5">
                          <Database className="h-3 w-3 text-purple-500" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-sm line-clamp-1">{mem.content}</p>
                          <p className="text-xs text-muted-foreground mt-0.5">{formatDate(mem.created_at)}</p>
                        </div>
                      </div>
                    </Link>
                  ))}
                  <Link href="/memory">
                    <Button variant="link" size="sm" className="mt-1 h-auto p-0 text-xs">
                      View all memories <ArrowRight className="h-3 w-3 ml-1" />
                    </Button>
                  </Link>
                </div>
              ) : (
                <div className="text-center py-6 text-muted-foreground">
                  <Brain className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No memories yet</p>
                  <p className="text-xs mt-1">Start chatting to build your memory</p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div variants={item} className="grid gap-6 lg:grid-cols-2">
          <Card className="border-0 shadow-md">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <FileText className="h-5 w-5 text-emerald-500" />
                Recent Documents
              </CardTitle>
            </CardHeader>
            <CardContent>
              {docsLoad ? (
                <div className="space-y-3">
                  {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-14 w-full" />)}
                </div>
              ) : recentDocs.length > 0 ? (
                <div className="space-y-2">
                  {recentDocs.map((doc) => (
                    <Link key={doc.id} href="/documents">
                      <div className="flex items-center gap-3 rounded-lg p-2.5 hover:bg-accent transition-colors">
                        <div className="rounded-lg bg-emerald-500/10 p-2">
                          <FileText className="h-4 w-4 text-emerald-500" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium truncate">{doc.filename}</p>
                          <p className="text-xs text-muted-foreground">{formatDate(doc.upload_time)}</p>
                        </div>
                        <div className="shrink-0">
                          <div className={`h-2 w-2 rounded-full ${doc.status === "indexed" ? "bg-emerald-500" : "bg-amber-500"}`} />
                        </div>
                      </div>
                    </Link>
                  ))}
                  <Link href="/documents">
                    <Button variant="link" size="sm" className="mt-1 h-auto p-0 text-xs">
                      View all documents <ArrowRight className="h-3 w-3 ml-1" />
                    </Button>
                  </Link>
                </div>
              ) : (
                <div className="text-center py-6 text-muted-foreground">
                  <Upload className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No documents yet</p>
                  <Link href="/documents">
                    <Button variant="link" size="sm" className="mt-1 h-auto p-0 text-xs">
                      Upload your first document
                    </Button>
                  </Link>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="border-0 shadow-md">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <BookOpen className="h-5 w-5 text-blue-500" />
                Knowledge Summary
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="rounded-xl bg-gradient-to-br from-blue-500/10 to-purple-500/10 p-4 text-center">
                  <p className="text-2xl font-bold text-blue-500">{docCount > 0 ? docCount : 0}</p>
                  <p className="text-xs text-muted-foreground mt-1">Documents</p>
                </div>
                <div className="rounded-xl bg-gradient-to-br from-purple-500/10 to-pink-500/10 p-4 text-center">
                  <p className="text-2xl font-bold text-purple-500">{memCount > 0 ? memCount : 0}</p>
                  <p className="text-xs text-muted-foreground mt-1">Memories</p>
                </div>
              </div>
              <div className="space-y-2">
                <Link href="/knowledge">
                  <div className="flex items-center justify-between rounded-lg border p-3 hover:bg-accent transition-colors">
                    <div className="flex items-center gap-3">
                      <div className="rounded-lg bg-blue-500/10 p-2">
                        <Brain className="h-4 w-4 text-blue-500" />
                      </div>
                      <div>
                        <p className="text-sm font-medium">Ask a question</p>
                        <p className="text-xs text-muted-foreground">Search across all your knowledge</p>
                      </div>
                    </div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  </div>
                </Link>
                <Link href="/analytics">
                  <div className="flex items-center justify-between rounded-lg border p-3 hover:bg-accent transition-colors">
                    <div className="flex items-center gap-3">
                      <div className="rounded-lg bg-emerald-500/10 p-2">
                        <BarChart3 className="h-4 w-4 text-emerald-500" />
                      </div>
                      <div>
                        <p className="text-sm font-medium">View insights</p>
                        <p className="text-xs text-muted-foreground">See your usage analytics</p>
                      </div>
                    </div>
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  </div>
                </Link>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>
    </div>
  )
}
