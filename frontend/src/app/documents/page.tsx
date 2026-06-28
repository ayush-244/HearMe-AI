"use client"

import { useState, useRef, useMemo, memo, useCallback } from "react"
import { useDocuments, useDeleteDocument, useExtractDocument, useAnalyzeDocument, useChunkDocument, useEmbedDocument, useIndexDocument } from "@/hooks/use-documents"
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
} from "lucide-react"
import { formatDate } from "@/lib/utils"
import { motion, AnimatePresence } from "framer-motion"
import { toast } from "@/components/ui/toast"
import { api } from "@/services/api-client"
import type { Document } from "@/types"

const FileIcon = memo(function FileIcon({ type }: { type: string }) {
  const icons: Record<string, React.ElementType> = { pdf: FileText, docx: FileSpreadsheet, txt: FileCode, md: FileCode }
  const Icon = icons[type] || FileText
  return <Icon className="h-5 w-5 text-muted-foreground" />
})

const statusConfig: Record<string, { label: string; color: string; bg: string }> = {
  uploaded: { label: "Uploaded", color: "text-amber-500", bg: "bg-amber-500/10" },
  extracted: { label: "Extracted", color: "text-blue-500", bg: "bg-blue-500/10" },
  analyzed: { label: "Analyzed", color: "text-purple-500", bg: "bg-purple-500/10" },
  chunked: { label: "Chunked", color: "text-cyan-500", bg: "bg-cyan-500/10" },
  embedded: { label: "Embedded", color: "text-indigo-500", bg: "bg-indigo-500/10" },
  indexed: { label: "Indexed", color: "text-emerald-500", bg: "bg-emerald-500/10" },
}

const pipelineActions: Record<string, { label: string; nextStatus: string }> = {
  uploaded: { label: "Extract", nextStatus: "extracted" },
  extracted: { label: "Analyze", nextStatus: "analyzed" },
  analyzed: { label: "Chunk", nextStatus: "chunked" },
  chunked: { label: "Embed", nextStatus: "embedded" },
  embedded: { label: "Index", nextStatus: "indexed" },
}

const DocumentCard = memo(function DocumentCard({ doc, onDelete, onProcess }: { doc: Document; onDelete: (id: string) => void; onProcess: (id: string, status: string) => void }) {
  const [deleting, setDeleting] = useState(false)
  const [processing, setProcessing] = useState(false)

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

  const status = statusConfig[doc.status] || statusConfig.uploaded
  const nextAction = pipelineActions[doc.status]
  const isIndexed = doc.status === "indexed"

  const handleProcess = useCallback(async () => {
    if (!nextAction) return
    setProcessing(true)
    try {
      await onProcess(doc.id, nextAction.nextStatus)
      toast({ title: `${nextAction.label} successful`, variant: "success" })
    } catch {
      toast({ title: `${nextAction.label} failed`, variant: "destructive" })
    }
    setProcessing(false)
  }, [doc.id, nextAction, onProcess])

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.2 }}
    >
      <Card className="group relative border-0 shadow-sm hover:shadow-md transition-all duration-200">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <div className={`rounded-xl p-3 ${status.bg}`}>
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
              <div className="mt-2 flex items-center gap-2">
                <Badge variant="secondary" className={`${status.color} ${status.bg} border-0 text-[11px]`}>
                  <CheckCircle2 className="h-3 w-3 mr-1" />
                  {status.label}
                </Badge>
                {nextAction && !isIndexed && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="h-6 text-[11px] px-2"
                    onClick={handleProcess}
                    disabled={processing}
                  >
                    {processing ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : <RefreshCw className="h-3 w-3 mr-1" />}
                    {nextAction.label}
                  </Button>
                )}
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
              onClick={handleDelete}
              disabled={deleting}
            >
              {deleting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4 text-destructive" />}
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
})

const DocumentRow = memo(function DocumentRow({ doc, onDelete, onProcess }: { doc: Document; onDelete: (id: string) => void; onProcess: (id: string, status: string) => void }) {
  const [deleting, setDeleting] = useState(false)
  const [processing, setProcessing] = useState(false)

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

  const status = statusConfig[doc.status] || statusConfig.uploaded
  const nextAction = pipelineActions[doc.status]
  const isIndexed = doc.status === "indexed"

  const handleProcess = useCallback(async () => {
    if (!nextAction) return
    setProcessing(true)
    try {
      await onProcess(doc.id, nextAction.nextStatus)
      toast({ title: `${nextAction.label} successful`, variant: "success" })
    } catch {
      toast({ title: `${nextAction.label} failed`, variant: "destructive" })
    }
    setProcessing(false)
  }, [doc.id, nextAction, onProcess])

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -10 }}
    >
      <div className="flex items-center gap-4 p-3 rounded-lg hover:bg-accent/50 transition-colors group">
        <div className={`rounded-lg p-2 ${status.bg}`}>
          <FileIcon type={doc.file_type} />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium truncate">{doc.filename}</p>
          <p className="text-xs text-muted-foreground">{formatDate(doc.upload_time)}</p>
        </div>
        <Badge variant="secondary" className={`${status.color} ${status.bg} border-0 text-[11px] shrink-0`}>
          {status.label}
        </Badge>
        {nextAction && !isIndexed && (
          <Button
            variant="outline"
            size="sm"
            className="h-7 text-[11px] px-2 shrink-0"
            onClick={handleProcess}
            disabled={processing}
          >
            {processing ? <Loader2 className="h-3 w-3 mr-1 animate-spin" /> : <RefreshCw className="h-3 w-3 mr-1" />}
            {nextAction.label}
          </Button>
        )}
        <span className="text-xs text-muted-foreground shrink-0">{(doc.size / 1024).toFixed(0)} KB</span>
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
          onClick={handleDelete}
          disabled={deleting}
        >
          {deleting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4 text-destructive" />}
        </Button>
      </div>
    </motion.div>
  )
})

export default function DocumentsPage() {
  const { data, isLoading, refetch } = useDocuments()
  const deleteDoc = useDeleteDocument()
  const extractDoc = useExtractDocument()
  const analyzeDoc = useAnalyzeDocument()
  const chunkDoc = useChunkDocument()
  const embedDoc = useEmbedDocument()
  const indexDoc = useIndexDocument()
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
    processing: data?.documents?.filter((d) => d.status !== "indexed" && d.status !== "uploaded").length ?? 0,
  }), [data])

  const handleUpload = useCallback(async (file: File) => {
    setUploading(true)
    try {
      await api.uploadDocument(file)
      toast({ title: "Upload successful", description: file.name, variant: "success" })
      refetch()
    } catch {
      toast({ title: "Upload failed", variant: "destructive" })
    }
    setUploading(false)
  }, [refetch])

  const handleDelete = useCallback(async (id: string) => {
    await deleteDoc.mutateAsync(id)
    refetch()
  }, [deleteDoc, refetch])

  const handleProcess = useCallback(async (id: string, nextStatus: string) => {
    switch (nextStatus) {
      case "extracted": await extractDoc.mutateAsync(id); break
      case "analyzed": await analyzeDoc.mutateAsync(id); break
      case "chunked": await chunkDoc.mutateAsync(id); break
      case "embedded": await embedDoc.mutateAsync(id); break
      case "indexed": await indexDoc.mutateAsync(id); break
    }
    refetch()
  }, [extractDoc, analyzeDoc, chunkDoc, embedDoc, indexDoc, refetch])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleUpload(file)
  }, [handleUpload])

  return (
    <div className="p-6 lg:p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <FileText className="h-8 w-8 text-emerald-500" />
            Documents
          </h1>
          <p className="text-muted-foreground">Upload and manage your documents.</p>
        </div>
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
        <Card className="border-0 shadow-sm bg-gradient-to-br from-emerald-500/5 to-transparent">
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-emerald-500">{counts.total}</p>
            <p className="text-xs text-muted-foreground mt-1">Total Documents</p>
          </CardContent>
        </Card>
        <Card className="border-0 shadow-sm bg-gradient-to-br from-blue-500/5 to-transparent">
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-blue-500">{counts.indexed}</p>
            <p className="text-xs text-muted-foreground mt-1">Indexed</p>
          </CardContent>
        </Card>
        <Card className="border-0 shadow-sm bg-gradient-to-br from-amber-500/5 to-transparent">
          <CardContent className="p-4 text-center">
            <p className="text-2xl font-bold text-amber-500">{counts.processing}</p>
            <p className="text-xs text-muted-foreground mt-1">Processing</p>
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
        <Card className="border-0 shadow-sm">
          <CardContent className="p-12 text-center text-muted-foreground">
            <FileText className="h-12 w-12 mx-auto mb-3 opacity-50" />
            <p className="font-medium">
              {searchQuery ? "No matching documents" : "No documents uploaded"}
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
                <DocumentCard key={doc.id} doc={doc} onDelete={handleDelete} onProcess={handleProcess} />
              ))}
            </div>
          ) : (
            <Card className="border-0 shadow-sm">
              <CardContent className="p-2">
                {documents.map((doc, i) => (
                  <div key={doc.id}>
                    {i > 0 && <div className="mx-3 border-t" />}
                    <DocumentRow doc={doc} onDelete={handleDelete} onProcess={handleProcess} />
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </AnimatePresence>
      )}
    </div>
  )
}
