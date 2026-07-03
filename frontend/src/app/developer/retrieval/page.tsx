import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { PageShell } from "@/components/ui/page-shell"
import { PageHeader } from "@/components/ui/page-header"
import { FEATURE_ACCENTS } from "@/lib/design-tokens"
import { Search } from "lucide-react"

export default function RetrievalPage() {
  return (
    <PageShell maxWidth="narrow">
      <PageHeader title="Retrieval" description="Search and retrieval diagnostics." icon={Search} iconClassName={FEATURE_ACCENTS.developer} />
      <Card>
        <CardHeader>
          <CardTitle>Retrieval Dashboard</CardTitle>
          <CardDescription>Inspect hybrid search queries, scores, and results.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-body-muted">Retrieval inspection tools will be available here.</p>
        </CardContent>
      </Card>
    </PageShell>
  )
}
