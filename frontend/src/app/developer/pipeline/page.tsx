import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { GitBranch } from "lucide-react"

export default function PipelinePage() {
  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-3xl">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
          <GitBranch className="h-8 w-8 text-amber-500" />
          Pipeline
        </h1>
        <p className="text-muted-foreground">Document processing pipeline monitoring.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Pipeline Monitor</CardTitle>
          <CardDescription>Track document extraction, chunking, embedding, and indexing.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Pipeline visualization and monitoring will be available here.</p>
        </CardContent>
      </Card>
    </div>
  )
}
