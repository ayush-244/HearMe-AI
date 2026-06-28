import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { HardDrive } from "lucide-react"

export default function VectorStorePage() {
  return (
    <div className="p-6 lg:p-8 space-y-6 max-w-3xl">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
          <HardDrive className="h-8 w-8 text-amber-500" />
          Vector Store
        </h1>
        <p className="text-muted-foreground">Vector database management.</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Vector Store Dashboard</CardTitle>
          <CardDescription>Inspect embeddings, collections, and similarity search.</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">Vector store management tools will be available here.</p>
        </CardContent>
      </Card>
    </div>
  )
}
