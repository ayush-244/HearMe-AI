"use client"

import { useDocuments } from "@/hooks/use-documents"
import { useMemories, useMemoryHealth } from "@/hooks/use-memory"
import { useHealth, useSearchHealth, useKnowledgeHealth, useVectorStoreHealth } from "@/hooks/use-health"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { BarChart3, Brain, Database, FileText, Search, Zap, Clock, CheckCircle2, Sparkles, Activity } from "lucide-react"

function safeStr(val: unknown, fallback = "—"): string {
  if (val === null || val === undefined) return fallback
  return String(val)
}

function safeNum(val: unknown, fallback = 0): number {
  if (typeof val === "number") return val
  return fallback
}

function safeBool(val: unknown): boolean {
  return val === true
}

function MetricRow({ label, value, sub, icon: Icon }: { label: string; value: React.ReactNode; sub?: string; icon: React.ElementType }) {
  return (
    <div className="flex items-center justify-between rounded-lg border p-3">
      <div className="flex items-center gap-3">
        <div className="rounded-lg bg-primary/10 p-2">
          <Icon className="h-4 w-4 text-primary" />
        </div>
        <div>
          <p className="text-sm font-medium">{label}</p>
          {sub && <p className="text-xs text-muted-foreground">{sub}</p>}
        </div>
      </div>
      <p className="text-lg font-bold">{value}</p>
    </div>
  )
}

function StatCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">{children}</CardContent>
    </Card>
  )
}

export default function AnalyticsPage() {
  const { data: docs } = useDocuments()
  const { data: mems } = useMemories({ include_working: true })
  const { data: memHealth } = useMemoryHealth()
  const { data: hRaw } = useHealth()
  const { data: shRaw } = useSearchHealth()
  const { data: khRaw } = useKnowledgeHealth()
  const { data: vhRaw } = useVectorStoreHealth()

  const h = (hRaw ?? {}) as Record<string, unknown>
  const sh = (shRaw ?? {}) as Record<string, unknown>
  const kh = (khRaw ?? {}) as Record<string, unknown>
  const vh = (vhRaw ?? {}) as Record<string, unknown>

  const docCount = docs?.count ?? 0
  const memCount = mems?.count ?? 0
  const mc = (memHealth?.memory_count ?? {}) as Record<string, number>

  return (
    <div className="p-6 lg:p-8 space-y-6">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
          <BarChart3 className="h-8 w-8 text-primary" />
          Analytics
        </h1>
        <p className="text-muted-foreground">System metrics, usage statistics, and health monitoring.</p>
      </div>

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview"><Activity className="h-4 w-4 mr-2" />Overview</TabsTrigger>
          <TabsTrigger value="knowledge"><Brain className="h-4 w-4 mr-2" />Knowledge</TabsTrigger>
          <TabsTrigger value="memory"><Database className="h-4 w-4 mr-2" />Memory</TabsTrigger>
          <TabsTrigger value="system"><Zap className="h-4 w-4 mr-2" />System</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6 mt-6">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Documents</CardTitle></CardHeader>
              <CardContent><p className="text-3xl font-bold">{docCount}</p></CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Memories</CardTitle></CardHeader>
              <CardContent><p className="text-3xl font-bold">{memCount}</p></CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Chunks Indexed</CardTitle></CardHeader>
              <CardContent><p className="text-3xl font-bold">{safeStr(kh["chunk_count"])}</p></CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">System Status</CardTitle></CardHeader>
              <CardContent>
                <Badge variant={safeBool(h["ready"]) ? "success" : "destructive"} className="text-sm">
                  {safeBool(h["ready"]) ? "Healthy" : "Issues"}
                </Badge>
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <StatCard title="Knowledge Engine">
              <MetricRow icon={Brain} label="Chunks" value={safeStr(kh["chunk_count"])} />
              <MetricRow icon={FileText} label="Sources" value={safeStr(kh["sources_count"])} />
              <MetricRow icon={Clock} label="Max Context Tokens" value={safeStr(kh["context_builder_max_tokens"])} />
              <MetricRow icon={CheckCircle2} label="Validation" value={safeBool(kh["ready"]) ? "Active" : "Off"} />
            </StatCard>

            <StatCard title="Search Engine">
              <MetricRow icon={Search} label="Default Top-K" value={safeStr(sh["default_top_k"])} />
              <MetricRow icon={Brain} label="Semantic Weight" value={sh["semantic_weight"] ? `${(safeNum(sh["semantic_weight"]) * 100).toFixed(0)}%` : "—"} />
              <MetricRow icon={Zap} label="Keyword Weight" value={sh["keyword_weight"] ? `${(safeNum(sh["keyword_weight"]) * 100).toFixed(0)}%` : "—"} />
              <MetricRow icon={Activity} label="BM25 Backend" value={safeStr(sh["keyword_backend"])} />
            </StatCard>
          </div>
        </TabsContent>

        <TabsContent value="knowledge" className="space-y-6 mt-6">
          <div className="grid gap-4 md:grid-cols-2">
            <StatCard title="Chunk Configuration">
              <MetricRow icon={FileText} label="Max Chunks" value={safeStr(kh["context_builder_max_chunks"])} />
              <MetricRow icon={FileText} label="Max Tokens" value={safeStr(kh["context_builder_max_tokens"])} />
              <MetricRow icon={Sparkles} label="Citation Style" value={safeStr(kh["citation_style"])} />
            </StatCard>
            <StatCard title="Conversation State">
              <MetricRow icon={Clock} label="History Limit" value={safeStr(kh["conversation_history_limit"])} />
              <MetricRow icon={Activity} label="Active Conversations" value={safeStr(kh["active_conversations"])} />
              <MetricRow icon={CheckCircle2} label="External Knowledge" value={safeBool(kh["allow_external_knowledge"]) ? "Allowed" : "Disabled"} />
            </StatCard>
          </div>
        </TabsContent>

        <TabsContent value="memory" className="space-y-6 mt-6">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Semantic</CardTitle></CardHeader>
              <CardContent><p className="text-3xl font-bold text-blue-500">{safeNum(mc["semantic"])}</p></CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Episodic</CardTitle></CardHeader>
              <CardContent><p className="text-3xl font-bold text-green-500">{safeNum(mc["episodic"])}</p></CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Preferences</CardTitle></CardHeader>
              <CardContent><p className="text-3xl font-bold text-purple-500">{safeNum(mc["preference"])}</p></CardContent>
            </Card>
            <Card>
              <CardHeader className="pb-2"><CardTitle className="text-sm text-muted-foreground">Working</CardTitle></CardHeader>
              <CardContent><p className="text-3xl font-bold text-amber-500">{safeNum(mc["working"])}</p></CardContent>
            </Card>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <StatCard title="Memory Configuration">
              <MetricRow icon={Zap} label="Threshold" value={safeStr(memHealth?.memory_threshold)} />
              <MetricRow icon={Clock} label="Forgetting Rate" value={safeStr(memHealth?.forgetting_rate)} />
              <MetricRow icon={Activity} label="Importance Decay" value={safeStr(memHealth?.importance_decay)} />
              <MetricRow icon={CheckCircle2} label="Auto-Consolidation" value={memHealth?.auto_consolidation_enabled ? "On" : "Off"} />
            </StatCard>
          </div>
        </TabsContent>

        <TabsContent value="system" className="space-y-6 mt-6">
          <div className="grid gap-4 md:grid-cols-2">
            {[
              { label: "API Server", ok: safeBool(h["ready"]), icon: Zap },
              { label: "Search Engine", ok: safeBool(sh["ready"]), icon: Search },
              { label: "Knowledge Engine", ok: safeBool(kh["ready"]), icon: Brain },
              { label: "Vector Store", ok: safeBool(vh["ready"]), icon: Database },
            ].map(({ label, ok, icon: Icon }) => (
              <Card key={label}>
                <CardContent className="p-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`rounded-lg p-2 ${ok ? "bg-emerald-500/10" : "bg-red-500/10"}`}>
                      <Icon className={`h-5 w-5 ${ok ? "text-emerald-500" : "text-red-500"}`} />
                    </div>
                    <div>
                      <p className="font-medium">{label}</p>
                      <p className="text-xs text-muted-foreground">{ok ? "Running" : "Unavailable"}</p>
                    </div>
                  </div>
                  <Badge variant={ok ? "success" : "destructive"}>{ok ? "Online" : "Offline"}</Badge>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
