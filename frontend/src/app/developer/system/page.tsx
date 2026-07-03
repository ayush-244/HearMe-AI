import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { PageShell } from "@/components/ui/page-shell"
import { PageHeader } from "@/components/ui/page-header"
import { FEATURE_ACCENTS } from "@/lib/design-tokens"
import { Cpu } from "lucide-react"

export default function SystemPage() {
  return (
    <PageShell maxWidth="narrow">
      <PageHeader
        title="System"
        description="System diagnostics and health monitoring."
        icon={Cpu}
        iconClassName={FEATURE_ACCENTS.developer}
      />

      <Card>
        <CardHeader>
          <CardTitle>System Overview</CardTitle>
          <CardDescription>Server health, resource usage, and service status.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-body-muted">System monitoring dashboard will be available here.</p>
        </CardContent>
      </Card>
    </PageShell>
  )
}
