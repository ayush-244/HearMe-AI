import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Search } from "lucide-react"

export default function RetrievalPage() {
  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-3xl">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
          <Search className="h-8 w-8 text-amber-500" />
          Retrieval
        </h1>
        <p className="text-muted-foreground">Search and retrieval diagnostics.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Retrieval Dashboard</CardTitle>
          <CardDescription>Inspect hybrid search queries, scores, and results.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Retrieval inspection tools will be available here.</p>
        </CardContent>
      </Card>
    </div>
  )
}
