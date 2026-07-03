import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { PageShell } from "@/components/ui/page-shell"
import { PageHeader } from "@/components/ui/page-header"
import { FEATURE_ACCENTS } from "@/lib/design-tokens"
import { FileCode } from "lucide-react"

export default function PromptsPage() {
  return (
    <PageShell maxWidth="narrow">
      <PageHeader title="Prompt Inspector" description="Inspect and debug LLM prompts." icon={FileCode} iconClassName={FEATURE_ACCENTS.developer} />
      <Card>
        <CardHeader>
          <CardTitle>Prompt Inspector</CardTitle>
          <CardDescription>View prompts sent to the LLM, including context and templates.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-body-muted">Prompt inspection tools will be available here.</p>
        </CardContent>
      </Card>
    </PageShell>
  )
}
