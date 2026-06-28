import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Code2 } from "lucide-react"

export default function DeveloperPage() {
  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-3xl">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
          <Code2 className="h-8 w-8 text-amber-500" />
          Developer
        </h1>
        <p className="text-muted-foreground">Developer tools and diagnostics.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Developer Mode</CardTitle>
          <CardDescription>Access system diagnostics, pipeline monitoring, and developer tools.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Use the developer sidebar to navigate between tools.</p>
        </CardContent>
      </Card>
    </div>
  )
}
