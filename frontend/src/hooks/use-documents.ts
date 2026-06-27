import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/services/api-client"

export function useDocuments() {
  return useQuery({ queryKey: ["documents"], queryFn: () => api.getDocuments() })
}

export function useDocument(id: string) {
  return useQuery({ queryKey: ["document", id], queryFn: () => api.getDocument(id), enabled: !!id })
}

export function useDeleteDocument() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: (id: string) => api.deleteDocument(id), onSuccess: () => qc.invalidateQueries({ queryKey: ["documents"] }) })
}

export function useExtractDocument() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: (id: string) => api.extractDocument(id), onSuccess: () => qc.invalidateQueries({ queryKey: ["document"] }) })
}

export function useAnalyzeDocument() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: (id: string) => api.analyzeDocument(id), onSuccess: () => qc.invalidateQueries({ queryKey: ["document"] }) })
}

export function useChunkDocument() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: (id: string) => api.chunkDocument(id), onSuccess: () => qc.invalidateQueries({ queryKey: ["document"] }) })
}

export function useEmbedDocument() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: (id: string) => api.embedDocument(id), onSuccess: () => qc.invalidateQueries({ queryKey: ["document"] }) })
}

export function useIndexDocument() {
  const qc = useQueryClient()
  return useMutation({ mutationFn: (id: string) => api.indexDocument(id), onSuccess: () => qc.invalidateQueries({ queryKey: ["document"] }) })
}
