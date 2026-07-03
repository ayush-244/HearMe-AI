"use client"

import { useDocuments } from "@/hooks/use-documents"
import { useMemories } from "@/hooks/use-memory"
import { useConversations } from "@/hooks/use-conversations"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { PageShell } from "@/components/ui/page-shell"
import { SurfaceCard } from "@/components/ui/surface-card"
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
import { FEATURE_ACCENTS, ICON_SIZE, MOTION, TYPOGRAPHY } from "@/lib/design-tokens"
import { cn } from "@/lib/utils"

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: MOTION.stagger / 1000 } },
}

const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: MOTION.fade / 1000 } },
}

function Greeting() {
  const hour = new Date().getHours()
  if (hour < 12) return "Good morning"
  if (hour < 17) return "Good afternoon"
  return "Good evening"
}

const suggestionPrompts = [
  { icon: Lightbulb, text: "Summarize my recent documents", accent: FEATURE_ACCENTS.knowledge },
  { icon: Brain, text: "What do you know about me?", accent: FEATURE_ACCENTS.chat },
  { icon: Activity, text: "Analyze my knowledge gaps", accent: FEATURE_ACCENTS.library },
  { icon: BookOpen, text: "Help me learn about a topic", accent: FEATURE_ACCENTS.memory },
]

const quickActions = [
  { icon: MessageSquare, label: "Start Chat", href: "/chat", desc: "Ask questions and get answers", accent: FEATURE_ACCENTS.chat },
  { icon: Upload, label: "Upload Document", href: "/library", desc: "Process PDFs and more", accent: FEATURE_ACCENTS.library },
  { icon: Brain, label: "Explore Knowledge", href: "/knowledge", desc: "Search your knowledge base", accent: FEATURE_ACCENTS.knowledge },
  { icon: Database, label: "View Memories", href: "/memory", desc: "What I remember about you", accent: FEATURE_ACCENTS.memory },
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
    <PageShell maxWidth="wide" className="space-y-8">
      <motion.div variants={container} initial="hidden" animate="show" className="space-y-8">

        <motion.div variants={item} className="space-y-2">
          <div className="flex items-center gap-2 text-caption mb-2">
            <Clock className={ICON_SIZE.sm} />
            <span>{new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" })}</span>
          </div>
          <h1 className={TYPOGRAPHY.pageTitle}>
            {Greeting()}, Ayush 👋
          </h1>
          <p className={TYPOGRAPHY.bodyMuted}>Ready to continue learning?</p>
        </motion.div>

        <motion.div variants={item} className="grid grid-cols-3 gap-3">
          {[
            { label: "Documents", value: docCount, icon: FileText, accent: FEATURE_ACCENTS.library },
            { label: "Conversations", value: convCount, icon: MessageSquare, accent: FEATURE_ACCENTS.chat },
            { label: "Memories", value: memCount, icon: Database, accent: FEATURE_ACCENTS.memory },
          ].map(({ label, value, icon: Icon, accent }) => (
            <SurfaceCard key={label} padding="md" className="flex items-center gap-3">
              <div className="icon-container">
                <Icon className={cn(ICON_SIZE.md, accent)} />
              </div>
              <div>
                <p className="text-xl font-semibold">{value}</p>
                <p className="text-caption">{label}</p>
              </div>
            </SurfaceCard>
          ))}
        </motion.div>

        <motion.div variants={item}>
          <p className="text-overline mb-3">Quick actions</p>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {quickActions.map((action) => (
              <Link key={action.href} href={action.href}>
                <SurfaceCard interactive padding="md" className="group h-full">
                  <div className="flex flex-col gap-3">
                    <div className="icon-container w-fit">
                      <action.icon className={cn(ICON_SIZE.md, action.accent)} />
                    </div>
                    <div>
                      <p className={TYPOGRAPHY.cardTitle}>{action.label}</p>
                      <p className="text-caption mt-1">{action.desc}</p>
                    </div>
                  </div>
                </SurfaceCard>
              </Link>
            ))}
          </div>
        </motion.div>

        <motion.div variants={item} className="grid gap-6 lg:grid-cols-3">
          <SurfaceCard padding="lg" className="lg:col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className={cn(ICON_SIZE.md, FEATURE_ACCENTS.chat)} />
              <h2 className={TYPOGRAPHY.cardTitle}>Suggested Prompts</h2>
            </div>
            <div className="grid gap-2 sm:grid-cols-2">
              {suggestionPrompts.map((p, i) => (
                <Link key={i} href={`/chat?prompt=${encodeURIComponent(p.text)}`}>
                  <div className="flex items-start gap-3 rounded-lg border border-border p-3 hover:bg-accent/50 transition-all duration-200 cursor-pointer group">
                    <div className="icon-container !p-1.5">
                      <p.icon className={cn(ICON_SIZE.sm, p.accent)} />
                    </div>
                    <p className="text-caption group-hover:text-foreground transition-colors">{p.text}</p>
                  </div>
                </Link>
              ))}
            </div>
          </SurfaceCard>

          <SurfaceCard padding="lg">
            <div className="flex items-center gap-2 mb-4">
              <Brain className={cn(ICON_SIZE.md, FEATURE_ACCENTS.memory)} />
              <h2 className={TYPOGRAPHY.cardTitle}>AI Memory</h2>
            </div>
            {memsLoad ? (
              <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
              </div>
            ) : recentMems.length > 0 ? (
              <div className="space-y-2">
                {recentMems.slice(0, 3).map((mem) => (
                  <Link key={mem.memory_id} href="/memory">
                    <div className="flex items-start gap-3 rounded-lg p-2 hover:bg-accent/50 transition-all duration-200">
                      <div className="icon-container !p-1.5 mt-0.5">
                        <Database className={cn(ICON_SIZE.xs, FEATURE_ACCENTS.memory)} />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-caption line-clamp-1">{mem.content}</p>
                        <p className="text-caption opacity-60 mt-0.5">{formatDate(mem.created_at)}</p>
                      </div>
                    </div>
                  </Link>
                ))}
                <Link href="/memory">
                  <Button variant="link" size="sm" className="mt-1 h-auto p-0 text-caption">
                    View all memories <ArrowRight className={cn(ICON_SIZE.xs, "ml-1")} />
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="text-center py-6">
                <Brain className={cn(ICON_SIZE.xl, "mx-auto mb-2 text-muted-foreground/40")} />
                <p className="text-caption">No memories yet</p>
                <p className="text-caption opacity-60 mt-1">Start chatting to build your memory</p>
              </div>
            )}
          </SurfaceCard>
        </motion.div>

        <motion.div variants={item} className="grid gap-6 lg:grid-cols-2">
          <SurfaceCard padding="lg">
            <div className="flex items-center gap-2 mb-4">
              <FileText className={cn(ICON_SIZE.md, FEATURE_ACCENTS.library)} />
              <h2 className={TYPOGRAPHY.cardTitle}>Recent Documents</h2>
            </div>
            {docsLoad ? (
              <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-14 w-full" />)}
              </div>
            ) : recentDocs.length > 0 ? (
              <div className="space-y-2">
                {recentDocs.map((doc) => (
                  <Link key={doc.id} href="/library">
                    <div className="flex items-center gap-3 rounded-lg p-2 hover:bg-accent/50 transition-all duration-200">
                      <div className="icon-container !p-1.5">
                        <FileText className={cn(ICON_SIZE.sm, FEATURE_ACCENTS.library)} />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-caption font-medium truncate">{doc.filename}</p>
                        <p className="text-caption opacity-60">{formatDate(doc.upload_time)}</p>
                      </div>
                      <div className={cn("h-1.5 w-1.5 rounded-full shrink-0", doc.status === "indexed" ? "bg-emerald-500" : "bg-amber-500")} />
                    </div>
                  </Link>
                ))}
                <Link href="/library">
                  <Button variant="link" size="sm" className="mt-1 h-auto p-0 text-caption">
                    View all documents <ArrowRight className={cn(ICON_SIZE.xs, "ml-1")} />
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="text-center py-6">
                <Upload className={cn(ICON_SIZE.xl, "mx-auto mb-2 text-muted-foreground/40")} />
                <p className="text-caption">No documents yet</p>
                <Link href="/library">
                  <Button variant="link" size="sm" className="mt-1 h-auto p-0 text-caption">
                    Upload your first document
                  </Button>
                </Link>
              </div>
            )}
          </SurfaceCard>

          <SurfaceCard padding="lg">
            <div className="flex items-center gap-2 mb-4">
              <BookOpen className={cn(ICON_SIZE.md, FEATURE_ACCENTS.chat)} />
              <h2 className={TYPOGRAPHY.cardTitle}>Knowledge</h2>
            </div>
            <div className="grid grid-cols-2 gap-3 mb-4">
              <SurfaceCard padding="md" className="text-center">
                <p className={cn("text-2xl font-semibold", FEATURE_ACCENTS.library)}>{docCount}</p>
                <p className="text-caption mt-1">Documents</p>
              </SurfaceCard>
              <SurfaceCard padding="md" className="text-center">
                <p className={cn("text-2xl font-semibold", FEATURE_ACCENTS.memory)}>{memCount}</p>
                <p className="text-caption mt-1">Memories</p>
              </SurfaceCard>
            </div>
            <div className="space-y-2">
              <Link href="/knowledge">
                <div className="flex items-center justify-between rounded-lg border border-border p-3 hover:bg-accent/50 transition-all duration-200">
                  <div className="flex items-center gap-3">
                    <div className="icon-container !p-1.5">
                      <Brain className={cn(ICON_SIZE.sm, FEATURE_ACCENTS.knowledge)} />
                    </div>
                    <div>
                      <p className="text-caption font-medium">Ask a question</p>
                      <p className="text-caption opacity-60">Search across all your knowledge</p>
                    </div>
                  </div>
                  <ArrowRight className={cn(ICON_SIZE.sm, "text-muted-foreground")} />
                </div>
              </Link>
              <Link href="/analytics">
                <div className="flex items-center justify-between rounded-lg border border-border p-3 hover:bg-accent/50 transition-all duration-200">
                  <div className="flex items-center gap-3">
                    <div className="icon-container !p-1.5">
                      <BarChart3 className={cn(ICON_SIZE.sm, FEATURE_ACCENTS.analytics)} />
                    </div>
                    <div>
                      <p className="text-caption font-medium">View insights</p>
                      <p className="text-caption opacity-60">See your usage analytics</p>
                    </div>
                  </div>
                  <ArrowRight className={cn(ICON_SIZE.sm, "text-muted-foreground")} />
                </div>
              </Link>
            </div>
          </SurfaceCard>
        </motion.div>
      </motion.div>
    </PageShell>
  )
}
