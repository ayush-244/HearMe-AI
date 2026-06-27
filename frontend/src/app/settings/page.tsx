"use client"

import { useTheme } from "next-themes"
import { useEffect, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Settings, Moon, Sun, Monitor, Brain, Database, MessageSquare, Globe, User } from "lucide-react"
import { useUiStore } from "@/store/ui-store"
import { toast } from "@/components/ui/toast"

function SettingRow({ label, description, children }: { label: string; description?: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-4">
      <div className="space-y-0.5">
        <p className="text-sm font-medium">{label}</p>
        {description && <p className="text-xs text-muted-foreground">{description}</p>}
      </div>
      <div className="w-48">{children}</div>
    </div>
  )
}

function SectionHeader({ icon: Icon, title, description }: { icon: React.ElementType; title: string; description?: string }) {
  return (
    <div className="flex items-center gap-3 mb-4">
      <div className="rounded-lg bg-primary/10 p-2">
        <Icon className="h-5 w-5 text-primary" />
      </div>
      <div>
        <h3 className="font-semibold">{title}</h3>
        {description && <p className="text-xs text-muted-foreground">{description}</p>}
      </div>
    </div>
  )
}

export default function SettingsPage() {
  const { theme, setTheme } = useTheme()
  const { selectedWorkspace, setSelectedWorkspace } = useUiStore()
  const [mounted, setMounted] = useState(false)
  const [workspace, setWorkspace] = useState(selectedWorkspace)
  useEffect(() => setMounted(true), [])

  function handleSave() {
    setSelectedWorkspace(workspace)
    toast({ title: "Settings saved", variant: "success" })
  }

  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-3xl">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
          <Settings className="h-8 w-8 text-primary" />
          Settings
        </h1>
        <p className="text-muted-foreground">Configure your HearMe AI experience.</p>
      </div>

      <Card>
        <CardHeader>
          <SectionHeader icon={Monitor} title="Appearance" />
        </CardHeader>
        <CardContent>
          <SettingRow label="Theme" description="Choose your preferred color scheme">
            <div className="flex gap-2">
              {[
                { value: "light", icon: Sun, label: "Light" },
                { value: "dark", icon: Moon, label: "Dark" },
                { value: "system", icon: Monitor, label: "System" },
              ].map(({ value, icon: Icon, label }) => (
                <Button
                  key={value}
                  variant={theme === value ? "default" : "outline"}
                  size="sm"
                  onClick={() => setTheme(value)}
                  className="flex-1"
                >
                  <Icon className="h-4 w-4 mr-1.5" />
                  {label}
                </Button>
              ))}
            </div>
          </SettingRow>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <SectionHeader icon={Globe} title="Workspace" description="Manage your workspace settings" />
        </CardHeader>
        <CardContent>
          <SettingRow label="Workspace ID" description="Scope documents and memories to this workspace">
            <Input value={workspace} onChange={(e) => setWorkspace(e.target.value)} />
          </SettingRow>
          <Button onClick={handleSave} className="mt-4">Save Changes</Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <SectionHeader icon={Brain} title="Knowledge Reasoning" />
        </CardHeader>
        <CardContent>
          <SettingRow label="Search Engine" description="Hybrid semantic + keyword search (configured on backend)">
            <Badge variant="secondary" className="w-full justify-center py-1.5">BM25 + Vector</Badge>
          </SettingRow>
          <Separator />
          <SettingRow label="Reasoning Mode" description="RAG pipeline with citations and guardrails">
            <Badge variant="secondary" className="w-full justify-center py-1.5">Active</Badge>
          </SettingRow>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <SectionHeader icon={Database} title="Memory System" />
        </CardHeader>
        <CardContent>
          <SettingRow label="Memory Storage" description="Persisted to JSON files">
            <Badge variant="secondary" className="w-full justify-center py-1.5">Active</Badge>
          </SettingRow>
          <Separator />
          <SettingRow label="Consolidation" description="Automatic merging of related memories">
            <Badge variant="secondary" className="w-full justify-center py-1.5">Manual</Badge>
          </SettingRow>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <SectionHeader icon={MessageSquare} title="About" />
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p><strong>HearMe AI</strong> v1.0.0</p>
          <p>AI-powered knowledge platform with sentiment analysis, hybrid search, knowledge reasoning, and long-term memory.</p>
          <p>Backend: FastAPI &bull; Frontend: Next.js 15 &bull; AI: Groq LLM + Sentence Transformers</p>
        </CardContent>
      </Card>
    </div>
  )
}
