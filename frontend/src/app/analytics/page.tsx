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

function StatCard({ icon: Icon, label, value, sub, color, gradient }: {
  icon: React.ElementType
  label: string
  value: string | number
  sub?: string
  color: string
  gradient: string
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className="border-0 shadow-md overflow-hidden">
        <div className={`h-1 ${gradient}`} />
        <CardContent className="p-5">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">{label}</p>
              <p className={`text-3xl font-bold ${color}`}>{value}</p>
              {sub && <p className="text-xs text-muted-foreground">{sub}</p>}
            </div>
            <div className={`rounded-xl ${gradient.replace("from-", "bg-").replace(" to-", "/10")} bg-opacity-10 p-3`}>
              <Icon className={`h-5 w-5 ${color}`} />
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
    <div className="p-6 lg:p-8 space-y-6">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
          <BarChart3 className="h-8 w-8 text-primary" />
          Analytics
        </h1>
        <p className="text-muted-foreground">Your usage and activity overview.</p>
      </motion.div>

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
              color="text-emerald-500"
              gradient="from-emerald-500 to-emerald-400"
            />
            <StatCard
              icon={MessageSquare}
              label="Questions Asked"
              value={12}
              sub="Across all sessions"
              color="text-blue-500"
              gradient="from-blue-500 to-blue-400"
            />
            <StatCard
              icon={Brain}
              label="Knowledge Searches"
              value={8}
              sub="Using your documents"
              color="text-purple-500"
              gradient="from-purple-500 to-purple-400"
            />
            <StatCard
              icon={Clock}
              label="Avg Response Time"
              value={avgResponseTime}
              sub="Last 30 days"
              color="text-amber-500"
              gradient="from-amber-500 to-amber-400"
            />
          </>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2 border-0 shadow-md">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Activity className="h-5 w-5 text-primary" />
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

        <Card className="border-0 shadow-md">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-lg">
              <Calendar className="h-5 w-5 text-primary" />
              Summary
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-emerald-500/10 p-2">
                  <FileText className="h-4 w-4 text-emerald-500" />
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
                <div className="rounded-lg bg-purple-500/10 p-2">
                  <Brain className="h-4 w-4 text-purple-500" />
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
                <div className="rounded-lg bg-amber-500/10 p-2">
                  <Clock className="h-4 w-4 text-amber-500" />
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
                <div className="rounded-lg bg-blue-500/10 p-2">
                  <BookOpen className="h-4 w-4 text-blue-500" />
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

      <Card className="border-0 shadow-md">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Activity className="h-5 w-5 text-primary" />
            Recent Activity
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[
              { action: "Documents Uploaded", count: docCount, icon: FileText, color: "text-emerald-500", bg: "bg-emerald-500/10", time: "All time" },
              { action: "Memories Stored", count: memCount, icon: Brain, color: "text-purple-500", bg: "bg-purple-500/10", time: "All time" },
              { action: "Conversations", count: 6, icon: MessageSquare, color: "text-blue-500", bg: "bg-blue-500/10", time: "This session" },
              { action: "Knowledge Queries", count: 8, icon: BookOpen, color: "text-amber-500", bg: "bg-amber-500/10", time: "Last 30 days" },
            ].map((item, i) => (
              <div key={i} className="flex items-center justify-between rounded-lg border p-3 hover:bg-accent/50 transition-colors">
                <div className="flex items-center gap-3">
                  <div className={`rounded-lg ${item.bg} p-2`}>
                    <item.icon className={`h-4 w-4 ${item.color}`} />
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
    </div>
  )
}
