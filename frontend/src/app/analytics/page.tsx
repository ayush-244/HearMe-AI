"use client"

import { useDocuments } from "@/hooks/use-documents"
import { useMemories } from "@/hooks/use-memory"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import {
  BarChart3,
  MessageSquare,
  FileText,
  Brain,
  Clock,
  TrendingUp,
  Calendar,
  Activity,
  BookOpen,
} from "lucide-react"
import { PageShell } from "@/components/ui/page-shell"
import { PageHeader } from "@/components/ui/page-header"
import { FEATURE_ACCENTS, ICON_SIZE } from "@/lib/design-tokens"
import { cn } from "@/lib/utils"
import { motion } from "framer-motion"

function formatNumber(n: number) {
  if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`
  if (n >= 1000) return `${(n / 1000).toFixed(1)}K`
  return n.toString()
}

const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
function WeeklyChart({ data }: { data: number[] }) {
  const max = Math.max(...data, 1)
  return (
    <div className="flex items-end gap-2 h-32">
      {data.map((value, i) => (
        <div key={i} className="flex-1 flex flex-col items-center gap-1">
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: `${(value / max) * 100}%` }}
            transition={{ duration: 0.5, delay: i * 0.05, ease: "easeOut" }}
            className="w-full rounded-t-md bg-gradient-to-t from-primary/60 to-primary/30"
            style={{ minHeight: value > 0 ? 4 : 0 }}
          />
          <span className="text-[10px] text-muted-foreground">{days[i]}</span>
        </div>
      ))}
    </div>
  )
}

function StatCard({ icon: Icon, label, value, sub, accent }: {
  icon: React.ElementType
  label: string
  value: string | number
  sub?: string
  accent: string
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      <Card>
        <CardContent className="p-5">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <p className="text-caption">{label}</p>
              <p className="text-3xl font-semibold text-foreground">{value}</p>
              {sub && <p className="text-caption">{sub}</p>}
            </div>
            <div className="icon-container">
              <Icon className={cn(ICON_SIZE.lg, accent)} />
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}

export default function AnalyticsPage() {
  const { data: docs, isLoading: docsLoad } = useDocuments()
  const { data: mems, isLoading: memsLoad } = useMemories({ include_working: true })

  const docCount = docs?.count ?? 0
  const memCount = mems?.count ?? 0
  const indexedCount = docs?.documents?.filter((d) => d.status === "indexed").length ?? 0

  const weeklyActivity = [3, 7, 2, 5, 8, 4, 6]
  const totalSize = docs?.documents?.reduce((acc, d) => acc + d.size, 0) ?? 0
  const avgResponseTime = "1.2s"

  return (
    <PageShell maxWidth="full">
      <PageHeader title="Analytics" description="Your usage and activity overview." icon={BarChart3} />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {docsLoad || memsLoad ? (
          Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-32" />)
        ) : (
          <>
            <StatCard
              icon={FileText}
              label="Documents Uploaded"
              value={docCount}
              sub={indexedCount > 0 ? `${indexedCount} indexed` : "No documents yet"}
              accent={FEATURE_ACCENTS.library}
            />
            <StatCard
              icon={MessageSquare}
              label="Questions Asked"
              value={12}
              sub="Across all sessions"
              accent={FEATURE_ACCENTS.chat}
            />
            <StatCard
              icon={Brain}
              label="Knowledge Searches"
              value={8}
              sub="Using your documents"
              accent={FEATURE_ACCENTS.knowledge}
            />
            <StatCard
              icon={Clock}
              label="Avg Response Time"
              value={avgResponseTime}
              sub="Last 30 days"
              accent={FEATURE_ACCENTS.developer}
            />
          </>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-section-title">
              <Activity className={cn(ICON_SIZE.lg, "text-muted-foreground")} />
              Weekly Activity
            </CardTitle>
          </CardHeader>
          <CardContent>
            <WeeklyChart data={weeklyActivity} />
            <div className="flex items-center justify-between mt-4 text-xs text-muted-foreground">
              <span>Last 7 days</span>
              <span className="flex items-center gap-1">
                <TrendingUp className="h-3 w-3 text-emerald-500" />
                +12% vs last week
              </span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-section-title">
              <Calendar className={cn(ICON_SIZE.lg, "text-muted-foreground")} />
              Summary
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="icon-container">
                  <FileText className={cn(ICON_SIZE.md, FEATURE_ACCENTS.library)} />
                </div>
                <div>
                  <p className="text-sm font-medium">Total Documents</p>
                  <p className="text-xs text-muted-foreground">{docCount} files</p>
                </div>
              </div>
              <p className="text-lg font-bold">{formatNumber(docCount)}</p>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="icon-container">
                  <Brain className={cn(ICON_SIZE.md, FEATURE_ACCENTS.memory)} />
                </div>
                <div>
                  <p className="text-sm font-medium">AI Memories</p>
                  <p className="text-xs text-muted-foreground">{memCount} entries</p>
                </div>
              </div>
              <p className="text-lg font-bold">{formatNumber(memCount)}</p>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="icon-container">
                  <Clock className={cn(ICON_SIZE.md, FEATURE_ACCENTS.developer)} />
                </div>
                <div>
                  <p className="text-sm font-medium">Most Active Day</p>
                  <p className="text-xs text-muted-foreground">{new Date().toLocaleDateString("en-US", { weekday: "long" })}</p>
                </div>
              </div>
              <p className="text-lg font-bold">{new Date().toLocaleDateString("en-US", { weekday: "short" })}</p>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="icon-container">
                  <BookOpen className={cn(ICON_SIZE.md, FEATURE_ACCENTS.chat)} />
                </div>
                <div>
                  <p className="text-sm font-medium">Total Storage</p>
                  <p className="text-xs text-muted-foreground">{totalSize > 0 ? `${(totalSize / 1024 / 1024).toFixed(1)} MB` : "0 MB"}</p>
                </div>
              </div>
              <p className="text-lg font-bold">{totalSize > 0 ? `${(totalSize / 1024 / 1024).toFixed(1)} MB` : "0 MB"}</p>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-section-title">
            <Activity className={cn(ICON_SIZE.lg, "text-muted-foreground")} />
            Recent Activity
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[
              { action: "Documents Uploaded", count: docCount, icon: FileText, accent: FEATURE_ACCENTS.library, time: "All time" },
              { action: "Memories Stored", count: memCount, icon: Brain, accent: FEATURE_ACCENTS.memory, time: "All time" },
              { action: "Conversations", count: 6, icon: MessageSquare, accent: FEATURE_ACCENTS.chat, time: "This session" },
              { action: "Knowledge Queries", count: 8, icon: BookOpen, accent: FEATURE_ACCENTS.knowledge, time: "Last 30 days" },
            ].map((item, i) => (
              <div key={i} className="flex items-center justify-between rounded-lg border border-border p-3 hover:bg-accent/50 transition-all duration-200">
                <div className="flex items-center gap-3">
                  <div className="icon-container">
                    <item.icon className={cn(ICON_SIZE.md, item.accent)} />
                  </div>
                  <div>
                    <p className="text-sm font-medium">{item.action}</p>
                    <p className="text-xs text-muted-foreground">{item.time}</p>
                  </div>
                </div>
                <p className="text-lg font-bold">{item.count}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </PageShell>
  )
}
