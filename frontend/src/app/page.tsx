"use client"

import { useDocuments } from "@/hooks/use-documents"
import { useMemories } from "@/hooks/use-memory"
import { useHealth, useSearchHealth, useKnowledgeHealth, useVectorStoreHealth } from "@/hooks/use-health"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import Link from "next/link"
import {
  MessageSquare,
  Brain,
  Database,
  FileText,
  Upload,
  Search,
  Sparkles,
  ArrowRight,
  Clock,
  CheckCircle2,
  AlertCircle,
  BarChart3,
} from "lucide-react"
import { formatDate, formatTime } from "@/lib/utils"
import { motion } from "framer-motion"

function StatCard({ icon: Icon, label, value, sub, href, color }: {
  icon: React.ElementType; label: string; value: string | number; sub?: string; href?: string; color?: string
}) {
  const content = (
    <Card className="hover:shadow-md transition-shadow cursor-pointer">
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <p className="text-sm text-muted-foreground">{label}</p>
            <p className={`text-2xl font-bold ${color || ""}`}>{value}</p>
            {sub && <p className="text-xs text-muted-foreground">{sub}</p>}
          </div>
          <div className={`rounded-lg p-2.5 ${color ? `${color}/10` : "bg-primary/10"}`}>
            <Icon className={`h-5 w-5 ${color || "text-primary"}`} />
          </div>
        </div>
      </CardContent>
    </Card>
  )
  return href ? <Link href={href}>{content}</Link> : content
}

export default function Home() {
  const { data: docs, isLoading: docsLoad } = useDocuments()
  const { data: mems } = useMemories()
  const { data: health } = useHealth()
  const { data: searchHealth } = useSearchHealth()
  const { data: khRaw } = useKnowledgeHealth()
  const { data: vectorHealth } = useVectorStoreHealth()
  const kh = (khRaw ?? {}) as Record<string, unknown>

  const docCount = docs?.count ?? 0
  const memCount = mems?.count ?? 0
  const allReady = health?.ready && searchHealth?.ready

  const recentDocs = docs?.documents?.slice(0, 4) ?? []

  return (
    <div className="p-6 lg:p-8 space-y-8">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight">
          Welcome to <span className="text-primary">HearMe AI</span>
        </h1>
        <p className="text-muted-foreground text-lg">
          Your intelligent knowledge platform with AI-powered search, reasoning, and memory.
        </p>
      </motion.div>

      <div className="grid gap-4 grid-cols-2 md:grid-cols-4">
        <StatCard icon={Brain} label="Knowledge Chunks" value={String(kh["chunk_count"] ?? "—")} sub="Indexed documents" href="/knowledge" color="text-blue-500" />
        <StatCard icon={Database} label="Memories" value={memCount} sub="Personal facts & preferences" href="/memory" color="text-purple-500" />
        <StatCard icon={FileText} label="Documents" value={docCount} sub={docCount > 0 ? "Uploaded files" : "No uploads yet"} href="/documents" color="text-emerald-500" />
        <StatCard icon={BarChart3} label="System" value={allReady ? "Healthy" : "Issues"} sub={allReady ? "All services online" : "Check analytics"} color={allReady ? "text-emerald-500" : "text-amber-500"} />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <MessageSquare className="h-5 w-5 text-primary" />
              Quick Actions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 sm:grid-cols-2">
              <Link href="/chat">
                <div className="rounded-lg border p-4 hover:bg-accent transition-colors space-y-2">
                  <div className="flex items-center gap-2">
                    <MessageSquare className="h-4 w-4 text-primary" />
                    <span className="font-medium">Chat with AI</span>
                  </div>
                  <p className="text-sm text-muted-foreground">Ask questions and get grounded answers</p>
                </div>
              </Link>
              <Link href="/documents">
                <div className="rounded-lg border p-4 hover:bg-accent transition-colors space-y-2">
                  <div className="flex items-center gap-2">
                    <Upload className="h-4 w-4 text-primary" />
                    <span className="font-medium">Upload Document</span>
                  </div>
                  <p className="text-sm text-muted-foreground">Process PDFs, DOCX, and more</p>
                </div>
              </Link>
              <Link href="/knowledge">
                <div className="rounded-lg border p-4 hover:bg-accent transition-colors space-y-2">
                  <div className="flex items-center gap-2">
                    <Brain className="h-4 w-4 text-primary" />
                    <span className="font-medium">Explore Knowledge</span>
                  </div>
                  <p className="text-sm text-muted-foreground">Browse indexed chunks and search</p>
                </div>
              </Link>
              <Link href="/memory">
                <div className="rounded-lg border p-4 hover:bg-accent transition-colors space-y-2">
                  <div className="flex items-center gap-2">
                    <Database className="h-4 w-4 text-primary" />
                    <span className="font-medium">View Memories</span>
                  </div>
                  <p className="text-sm text-muted-foreground">Your personal semantic memory</p>
                </div>
              </Link>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Clock className="h-5 w-5 text-primary" />
              Recent Uploads
            </CardTitle>
          </CardHeader>
          <CardContent>
            {docsLoad ? (
              <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-12 w-full" />)}
              </div>
            ) : recentDocs.length > 0 ? (
              <div className="space-y-3">
                {recentDocs.map((doc) => (
                  <Link key={doc.id} href={`/documents`}>
                    <div className="flex items-center gap-3 rounded-lg p-2 hover:bg-accent transition-colors">
                      <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium truncate">{doc.filename}</p>
                        <p className="text-xs text-muted-foreground">{formatDate(doc.upload_time)}</p>
                      </div>
                      <Badge variant={doc.status === "uploaded" ? "warning" : "success"} className="shrink-0">
                        {doc.status}
                      </Badge>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="text-center py-6 text-muted-foreground">
                <Upload className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No documents yet</p>
                <Link href="/documents">
                  <Button variant="link" className="mt-1">Upload your first document</Button>
                </Link>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <CheckCircle2 className="h-5 w-5 text-primary" />
            System Health
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { label: "API Server", ok: health?.ready, icon: Sparkles },
              { label: "Search Engine", ok: searchHealth?.ready, icon: Search },
              { label: "Knowledge Engine", ok: kh["ready"] as boolean, icon: Brain },
              { label: "Vector Store", ok: vectorHealth?.ready, icon: Database },
            ].map(({ label, ok, icon: Icon }) => (
              <div key={label} className="flex items-center gap-3 rounded-lg border p-3">
                <Icon className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm flex-1">{label}</span>
                {ok === undefined ? (
                  <Skeleton className="h-4 w-16" />
                ) : ok ? (
                  <Badge variant="success">Online</Badge>
                ) : (
                  <Badge variant="destructive">Offline</Badge>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
