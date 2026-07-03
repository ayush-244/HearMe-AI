"use client"

import { useState, useRef, useMemo, memo, useCallback } from "react"
import { useDocuments, useDeleteDocument } from "@/hooks/use-documents"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Input } from "@/components/ui/input"
import {
  FileText,
  Upload,
  Trash2,
  Search,
  Loader2,
  FileUp,
  LayoutGrid,
  List,
  FileSpreadsheet,
  FileCode,
  Clock,
  CheckCircle2,
  RefreshCw,
  AlertCircle,
  BookOpen,
  ExternalLink,
} from "lucide-react"
import { formatDate } from "@/lib/utils"
import { motion, AnimatePresence } from "framer-motion"
import { toast } from "@/components/ui/toast"
import { api } from "@/services/api-client"
import { useDeveloperStore } from "@/stores/developer-store"
import type { Document } from "@/types"
import Link from "next/link"
import { PageShell } from "@/components/ui/page-shell"
import { PageHeader } from "@/components/ui/page-header"
import { FEATURE_ACCENTS } from "@/lib/design-tokens"

const FileIcon = memo(function FileIcon({ type }: { type: string }) {
  const icons: Record<string, React.ElementType> = { pdf: FileText, docx: FileSpreadsheet, txt: FileCode, md: FileCode }
  const Icon = icons[type] || FileText
  return <Icon className="h-5 w-5 text-muted-foreground" />
})

const DocumentCard = memo(function DocumentCard({
  doc,
  onDelete,
}: {
  doc: Document
  onDelete: (id: string) => void
}) {
  const [deleting, setDeleting] = useState(false)
  const developerMode = useDeveloperStore((s) => s.developerMode)

  const isReady = doc.status === "indexed"
  const isFailed = doc.status === "failed"
  const isProcessing = !isReady && !isFailed && doc.status !== "uploaded"

  const handleDelete = useCallback(async () => {
    setDeleting(true)
    try {
      await onDelete(doc.id)
      toast({ title: "Document deleted", variant: "success" })
    } catch {
      toast({ title: "Delete failed", variant: "destructive" })
    }
    setDeleting(false)
  }, [doc.id, onDelete])

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.2 }}
    >
      <Card className="group relative transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <div className="icon-container">
              <FileIcon type={doc.file_type} />
            </div>
            <div className="min-w-0 flex-1">
              <p className="font-medium text-sm truncate">{doc.filename}</p>
              <div className="flex items-center gap-3 mt-1.5 text-xs text-muted-foreground">
                <span className="uppercase">{doc.file_type}</span>
                <span>{(doc.size / 1024).toFixed(0)} KB</span>
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {formatDate(doc.upload_time)}
                </span>
              </div>
              <div className="mt-2">
                {isReady ? (
                  <Badge variant="secondary" className="text-emerald-500 bg-emerald-500/10 border-0 text-[11px]">
                    <CheckCircle2 className="h-3 w-3 mr-1" />
                    Ready
                  </Badge>
                ) : isFailed ? (
                  <Badge variant="secondary" className="text-red-500 bg-red-500/10 border-0 text-[11px]">
                    <AlertCircle className="h-3 w-3 mr-1" />
                    Failed
                  </Badge>
                ) : isProcessing ? (
                  <Badge variant="secondary" className="text-blue-500 bg-blue-500/10 border-0 text-[11px]">
                    <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                    Processing
                  </Badge>
                ) : (
                  <Badge variant="secondary" className="text-amber-500 bg-amber-500/10 border-0 text-[11px]">
                    Pending
                  </Badge>
                )}
                {isFailed && developerMode && doc.failed_stage && (
                  <span className="text-[10px] text-red-400 ml-2">Failed at: {doc.failed_stage}</span>
                )}
              </div>
            </div>
            <div className="flex items-center gap-1 shrink-0">
              {isReady && (
                <Button variant="ghost" size="icon" className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity" asChild>
                  <Link href={`/chat?doc=${doc.id}`} title="Open in chat">
                    <ExternalLink className="h-4 w-4" />
                  </Link>
                </Button>
              )}
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={handleDelete}
                disabled={deleting}
              >
                {deleting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4 text-destructive" />}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
})

export default function LibraryPage() {
  const { data, isLoading, refetch } = useDocuments()
  const deleteDoc = useDeleteDocument()
  const [uploading, setUploading] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid")
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isDragOver, setIsDragOver] = useState(false)

  const documents = useMemo(() => {
    const docs = data?.documents ?? []
    if (!searchQuery.trim()) return docs
    const q = searchQuery.toLowerCase()
    return docs.filter((d) => d.filename.toLowerCase().includes(q))
  }, [data, searchQuery])

  const counts = useMemo(() => ({
    total: data?.documents?.length ?? 0,
    indexed: data?.documents?.filter((d) => d.status === "indexed").length ?? 0,
    failed: data?.documents?.filter((d) => d.status === "failed").length ?? 0,
  }), [data])

  const runPipeline = useCallback(async (docId: string) => {
    const stages = ["extract", "analyze", "chunk", "embed", "index"]
    for (const stage of stages) {
      try {
        switch (stage) {
          case "extract": await api.extractDocument(docId); break
          case "analyze": await api.analyzeDocument(docId); break
          case "chunk": await api.chunkDocument(docId); break
          case "embed": await api.embedDocument(docId); break
          case "index": await api.indexDocument(docId); break
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Processing failed"
        toast({ title: `Pipeline failed at ${stage}`, variant: "destructive", description: msg })
        refetch()
        return
      }
    }
    refetch()
    toast({ title: "Document processed", variant: "success" })
  }, [refetch])

  const handleUpload = useCallback(async (file: File) => {
    setUploading(true)
    try {
      const result = await api.uploadDocument(file) as { document_id: string }
      const docId = result.document_id
      refetch()
      toast({ title: "Uploaded", description: "Processing document..." })
      await runPipeline(docId)
    } catch {
      toast({ title: "Upload failed", variant: "destructive" })
    }
    setUploading(false)
    if (fileInputRef.current) {
      fileInputRef.current.value = ""
    }
  }, [refetch, runPipeline])

  const handleDelete = useCallback(async (id: string) => {
    await deleteDoc.mutateAsync(id)
    refetch()
  }, [deleteDoc, refetch])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleUpload(file)
  }, [handleUpload])

  return (
    <PageShell maxWidth="full">
      <div className="flex items-center justify-between">
        <PageHeader
          title="Library"
          description="Your document collection — uploaded and ready to search."
          icon={BookOpen}
          iconClassName={FEATURE_ACCENTS.library}
        />
        <div className="flex items-center gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.txt,.md"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && handleUpload(e.target.files[0])}
          />
          <Button
            onClick={() => setViewMode(viewMode === "grid" ? "list" : "grid")}
            variant="outline"
            size="icon"
            className="h-9 w-9"
          >
            {viewMode === "grid" ? <List className="h-4 w-4" /> : <LayoutGrid className="h-4 w-4" />}
          </Button>
          <Button onClick={() => fileInputRef.current?.click()} disabled={uploading}>
            {uploading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Upload className="h-4 w-4 mr-2" />}
            Upload
          </Button>
        </div>
      </div>

      <div className="grid gap-4 grid-cols-3">
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-semibold text-emerald-400">{counts.total}</p>
            <p className="text-caption mt-1">Total Documents</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-semibold text-emerald-400">{counts.indexed}</p>
            <p className="text-caption mt-1">Indexed</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-semibold text-amber-400">{documents.filter((d) => d.status !== "indexed" && d.status !== "failed").length}</p>
            <p className="text-caption mt-1">Processing</p>
          </CardContent>
        </Card>
      </div>

      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search documents..."
            className="pl-9 h-10"
          />
        </div>
        <Button variant="outline" size="icon" className="h-10 w-10" onClick={() => refetch()}>
          <RefreshCw className="h-4 w-4" />
        </Button>
      </div>

      <div
        className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 cursor-pointer ${
          isDragOver
            ? "border-primary bg-primary/5 scale-[1.01]"
            : "border-muted-foreground/25 hover:border-muted-foreground/50 hover:bg-accent/50"
        }`}
        onDragOver={(e) => { e.preventDefault(); setIsDragOver(true) }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <div className={`transition-transform duration-200 ${isDragOver ? "scale-110" : ""}`}>
          <FileUp className={`h-10 w-10 mx-auto mb-3 ${isDragOver ? "text-primary" : "text-muted-foreground"}`} />
          <p className="font-medium">{isDragOver ? "Drop file here" : "Drag & drop files here"}</p>
          <p className="text-sm text-muted-foreground mt-1">PDF, DOCX, TXT, MD — up to 20 MB</p>
        </div>
      </div>

      {isLoading ? (
        <div className={viewMode === "grid" ? "grid gap-4 md:grid-cols-2 lg:grid-cols-3" : "space-y-2"}>
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className={viewMode === "grid" ? "h-28" : "h-14"} />
          ))}
        </div>
      ) : documents.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center text-muted-foreground">
            <BookOpen className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p className="font-medium">
              {searchQuery ? "No matching documents" : "Your library is empty"}
            </p>
            <p className="text-sm mt-1">
              {searchQuery ? "Try a different search term." : "Upload a PDF, DOCX, TXT, or Markdown file to get started."}
            </p>
          </CardContent>
        </Card>
      ) : (
        <AnimatePresence mode="popLayout">
          {viewMode === "grid" ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {documents.map((doc) => (
                <DocumentCard
                  key={doc.id}
                  doc={doc}
                  onDelete={handleDelete}
                />
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="p-2">
                {documents.map((doc, i) => (
                  <div key={doc.id}>
                    {i > 0 && <div className="mx-3 border-t" />}
                    <div className="flex items-center gap-4 p-3 rounded-lg hover:bg-accent/50 transition-all duration-200 group">
                      <div className="icon-container !p-2">
                        <FileIcon type={doc.file_type} />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium truncate">{doc.filename}</p>
                        <p className="text-xs text-muted-foreground">{formatDate(doc.upload_time)}</p>
                      </div>
                      <Badge variant="secondary" className={`${
                        doc.status === "indexed" ? "text-emerald-500 bg-emerald-500/10" :
                        doc.status === "failed" ? "text-red-500 bg-red-500/10" :
                        "text-blue-500 bg-blue-500/10"
                      } border-0 text-[11px] shrink-0`}>
                        {doc.status === "indexed" ? "Ready" : doc.status === "failed" ? "Failed" : "Processing"}
                      </Badge>
                      <span className="text-xs text-muted-foreground shrink-0">{(doc.size / 1024).toFixed(0)} KB</span>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
                        onClick={() => handleDelete(doc.id)}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </AnimatePresence>
      )}
    </PageShell>
  )
}
