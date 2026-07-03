"use client"

import { useTheme } from "next-themes"
import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Settings, Moon, Sun, Monitor, Globe, Code2, User, Bell, Palette } from "lucide-react"
import { useUiStore } from "@/store/ui-store"
import { useDeveloperStore } from "@/stores/developer-store"
import { Switch } from "@/components/ui/switch"
import { toast } from "@/components/ui/toast"
import { PageShell } from "@/components/ui/page-shell"
import { PageHeader } from "@/components/ui/page-header"
import { motion } from "framer-motion"

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

export default function SettingsPage() {
  const { theme, setTheme } = useTheme()
  const { selectedWorkspace, setSelectedWorkspace } = useUiStore()
  const { developerMode, toggleDeveloperMode } = useDeveloperStore()
  const [workspace, setWorkspace] = useState(selectedWorkspace)

  function handleSave() {
    setSelectedWorkspace(workspace)
    toast({ title: "Settings saved", variant: "success" })
  }

  return (
    <PageShell maxWidth="narrow">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <PageHeader
          title="Settings"
          description="Manage your preferences and configuration."
          icon={Settings}
        />
      </motion.div>

      <Tabs defaultValue="general">
        <TabsList className="w-full justify-start">
          <TabsTrigger value="general" className="gap-2">
            <User className="h-4 w-4" /> General
          </TabsTrigger>
          <TabsTrigger value="appearance" className="gap-2">
            <Palette className="h-4 w-4" /> Appearance
          </TabsTrigger>
          <TabsTrigger value="developer" className="gap-2">
            <Code2 className="h-4 w-4" /> Developer
          </TabsTrigger>
        </TabsList>

        <TabsContent value="general" className="mt-6 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe className="h-5 w-5 text-muted-foreground" />
                Workspace
              </CardTitle>
              <CardDescription>Manage your workspace configuration.</CardDescription>
            </CardHeader>
            <CardContent>
              <SettingRow label="Workspace ID" description="Scope documents and memories to this workspace">
                <Input value={workspace} onChange={(e) => setWorkspace(e.target.value)} />
              </SettingRow>
              <Button onClick={handleSave} className="mt-2">Save Changes</Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5 text-muted-foreground" />
                Notifications
              </CardTitle>
              <CardDescription>Manage your notification preferences.</CardDescription>
            </CardHeader>
            <CardContent>
              <SettingRow label="Upload Notifications" description="Get notified when document processing completes">
                <Switch checked={true} onCheckedChange={() => toast({ title: "Setting saved" })} />
              </SettingRow>
              <Separator />
              <SettingRow label="Memory Updates" description="Notify me when new memories are created">
                <Switch checked={false} onCheckedChange={() => toast({ title: "Setting saved" })} />
              </SettingRow>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="appearance" className="mt-6 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Palette className="h-5 w-5 text-muted-foreground" />
                Appearance
              </CardTitle>
              <CardDescription>Customize how HearMe AI looks.</CardDescription>
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
        </TabsContent>

        <TabsContent value="developer" className="mt-6 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Code2 className="h-5 w-5 text-amber-500" />
                Developer Mode
              </CardTitle>
              <CardDescription>Access developer tools and diagnostics.</CardDescription>
            </CardHeader>
            <CardContent>
              <SettingRow label="Developer Mode" description="Show developer sidebar and tools">
                <div className="flex items-center justify-end gap-3">
                  <span className="text-xs text-muted-foreground">{developerMode ? "ON" : "OFF"}</span>
                  <Switch checked={developerMode} onCheckedChange={toggleDeveloperMode} />
                </div>
              </SettingRow>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </PageShell>
  )
}
