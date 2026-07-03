import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { PageShell } from "@/components/ui/page-shell"
import { PageHeader } from "@/components/ui/page-header"
import { FEATURE_ACCENTS } from "@/lib/design-tokens"
import { GitBranch } from "lucide-react"

export default function PipelinePage() {
  return (
    <PageShell maxWidth="narrow">
      <PageHeader title="Pipeline" description="Document processing pipeline monitoring." icon={GitBranch} iconClassName={FEATURE_ACCENTS.developer} />
      <Card>
        <CardHeader>
          <CardTitle>Pipeline Monitor</CardTitle>
          <CardDescription>Track document extraction, chunking, embedding, and indexing.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-body-muted">Pipeline visualization and monitoring will be available here.</p>
        </CardContent>
      </Card>
    </PageShell>
  )
}
