import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Cpu } from "lucide-react"

export default function SystemPage() {
  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-3xl">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
          <Cpu className="h-8 w-8 text-amber-500" />
          System
        </h1>
        <p className="text-muted-foreground">System diagnostics and health monitoring.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>System Overview</CardTitle>
          <CardDescription>Server health, resource usage, and service status.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">System monitoring dashboard will be available here.</p>
        </CardContent>
      </Card>
    </div>
  )
}
