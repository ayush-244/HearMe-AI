import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { PageShell } from "@/components/ui/page-shell"
import { PageHeader } from "@/components/ui/page-header"
import { FEATURE_ACCENTS } from "@/lib/design-tokens"
import { Globe } from "lucide-react"

export default function ApiExplorerPage() {
  return (
    <PageShell maxWidth="narrow">
      <PageHeader title="API Explorer" description="Explore and test backend API endpoints." icon={Globe} iconClassName={FEATURE_ACCENTS.developer} />
      <Card>
        <CardHeader>
          <CardTitle>API Explorer</CardTitle>
          <CardDescription>Browse and invoke backend API endpoints directly.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-body-muted">API exploration tools will be available here.</p>
        </CardContent>
      </Card>
    </PageShell>
  )
}
