"use client"

import { useState, useRef } from "react"
import { useDocuments, useDeleteDocument, useExtractDocument, useAnalyzeDocument, useChunkDocument, useEmbedDocument, useIndexDocument } from "@/hooks/use-documents"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Skeleton } from "@/components/ui/skeleton"
import { FileText, Upload, Trash2, Download, Search, CheckCircle2, Loader2, AlertCircle, FileUp, FileSpreadsheet, FileCode } from "lucide-react"
import { formatDate, formatTime } from "@/lib/utils"
import { motion } from "framer-motion"
import { toast } from "@/components/ui/toast"
import { api } from "@/services/api-client"
import type { Document } from "@/types"

function FileIcon({ type }: { type: string }) {
  const icons: Record<string, React.ElementType> = { pdf: FileText, docx: FileSpreadsheet, txt: FileCode, md: FileCode }
  const Icon = icons[type] || FileText
  return <Icon className="h-5 w-5 text-muted-foreground" />
}

function DocumentCard({ doc, onAction }: { doc: Document; onAction: () => void }) {
  const [processing, setProcessing] = useState<string | null>(null)
  const del = useDeleteDocument()
  const extract = useExtractDocument()
  const analyze = useAnalyzeDocument()
  const chunk = useChunkDocument()
  const embed = useEmbedDocument()
  const index = useIndexDocument()

  async function handleAction(action: string) {
    setProcessing(action)
    try {
      switch (action) {
        case "extract": await extract.mutateAsync(doc.id); break
        case "analyze": await analyze.mutateAsync(doc.id); break
        case "chunk": await chunk.mutateAsync(doc.id); break
        case "embed": await embed.mutateAsync(doc.id); break
        case "index": await index.mutateAsync(doc.id); break
        case "delete": await del.mutateAsync(doc.id); break
      }
      toast({ title: `${action} completed`, variant: "success" })
      onAction()
    } catch {
      toast({ title: `${action} failed`, variant: "destructive" })
    }
    setProcessing(null)
  }

  const steps = ["extract", "analyze", "chunk", "embed", "index"]
  const statusIdx = steps.indexOf(doc.status)
  const progress = Math.max(0, (statusIdx + (doc.status === "uploaded" ? 0 : statusIdx >= 0 ? 1 : 0)) / steps.length * 100)

  return (
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
      <Card>
        <CardContent className="p-4">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-3 min-w-0 flex-1">
              <div className="rounded-lg bg-muted p-2.5 mt-0.5">
                <FileIcon type={doc.file_type} />
              </div>
              <div className="min-w-0 flex-1">
                <p className="font-medium truncate">{doc.filename}</p>
                <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                  <span>{doc.file_type.toUpperCase()}</span>
                  <span>{(doc.size / 1024).toFixed(0)} KB</span>
                  <span>{formatDate(doc.upload_time)}</span>
                </div>
                <Progress value={progress} className="mt-2 h-1.5" />
                <div className="flex items-center gap-1.5 mt-2 flex-wrap">
                  {steps.map((s) => (
                    <Badge key={s} variant={statusIdx >= steps.indexOf(s) ? "success" : "secondary"} className="text-[10px] px-1.5 py-0">
                      {s}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
            <div className="flex gap-1 shrink-0">
              <Button variant="outline" size="sm" onClick={() => handleAction("extract")} disabled={processing !== null} className="h-8 text-xs">
                {processing === "extract" ? <Loader2 className="h-3 w-3 animate-spin" /> : <Download className="h-3 w-3" />}
                Extract
              </Button>
              <Button variant="outline" size="sm" onClick={() => handleAction("chunk")} disabled={processing !== null} className="h-8 text-xs">
                Chunk
              </Button>
              <Button variant="outline" size="sm" onClick={() => handleAction("index")} disabled={processing !== null} className="h-8 text-xs">
                Index
              </Button>
              <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => handleAction("delete")} disabled={processing !== null}>
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}

export default function DocumentsPage() {
  const { data, isLoading, refetch } = useDocuments()
  const [uploading, setUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  async function handleUpload(file: File) {
    setUploading(true)
    try {
      await api.uploadDocument(file)
      toast({ title: "Upload successful", description: file.name, variant: "success" })
      refetch()
    } catch {
      toast({ title: "Upload failed", variant: "destructive" })
    }
    setUploading(false)
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file) handleUpload(file)
  }

  const documents = data?.documents ?? []
  const counts = {
    total: documents.length,
    extracted: documents.filter((d) => d.status !== "uploaded").length,
    indexed: documents.filter((d) => d.status === "indexed" || stepsComplete(d) >= 5).length,
  }

  function stepsComplete(doc: Document) {
    const steps = ["extract", "analyze", "chunk", "embed", "index"]
    return steps.indexOf(doc.status) + 1
  }

  return (
    <div className="p-6 lg:p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <FileText className="h-8 w-8 text-emerald-500" />
            Documents
          </h1>
          <p className="text-muted-foreground">Upload, process, and index documents for knowledge search.</p>
        </div>
        <div className="flex gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.txt,.md"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])}
          />
          <Button onClick={() => fileInputRef.current?.click()} disabled={uploading}>
            {uploading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Upload className="h-4 w-4 mr-2" />}
            Upload
          </Button>
        </div>
      </div>

      <div className="grid gap-4 grid-cols-3">
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold">{counts.total}</p>
            <p className="text-sm text-muted-foreground">Total Documents</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-emerald-500">{counts.extracted}</p>
            <p className="text-sm text-muted-foreground">Extracted</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-blue-500">{counts.indexed}</p>
            <p className="text-sm text-muted-foreground">Indexed</p>
          </CardContent>
        </Card>
      </div>

      <div
        className="border-2 border-dashed rounded-xl p-8 text-center hover:bg-accent/50 transition-colors cursor-pointer"
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <FileUp className="h-10 w-10 mx-auto mb-3 text-muted-foreground" />
        <p className="font-medium">Drag & drop files here</p>
        <p className="text-sm text-muted-foreground mt-1">PDF, DOCX, TXT, MD — up to 20 MB</p>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-28" />)}
        </div>
      ) : documents.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center text-muted-foreground">
            <FileText className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p className="font-medium">No documents uploaded</p>
            <p className="text-sm mt-1">Upload a PDF, DOCX, TXT, or Markdown file to get started.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {documents.map((doc) => (
            <DocumentCard key={doc.id} doc={doc} onAction={refetch} />
          ))}
        </div>
      )}
    </div>
  )
}
