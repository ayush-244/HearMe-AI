import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Globe } from "lucide-react"

export default function ApiExplorerPage() {
  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-3xl">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
          <Globe className="h-8 w-8 text-amber-500" />
          API Explorer
        </h1>
        <p className="text-muted-foreground">Explore and test backend API endpoints.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>API Explorer</CardTitle>
          <CardDescription>Browse and invoke backend API endpoints directly.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">API exploration tools will be available here.</p>
        </CardContent>
      </Card>
    </div>
  )
}
