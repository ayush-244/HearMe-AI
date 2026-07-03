import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { PageShell } from "@/components/ui/page-shell"
import { PageHeader } from "@/components/ui/page-header"
import { FEATURE_ACCENTS } from "@/lib/design-tokens"
import { HardDrive } from "lucide-react"

export default function VectorStorePage() {
  return (
    <PageShell maxWidth="narrow">
      <PageHeader title="Vector Store" description="Vector database management." icon={HardDrive} iconClassName={FEATURE_ACCENTS.developer} />
      <Card>
        <CardHeader>
          <CardTitle>Vector Store Dashboard</CardTitle>
          <CardDescription>Inspect embeddings, collections, and similarity search.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-body-muted">Vector store management tools will be available here.</p>
        </CardContent>
      </Card>
    </PageShell>
  )
}
