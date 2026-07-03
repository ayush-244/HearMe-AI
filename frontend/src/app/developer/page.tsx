import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { PageShell } from "@/components/ui/page-shell"
import { PageHeader } from "@/components/ui/page-header"
import { FEATURE_ACCENTS } from "@/lib/design-tokens"
import { Code2 } from "lucide-react"

export default function DeveloperPage() {
  return (
    <PageShell maxWidth="narrow">
      <PageHeader
        title="Developer"
        description="Developer tools and diagnostics."
        icon={Code2}
        iconClassName={FEATURE_ACCENTS.developer}
      />

      <Card>
        <CardHeader>
          <CardTitle>Developer Mode</CardTitle>
          <CardDescription>Access system diagnostics, pipeline monitoring, and developer tools.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-body-muted">Use the developer sidebar to navigate between tools.</p>
        </CardContent>
      </Card>
    </PageShell>
  )
}
